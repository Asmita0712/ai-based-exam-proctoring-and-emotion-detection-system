"""
Offline feature extraction script (Phase 4).

Processes recorded sessions in data/raw/, applies FeatureStandardizer across all
windows, creates train/val/test splits partitioned STRICTLY by subject ID (RULE: no data leakage),
and saves processed feature matrices and labels into data/features/ and data/splits/.
"""
import argparse
import glob
import json
import os
from typing import Any, Dict, List, Tuple
import numpy as np

from ml.utils.feature_standardizer import FeatureStandardizer, FEATURE_DIM


def extract_features_from_sessions(
    raw_dir: str = "data/raw",
    features_dir: str = "data/features",
    splits_dir: str = "data/splits",
    train_ratio: float = 0.6,
    val_ratio: float = 0.2,
) -> Dict[str, Any]:
    """
    Extracts 24-D feature vectors per window from session JSON files and splits by subject.
    """
    os.makedirs(features_dir, exist_ok=True)
    os.makedirs(splits_dir, exist_ok=True)

    session_files = glob.glob(os.path.join(raw_dir, "*.json"))
    if not session_files:
        raise FileNotFoundError(f"No session JSON files found in '{raw_dir}'. Run collect_data.py first.")

    standardizer = FeatureStandardizer()
    subject_sessions: Dict[str, List[Dict[str, Any]]] = {}

    for path in session_files:
        with open(path, "r") as f:
            data = json.load(f)
        subj = data["subject_id"]
        if subj not in subject_sessions:
            subject_sessions[subj] = []
        subject_sessions[subj].append(data)

    subjects = sorted(list(subject_sessions.keys()))
    np.random.seed(42)
    shuffled_subjects = np.random.permutation(subjects)

    n_train = max(1, int(len(subjects) * train_ratio))
    n_val = max(1, int(len(subjects) * val_ratio))

    train_subjs = list(shuffled_subjects[:n_train])
    val_subjs = list(shuffled_subjects[n_train : n_train + n_val])
    test_subjs = list(shuffled_subjects[n_train + n_val :])

    # Ensure test subjects exist
    if not test_subjs:
        test_subjs = [val_subjs.pop()]

    splits_info = {
        "train_subjects": train_subjs,
        "val_subjects": val_subjs,
        "test_subjects": test_subjs,
    }

    with open(os.path.join(splits_dir, "subject_splits.json"), "w") as f:
        json.dump(splits_info, f, indent=2)

    def process_subset(subjs: List[str]) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        X_list, y_list, sess_ids = [], [], []
        for s in subjs:
            for session in subject_sessions.get(s, []):
                sess_label = session["label"]
                for w in session["windows"]:
                    vec = standardizer.vectorize(w)
                    X_list.append(vec)
                    # Window label: normal windows in suspicious sessions carry label if active
                    is_window_susp = bool(
                        w.get("looking_away")
                        or w.get("turned_away")
                        or w.get("multi_person_flag")
                        or w.get("sustained_talking")
                        or w.get("tab_hidden")
                    )
                    y_list.append(1 if (sess_label == 1 and is_window_susp) else 0)
                    sess_ids.append(session["session_id"])

        return np.array(X_list, dtype=np.float32), np.array(y_list, dtype=np.float32), sess_ids

    X_train, y_train, _ = process_subset(train_subjs)
    X_val, y_val, _ = process_subset(val_subjs)
    X_test, y_test, _ = process_subset(test_subjs)

    np.save(os.path.join(features_dir, "X_train.npy"), X_train)
    np.save(os.path.join(features_dir, "y_train.npy"), y_train)
    np.save(os.path.join(features_dir, "X_val.npy"), X_val)
    np.save(os.path.join(features_dir, "y_val.npy"), y_val)
    np.save(os.path.join(features_dir, "X_test.npy"), X_test)
    np.save(os.path.join(features_dir, "y_test.npy"), y_test)

    summary = {
        "train_samples": len(X_train),
        "val_samples": len(X_val),
        "test_samples": len(X_test),
        "feature_dim": FEATURE_DIM,
        "splits": splits_info,
    }

    with open(os.path.join(features_dir, "feature_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    return summary


def main():
    parser = argparse.ArgumentParser(description="Extract features and create subject-independent splits.")
    parser.add_argument("--raw_dir", default="data/raw")
    parser.add_argument("--features_dir", default="data/features")
    parser.add_argument("--splits_dir", default="data/splits")
    args = parser.parse_args()

    print("Extracting features from recorded sessions...")
    summary = extract_features_from_sessions(args.raw_dir, args.features_dir, args.splits_dir)
    print(f"Feature extraction complete! Train: {summary['train_samples']}, Val: {summary['val_samples']}, Test: {summary['test_samples']} windows.")


if __name__ == "__main__":
    main()
