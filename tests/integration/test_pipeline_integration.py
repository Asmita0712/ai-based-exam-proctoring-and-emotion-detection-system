"""
Integration tests for Phase 1 multimodal proctoring pipelines.
"""
import numpy as np
import pytest

from ml.pipelines.visual_pipeline import VisualPipeline
from ml.pipelines.audio_pipeline import AudioPipeline
from ml.pipelines.feature_pipeline import build_feature_window
from ml.pipelines.inference_pipeline import run_inference
from ml.utils.tab_tracker import TabTracker


def test_full_multimodal_pipeline_integration():
    # 1. Initialize pipelines
    visual_pipe = VisualPipeline()
    audio_pipe = AudioPipeline(sample_rate=16000)
    tab_tracker = TabTracker()

    # 2. Process synthetic visual frame (e.g. blank canvas)
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    visual_signals = visual_pipe.process_frame(dummy_frame)

    assert "person_count" in visual_signals
    assert "gaze" in visual_signals
    assert "head_pose" in visual_signals

    # 3. Process synthetic audio chunk
    dummy_audio = np.zeros(512, dtype=np.float32)
    audio_signals = audio_pipe.process_chunk(dummy_audio)

    assert "speech_probability" in audio_signals
    assert "sustained_talking" in audio_signals

    # 4. Simulate browser event
    tab_tracker.record_event("tab_hidden")
    browser_status = tab_tracker.get_status()

    assert browser_status["tab_hidden"] is True
    assert browser_status["switch_count"] == 1

    # 5. Build unified timestamped feature window
    feature_window = build_feature_window(
        visual_signals=visual_signals,
        audio_signals=audio_signals,
        browser_events=[browser_status],
        window_start=1700000000.0,
    )

    assert feature_window["timestamp"] == 1700000000.0
    assert feature_window["tab_hidden"] is True

    # 6. Run end-to-end inference
    result = run_inference(session_id="test_session_123", feature_window=feature_window)

    assert result["session_id"] == "test_session_123"
    assert "suspicion_score" in result
    assert "flag" in result
    assert "contributors" in result
    assert isinstance(result["contributors"], list)
    # The tab was hidden and no person detected in zero-frame, so both should contribute
    assert "browser_focus_lost" in result["contributors"]
    assert "no_person_detected" in result["contributors"]
