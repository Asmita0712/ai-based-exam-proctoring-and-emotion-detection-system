"""
Full Evaluation Pipeline Script (Phase 4).

Executes:
1. Model evaluation across test set (Accuracy, Precision, Recall, F1, MCC, ROC-AUC, FPR)
2. Modality ablation study (Leave-one-out for all 6 modalities including Emotion)
3. Baseline comparison against Lamba & Sharma CNN-BiLSTM (87.5% accuracy)
Saves results into evaluation_report.json and prints human-readable summary table.
"""
import argparse
import json
import os
from typing import Any, Dict
import numpy as np

from evaluation.metrics import compute_metrics
from evaluation.ablation import run_ablation
from evaluation.baseline_comparison import compare_to_baseline
from ml.fusion.learned_fusion import LearnedFusion
from ml.temporal.bilstm import BiLSTMTemporalModel
from ml.temporal.sequence_builder import build_sequences


def run_full_evaluation(
    features_dir: str = "data/features",
    checkpoints_dir: str = "models/checkpoints",
    output_path: str = "docs/experiments/evaluation_report.json",
    seq_length: int = 15,
) -> Dict[str, Any]:
    """
    Evaluates trained models on the test set, performs ablation, and compares to baseline.
    """
    X_test_path = os.path.join(features_dir, "X_test.npy")
    y_test_path = os.path.join(features_dir, "y_test.npy")

    if not os.path.exists(X_test_path) or not os.path.exists(y_test_path):
        raise FileNotFoundError(f"Test data not found in '{features_dir}'. Run extract_features.py first.")

    X_test = np.load(X_test_path)
    y_test = np.load(y_test_path)

    # Load models
    mlp_path = os.path.join(checkpoints_dir, "learned_fusion.pth")
    bilstm_path = os.path.join(checkpoints_dir, "bilstm_temporal.pth")

    fusion_mlp = LearnedFusion(model_type="mlp", weights_path=mlp_path if os.path.exists(mlp_path) else None)
    bilstm = BiLSTMTemporalModel(weights_path=bilstm_path if os.path.exists(bilstm_path) else None, sequence_length=seq_length)

    print("\n=======================================================")
    print("            PHASE 4 SCIENTIFIC EVALUATION             ")
    print("=======================================================")

    # 1. Learned Fusion Evaluation
    mlp_probs = np.array([fusion_mlp.predict_proba(x) for x in X_test])
    mlp_preds = (mlp_probs >= 0.5).astype(int)
    mlp_metrics = compute_metrics(y_test, mlp_preds, mlp_probs)

    print("\n--- [1] Learned Multimodal Fusion (MLP) Test Metrics ---")
    print(f"Accuracy: {mlp_metrics['accuracy'] * 100:.2f}%")
    print(f"F1-Score: {mlp_metrics['f1_score']:.4f}")
    print(f"Precision: {mlp_metrics['precision']:.4f} | Recall: {mlp_metrics['recall']:.4f}")
    print(f"MCC: {mlp_metrics['mcc']:.4f} | False Positive Rate: {mlp_metrics['false_positive_rate']:.4f}")
    if mlp_metrics.get("roc_auc"):
        print(f"ROC-AUC: {mlp_metrics['roc_auc']:.4f}")

    # 2. Temporal BiLSTM Evaluation
    X_test_seq = build_sequences(list(X_test), sequence_length=seq_length, step=1)
    y_test_seq = np.array([
        1.0 if np.mean(y_test[i : i + seq_length]) >= 0.25 else 0.0
        for i in range(0, len(y_test) - seq_length + 1, 1)
    ], dtype=np.float32)

    if len(y_test_seq) < len(X_test_seq):
        y_test_seq = np.pad(y_test_seq, (0, len(X_test_seq) - len(y_test_seq)), mode='edge')
    elif len(y_test_seq) > len(X_test_seq):
        y_test_seq = y_test_seq[: len(X_test_seq)]

    bilstm_probs = np.array([bilstm.predict_sequence(seq)["suspicion_probability"] for seq in X_test_seq])
    bilstm_preds = (bilstm_probs >= 0.5).astype(int)
    bilstm_metrics = compute_metrics(y_test_seq, bilstm_preds, bilstm_probs)

    print("\n--- [2] Learned Fusion + Temporal Context (BiLSTM) Metrics ---")
    print(f"Accuracy: {bilstm_metrics['accuracy'] * 100:.2f}%")
    print(f"F1-Score: {bilstm_metrics['f1_score']:.4f}")
    print(f"Precision: {bilstm_metrics['precision']:.4f} | Recall: {bilstm_metrics['recall']:.4f}")
    print(f"MCC: {bilstm_metrics['mcc']:.4f} | False Positive Rate: {bilstm_metrics['false_positive_rate']:.4f}")

    # 3. Modality Ablation Study
    print("\n--- [3] Modality Ablation Study (Leave-One-Out) ---")
    ablation_res = run_ablation(
        predict_fn=lambda X: np.array([fusion_mlp.predict_proba(x) for x in X]),
        X_test=X_test,
        y_test=y_test,
    )
    for rank_idx, item in enumerate(ablation_res["impact_ranking"], 1):
        print(f"Rank {rank_idx}: Modality '{item['modality']}' -> F1 drop when removed: {item['f1_drop']:.4f} (Accuracy drop: {item['accuracy_drop']:.4f})")

    # 4. Baseline Comparison against Lamba & Sharma
    print("\n--- [4] Comparison against Published Baseline (Lamba & Sharma CNN-BiLSTM 87.5%) ---")
    comparison = compare_to_baseline(bilstm_metrics)
    print(comparison["summary"])

    report = {
        "mlp_fusion_metrics": mlp_metrics,
        "bilstm_temporal_metrics": bilstm_metrics,
        "ablation_study": ablation_res,
        "baseline_comparison": comparison,
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nFull scientific evaluation report saved to: {output_path}")

    return report


def main():
    parser = argparse.ArgumentParser(description="Run scientific evaluation, ablation study, and baseline comparison.")
    parser.add_argument("--features_dir", default="data/features")
    parser.add_argument("--checkpoints_dir", default="models/checkpoints")
    parser.add_argument("--output_path", default="docs/experiments/evaluation_report.json")
    args = parser.parse_args()

    run_full_evaluation(
        features_dir=args.features_dir,
        checkpoints_dir=args.checkpoints_dir,
        output_path=args.output_path,
    )


if __name__ == "__main__":
    main()
