"""
Proctoring service -- the seam between the API layer and ml/pipelines.

RULE 2 / RULE 3: FastAPI routes call into this service; this service
(not the routes) is responsible for calling into ml/pipelines/inference_pipeline.py.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import numpy as np

from app.schemas.events import BrowserEvent
from app.schemas.results import SuspicionResult, ModalitySignals
from ml.pipelines.feature_pipeline import build_feature_window
from ml.pipelines.inference_pipeline import run_inference
from ml.utils.tab_tracker import TabTracker

# Active session tab trackers: session_id -> TabTracker
_SESSION_TAB_TRACKERS: Dict[str, TabTracker] = {}
# Session inference history: session_id -> List[SuspicionResult]
_SESSION_RESULTS: Dict[str, List[SuspicionResult]] = {}


def get_tab_tracker(session_id: str) -> TabTracker:
    """Retrieves or creates a TabTracker for the given session ID."""
    if session_id not in _SESSION_TAB_TRACKERS:
        _SESSION_TAB_TRACKERS[session_id] = TabTracker()
    return _SESSION_TAB_TRACKERS[session_id]


def record_browser_event(event: BrowserEvent) -> Dict[str, Any]:
    """
    Records a browser tab or window focus event into the session's TabTracker.
    """
    tracker = get_tab_tracker(event.session_id)
    ts = event.timestamp.timestamp() if hasattr(event.timestamp, "timestamp") else None
    return tracker.record_event(event.type, timestamp=ts)


def process_window_inference(
    session_id: str,
    visual_signals: Optional[Dict[str, Any]] = None,
    audio_signals: Optional[Dict[str, Any]] = None,
    mode: str = "temporal",
) -> SuspicionResult:
    """
    Orchestrates window feature construction and calls inference_pipeline.run_inference.
    Stores and returns the resulting SuspicionResult.
    """
    tracker = get_tab_tracker(session_id)
    browser_status = tracker.get_status()

    now_dt = datetime.now(timezone.utc)
    feature_window = build_feature_window(
        visual_signals=visual_signals or {},
        audio_signals=audio_signals or {},
        browser_events=[browser_status],
        window_start=now_dt.timestamp(),
    )

    inference_out = run_inference(
        session_id=session_id,
        feature_window=feature_window,
        mode=mode,
    )

    gaze_d = feature_window.get("gaze") or {}
    pose_d = feature_window.get("head_pose") or {}
    emo_d = feature_window.get("emotion") or {}

    mod_signals = ModalitySignals(
        gaze_ratio=gaze_d.get("gaze_ratio"),
        looking_away=feature_window.get("looking_away"),
        yaw=pose_d.get("yaw"),
        pitch=pose_d.get("pitch"),
        turned_away=feature_window.get("turned_away"),
        person_count=feature_window.get("person_count"),
        multi_person_flag=feature_window.get("multi_person_flag"),
        speech_probability=feature_window.get("speech_probability"),
        sustained_talking=feature_window.get("sustained_talking"),
        tab_hidden=feature_window.get("tab_hidden"),
        dominant_emotion=emo_d.get("dominant_emotion"),
        emotion_confidence=emo_d.get("emotion_confidence"),
    )

    susp_result = SuspicionResult(
        session_id=session_id,
        window_start=now_dt,
        suspicion_score=float(inference_out["suspicion_score"]),
        flag=bool(inference_out["flag"]),
        contributors=inference_out.get("contributors", []),
        signals=mod_signals,
    )

    if session_id not in _SESSION_RESULTS:
        _SESSION_RESULTS[session_id] = []
    _SESSION_RESULTS[session_id].append(susp_result)

    return susp_result


def get_session_results(session_id: str) -> List[SuspicionResult]:
    """Retrieves all recorded SuspicionResult records for a session."""
    return _SESSION_RESULTS.get(session_id, [])


def reset_session(session_id: str) -> None:
    """Cleans up in-memory trackers and history for a session."""
    if session_id in _SESSION_TAB_TRACKERS:
        _SESSION_TAB_TRACKERS[session_id].reset()
    if session_id in _SESSION_RESULTS:
        del _SESSION_RESULTS[session_id]
