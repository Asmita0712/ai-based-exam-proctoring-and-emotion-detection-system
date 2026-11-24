"""
API routes for MCQ Exam management, open student attempts, and teacher analytics.
Implements:
- Open access for students (no registration required) with signed attempt tokens
- Strict RBAC protection on teacher creation, dashboard, and publishing routes
- Server-authoritative timer and idempotent answer autosaving
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_current_student_attempt,
    require_admin,
    require_teacher,
)
from app.db.models import ExamAttempt, User
from app.db.session import get_db
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
    SubmissionReport,
    SystemAnalyticsResponse,
    TeacherDashboardResponse,
)
from app.services import exam_service

router = APIRouter(prefix="/exams", tags=["exams"])


# =====================================================================
# TEACHER & ADMIN PROTECTED ENDPOINTS
# =====================================================================

@router.post("/", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
def create_exam(
    request: ExamCreateRequest,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
) -> ExamResponse:
    """Allows an authenticated teacher or admin to create a new MCQ examination."""
    return exam_service.create_exam(request=request, teacher_id=current_user.id, db=db)


@router.get("/analytics/summary", response_model=SystemAnalyticsResponse)
def get_system_analytics_summary(
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
) -> SystemAnalyticsResponse:
    """Retrieves aggregate platform analytics for the Teacher Dashboard."""
    return exam_service.get_system_overview(db=db)


@router.patch("/{exam_id}/publish", response_model=ExamResponse)
def toggle_exam_publish(
    exam_id: str,
    is_published: bool = Query(..., description="Target published state"),
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
) -> ExamResponse:
    """Toggles examination published state (Teachers/Admins only)."""
    updated = exam_service.toggle_publish(exam_id=exam_id, is_published=is_published, db=db)
    if not updated:
        raise HTTPException(status_code=404, detail="Exam not found")
    return updated


@router.get("/{exam_id}/teacher", response_model=ExamResponse)
def get_exam_for_teacher(
    exam_id: str,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
) -> ExamResponse:
    """Returns full exam definition with answer keys for authorized teacher inspection."""
    exam = exam_service.get_exam_for_teacher(exam_id=exam_id, db=db)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return exam


@router.get("/{exam_id}/dashboard", response_model=TeacherDashboardResponse)
def get_teacher_dashboard(
    exam_id: str,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
) -> TeacherDashboardResponse:
    """Retrieves all student submissions and AI cheating analytics for this exam."""
    dashboard = exam_service.get_teacher_dashboard(exam_id=exam_id, db=db)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Exam not found")
    return dashboard


# =====================================================================
# PUBLIC STUDENT & OPEN ACCESS ENDPOINTS
# =====================================================================

@router.get("/", response_model=List[ExamPublicSummary])
def list_exams(
    published_only: bool = Query(True, description="Filter only published exams"),
    db: Session = Depends(get_db),
) -> List[ExamPublicSummary]:
    """
    Public list of examinations available in the Student Lobby.
    SECURITY: Completely omits questions and answer keys.
    """
    return exam_service.list_public_exams(published_only=published_only, db=db)


@router.get("/teacher/list", response_model=List[ExamResponse])
def list_teacher_exams(
    published_only: bool = Query(False, description="Filter only published exams"),
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
) -> List[ExamResponse]:
    """
    Teacher/Admin only list of examinations with full question definitions.
    """
    return exam_service.list_exams(published_only=published_only, db=db)


@router.get("/{exam_id}", response_model=ExamStudentView)
def get_exam_for_student(
    exam_id: str,
    db: Session = Depends(get_db),
) -> ExamStudentView:
    """
    Public student view of an examination.
    SECURITY: Strips correct_option_index from all questions.
    """
    exam = exam_service.get_exam_for_student(exam_id=exam_id, db=db)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return exam


@router.post("/{exam_id}/start", response_model=ExamStartResponse)
def start_exam(
    exam_id: str,
    request: ExamStartRequest,
    db: Session = Depends(get_db),
) -> ExamStartResponse:
    """
    OPEN ACCESS: Any student can begin an examination without creating an account.
    Returns server-authoritative timer, clean question list, and signed attempt_token.
    """
    start_resp = exam_service.start_exam_attempt(exam_id=exam_id, request=request, db=db)
    if not start_resp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to start examination. Verify that the exam is published and the access code is correct.",
        )
    return start_resp


@router.post("/{exam_id}/autosave", response_model=AnswerAutosaveResponse)
def autosave_answer(
    exam_id: str,
    request: AnswerAutosaveRequest,
    attempt: ExamAttempt = Depends(get_current_student_attempt),
    db: Session = Depends(get_db),
) -> AnswerAutosaveResponse:
    """
    Idempotent autosave of a student's answer choice during an active examination.
    Enforces server-authoritative timer check and cryptographic attempt ownership.
    """
    if attempt.exam_id != exam_id:
        raise HTTPException(status_code=400, detail="Attempt does not match this exam.")
    try:
        return exam_service.autosave_answer(attempt=attempt, request=request, db=db)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/{exam_id}/submit", response_model=SubmissionReport)
def submit_exam(
    exam_id: str,
    request: ExamSubmitRequest,
    attempt: ExamAttempt = Depends(get_current_student_attempt),
    db: Session = Depends(get_db),
) -> SubmissionReport:
    """
    Finalizes and grades student MCQ answers in a single ACID transaction,
    pairing them with the student's live AI proctoring integrity report.
    Cryptographically validates attempt ownership (prevents student ID spoofing).
    """
    if attempt.exam_id != exam_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attempt token does not match the requested examination.",
        )
    if attempt.is_submitted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This examination attempt has already been submitted and graded.",
        )

    report = exam_service.submit_exam(exam_id=exam_id, request=request, db=db, attempt=attempt)
    if not report:
        raise HTTPException(status_code=404, detail="Exam or attempt not found")
    return report
