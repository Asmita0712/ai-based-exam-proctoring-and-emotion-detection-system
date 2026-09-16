"""
Pydantic schemas for suspicion results / evidence output.

Fields here intentionally mirror the common feature representation
described in the architecture (RULE 6), so the API layer never needs
its own parallel definition of what a "result" looks like.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ModalitySignals(BaseModel):
    """Per-modality signals for one time window. All optional in Phase 0
    since no modality is implemented yet -- populated stage by stage
    through Phase 1 and Phase 2."""
    gaze_ratio: Optional[float] = None
    looking_away: Optional[bool] = None
    yaw: Optional[float] = None
    pitch: Optional[float] = None
    turned_away: Optional[bool] = None
    person_count: Optional[int] = None
    multi_person_flag: Optional[bool] = None
    speech_probability: Optional[float] = None
    sustained_talking: Optional[bool] = None
    tab_hidden: Optional[bool] = None
    dominant_emotion: Optional[str] = None
    emotion_confidence: Optional[float] = None


class SuspicionResult(BaseModel):
    session_id: str
    window_start: datetime
    suspicion_score: float
    flag: bool
    contributors: list[str] = []
    signals: ModalitySignals
