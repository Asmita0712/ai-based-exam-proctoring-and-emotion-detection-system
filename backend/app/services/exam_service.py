"""
Persistent Examination Service backed by SQLAlchemy / PostgreSQL.
Implements:
- Open-access student attempt initialization with signed JWT tokens
- Server-authoritative timer enforcement (started_at / ends_at)
- Idempotent answer autosave
- Transaction-safe answer grading and proctoring report pairing
- High-concurrency aggregate analytics for teacher dashboards
"""
from datetime import datetime, timedelta, timezone
import json
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.security import create_attempt_token
from app.db.models import (
    Exam,
    ExamAttempt,
    ProctoringEvent,
    ProctoringSession,
    Question,
    StudentAnswer,
    User,
)
from app.schemas.exam import (
    AnswerAutosaveRequest,
    AnswerAutosaveResponse,
    ExamCreateRequest,
    ExamPublicSummary,
    ExamResponse,
    ExamStartRequest,
    ExamStartResponse,
    ExamStudentView,
    ExamSubmitRequest,
    ExamSummaryItem,
    Question as QuestionSchema,
    QuestionStudentView,
    SubmissionReport,
    SystemAnalyticsResponse,
    TeacherDashboardResponse,
)
from app.services import proctoring_service


def _utc_now():
    return datetime.now(timezone.utc)


