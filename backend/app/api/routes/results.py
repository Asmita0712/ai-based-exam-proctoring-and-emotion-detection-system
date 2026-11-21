"""
Results endpoints -- exposes suspicion scores, modality signals, and evidence
produced by the multimodal inference pipeline.
"""
from typing import List
from fastapi import APIRouter
from app.schemas.results import SuspicionResult
from app.services import proctoring_service

router = APIRouter(prefix="/results", tags=["results"])


@router.get("/{session_id}", response_model=List[SuspicionResult])
def get_results(session_id: str) -> List[SuspicionResult]:
    """Retrieves all suspicious activity inference records for the session."""
    return proctoring_service.get_session_results(session_id)
