"""
Modality importance and contribution analysis module (Phase 3, Part C).

Adheres to:
- RULE 9: Preserves modality-level outputs for explainability and ablation
- Answers: "How much does gaze, head pose, person, audio, tab, and emotion contribute?"
- Never invents values -- derives them directly from model weight magnitudes or input attributions
"""
from typing import Any, Dict, Optional, Union
import numpy as np
import torch

from ml.fusion.learned_fusion import LearnedFusion, LogisticRegressionFusion, MLPFusionModel
from ml.utils.feature_standardizer import MODALITY_SLICES, FEATURE_DIM


def compute_modality_importance(
    fusion_engine: Union[LearnedFusion, torch.nn.Module],
    sample_X: Optional[np.ndarray] = None,
) -> Dict[str, float]:
    """
    Computes normalized relative importance [0.0 - 1.0] for each modality
    based on the trained model parameters and input gradients.

    Args:
        fusion_engine: An instance of LearnedFusion or an underlying PyTorch nn.Module.
        sample_X: Optional 2D array of feature samples (N, 24) for gradient attribution.

    Returns:
        Dictionary mapping modality name to fractional contribution (summing to 1.0):
        {
            "gaze": float,
            "head_pose": float,
            "person": float,
            "audio": float,
            "tab": float,
            "emotion": float,
        }
    """
    model = fusion_engine.model if isinstance(fusion_engine, LearnedFusion) else fusion_engine
    model.eval()

    device = next(model.parameters()).device

    # 1. Linear / Logistic Regression model
    if isinstance(model, LogisticRegressionFusion) or hasattr(model, "linear"):
        with torch.no_grad():
            w = torch.abs(model.linear.weight.squeeze()).cpu().numpy()
            feature_importance = w

    # 2. PyTorch MLP: Gradient-based or first-layer weight magnitude
    elif isinstance(model, MLPFusionModel) or hasattr(model, "net"):
        if sample_X is not None and len(sample_X) > 0:
            # Gradient attribution over sample data
            X_tensor = torch.from_numpy(sample_X.astype(np.float32)).to(device)
            X_tensor.requires_grad = True
            out = model(X_tensor)
            out.sum().backward()
            feature_importance = torch.abs(X_tensor.grad).mean(dim=0).cpu().numpy()
        else:
            # Input-layer connection weights magnitude: sum of abs weights entering first layer
            first_linear = model.net[0]
            with torch.no_grad():
                feature_importance = torch.abs(first_linear.weight).sum(dim=0).cpu().numpy()
    else:
        # Fallback to equal weighting if unknown
        feature_importance = np.ones(FEATURE_DIM, dtype=np.float32)

    # Aggregate importance per modality slice
    modality_scores: Dict[str, float] = {}
    for modality_name, (start, end) in MODALITY_SLICES.items():
        slice_imp = float(np.sum(feature_importance[start:end]))
        modality_scores[modality_name] = max(0.0, slice_imp)

    total = sum(modality_scores.values())
    if total > 1e-8:
        return {k: round(v / total, 4) for k, v in modality_scores.items()}
    else:
        # Uniform distribution fallback
        uniform = round(1.0 / len(MODALITY_SLICES), 4)
        return {k: uniform for k in MODALITY_SLICES}
