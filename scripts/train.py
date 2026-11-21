"""
Model training script (Phase 4).

Trains:
1. Baseline Logistic Regression / Rule-based parameters
2. Learned Fusion MLP
3. Temporal Context BiLSTM
Saves model checkpoints under models/checkpoints/.
"""
import argparse
import os
import numpy as np

from ml.fusion.learned_fusion import LearnedFusion
from ml.temporal.bilstm import BiLSTMTemporalModel
from ml.temporal.sequence_builder import build_sequences


def train_all_models(
    features_dir: str = "data/features",
    checkpoints_dir: str = "models/checkpoints",
    epochs_mlp: int = 40,
    epochs_bilstm: int = 35,
    seq_length: int = 15,
) -> dict:
    """
    Trains learned fusion MLP and BiLSTM models and saves checkpoints.
    """
    os.makedirs(checkpoints_dir, exist_ok=True)

    X_train_path = os.path.join(features_dir, "X_train.npy")
    y_train_path = os.path.join(features_dir, "y_train.npy")

    if not os.path.exists(X_train_path) or not os.path.exists(y_train_path):
        raise FileNotFoundError(f"Feature matrices not found in '{features_dir}'. Run extract_features.py first.")

    X_train = np.load(X_train_path)
    y_train = np.load(y_train_path)

    print(f"Training on {len(X_train)} window samples...")

    # 1. Train Learned Fusion MLP
    print("\n--- [1/2] Training Learned Fusion MLP ---")
    fusion_mlp = LearnedFusion(model_type="mlp")
    mlp_res = fusion_mlp.fit(X_train, y_train, epochs=epochs_mlp, lr=0.008, batch_size=32)
    mlp_path = os.path.join(checkpoints_dir, "learned_fusion.pth")
    fusion_mlp.save(mlp_path)
    print(f"Learned Fusion MLP trained successfully! Saved to {mlp_path}. Final loss: {mlp_res['final_loss']}")

    # 2. Train Temporal BiLSTM
    print("\n--- [2/2] Training Temporal Context BiLSTM ---")
    X_train_seq = build_sequences(list(X_train), sequence_length=seq_length, step=2)
    # Binary sequence label: 1 if at least 25% of sequence windows were suspicious
    y_train_seq = np.array([
        1.0 if np.mean(y_train[i : i + seq_length]) >= 0.25 else 0.0
        for i in range(0, len(y_train) - seq_length + 1, 2)
    ], dtype=np.float32)

    # Ensure shape alignment if padding occurred
    if len(y_train_seq) < len(X_train_seq):
        y_train_seq = np.pad(y_train_seq, (0, len(X_train_seq) - len(y_train_seq)), mode='edge')
    elif len(y_train_seq) > len(X_train_seq):
        y_train_seq = y_train_seq[: len(X_train_seq)]

    bilstm = BiLSTMTemporalModel(sequence_length=seq_length)
    bilstm_res = bilstm.fit(X_train_seq, y_train_seq, epochs=epochs_bilstm, lr=0.005, batch_size=16)
    bilstm_path = os.path.join(checkpoints_dir, "bilstm_temporal.pth")
    bilstm.save(bilstm_path)
    print(f"Temporal BiLSTM trained successfully! Saved to {bilstm_path}. Final loss: {bilstm_res['final_loss']}")

    return {
        "mlp_checkpoint": mlp_path,
        "mlp_final_loss": mlp_res["final_loss"],
        "bilstm_checkpoint": bilstm_path,
        "bilstm_final_loss": bilstm_res["final_loss"],
    }


def main():
    parser = argparse.ArgumentParser(description="Train Learned Fusion and BiLSTM models.")
    parser.add_argument("--features_dir", default="data/features")
    parser.add_argument("--checkpoints_dir", default="models/checkpoints")
    parser.add_argument("--epochs_mlp", type=int, default=30)
    parser.add_argument("--epochs_bilstm", type=int, default=25)
    parser.add_argument("--seq_length", type=int, default=15)
    args = parser.parse_args()

    train_all_models(
        features_dir=args.features_dir,
        checkpoints_dir=args.checkpoints_dir,
        epochs_mlp=args.epochs_mlp,
        epochs_bilstm=args.epochs_bilstm,
        seq_length=args.seq_length,
    )


if __name__ == "__main__":
    main()
