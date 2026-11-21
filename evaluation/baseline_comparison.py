"""
Baseline comparison against published literature (Phase 4).

Compares our measured system results against the Lamba & Sharma
CNN-BiLSTM baseline (87.5% accuracy) documented in the project synopsis.
"""
from typing import Any, Dict


PUBLISHED_BASELINE = {
    "source": "Lamba & Sharma (CNN-BiLSTM)",
    "accuracy": 0.875,
    "description": "Multimodal baseline using CNN for spatial features and BiLSTM for temporal sequence context."
}


def compare_to_baseline(our_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compares our empirical system metrics to the published benchmark.

    Args:
        our_metrics: Dictionary containing at least 'accuracy' and optionally 'f1_score', 'mcc', etc.

    Returns:
        Structured comparison dictionary highlighting baseline vs. current performance.
    """
    our_acc = float(our_metrics.get("accuracy", 0.0))
    base_acc = float(PUBLISHED_BASELINE["accuracy"])
    diff = round(our_acc - base_acc, 4)

    return {
        "published_baseline": PUBLISHED_BASELINE,
        "our_system": {
            "accuracy": our_acc,
            "f1_score": our_metrics.get("f1_score"),
            "mcc": our_metrics.get("mcc"),
            "false_positive_rate": our_metrics.get("false_positive_rate"),
        },
        "accuracy_delta": diff,
        "outperforms_baseline": bool(diff >= 0.0),
        "summary": (
            f"Our system achieved {our_acc * 100:.2f}% accuracy compared to the "
            f"published {base_acc * 100:.2f}% baseline (Delta: {diff * 100:+.2f}%)."
        ),
    }
