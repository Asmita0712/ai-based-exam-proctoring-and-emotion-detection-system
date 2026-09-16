"""
Unit tests for SileroVADDetector.
"""
import numpy as np
import pytest
from ml.models.audio.vad_detector import SileroVADDetector


def test_silero_vad_silence():
    vad = SileroVADDetector(sample_rate=16000, speech_threshold=0.5, rolling_window_chunks=5)

    # 5 chunks of pure silence
    silence = np.zeros(512, dtype=np.float32)
    for _ in range(5):
        res = vad.process_chunk(silence)

    assert "speech_probability" in res
    assert "sustained_talking" in res
    assert res["sustained_talking"] is False
    assert res["speech_probability"] < 0.2


def test_silero_vad_buffer():
    vad = SileroVADDetector(sample_rate=16000)
    # 1 second of silence buffer
    buffer = np.zeros(16000, dtype=np.float32)
    res = vad.process_audio_buffer(buffer)

    assert "speech_probability" in res
    assert "sustained_talking" in res
    assert res["sustained_talking"] is False
