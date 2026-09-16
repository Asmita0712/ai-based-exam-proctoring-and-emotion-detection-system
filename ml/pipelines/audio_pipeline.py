"""
Audio pipeline: orchestrates VAD-based speech activity detection over audio chunks.

Adheres to:
- RULE 4: Clean reusable interface
- RULE 10: Configurable thresholds
- RULE 14: Runs on CPU
"""
from typing import Any, Dict, Optional, Union
import numpy as np
import torch

from ml.models.audio.vad_detector import SileroVADDetector


class AudioPipeline:
    """Orchestrates audio activity detection using Silero VAD."""

    def __init__(self, sample_rate: int = 16000, speech_threshold: float = 0.5) -> None:
        self.sample_rate = sample_rate
        self.detector = SileroVADDetector(sample_rate=sample_rate, speech_threshold=speech_threshold)

    def process_chunk(self, chunk: Union[np.ndarray, torch.Tensor]) -> Dict[str, Any]:
        """
        Processes a single audio chunk and returns speech activity metrics.
        """
        return self.detector.process_chunk(chunk)

    def process_buffer(self, buffer: Union[np.ndarray, torch.Tensor]) -> Dict[str, Any]:
        """
        Processes an arbitrary audio buffer.
        """
        return self.detector.process_audio_buffer(buffer)

    def reset(self) -> None:
        self.detector.reset()


_DEFAULT_AUDIO_PIPELINE: Optional[AudioPipeline] = None


def get_audio_pipeline() -> AudioPipeline:
    global _DEFAULT_AUDIO_PIPELINE
    if _DEFAULT_AUDIO_PIPELINE is None:
        _DEFAULT_AUDIO_PIPELINE = AudioPipeline()
    return _DEFAULT_AUDIO_PIPELINE


def process_audio_chunk(chunk: Any, sample_rate: int = 16000) -> Dict[str, Any]:
    """Module-level entrypoint for audio chunk processing."""
    pipeline = get_audio_pipeline()
    if pipeline.sample_rate != sample_rate:
        pipeline = AudioPipeline(sample_rate=sample_rate)
    return pipeline.process_chunk(chunk)
