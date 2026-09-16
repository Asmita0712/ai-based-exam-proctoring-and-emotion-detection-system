"""
Feature pipeline: merges visual, audio, and browser-event signals into
the common per-window feature representation (RULE 5 & RULE 6).
"""
import time
from typing import Any, Dict, List, Optional


def build_feature_window(
    visual_signals: Optional[Dict[str, Any]] = None,
    audio_signals: Optional[Dict[str, Any]] = None,
    browser_events: Optional[List[Dict[str, Any]]] = None,
    window_start: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Returns a single timestamped feature dict combining all modalities
    for one time window.

    Adheres to:
    - RULE 5: Timestamped window-level features
    - RULE 6: Common feature representation before fusion
    - Gracefully handles missing modality dictionaries
    """
    now = window_start if window_start is not None else time.time()
    visual = visual_signals or {}
    audio = audio_signals or {}
    events = browser_events or []

    # Calculate browser summary for window
    tab_hidden = any(e.get("type") == "tab_hidden" for e in events) or any(e.get("tab_hidden", False) for e in events)
    window_blur = any(e.get("type") == "window_blur" for e in events) or any(e.get("window_blur", False) for e in events)
    is_away = tab_hidden or window_blur

    return {
        "timestamp": now,
        # Visual signals
        "person_count": visual.get("person_count", 1),
        "multi_person_flag": visual.get("multi_person_flag", False),
        "no_person_flag": visual.get("no_person_flag", False),
        "gaze": visual.get("gaze", {}),
        "looking_away": visual.get("looking_away", False),
        "head_pose": visual.get("head_pose", {}),
        "turned_away": visual.get("turned_away", False),
        # Audio signals
        "audio": audio,
        "speech_probability": audio.get("speech_probability", 0.0),
        "sustained_talking": audio.get("sustained_talking", False),
        # Browser signals
        "tab_hidden": tab_hidden,
        "window_blur": window_blur,
        "is_away": is_away,
        "browser_events_count": len(events),
        # Modality placeholder for Phase 2
        "emotion": None,
    }