def _normalize_dt(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def create_exam(request: ExamCreateRequest, teacher_id: Optional[str], db: Session) -> ExamResponse:
    """Creates an examination and its questions in PostgreSQL within a single atomic transaction."""
    exam_id = f"exam-{uuid.uuid4().hex[:8]}"
    exam = Exam(
        id=exam_id,
        title=request.title,
        description=request.description or "",
        duration_minutes=request.duration_minutes,
        instructions=request.instructions or "",
        access_code=request.access_code or None,
        is_published=request.is_published,
        teacher_id=teacher_id,
    )
    db.add(exam)
    db.flush()

    for idx, q_data in enumerate(request.questions):
        q = Question(
            id=f"q-{uuid.uuid4().hex[:8]}",
            exam_id=exam_id,
            question_text=q_data.question_text,
            options_json=json.dumps(q_data.options),
            correct_option_index=q_data.correct_option_index,
            points=q_data.points,
            order=idx,
        )
        db.add(q)

    db.commit()
    db.refresh(exam)
    return _build_exam_response(exam)


def list_public_exams(published_only: bool, db: Session) -> List[ExamPublicSummary]:
    """
    Retrieves examinations for the public student lobby, omitting questions and answer keys.
    SECURITY BOUNDARY: Prevents any leakage of questions, options, or answer keys to unauthenticated callers.
    """
    query = db.query(Exam)
    if published_only:
        query = query.filter(Exam.is_published == True)
    
    exams = query.order_by(Exam.created_at.desc()).all()
    results = []
    for e in exams:
        tot_pts = sum(q.points for q in e.questions)
        results.append(
            ExamPublicSummary(
                id=e.id,
                title=e.title,
                description=e.description or "",
                instructions=e.instructions or "",
                duration_minutes=e.duration_minutes,
                is_published=e.is_published,
                has_access_code=bool(e.access_code),
                questions_count=len(e.questions),
                total_points=tot_pts,
                created_at=e.created_at.strftime("%Y-%m-%d"),
            )
        )
    return results


def list_exams(published_only: bool, db: Session) -> List[ExamResponse]:
    """Retrieves all examinations from the database with eager question counting."""
    query = db.query(Exam)
    if published_only:
        query = query.filter(Exam.is_published == True)
    
    exams = query.order_by(Exam.created_at.desc()).all()
    return [_build_exam_response(e) for e in exams]


def get_exam_for_student(exam_id: str, db: Session) -> Optional[ExamStudentView]:
    """
    Returns student view of an exam.
    SECURITY BOUNDARY: Strips correct_option_index from all questions.
    """
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        return None

    clean_questions = [
        QuestionStudentView(
            id=q.id,
            question_text=q.question_text,
            options=q.options,
            points=q.points,
        )
        for q in exam.questions
    ]

    total_points = sum(q.points for q in exam.questions)
    return ExamStudentView(
        id=exam.id,
        title=exam.title,
        description=exam.description or "",
        instructions=exam.instructions or "",
        duration_minutes=exam.duration_minutes,
        is_published=exam.is_published,
        has_access_code=bool(exam.access_code),
        questions=clean_questions,
        total_points=total_points,
    )


def get_exam_for_teacher(exam_id: str, db: Session) -> Optional[ExamResponse]:
    """Returns complete exam with answer keys for authorized teacher inspection."""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        return None
    return _build_exam_response(exam)


def toggle_publish(exam_id: str, is_published: bool, db: Session) -> Optional[ExamResponse]:
    """Toggles examination published status in the database."""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        return None
    exam.is_published = is_published
    db.commit()
    db.refresh(exam)
    return _build_exam_response(exam)


def start_exam_attempt(
    exam_id: str,
    request: ExamStartRequest,
    db: Session,
) -> Optional[ExamStartResponse]:
    """
    Open-access student attempt initialization.
    Validates exam availability and access code, initializes server-authoritative
    timer (started_at and ends_at), provisions proctoring session, and signs attempt JWT.
    """
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam or not exam.is_published:
        return None

    # Check access code if required
    if exam.access_code:
        if not request.access_code or request.access_code.strip() != exam.access_code.strip():
            return None

    now = _utc_now()
    ends_at = now + timedelta(minutes=exam.duration_minutes)

    attempt_id = f"att-{uuid.uuid4().hex[:12]}"
    session_id = f"sess-{uuid.uuid4().hex[:12]}"

    attempt = ExamAttempt(
        id=attempt_id,
        exam_id=exam_id,
        student_name=request.student_name.strip(),
        student_id=request.student_id.strip(),
        started_at=now,
        ends_at=ends_at,
        is_submitted=False,
    )
    db.add(attempt)

    # Initialize associated proctoring session
    proc_session = ProctoringSession(
        id=session_id,
        attempt_id=attempt_id,
        exam_id=exam_id,
        started_at=now,
        total_frames_analyzed=0,
        flagged_frames_count=0,
        integrity_score=100.0,
        verdict="VERIFIED_CLEAN",
        verdict_label="Clean Exam Conduct",
        verdict_color="#34d399",
    )
    db.add(proc_session)
    db.commit()

    token = create_attempt_token(
        attempt_id=attempt_id,
        exam_id=exam_id,
        student_id=request.student_id.strip(),
        expires_minutes=exam.duration_minutes + 15,
    )

    student_view = get_exam_for_student(exam_id, db)
    remaining_secs = max(0, int((ends_at - now).total_seconds()))

    return ExamStartResponse(
        attempt_id=attempt_id,
        attempt_token=token,
        session_id=session_id,
        exam=student_view,
        started_at=now.isoformat(),
        ends_at=ends_at.isoformat(),
        remaining_seconds=remaining_secs,
    )


def autosave_answer(
    attempt: ExamAttempt,
    request: AnswerAutosaveRequest,
    db: Session,
) -> AnswerAutosaveResponse:
    """
    Idempotent upsert of a student's answer choice during an active examination.
    Enforces server-authoritative timer: rejects modifications if now > ends_at.
    """
    now = _utc_now()
    if attempt.is_submitted:
        raise ValueError("Cannot modify answers for an already submitted examination.")

    ends_at = _normalize_dt(attempt.ends_at)
    remaining_secs = max(0, int((ends_at - now).total_seconds())) if ends_at else 0
    if remaining_secs <= 0:
        raise ValueError("Examination time has expired.")

    # Upsert answer record
    existing = (
        db.query(StudentAnswer)
        .filter(
            StudentAnswer.attempt_id == attempt.id,
            StudentAnswer.question_id == request.question_id,
        )
        .first()
    )

    if existing:
        existing.selected_option = request.selected_option
        existing.updated_at = now
    else:
        new_ans = StudentAnswer(
            attempt_id=attempt.id,
            question_id=request.question_id,
            selected_option=request.selected_option,
            updated_at=now,
        )
        db.add(new_ans)

    db.commit()
    return AnswerAutosaveResponse(
        success=True,
        question_id=request.question_id,
        selected_option=request.selected_option,
        saved_at=now.isoformat(),
        remaining_seconds=remaining_secs,
    )


def submit_exam(
    exam_id: str,
    request: ExamSubmitRequest,
    db: Session,
    attempt: Optional[ExamAttempt] = None,
) -> Optional[SubmissionReport]:
    """
    Finalizes and grades an examination attempt in a single ACID transaction.
    Grades submitted answers against canonical correct_option_index,
    computes percentage score, retrieves AI proctoring summary, and records report.
    """
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        return None

    now = _utc_now()

    # If attempt was not passed in via token, look up active or matching attempt
    if not attempt:
        attempt = (
            db.query(ExamAttempt)
            .filter(
                ExamAttempt.exam_id == exam_id,
                ExamAttempt.student_id == request.student_id,
                ExamAttempt.is_submitted == False,
            )
            .order_by(ExamAttempt.started_at.desc())
            .first()
        )

    # 1. Grade the questions
    earned_score = 0
    total_points = 0
    question_results = []

    # Map question_id -> Question
    q_map = {q.id: q for q in exam.questions}

    # Record or update answers from submission request
    for q in exam.questions:
        total_points += q.points
        user_choice = request.answers.get(q.id)
        is_correct = (user_choice is not None) and (user_choice == q.correct_option_index)

        if is_correct:
            earned_score += q.points

        question_results.append({
            "question_id": q.id,
            "question_text": q.question_text,
            "selected_option": user_choice,
            "correct_option": q.correct_option_index,
            "is_correct": is_correct,
            "points_earned": q.points if is_correct else 0,
            "points_possible": q.points,
        })

        if attempt:
            ans_record = (
                db.query(StudentAnswer)
                .filter(StudentAnswer.attempt_id == attempt.id, StudentAnswer.question_id == q.id)
                .first()
            )
            if ans_record:
                if user_choice is not None:
                    ans_record.selected_option = user_choice
                ans_record.is_correct = is_correct
            elif user_choice is not None:
                db.add(StudentAnswer(
                    attempt_id=attempt.id,
                    question_id=q.id,
                    selected_option=user_choice,
                    is_correct=is_correct,
                ))

    pct = round((earned_score / max(1, total_points)) * 100.0, 1)

    # 2. Correlate Proctoring Summary
    session_id = request.session_id
    proctoring_summary = proctoring_service.get_session_summary(session_id, db=db)

    # Update attempt and proctoring session in DB
    if attempt:
        attempt.is_submitted = True
        attempt.submitted_at = now
        attempt.score = float(earned_score)
        attempt.max_score = float(total_points)
        attempt.percentage = pct

        proc_sess = db.query(ProctoringSession).filter(ProctoringSession.id == session_id).first()
        if proc_sess:
            proc_sess.ended_at = now
            proc_sess.total_frames_analyzed = proctoring_summary.total_frames_analyzed
            proc_sess.flagged_frames_count = proctoring_summary.flagged_frames_count
            proc_sess.integrity_score = proctoring_summary.integrity_score
            proc_sess.verdict = proctoring_summary.verdict
            proc_sess.verdict_label = proctoring_summary.verdict_label
            proc_sess.verdict_color = proctoring_summary.verdict_color
            proc_sess.dominant_emotion = proctoring_summary.dominant_emotion
            proc_sess.violations_json = json.dumps(proctoring_summary.violations_summary)
            proc_sess.top_contributors_json = json.dumps(proctoring_summary.top_contributors)

    db.commit()

    submission_id = attempt.id if attempt else f"sub-{uuid.uuid4().hex[:8]}"

    return SubmissionReport(
        submission_id=submission_id,
        exam_id=exam_id,
        student_name=attempt.student_name if attempt else request.student_name,
        student_id=attempt.student_id if attempt else (request.student_id or "STU-001"),
        session_id=session_id,
        score=earned_score,
        total_points=total_points,
        percentage=pct,
        submitted_at=now.isoformat(),
        integrity_score=proctoring_summary.integrity_score,
        verdict=proctoring_summary.verdict,
        verdict_label=proctoring_summary.verdict_label,
        verdict_color=proctoring_summary.verdict_color,
        proctoring_summary=proctoring_summary,
        question_results=question_results,
    )


def get_teacher_dashboard(exam_id: str, db: Session) -> Optional[TeacherDashboardResponse]:
    """Retrieves all student submissions and AI integrity analytics for this exam from PostgreSQL."""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        return None

    attempts = (
        db.query(ExamAttempt)
        .filter(ExamAttempt.exam_id == exam_id, ExamAttempt.is_submitted == True)
        .order_by(ExamAttempt.submitted_at.desc())
        .all()
    )

    reports = []
    total_score = 0.0
    flagged_count = 0

    for att in attempts:
        total_score += att.percentage
        proc_sess = att.proctoring_session

        int_score = proc_sess.integrity_score if proc_sess else 100.0
        verdict = proc_sess.verdict if proc_sess else "VERIFIED_CLEAN"
        v_label = proc_sess.verdict_label if proc_sess else "Clean Exam Conduct"
        v_color = proc_sess.verdict_color if proc_sess else "#34d399"

        if verdict != "VERIFIED_CLEAN":
            flagged_count += 1

        summary = proctoring_service.get_session_summary(proc_sess.id, db=db) if proc_sess else None

        reports.append(
            SubmissionReport(
                submission_id=att.id,
                exam_id=exam_id,
                student_name=att.student_name,
                student_id=att.student_id,
                session_id=proc_sess.id if proc_sess else f"sess-{att.id}",
                score=int(att.score),
                total_points=int(att.max_score),
                percentage=att.percentage,
                submitted_at=att.submitted_at.isoformat() if att.submitted_at else att.started_at.isoformat(),
                integrity_score=int_score,
                verdict=verdict,
                verdict_label=v_label,
                verdict_color=v_color,
                proctoring_summary=summary,
            )
        )

    avg_score = round(total_score / max(1, len(attempts)), 1) if attempts else 0.0

    return TeacherDashboardResponse(
        exam_id=exam_id,
        exam_title=exam.title,
        total_submissions=len(attempts),
        average_score=avg_score,
        flagged_students_count=flagged_count,
        submissions=reports,
    )


def get_system_overview(db: Session) -> SystemAnalyticsResponse:
    """Aggregates platform-wide metrics across all examinations for the Teacher Dashboard."""
    total_exams = db.query(Exam).count()
    published_exams = db.query(Exam).filter(Exam.is_published == True).count()
    
    attempts = db.query(ExamAttempt).filter(ExamAttempt.is_submitted == True).all()
    total_submissions = len(attempts)

    class_avg = 0.0
    avg_integrity = 100.0
    flagged_students = 0

    if attempts:
        total_pct = sum(a.percentage for a in attempts)
        class_avg = round(total_pct / total_submissions, 1)

        total_int = 0.0
        for a in attempts:
            sess = a.proctoring_session
            s_int = sess.integrity_score if sess else 100.0
            total_int += s_int
            if (sess and sess.verdict != "VERIFIED_CLEAN") or s_int < 80.0:
                flagged_students += 1
        avg_integrity = round(total_int / total_submissions, 1)

    recent_exams_db = db.query(Exam).order_by(Exam.created_at.desc()).limit(10).all()
    recent_items = []
    for e in recent_exams_db:
        sub_count = db.query(ExamAttempt).filter(ExamAttempt.exam_id == e.id, ExamAttempt.is_submitted == True).count()
        tot_pts = sum(q.points for q in e.questions)
        recent_items.append(
            ExamSummaryItem(
                id=e.id,
                title=e.title,
                description=e.description or "",
                duration_minutes=e.duration_minutes,
                questions_count=len(e.questions),
                total_points=tot_pts,
                is_published=e.is_published,
                created_at=e.created_at.strftime("%Y-%m-%d"),
                submissions_count=sub_count,
            )
        )

    return SystemAnalyticsResponse(
        total_exams=total_exams,
        published_exams=published_exams,
        total_submissions=total_submissions,
        class_average=class_avg,
        average_integrity=avg_integrity,
        flagged_students_count=flagged_students,
        recent_exams=recent_items,
    )


def _build_exam_response(exam: Exam) -> ExamResponse:
    """Helper to transform Exam ORM entity into ExamResponse schema."""
    questions = [
        QuestionSchema(
            id=q.id,
            question_text=q.question_text,
            options=q.options,
            correct_option_index=q.correct_option_index,
            points=q.points,
        )
        for q in exam.questions
    ]
    tot_pts = sum(q.points for q in exam.questions)
    return ExamResponse(
        id=exam.id,
        title=exam.title,
        description=exam.description or "",
        instructions=exam.instructions or "",
        duration_minutes=exam.duration_minutes,
        is_published=exam.is_published,
        access_code=exam.access_code,
        questions_count=len(exam.questions),
        total_points=tot_pts,
        created_at=exam.created_at.strftime("%Y-%m-%d"),
        questions=questions,
    )
