"""
Modality ablation study module (Phase 4).

Systematically masks/removes one modality at a time to evaluate its
direct contribution to overall classification performance:
- without_gaze
- without_head_pose
- without_multi_person
- without_audio
- without_tab_behavior
- without_emotion (crucial for evaluating emotion as differentiator)
"""
from typing import Any, Callable, Dict, List, Optional
import numpy as np

from evaluation.metrics import compute_metrics
from ml.utils.feature_standardizer import MODALITY_SLICES, FEATURE_DIM


def mask_modality(X: np.ndarray, modality: str) -> np.ndarray:
    """
    Zeros out the feature dimensions corresponding to a specific modality.
    """
    X_ablated = X.copy()
    if modality not in MODALITY_SLICES:
        raise KeyError(f"Unknown modality '{modality}'. Options: {list(MODALITY_SLICES.keys())}")
    start, end = MODALITY_SLICES[modality]
    X_ablated[..., start:end] = 0.0
    return X_ablated


def run_ablation(
    predict_fn: Callable[[np.ndarray], np.ndarray],
    X_test: np.ndarray,
    y_test: np.ndarray,
    modalities_to_ablate: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Performs leave-one-modality-out ablation study.

    Args:
        predict_fn: Callable taking feature array X and returning predicted probabilities (N,).
        X_test: Test feature vectors of shape (N, 24) or sequences (N, seq_len, 24).
        y_test: Ground truth binary labels of shape (N,).
        modalities_to_ablate: List of modalities to test. Defaults to all 6 modalities.

    Returns:
        Structured dictionary showing full system performance vs. each ablated variation.
    """
    if modalities_to_ablate is None:
        modalities_to_ablate = ["gaze", "head_pose", "person", "audio", "tab", "emotion"]

    # Full system evaluation
    prob_full = predict_fn(X_test)
    pred_full = (prob_full >= 0.5).astype(int)
    full_metrics = compute_metrics(y_test, pred_full, prob_full)

    ablation_results: Dict[str, Any] = {
        "full_system": full_metrics,
        "ablations": {},
        "impact_ranking": [],
    }

    impact_list = []
    base_f1 = full_metrics.get("f1_score", 0.0)
    base_acc = full_metrics.get("accuracy", 0.0)

    for mod in modalities_to_ablate:
        X_abl = mask_modality(X_test, mod)
        prob_abl = predict_fn(X_abl)
        pred_abl = (prob_abl >= 0.5).astype(int)
        abl_metrics = compute_metrics(y_test, pred_abl, prob_abl)

        acc_drop = round(base_acc - abl_metrics.get("accuracy", 0.0), 4)
        f1_drop = round(base_f1 - abl_metrics.get("f1_score", 0.0), 4)

        ablation_results["ablations"][f"without_{mod}"] = {
            "metrics": abl_metrics,
            "accuracy_drop": acc_drop,
            "f1_drop": f1_drop,
        }
        impact_list.append((mod, f1_drop, acc_drop))

    # Rank modalities by contribution (highest drop when removed = highest importance)
    impact_list.sort(key=lambda item: item[1], reverse=True)
    ablation_results["impact_ranking"] = [
        {"modality": mod, "f1_drop": f1_d, "accuracy_drop": acc_d}
        for mod, f1_d, acc_d in impact_list
    ]

    return ablation_results
