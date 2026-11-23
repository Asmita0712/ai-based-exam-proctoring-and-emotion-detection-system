"""
Proctoring service -- the seam between the API layer and ml/pipelines.

RULE 2 / RULE 3: FastAPI routes call into this service; this service
(not the routes) is responsible for calling into ml/pipelines/inference_pipeline.py.
"""
import base64
import cv2
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import numpy as np

from app.schemas.events import BrowserEvent
from app.schemas.results import SuspicionResult, ModalitySignals, ExamSummary
from ml.pipelines.feature_pipeline import build_feature_window
from ml.pipelines.inference_pipeline import run_inference
from ml.utils.tab_tracker import TabTracker

# Singleton VisualPipeline for fast real-time frame inference
_VISUAL_PIPELINE: Optional[Any] = None


def get_visual_pipeline():
    global _VISUAL_PIPELINE
    if _VISUAL_PIPELINE is None:
        from ml.pipelines.visual_pipeline import VisualPipeline
        _VISUAL_PIPELINE = VisualPipeline()
    return _VISUAL_PIPELINE

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
    browser_signals: Optional[Dict[str, Any]] = None,
    mode: str = "temporal",
) -> SuspicionResult:
    """
    Orchestrates window feature construction and calls inference_pipeline.run_inference.
    Stores and returns the resulting SuspicionResult.
    """
    tracker = get_tab_tracker(session_id)

    # Sync tracker with live browser signals from client
    if browser_signals is not None:
        if "tab_hidden" in browser_signals:
            tracker.tab_hidden = bool(browser_signals["tab_hidden"])
        if "window_blur" in browser_signals:
            tracker.window_blur = bool(browser_signals["window_blur"])
        if "is_away" in browser_signals and not browser_signals["is_away"]:
            tracker.tab_hidden = False
            tracker.window_blur = False

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


def get_session_summary(session_id: str) -> ExamSummary:
    """
    Computes post-exam cumulative integrity metrics and forensic verdict
    over all recorded inference frames for the given session.
    """
    results = _SESSION_RESULTS.get(session_id, [])
    total_frames = len(results)

    if total_frames == 0:
        return ExamSummary(
            session_id=session_id,
            total_frames_analyzed=0,
            exam_duration_seconds=0.0,
            flagged_frames_count=0,
            flagged_percentage=0.0,
            integrity_score=100.0,
            verdict="VERIFIED_CLEAN",
            verdict_label="Clean Exam Conduct (No Violations Recorded)",
            verdict_color="#34d399",
            violations_summary={
                "multi_person": 0,
                "looking_away": 0,
                "head_turned": 0,
                "speech_detected": 0,
                "tab_unfocused": 0,
                "absence": 0,
            },
            dominant_emotion="neutral",
            top_contributors=[],
        )

    # Calculate duration
    start_time = results[0].window_start
    end_time = results[-1].window_start
    duration_secs = max(1.0, (end_time - start_time).total_seconds())

    # Count flags & categories
    flagged_count = sum(1 for r in results if r.flag)
    flagged_pct = round((flagged_count / total_frames) * 100, 1)

    multi_person_count = sum(1 for r in results if r.signals.multi_person_flag or (r.signals.person_count and r.signals.person_count > 1))
    looking_away_count = sum(1 for r in results if r.signals.looking_away)
    head_turned_count = sum(1 for r in results if r.signals.turned_away)
    speech_count = sum(1 for r in results if r.signals.sustained_talking)
    tab_away_count = sum(1 for r in results if r.signals.tab_hidden)
    absence_count = sum(1 for r in results if r.signals.person_count == 0)

    # Emotional distribution
    emotions = [r.signals.dominant_emotion for r in results if r.signals.dominant_emotion]
    dominant_emotion = max(set(emotions), key=emotions.count) if emotions else "neutral"

    # Top contributors
    all_contributors = []
    for r in results:
        all_contributors.extend(r.contributors)
    from collections import Counter
    top_contribs = [item for item, _ in Counter(all_contributors).most_common(5)]

    # Compute Integrity Score (0 - 100)
    multi_person_penalty = min(35.0, (multi_person_count / total_frames) * 120.0)
    tab_penalty = min(25.0, (tab_away_count / total_frames) * 80.0)
    absence_penalty = min(25.0, (absence_count / total_frames) * 80.0)
    flag_penalty = min(50.0, flagged_pct * 0.8)

    total_penalty = flag_penalty + multi_person_penalty + tab_penalty + absence_penalty
    integrity_score = round(max(0.0, min(100.0, 100.0 - total_penalty)), 1)

    # Determine Verdict
    if integrity_score >= 85.0 and multi_person_count == 0:
        verdict = "VERIFIED_CLEAN"
        verdict_label = "Clean Exam Conduct (Verified Passed)"
        verdict_color = "#34d399"
    elif integrity_score >= 65.0:
        verdict = "SUSPICIOUS_REVIEW_NEEDED"
        verdict_label = "Borderline Activity (Manual Proctor Review Required)"
        verdict_color = "#fbbf24"
    else:
        verdict = "CHEATING_FLAGGED"
        verdict_label = "High Cheating Probability (Integrity Breach Flagged)"
        verdict_color = "#ef4444"

    return ExamSummary(
        session_id=session_id,
        total_frames_analyzed=total_frames,
        exam_duration_seconds=round(duration_secs, 1),
        flagged_frames_count=flagged_count,
        flagged_percentage=flagged_pct,
        integrity_score=integrity_score,
        verdict=verdict,
        verdict_label=verdict_label,
        verdict_color=verdict_color,
        violations_summary={
            "multi_person": multi_person_count,
            "looking_away": looking_away_count,
            "head_turned": head_turned_count,
            "speech_detected": speech_count,
            "tab_unfocused": tab_away_count,
            "absence": absence_count,
        },
        dominant_emotion=dominant_emotion,
        top_contributors=top_contribs,
    )


