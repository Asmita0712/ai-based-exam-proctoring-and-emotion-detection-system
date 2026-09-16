"""
Session endpoints.

Phase 0: skeleton routes wired to session_service so the contract
is fixed early. No ML dependency here at all.
"""
from fastapi import APIRouter, HTTPException
from app.schemas.session import SessionCreateRequest, SessionResponse
from app.services import session_service

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/", response_model=SessionResponse)
def create_session(request: SessionCreateRequest) -> SessionResponse:
    return session_service.create_session(request)


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: str) -> SessionResponse:
    session = session_service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/{session_id}/end", response_model=SessionResponse)
def end_session(session_id: str) -> SessionResponse:
    session = session_service.end_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
