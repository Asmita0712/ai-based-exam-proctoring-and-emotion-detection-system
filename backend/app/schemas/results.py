"""
Pydantic schemas for suspicion results / evidence output and forensic summaries.
"""
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel


class ModalitySignals(BaseModel):
    """Per-modality signals for one time window."""
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
    contributors: List[str] = []
    signals: ModalitySignals
    sampling_interval_ms: Optional[int] = 1000
    inference_status: Optional[str] = "ACTIVE"


class ExamSummary(BaseModel):
    session_id: str
    total_frames_analyzed: int
    exam_duration_seconds: float
    flagged_frames_count: int
    flagged_percentage: float
    integrity_score: float
    verdict: str
    verdict_label: str
    verdict_color: str
    violations_summary: Dict[str, int] = {}
    dominant_emotion: str = "neutral"
    top_contributors: List[str] = []
    monitoring_coverage_pct: float = 100.0
    monitoring_gaps_count: int = 0
    delayed_frames_count: int = 0
