"""
Proctoring event endpoints (browser tab/window events, and eventually
the streaming webcam/audio ingestion hooks).

Phase 0: route contract only. The underlying service raises
NotImplementedError until Phase 1 wires up the real pipeline --
this is deliberate, not an oversight (see proctoring_service.py).
"""
from fastapi import APIRouter, HTTPException
from app.schemas.events import BrowserEvent
from app.services import proctoring_service

router = APIRouter(prefix="/proctoring", tags=["proctoring"])


@router.post("/events")
def submit_browser_event(event: BrowserEvent) -> dict:
    try:
        proctoring_service.record_browser_event(event)
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc))
    return {"received": True}
