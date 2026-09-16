"""
Visual pipeline: orchestrates face/person, gaze, head-pose, and (from
Phase 2) emotion modules over a single video frame.

Phase 0: interface stub only. RULE 15 -- the project must stay usable
even before advanced models exist, so this raises NotImplementedError
rather than silently returning fake data.
"""
from typing import Any


def process_frame(frame: Any) -> dict:
    """
    Args:
        frame: a single video frame (e.g. a numpy array from OpenCV).

    Returns:
        A structured dict of per-modality visual signals for this frame.
        Implemented incrementally in Phase 1 (face/gaze/head-pose) and
        Phase 2 (emotion).
    """
    raise NotImplementedError("Implemented in Phase 1: visual modality modules.")
