"""
Unit tests for compute_modality_importance (Phase 3 Part C).
"""
import numpy as np
import pytest

from ml.fusion.learned_fusion import LearnedFusion
from ml.fusion.modality_attention import compute_modality_importance


def test_modality_importance_mlp():
    fusion = LearnedFusion(model_type="mlp", device="cpu")
    imp = compute_modality_importance(fusion)

    assert set(imp.keys()) == {"gaze", "head_pose", "person", "audio", "tab", "emotion"}
    # Must sum to 1.0 (approx due to rounding)
    assert 0.99 <= sum(imp.values()) <= 1.01
    for k, v in imp.items():
        assert 0.0 <= v <= 1.0


def test_modality_importance_with_sample_gradients():
    fusion = LearnedFusion(model_type="mlp", device="cpu")
    sample_X = np.random.randn(5, 24).astype(np.float32)
    imp = compute_modality_importance(fusion, sample_X=sample_X)

    assert len(imp) == 6
    assert 0.99 <= sum(imp.values()) <= 1.01
