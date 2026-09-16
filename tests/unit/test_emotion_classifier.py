"""
Unit tests for EmotionClassifier (Phase 2).
"""
import numpy as np
import pytest

from ml.models.emotion.emotion_classifier import EmotionClassifier, EMOTION_LABELS


def test_emotion_classifier_normal_face():
    classifier = EmotionClassifier(device="cpu", smoothing_window=5)
    # Synthetic face crop (e.g. 80x80 BGR image)
    fake_face = np.random.randint(50, 200, (80, 80, 3), dtype=np.uint8)

    res = classifier.predict(fake_face)

    assert "dominant_emotion" in res
    assert "emotion_confidence" in res
    assert "emotion_scores" in res
    assert res["dominant_emotion"] in EMOTION_LABELS
    assert 0.0 <= res["emotion_confidence"] <= 1.0
    assert len(res["emotion_scores"]) == 7


def test_emotion_classifier_missing_face():
    classifier = EmotionClassifier(device="cpu")

    # None input
    res_none = classifier.predict(None)
    assert res_none["dominant_emotion"] == "neutral"
    assert res_none["emotion_confidence"] == 0.0

    # Empty array input
    res_empty = classifier.predict(np.zeros((0, 0, 3), dtype=np.uint8))
    assert res_empty["dominant_emotion"] == "neutral"
    assert res_empty["emotion_confidence"] == 0.0

    # Tiny array (< 10x10)
    res_tiny = classifier.predict(np.zeros((4, 4, 3), dtype=np.uint8))
    assert res_tiny["dominant_emotion"] == "neutral"
    assert res_tiny["emotion_confidence"] == 0.0


def test_emotion_temporal_smoothing():
    classifier = EmotionClassifier(device="cpu", smoothing_window=4)
    fake_face = np.ones((64, 64, 3), dtype=np.uint8) * 128

    # Pass 4 consecutive frames
    for _ in range(4):
        res = classifier.predict(fake_face)

    assert len(classifier.history) == 4
    assert res["dominant_emotion"] in EMOTION_LABELS
