"""
Pydantic schemas for exam sessions.

Phase 0: structure only. Real session lifecycle logic arrives with
Phase 1's integration pipeline.
"""
from datetime import datetime
from pydantic import BaseModel


class SessionCreateRequest(BaseModel):
    student_id: str
    exam_id: str


class SessionResponse(BaseModel):
    session_id: str
    student_id: str
    exam_id: str
    started_at: datetime
    status: str  # "active" | "ended"
