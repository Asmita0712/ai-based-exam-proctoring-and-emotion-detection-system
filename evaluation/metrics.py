"""
Evaluation metrics calculation module (Phase 4).

Computes:
- Accuracy
- Precision
- Recall
- F1 / F-score
- Matthews Correlation Coefficient (MCC)
- ROC-AUC (when probabilities provided)
- False Positive Rate (FPR)
- Confusion Matrix [[TN, FP], [FN, TP]]
"""
from typing import Any, Dict, Optional, Union
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    matthews_corrcoef,
    roc_auc_score,
    confusion_matrix,
)


def compute_metrics(
    y_true: Union[list, np.ndarray],
    y_pred: Union[list, np.ndarray],
    y_prob: Optional[Union[list, np.ndarray]] = None,
) -> Dict[str, Any]:
    """
    Computes scientific classification and proctoring evaluation metrics.

    Args:
        y_true: Ground truth binary labels (0 = not suspicious, 1 = suspicious).
        y_pred: Predicted binary labels (0 or 1).
        y_prob: Predicted suspicion probabilities [0.0 - 1.0] (optional).

    Returns:
        Structured dictionary of computed metrics.
    """
    y_t = np.asarray(y_true).astype(int)
    y_p = np.asarray(y_pred).astype(int)

    if len(y_t) == 0:
        return {}

    acc = float(accuracy_score(y_t, y_p))
    prec = float(precision_score(y_t, y_p, zero_division=0))
    rec = float(recall_score(y_t, y_p, zero_division=0))
    f1 = float(f1_score(y_t, y_p, zero_division=0))
    mcc = float(matthews_corrcoef(y_t, y_p))

    # Confusion matrix: [[TN, FP], [FN, TP]]
    cm = confusion_matrix(y_t, y_p, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    # False Positive Rate: FP / (FP + TN)
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0

    # ROC-AUC
    roc_auc = None
    if y_prob is not None:
        y_pr = np.asarray(y_prob).astype(float)
        # roc_auc requires at least 2 distinct classes in y_true
        if len(np.unique(y_t)) > 1:
            try:
                roc_auc = float(roc_auc_score(y_t, y_pr))
            except Exception:
                roc_auc = None

    return {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "mcc": round(mcc, 4),
        "false_positive_rate": round(fpr, 4),
        "roc_auc": round(roc_auc, 4) if roc_auc is not None else None,
        "confusion_matrix": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp),
        },
        "sample_count": int(len(y_t)),
    }
