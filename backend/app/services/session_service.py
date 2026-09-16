"""
Session lifecycle service.

RULE 2 / RULE 3: business logic lives here, not inside route functions,
and there is no ML inference in this layer -- it only manages session
state and hands off to ml/pipelines in later phases.

Phase 0: in-memory placeholder implementation only.
"""
import uuid
from datetime import datetime, timezone
from app.schemas.session import SessionCreateRequest, SessionResponse

# NOTE: in-memory store is a Phase 0 placeholder. Replace with a real
# persistence layer (DB) when session durability actually matters --
# not required for the basic model milestone.
_sessions: dict[str, SessionResponse] = {}


def create_session(request: SessionCreateRequest) -> SessionResponse:
    session_id = str(uuid.uuid4())
    session = SessionResponse(
        session_id=session_id,
        student_id=request.student_id,
        exam_id=request.exam_id,
        started_at=datetime.now(timezone.utc),
        status="active",
    )
    _sessions[session_id] = session
    return session


def get_session(session_id: str) -> SessionResponse | None:
    return _sessions.get(session_id)


def end_session(session_id: str) -> SessionResponse | None:
    session = _sessions.get(session_id)
    if session:
        session.status = "ended"
    return session
