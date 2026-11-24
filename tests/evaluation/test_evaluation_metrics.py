"""
Unit tests for evaluation metrics, ablation, and baseline comparison (Phase 4).
"""
import numpy as np
import pytest

from evaluation.metrics import compute_metrics
from evaluation.ablation import run_ablation, mask_modality
from evaluation.baseline_comparison import compare_to_baseline, PUBLISHED_BASELINE

pytestmark = pytest.mark.integration


def test_compute_metrics():
    y_true = [0, 1, 0, 1, 1]
    y_pred = [0, 1, 0, 1, 0]
    y_prob = [0.1, 0.9, 0.2, 0.85, 0.4]

    metrics = compute_metrics(y_true, y_pred, y_prob)
    assert "accuracy" in metrics
    assert "f1_score" in metrics
    assert "precision" in metrics
    assert "recall" in metrics
    assert "mcc" in metrics
    assert "false_positive_rate" in metrics
    assert "roc_auc" in metrics
    assert "confusion_matrix" in metrics
    assert metrics["sample_count"] == 5
    assert metrics["accuracy"] == 0.8


def test_compare_to_baseline():
    our_metrics = {"accuracy": 0.92, "f1_score": 0.91}
    comp = compare_to_baseline(our_metrics)

    assert comp["outperforms_baseline"] is True
    assert comp["accuracy_delta"] == round(0.92 - PUBLISHED_BASELINE["accuracy"], 4)
    assert "summary" in comp


def test_mask_modality():
    X = np.ones((5, 24), dtype=np.float32)
    # Gaze is slice (0, 4)
    X_abl = mask_modality(X, "gaze")
    assert np.all(X_abl[:, 0:4] == 0.0)
    assert np.all(X_abl[:, 4:24] == 1.0)


def test_run_ablation():
    X_test = np.random.randn(10, 24).astype(np.float32)
    y_test = np.random.randint(0, 2, size=(10,)).astype(int)

    def dummy_predict(X):
        return np.clip(np.mean(X, axis=1) * 0.5 + 0.5, 0.0, 1.0)

    ablation = run_ablation(dummy_predict, X_test, y_test, modalities_to_ablate=["gaze", "emotion"])
    assert "full_system" in ablation
    assert "without_gaze" in ablation["ablations"]
    assert "without_emotion" in ablation["ablations"]
    assert len(ablation["impact_ranking"]) == 2
