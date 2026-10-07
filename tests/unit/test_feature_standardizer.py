"""
Unit tests for FeatureStandardizer (Phase 3 Part A).
"""
import numpy as np
import pytest

from ml.utils.feature_standardizer import FeatureStandardizer, FEATURE_DIM, MODALITY_SLICES


def test_feature_standardizer_dimensions():
    standardizer = FeatureStandardizer()
    assert standardizer.feature_dim == 24
    assert len(standardizer.feature_names) == 24

    # Empty window
    vec = standardizer.vectorize({})
    assert isinstance(vec, np.ndarray)
    assert vec.shape == (24,)
    assert vec.dtype == np.float32


def test_feature_standardizer_values():
    standardizer = FeatureStandardizer()
    window = {
        "person_count": 2,
        "multi_person_flag": True,
        "looking_away": True,
        "turned_away": True,
        "speech_probability": 0.8,
        "sustained_talking": True,
        "tab_hidden": True,
        "emotion": {
            "dominant_emotion": "fear",
            "emotion_confidence": 0.75,
            "emotion_scores": {"fear": 0.75, "neutral": 0.25},
        },
    }
    vec = standardizer.vectorize(window)

    # Looking away is index 2
    assert vec[2] == 1.0
    # Turned away is index 7
    assert vec[7] == 1.0
    # Multi person flag is index 9
    assert vec[9] == 1.0
    # Sustained talking is index 12
    assert vec[12] == 1.0
    # Tab hidden is index 13
    assert vec[13] == 1.0
    # Emotion fear is index 18
    assert vec[18] == 0.75


def test_batch_vectorize():
    standardizer = FeatureStandardizer()
    windows = [{}, {"person_count": 1}, {"person_count": 2}]
    mat = standardizer.batch_vectorize(windows)

    assert mat.shape == (3, 24)
