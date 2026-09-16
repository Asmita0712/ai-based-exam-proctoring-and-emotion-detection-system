"""
Proctoring service -- the seam between the API layer and ml/pipelines.

RULE 2 / RULE 3: FastAPI routes call into this service; this service
(not the routes) is responsible for eventually calling into
ml/pipelines/inference_pipeline.py.

Phase 0: intentionally not implemented yet. No ML code exists to call
into. This is the documented placeholder Phase 1 will fill in.
"""
from typing import Any, Dict
from app.schemas.events import BrowserEvent
from ml.utils.tab_tracker import TabTracker

# Active session tab trackers: session_id -> TabTracker
_SESSION_TAB_TRACKERS: Dict[str, TabTracker] = {}


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
