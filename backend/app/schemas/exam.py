"""
Pydantic schemas for MCQ Exam management, student attempts, and teacher dashboards.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.results import ExamSummary


class Question(BaseModel):
    id: str
    question_text: str
    options: List[str]
    correct_option_index: int
    points: int = 1


class QuestionStudentView(BaseModel):
    id: str
    question_text: str
    options: List[str]
    points: int = 1


class ExamCreateRequest(BaseModel):
    title: str
    description: Optional[str] = "Standard Online Multiple Choice Examination"
    instructions: Optional[str] = "Ensure your camera and microphone are functional. Do not switch tabs or look away."
    duration_minutes: int = 15
    is_published: bool = True
    access_code: Optional[str] = None
    questions: List[Question]


class ExamResponse(BaseModel):
    id: str
    title: str
    description: str
    instructions: Optional[str] = ""
    duration_minutes: int
    is_published: bool = True
    access_code: Optional[str] = None
    questions_count: int
    total_points: int
    created_at: str
    questions: List[Question]


class ExamPublicSummary(BaseModel):
    id: str
    title: str
    description: str
    instructions: Optional[str] = ""
    duration_minutes: int
    is_published: bool = True
    has_access_code: bool = False
    questions_count: int
    total_points: int
    created_at: str


class ExamStudentView(BaseModel):
    id: str
    title: str
    description: str
    instructions: Optional[str] = ""
    duration_minutes: int
    is_published: bool = True
    has_access_code: bool = False
    questions: List[QuestionStudentView]
    total_points: int


class ExamStartRequest(BaseModel):
    student_name: str
    student_id: str
    access_code: Optional[str] = None


class ExamStartResponse(BaseModel):
    attempt_id: str
    attempt_token: str
    session_id: str
    exam: ExamStudentView
    started_at: str
    ends_at: str
    remaining_seconds: int


class AnswerAutosaveRequest(BaseModel):
    question_id: str
    selected_option: int


class AnswerAutosaveResponse(BaseModel):
    success: bool
    question_id: str
    selected_option: int
    saved_at: str
    remaining_seconds: int


class ExamSubmitRequest(BaseModel):
    student_name: str
    student_id: Optional[str] = "STU-001"
    session_id: str
    answers: Dict[str, int]  # question_id -> selected_option_index


class SubmissionReport(BaseModel):
    submission_id: str
    exam_id: str
    student_name: str
    student_id: str
    session_id: str
    score: int
    total_points: int
    percentage: float
    submitted_at: str
    integrity_score: float
    verdict: str
    verdict_label: str
    verdict_color: str
    proctoring_summary: Optional[ExamSummary] = None
    question_results: Optional[List[Dict[str, Any]]] = None


class TeacherDashboardResponse(BaseModel):
    exam_id: str
    exam_title: str
    total_submissions: int
    average_score: float
    flagged_students_count: int
    submissions: List[SubmissionReport]


class ExamSummaryItem(BaseModel):
    id: str
    title: str
    description: str
    duration_minutes: int
    questions_count: int
    total_points: int
    is_published: bool
    created_at: str
    submissions_count: int = 0


class SystemAnalyticsResponse(BaseModel):
    total_exams: int
    published_exams: int
    total_submissions: int
    class_average: float
    average_integrity: float
    flagged_students_count: int
    recent_exams: List[ExamSummaryItem]
