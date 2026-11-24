"""
SQLAlchemy ORM models for SentinelProctor AI.
Implements:
- Users (Teachers & Administrators)
- Examinations & Questions
- Student Attempts & Answers
- Proctoring Sessions & Forensic Events
- System Audit Logs
"""
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


def _utc_now():
    return datetime.now(timezone.utc)


class User(Base):
    """Staff user accounts (Teachers & Admins). Students do not require user accounts."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="teacher", index=True)  # 'teacher' | 'admin'
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utc_now, nullable=False)

    exams = relationship("Exam", back_populates="creator", cascade="all, delete-orphan")


class Exam(Base):
    """Examinations created by teachers."""
    __tablename__ = "exams"

    id = Column(String(64), primary_key=True, default=lambda: f"exam-{uuid.uuid4().hex[:8]}")
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    duration_minutes = Column(Integer, nullable=False, default=30)
    instructions = Column(Text, nullable=True)
    access_code = Column(String(64), nullable=True, index=True)
    is_published = Column(Boolean, default=False, nullable=False, index=True)
    teacher_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now, nullable=False)

    creator = relationship("User", back_populates="exams")
    questions = relationship("Question", back_populates="exam", cascade="all, delete-orphan", order_by="Question.order")
    attempts = relationship("ExamAttempt", back_populates="exam", cascade="all, delete-orphan")


class Question(Base):
    """MCQ Questions belonging to an exam."""
    __tablename__ = "questions"

    id = Column(String(64), primary_key=True, default=lambda: f"q-{uuid.uuid4().hex[:8]}")
    exam_id = Column(String(64), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    options_json = Column(Text, nullable=False)  # JSON-encoded List[str]
    correct_option_index = Column(Integer, nullable=False)  # Hidden from student view
    points = Column(Integer, default=1, nullable=False)
    order = Column(Integer, default=0, nullable=False)

    exam = relationship("Exam", back_populates="questions")

    @property
    def options(self) -> List[str]:
        return json.loads(self.options_json)

    @options.setter
    def options(self, val: List[str]):
        self.options_json = json.dumps(val)


class ExamAttempt(Base):
    """
    Open-access student examination attempt.
    Server-authoritative timer: started_at and ends_at.
    """
    __tablename__ = "exam_attempts"

    id = Column(String(64), primary_key=True, default=lambda: f"att-{uuid.uuid4().hex[:12]}")
    exam_id = Column(String(64), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True)
    student_name = Column(String(255), nullable=False, index=True)
    student_id = Column(String(100), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), default=_utc_now, nullable=False)
    ends_at = Column(DateTime(timezone=True), nullable=False, index=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    is_submitted = Column(Boolean, default=False, nullable=False, index=True)
    
    # Grading results
    score = Column(Float, default=0.0, nullable=False)
    max_score = Column(Float, default=0.0, nullable=False)
    percentage = Column(Float, default=0.0, nullable=False)
    
    # Relationships
    exam = relationship("Exam", back_populates="attempts")
    answers = relationship("StudentAnswer", back_populates="attempt", cascade="all, delete-orphan")
    proctoring_session = relationship("ProctoringSession", back_populates="attempt", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_attempt_exam_student", "exam_id", "student_id"),
    )


class StudentAnswer(Base):
    """Individual question responses autosaved or submitted by students."""
    __tablename__ = "student_answers"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    attempt_id = Column(String(64), ForeignKey("exam_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(String(64), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    selected_option = Column(Integer, nullable=False)
    is_correct = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now, nullable=False)

    attempt = relationship("ExamAttempt", back_populates="answers")

    __table_args__ = (
        Index("idx_answer_attempt_question", "attempt_id", "question_id", unique=True),
    )


class ProctoringSession(Base):
    """Persistent proctoring session paired with a student attempt."""
    __tablename__ = "proctoring_sessions"

    id = Column(String(64), primary_key=True)  # Matches session_id (e.g. sess-...)
    attempt_id = Column(String(64), ForeignKey("exam_attempts.id", ondelete="CASCADE"), nullable=True, unique=True, index=True)
    exam_id = Column(String(64), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True)
    
    started_at = Column(DateTime(timezone=True), default=_utc_now, nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    total_frames_analyzed = Column(Integer, default=0, nullable=False)
    flagged_frames_count = Column(Integer, default=0, nullable=False)
    integrity_score = Column(Float, default=100.0, nullable=False)
    verdict = Column(String(50), default="VERIFIED_CLEAN", nullable=False)
    verdict_label = Column(String(255), default="Clean Exam Conduct", nullable=False)
    verdict_color = Column(String(20), default="#34d399", nullable=False)
    
    # Forensic metrics
    monitoring_coverage_pct = Column(Float, default=100.0, nullable=False)
    violations_json = Column(Text, default="{}", nullable=False)
    top_contributors_json = Column(Text, default="[]", nullable=False)
    dominant_emotion = Column(String(50), default="neutral", nullable=False)

    attempt = relationship("ExamAttempt", back_populates="proctoring_session")
    events = relationship("ProctoringEvent", back_populates="session", cascade="all, delete-orphan", order_by="ProctoringEvent.timestamp")


class ProctoringEvent(Base):
    """Forensic timeline events (browser blurs, audio bursts, visual flags)."""
    __tablename__ = "proctoring_events"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(64), ForeignKey("proctoring_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=_utc_now, nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # 'tab_hidden', 'window_blur', 'face_absent', etc.
    payload_json = Column(Text, default="{}", nullable=False)

    session = relationship("ProctoringSession", back_populates="events")


class AuditLog(Base):
    """Immutable audit trail for institutional compliance."""
    __tablename__ = "audit_logs"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_id = Column(String(100), nullable=True, index=True)
    actor_role = Column(String(50), nullable=False)  # 'student', 'teacher', 'admin', 'system'
    action = Column(String(100), nullable=False, index=True)
    target = Column(String(100), nullable=True)
    details_json = Column(Text, default="{}", nullable=False)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=_utc_now, nullable=False, index=True)
