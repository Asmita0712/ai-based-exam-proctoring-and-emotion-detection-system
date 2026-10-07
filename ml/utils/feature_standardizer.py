"""
Feature standardization and vectorization module (Phase 3, Part A).

Adheres to:
- RULE 5: Timestamped/window-level features
- RULE 6: Common standardized feature representation before fusion
- RULE 9: Preserves modality metadata mapping for explainability & ablation
- Robust missing modality handling
"""
from typing import Any, Dict, List, Tuple
import numpy as np


# Ordered feature names for explainability and ablation
FEATURE_NAMES: List[str] = [
    # Gaze (4)
    "gaze_h_norm",
    "gaze_v_norm",
    "looking_away",
    "gaze_confidence",
    # Head Pose (4)
    "yaw_norm",
    "pitch_norm",
    "roll_norm",
    "turned_away",
    # Person presence (3)
    "person_count_norm",
    "multi_person_flag",
    "no_person_flag",
    # Audio activity (2)
    "speech_probability",
    "sustained_talking",
    # Browser / Tab (3)
    "tab_hidden",
    "window_blur",
    "is_away",
    # Emotion behavioral signal (8)
    "emotion_angry",
    "emotion_disgust",
    "emotion_fear",
    "emotion_happy",
    "emotion_sad",
    "emotion_surprise",
    "emotion_neutral",
    "emotion_confidence",
]

FEATURE_DIM: int = len(FEATURE_NAMES)  # 24

# Mapping from modality name to (start_idx, end_idx) slice
MODALITY_SLICES: Dict[str, Tuple[int, int]] = {
    "gaze": (0, 4),
    "head_pose": (4, 8),
    "person": (8, 11),
    "audio": (11, 13),
    "tab": (13, 16),
    "emotion": (16, 24),
}


class FeatureStandardizer:
    """Standardizes per-window multimodal dictionaries into numeric vectors."""

    def __init__(self) -> None:
        self.feature_names = FEATURE_NAMES
        self.modality_slices = MODALITY_SLICES
        self.feature_dim = FEATURE_DIM

    def vectorize(self, window: Dict[str, Any]) -> np.ndarray:
        """
        Converts a single window feature dictionary into a normalized 1D numpy array of shape (24,).
        Missing modality keys are populated with neutral/zero defaults.
        """
        vec = np.zeros(self.feature_dim, dtype=np.float32)

        # 1. Gaze (4)
        gaze_dict = window.get("gaze") or {}
        g_h = float(gaze_dict.get("gaze_ratio", 0.5))
        g_v = float(gaze_dict.get("vertical_ratio", 0.5))
        vec[0] = np.clip((g_h - 0.5) * 2.0, -1.0, 1.0)  # center 0.5 -> 0.0, range [-1, 1]
        vec[1] = np.clip((g_v - 0.5) * 2.0, -1.0, 1.0)
        vec[2] = 1.0 if window.get("looking_away", False) else 0.0
        vec[3] = float(gaze_dict.get("confidence", 0.0))

        # 2. Head Pose (4)
        pose_dict = window.get("head_pose") or {}
        yaw = float(pose_dict.get("yaw", 0.0))
        pitch = float(pose_dict.get("pitch", 0.0))
        roll = float(pose_dict.get("roll", 0.0))
        vec[4] = np.clip(yaw / 90.0, -1.0, 1.0)
        vec[5] = np.clip(pitch / 90.0, -1.0, 1.0)
        vec[6] = np.clip(roll / 90.0, -1.0, 1.0)
        vec[7] = 1.0 if window.get("turned_away", False) else 0.0

        # 3. Person (3)
        p_count = float(window.get("person_count", 1))
        vec[8] = np.clip(p_count / 3.0, 0.0, 1.0)
        vec[9] = 1.0 if window.get("multi_person_flag", False) or p_count > 1 else 0.0
        vec[10] = 1.0 if window.get("no_person_flag", False) or p_count == 0 else 0.0

        # 4. Audio (2)
        audio_dict = window.get("audio") or {}
        vec[11] = float(window.get("speech_probability", audio_dict.get("speech_probability", 0.0)))
        vec[12] = 1.0 if (window.get("sustained_talking", False) or audio_dict.get("sustained_talking", False)) else 0.0

        # 5. Tab / Browser (3)
        vec[13] = 1.0 if window.get("tab_hidden", False) else 0.0
        vec[14] = 1.0 if window.get("window_blur", False) else 0.0
        vec[15] = 1.0 if window.get("is_away", False) or vec[13] == 1.0 or vec[14] == 1.0 else 0.0

        # 6. Emotion (8)
        emo_dict = window.get("emotion") or {}
        emo_scores = emo_dict.get("emotion_scores") or {}
        vec[16] = float(emo_scores.get("angry", 0.0))
        vec[17] = float(emo_scores.get("disgust", 0.0))
        vec[18] = float(emo_scores.get("fear", 0.0))
        vec[19] = float(emo_scores.get("happy", 0.0))
        vec[20] = float(emo_scores.get("sad", 0.0))
        vec[21] = float(emo_scores.get("surprise", 0.0))
        # Default neutral to 1.0 if no emotion scores present
        vec[22] = float(emo_scores.get("neutral", 1.0 if not emo_scores else 0.0))
        vec[23] = float(emo_dict.get("emotion_confidence", 0.0))

        return vec

    def batch_vectorize(self, windows: List[Dict[str, Any]]) -> np.ndarray:
        """
        Converts a list of window dicts into a 2D numpy array of shape (N, 24).
        """
        if not windows:
            return np.empty((0, self.feature_dim), dtype=np.float32)
        return np.vstack([self.vectorize(w) for w in windows])

    def get_modality_slice(self, modality_name: str) -> Tuple[int, int]:
        """Returns (start_idx, end_idx) for a modality name."""
        if modality_name not in self.modality_slices:
            raise KeyError(f"Unknown modality '{modality_name}'. Available: {list(self.modality_slices.keys())}")
        return self.modality_slices[modality_name]
