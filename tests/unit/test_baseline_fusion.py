"""
Unit tests for RuleBasedFusion baseline.
"""
import pytest
from ml.fusion.baseline_fusion import RuleBasedFusion, fuse


def test_baseline_fusion_normal():
    # Normal state: 1 person, looking at screen, head forward, no speech, tab visible
    normal_signals = {
        "person_count": 1,
        "multi_person_flag": False,
        "looking_away": False,
        "turned_away": False,
        "sustained_talking": False,
        "speech_probability": 0.05,
        "tab_hidden": False,
        "window_blur": False,
    }
    result = fuse(normal_signals)
    assert result["suspicion_score"] == 0.0
    assert result["flag"] is False
    assert len(result["contributors"]) == 0


def test_baseline_fusion_multi_and_gaze():
    # Suspicious: multiple persons and looking away
    suspicious_signals = {
        "person_count": 2,
        "multi_person_flag": True,
        "looking_away": True,
        "turned_away": False,
        "sustained_talking": False,
        "speech_probability": 0.05,
        "tab_hidden": False,
        "window_blur": False,
    }
    fusion = RuleBasedFusion(threshold=0.45)
    result = fusion.fuse(suspicious_signals)

    # 0.30 (multi_person) + 0.20 (gaze) = 0.50 >= 0.45 threshold
    assert result["suspicion_score"] >= 0.45
    assert result["flag"] is True
    assert "multiple_persons_detected" in result["contributors"]
    assert "gaze_looking_away" in result["contributors"]


def test_baseline_fusion_empty_signals():
    # Missing signals handled gracefully without errors
    result = fuse({})
    assert "suspicion_score" in result
    assert "flag" in result
    assert "contributors" in result
