"""
Unit tests for PersonDetector and MultiPersonTracker.
"""
import numpy as np
import pytest
from ml.models.face.person_detector import PersonDetector
from ml.models.face.multi_person_detector import MultiPersonTracker


def test_person_detector_empty_frame():
    detector = PersonDetector(conf_threshold=0.5, device="cpu")
    empty_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    res = detector.detect(empty_frame)

    assert "person_count" in res
    assert "boxes" in res
    assert "confidence" in res
    assert isinstance(res["person_count"], int)
    assert isinstance(res["boxes"], list)
    assert isinstance(res["confidence"], list)


def test_multi_person_tracker_debounce():
    tracker = MultiPersonTracker(history_len=5, multi_person_ratio_threshold=0.5)

    # 1 person for 4 frames: flag should be False
    for _ in range(4):
        res = tracker.update({"person_count": 1, "boxes": [[]], "confidence": [0.9]})
        assert res["multi_person_flag"] is False

    # 1 momentary glitch with 2 persons: flag should still be False (debounce)
    res = tracker.update({"person_count": 2, "boxes": [[], []], "confidence": [0.8, 0.8]})
    assert res["multi_person_flag"] is False

    # 3 consecutive multi-person frames: should trigger flag
    tracker.update({"person_count": 2, "boxes": [[], []], "confidence": [0.8, 0.8]})
    res = tracker.update({"person_count": 2, "boxes": [[], []], "confidence": [0.8, 0.8]})
    assert res["multi_person_flag"] is True
