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
    assert "emotion" in visual_signals
    assert visual_signals["emotion"]["dominant_emotion"] == "neutral"

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
    assert "emotion" in feature_window
    assert feature_window["dominant_emotion"] == "neutral"
    assert "emotion_confidence" in feature_window

    # 6. Run end-to-end inference across all 3 modes (Part E)
    # Mode A: Baseline rule-based
    res_base = run_inference(session_id="test_session_123", feature_window=feature_window, mode="baseline")
    assert res_base["session_id"] == "test_session_123"
    assert res_base["mode"] == "baseline"
    assert "suspicion_score" in res_base
    assert "browser_focus_lost" in res_base["contributors"]
    assert "no_person_detected" in res_base["contributors"]

    # Mode B: Learned fusion
    res_learned = run_inference(session_id="test_session_123", feature_window=feature_window, mode="learned")
    assert res_learned["mode"] == "learned"
    assert "modality_importance" in res_learned
    assert "gaze" in res_learned["modality_importance"]

    # Mode C: Temporal BiLSTM
    res_temporal = run_inference(session_id="test_session_123", feature_window=feature_window, mode="temporal")
    assert res_temporal["mode"] == "temporal"
    assert "temporal_context" in res_temporal
    assert "is_sustained" in res_temporal["temporal_context"]
