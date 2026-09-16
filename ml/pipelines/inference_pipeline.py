"""
End-to-end inference pipeline: the single entrypoint the backend
(proctoring_service) will call once modalities, fusion, and the
temporal model exist.

RULE 2 / RULE 3: this is the clean interface between backend and ML --
the backend never imports individual modality modules directly.

Phase 0: interface stub only.
"""
from typing import Any


def run_inference(session_id: str, feature_window: dict) -> dict:
    """
    Returns a SuspicionResult-shaped dict:
        {"suspicion_score": ..., "flag": ..., "contributors": [...]}

    Phase 1 wires this to rule-based fusion. Phase 3 replaces the
    internals with learned fusion + temporal BiLSTM without changing
    this function's signature.
    """
    raise NotImplementedError("Implemented in Phase 1 (rule-based fusion) onward.")