def reset_session(session_id: str) -> None:
    """Cleans up in-memory trackers and history for a session."""
    if session_id in _SESSION_TAB_TRACKERS:
        _SESSION_TAB_TRACKERS[session_id].reset()
    if session_id in _SESSION_RESULTS:
        del _SESSION_RESULTS[session_id]


def process_frame_inference(
    session_id: str,
    image_base64: str,
    mode: str = "temporal",
    audio_signals: Optional[Dict[str, Any]] = None,
    browser_signals: Optional[Dict[str, Any]] = None,
) -> SuspicionResult:
    """
    Decodes a base64 image frame from the browser, runs real-time visual
    pipeline (YOLO + MediaPipe Iris + Head Pose + Emotion), and executes
    multimodal suspicion inference.
    """
    if "," in image_base64:
        image_base64 = image_base64.split(",", 1)[1]

    img_bytes = base64.b64decode(image_base64)
    np_arr = np.frombuffer(img_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    visual_signals = {}
    if frame is not None and frame.size > 0:
        vp = get_visual_pipeline()
        visual_signals = vp.process_frame(frame)
        from app.core.logging import get_logger
        _log = get_logger("proctoring_service")
        _log.info(
            "FRAME INFERENCE: size=%dx%d, persons=%s, looking_away=%s (gaze_ratio=%.2f), yaw=%.1f, pitch=%.1f, emo=%s",
            frame.shape[1], frame.shape[0],
            visual_signals.get("person_count"),
            visual_signals.get("looking_away"),
            visual_signals.get("gaze", {}).get("gaze_ratio", 0.5),
            visual_signals.get("head_pose", {}).get("yaw", 0.0),
            visual_signals.get("head_pose", {}).get("pitch", 0.0),
            visual_signals.get("emotion", {}).get("dominant_emotion"),
        )

    return process_window_inference(
        session_id=session_id,
        visual_signals=visual_signals,
        audio_signals=audio_signals,
        browser_signals=browser_signals,
        mode=mode,
    )
