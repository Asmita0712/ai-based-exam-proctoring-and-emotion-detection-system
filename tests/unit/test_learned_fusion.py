"""
Unit tests for LearnedFusion (Phase 3 Part B).
"""
import numpy as np
import pytest

from ml.fusion.learned_fusion import LearnedFusion, LogisticRegressionFusion, MLPFusionModel


def test_learned_fusion_mlp_prediction():
    fusion = LearnedFusion(model_type="mlp", device="cpu")
    dummy_vec = np.zeros(24, dtype=np.float32)

    prob = fusion.predict_proba(dummy_vec)
    assert 0.0 <= prob <= 1.0

    res = fusion.predict(dummy_vec, threshold=0.5)
    assert "suspicion_score" in res
    assert "flag" in res
    assert res["model_type"] == "mlp"


def test_learned_fusion_logistic_prediction():
    fusion = LearnedFusion(model_type="logistic", device="cpu")
    dummy_vec = np.zeros(24, dtype=np.float32)

    res = fusion.predict(dummy_vec)
    assert "suspicion_score" in res
    assert res["model_type"] == "logistic"


def test_learned_fusion_training():
    fusion = LearnedFusion(model_type="mlp", device="cpu")
    # Synthetic training batch
    X = np.random.randn(20, 24).astype(np.float32)
    y = np.random.randint(0, 2, size=(20,)).astype(np.float32)

    res = fusion.fit(X, y, epochs=3, batch_size=4)
    assert res["epochs"] == 3
    assert "final_loss" in res
