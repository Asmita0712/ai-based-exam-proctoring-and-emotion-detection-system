"""
Proctoring service -- the seam between the API layer and ml/pipelines.

RULE 2 / RULE 3: FastAPI routes call into this service; this service
(not the routes) is responsible for calling into ml/pipelines/inference_pipeline.py.
"""
import base64
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.events import BrowserEvent
from app.schemas.results import SuspicionResult, ModalitySignals, ExamSummary
from ml.pipelines.feature_pipeline import build_feature_window
from ml.pipelines.inference_pipeline import run_inference
from ml.utils.tab_tracker import TabTracker

logger = get_logger(__name__)
settings = get_settings()

# Singleton VisualPipeline for fast real-time frame inference
_VISUAL_PIPELINE: Optional[Any] = None


def get_visual_pipeline():
    """
    Lazy initialization of heavy Visual Pipeline (YOLOv8 + MediaPipe).
    Never loads heavy models on application startup (RULE 14 & Free-Tier Guard).
    Returns None if heavy AI is disabled or dependencies/weights are unavailable.
    """
    global _VISUAL_PIPELINE
    if not settings.enable_heavy_ai:
        return None

    if _VISUAL_PIPELINE is None:
        try:
            from ml.pipelines.visual_pipeline import VisualPipeline
            _VISUAL_PIPELINE = VisualPipeline()
            logger.info("Visual AI pipeline initialized successfully.")
        except Exception as e:
            logger.warning("Heavy Visual AI models could not be loaded: %s", e)
            _VISUAL_PIPELINE = None

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
    raw_visual = visual_signals or {}
    inf_status = raw_visual.get("inference_status", "ACTIVE" if settings.enable_heavy_ai else "FREE_TIER_CPU_ONLY")

    # If visual inference is disabled or unavailable, pass empty visual dict to build_feature_window
    # so no fake visual cheating flags are generated (RULE 15 & Free-Tier Guard)
    safe_visual = raw_visual if inf_status == "ACTIVE" else {}

    feature_window = build_feature_window(
        visual_signals=safe_visual,
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

    if inf_status == "ACTIVE":
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
    else:
        # Free-tier or inference unavailable: honest representation without fabricating signals
        mod_signals = ModalitySignals(
            gaze_ratio=None,
            looking_away=None,
            yaw=None,
            pitch=None,
            turned_away=None,
            person_count=None,
            multi_person_flag=None,
            speech_probability=feature_window.get("speech_probability"),
            sustained_talking=feature_window.get("sustained_talking"),
            tab_hidden=feature_window.get("tab_hidden"),
            dominant_emotion=None,
            emotion_confidence=None,
        )

    susp_result = SuspicionResult(
        session_id=session_id,
        window_start=now_dt,
        suspicion_score=float(inference_out["suspicion_score"]),
        flag=bool(inference_out["flag"]),
        contributors=inference_out.get("contributors", []),
        signals=mod_signals,
        inference_status=inf_status,
    )

    if session_id not in _SESSION_RESULTS:
        _SESSION_RESULTS[session_id] = []
    _SESSION_RESULTS[session_id].append(susp_result)

    return susp_result


def get_session_results(session_id: str) -> List[SuspicionResult]:
    """Retrieves all recorded SuspicionResult records for a session."""
    return _SESSION_RESULTS.get(session_id, [])


def get_session_summary(session_id: str, db: Optional[Any] = None) -> ExamSummary:
    """
    Computes post-exam cumulative integrity metrics and forensic verdict
    over all recorded inference frames for the given session.
    Checks memory buffer first, with database fallback.
    """
    results = _SESSION_RESULTS.get(session_id, [])
    total_frames = len(results)

    if total_frames == 0:
        # Check database fallback
        close_db = False
        try:
            if db is None:
                from app.db.session import SessionLocal
                db = SessionLocal()
                close_db = True
            from app.db.models import ProctoringSession
            proc = db.query(ProctoringSession).filter(ProctoringSession.id == session_id).first()
            if proc and proc.total_frames_analyzed > 0:
                violations = json.loads(proc.violations_json) if proc.violations_json else {}
                top_c = json.loads(proc.top_contributors_json) if proc.top_contributors_json else []
                duration = 0.0
                if proc.started_at and proc.ended_at:
                    duration = max(1.0, (proc.ended_at - proc.started_at).total_seconds())
                flag_pct = round((proc.flagged_frames_count / max(1, proc.total_frames_analyzed)) * 100, 1)
                return ExamSummary(
                    session_id=session_id,
                    total_frames_analyzed=proc.total_frames_analyzed,
                    exam_duration_seconds=round(duration, 1),
                    flagged_frames_count=proc.flagged_frames_count,
                    flagged_percentage=flag_pct,
                    integrity_score=proc.integrity_score,
                    verdict=proc.verdict,
                    verdict_label=proc.verdict_label,
                    verdict_color=proc.verdict_color,
                    violations_summary=violations,
                    dominant_emotion=proc.dominant_emotion,
                    top_contributors=top_c,
                    monitoring_coverage_pct=proc.monitoring_coverage_pct or 100.0,
                )
        except Exception:
            pass
        finally:
            if close_db and db:
                try:
                    db.close()
                except Exception:
                    pass

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
            monitoring_coverage_pct=100.0,
        )

    # Calculate duration
    start_time = results[0].window_start
    end_time = results[-1].window_start
    duration_secs = max(1.0, (end_time - start_time).total_seconds())

    # Count flags & categories
    flagged_count = sum(1 for r in results if r.flag)
    flagged_pct = round((flagged_count / total_frames) * 100, 1)

    multi_person_count = sum(1 for r in results if r.signals.multi_person_flag)
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
    if _VISUAL_PIPELINE is not None:
        _VISUAL_PIPELINE.reset()
    from ml.pipelines.inference_pipeline import _DEFAULT_INFERENCE_PIPELINE
    _DEFAULT_INFERENCE_PIPELINE.reset_session(session_id)


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
    Features:
    - Adaptive sampling feedback based on active concurrent load
    - Backpressure protection preventing thread starvation at 500 concurrent sessions
    """
    from app.services.proctoring_worker import get_queue_manager
    qm = get_queue_manager()
    active_count = len(_SESSION_RESULTS)
    target_interval = qm.calculate_sampling_interval_ms(active_count)

    # Check adaptive sampling & backpressure
    should_process = qm.should_sample_frame(session_id, active_session_count=active_count)

    # If throttled under high load, return previous inference state with updated audio/browser telemetry
    if not should_process and session_id in _SESSION_RESULTS and _SESSION_RESULTS[session_id]:
        last_res = _SESSION_RESULTS[session_id][-1]
        # Clone with updated timing
        return SuspicionResult(
            session_id=session_id,
            window_start=datetime.now(timezone.utc),
            suspicion_score=last_res.suspicion_score,
            flag=last_res.flag,
            contributors=last_res.contributors,
            signals=last_res.signals,
            sampling_interval_ms=target_interval,
        )

    qm.mark_in_flight_start(session_id)
    try:
        frame = None
        if cv2 is not None and image_base64:
            try:
                raw_b64 = image_base64
                if "," in raw_b64:
                    raw_b64 = raw_b64.split(",", 1)[1]
                img_bytes = base64.b64decode(raw_b64)
                np_arr = np.frombuffer(img_bytes, np.uint8)
                frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            except Exception as e:
                logger.warning("Frame decode error: %s", e)

        visual_signals = {}
        if not settings.enable_heavy_ai:
            visual_signals = {"inference_status": "FREE_TIER_CPU_ONLY"}
        elif frame is not None and frame.size > 0:
            vp = get_visual_pipeline()
            if vp is not None:
                try:
                    visual_signals = vp.process_frame(frame)
                    visual_signals["inference_status"] = "ACTIVE"
                except Exception as e:
                    logger.warning("Visual AI pipeline processing error: %s", e)
                    visual_signals = {"inference_status": "INFERENCE_UNAVAILABLE"}
            else:
                visual_signals = {"inference_status": "INFERENCE_UNAVAILABLE"}
        else:
            visual_signals = {"inference_status": "INFERENCE_UNAVAILABLE"}

        result = process_window_inference(
            session_id=session_id,
            visual_signals=visual_signals,
            audio_signals=audio_signals,
            browser_signals=browser_signals,
            mode=mode,
        )
        result.sampling_interval_ms = target_interval
        return result
    finally:
        qm.mark_in_flight_end(session_id)
