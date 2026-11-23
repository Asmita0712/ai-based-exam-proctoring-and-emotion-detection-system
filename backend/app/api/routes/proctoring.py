"""
Proctoring event and inference endpoints.
"""
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.schemas.events import BrowserEvent
from app.schemas.results import SuspicionResult
from app.services import proctoring_service

router = APIRouter(prefix="/proctoring", tags=["proctoring"])


class WindowInferenceRequest(BaseModel):
    session_id: str
    visual_signals: Optional[Dict[str, Any]] = None
    audio_signals: Optional[Dict[str, Any]] = None
    browser_signals: Optional[Dict[str, Any]] = None
    mode: Optional[str] = "temporal"


class FrameInferenceRequest(BaseModel):
    session_id: str
    image_base64: str
    mode: Optional[str] = "temporal"
    audio_signals: Optional[Dict[str, Any]] = None
    browser_signals: Optional[Dict[str, Any]] = None


@router.post("/events")
def submit_browser_event(event: BrowserEvent) -> dict:
    proctoring_service.record_browser_event(event)
    return {"received": True}


@router.post("/analyze-window", response_model=SuspicionResult)
def analyze_window(request: WindowInferenceRequest) -> SuspicionResult:
    """Runs multimodal inference over current window signals."""
    return proctoring_service.process_window_inference(
        session_id=request.session_id,
        visual_signals=request.visual_signals,
        audio_signals=request.audio_signals,
        browser_signals=request.browser_signals,
        mode=request.mode or "temporal",
    )


@router.post("/analyze-frame", response_model=SuspicionResult)
def analyze_frame(request: FrameInferenceRequest) -> SuspicionResult:
    """Processes a live webcam frame from the browser and executes multimodal inference."""
    return proctoring_service.process_frame_inference(
        session_id=request.session_id,
        image_base64=request.image_base64,
        mode=request.mode or "temporal",
        audio_signals=request.audio_signals,
        browser_signals=request.browser_signals,
    )


class ResetSessionRequest(BaseModel):
    session_id: str


@router.post("/session/reset")
def reset_session(request: ResetSessionRequest) -> dict:
    """Resets all tracked state and results for a session."""
    proctoring_service.reset_session(request.session_id)
    return {"reset": True, "session_id": request.session_id}
