"""
Results endpoints -- will expose suspicion scores/evidence once
Phase 1 (rule-based fusion) and later Phase 3 (learned fusion +
temporal model) produce real SuspicionResult records.

Phase 0: route contract only, backed by an empty in-memory list.
"""
from fastapi import APIRouter
from app.schemas.results import SuspicionResult

router = APIRouter(prefix="/results", tags=["results"])


@router.get("/{session_id}", response_model=list[SuspicionResult])
def get_results(session_id: str) -> list[SuspicionResult]:
    # Phase 0: no fusion pipeline exists yet, so this is correctly empty.
    return []
