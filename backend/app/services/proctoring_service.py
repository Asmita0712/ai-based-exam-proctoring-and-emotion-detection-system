"""
Proctoring service -- the seam between the API layer and ml/pipelines.

RULE 2 / RULE 3: FastAPI routes call into this service; this service
(not the routes) is responsible for eventually calling into
ml/pipelines/inference_pipeline.py.

Phase 0: intentionally not implemented yet. No ML code exists to call
into. This is the documented placeholder Phase 1 will fill in.
"""
from app.schemas.events import BrowserEvent


def record_browser_event(event: BrowserEvent) -> None:
    """
    Placeholder. Phase 1 will persist/forward this event into the
    feature-extraction pipeline. Deliberately not implemented in
    Phase 0 to avoid faking behavior that doesn't exist yet.
    """
    raise NotImplementedError(
        "record_browser_event is implemented in Phase 1 "
        "(tab/window tracking integration)."
    )
