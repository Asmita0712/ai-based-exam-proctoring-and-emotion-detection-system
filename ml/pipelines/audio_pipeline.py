"""
Audio pipeline: orchestrates VAD-based speech activity detection over
microphone audio chunks.

Phase 0: interface stub only, see ml/pipelines/visual_pipeline.py for
the rationale.
"""
from typing import Any


def process_audio_chunk(chunk: Any, sample_rate: int) -> dict:
    """
    Args:
        chunk: raw audio samples for one short window.
        sample_rate: sample rate of the input audio.

    Returns:
        A structured dict with speech activity signals.
        Implemented in Phase 1 (Silero VAD integration).
    """
    raise NotImplementedError("Implemented in Phase 1: audio_vad module.")
