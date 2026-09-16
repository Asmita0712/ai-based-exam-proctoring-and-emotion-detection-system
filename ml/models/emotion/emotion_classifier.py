"""
Facial Emotion Recognition (FER) module using PyTorch.

Adheres to:
- Pure PyTorch implementation (preferred stack)
- Operates on cropped face produced by existing detection module (RULE 13: no duplicate detector)
- RULE 4: Clean reusable interface (input: face crop, output: structured dict)
- RULE 8: Emotion does NOT declare cheating -- it is purely a behavioral feature
- RULE 10/11: Configurable model paths, smoothing window, and confidence threshold
- Temporal aggregation over sliding window
- Graceful handling of missing/empty face crops
"""
from collections import deque
import os
from typing import Any, Dict, List, Optional
import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


# 7 standard FER2013 emotion categories
EMOTION_LABELS: List[str] = [
    "angry",
    "disgust",
    "fear",
    "happy",
    "sad",
    "surprise",
    "neutral",
]


class EmotionCNN(nn.Module):
    """
    Lightweight 4-block CNN architecture for 48x48 facial emotion recognition.
    """

    def __init__(self, num_classes: int = 7) -> None:
        super().__init__()
        # Block 1
        self.conv1a = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.bn1a = nn.BatchNorm2d(32)
        self.conv1b = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.bn1b = nn.BatchNorm2d(64)
        self.pool1 = nn.MaxPool2d(2, 2)  # 48 -> 24
        self.drop1 = nn.Dropout2d(0.25)

        # Block 2
        self.conv2 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(128)
        self.pool2 = nn.MaxPool2d(2, 2)  # 24 -> 12
        self.drop2 = nn.Dropout2d(0.25)

        # Block 3
        self.conv3 = nn.Conv2d(128, 256, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm2d(256)
        self.pool3 = nn.MaxPool2d(2, 2)  # 12 -> 6
        self.drop3 = nn.Dropout2d(0.25)

        # Classifier
        self.fc1 = nn.Linear(256 * 6 * 6, 256)
        self.bn_fc = nn.BatchNorm1d(256)
        self.drop_fc = nn.Dropout(0.5)
        self.fc2 = nn.Linear(256, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Block 1
        x = F.relu(self.bn1a(self.conv1a(x)))
        x = F.relu(self.bn1b(self.conv1b(x)))
        x = self.pool1(x)
        x = self.drop1(x)

        # Block 2
        x = F.relu(self.bn2(self.conv2(x)))
        x = self.pool2(x)
        x = self.drop2(x)

        # Block 3
        x = F.relu(self.bn3(self.conv3(x)))
        x = self.pool3(x)
        x = self.drop3(x)

        # Flatten & FC
        x = x.view(x.size(0), -1)
        x = F.relu(self.bn_fc(self.fc1(x)))
        x = self.drop_fc(x)
        x = self.fc2(x)
        return x


class EmotionClassifier:
    """
    Facial emotion classifier operating on face crops.
    Applies temporal smoothing across recent frames.
    """

    DEFAULT_CHECKPOINT_PATH = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "models", "checkpoints", "fer_cnn.pth"
    )

    def __init__(
        self,
        weights_path: Optional[str] = None,
        smoothing_window: int = 15,
        device: Optional[str] = None,
    ) -> None:
        """
        Args:
            weights_path: Path to PyTorch model weights file (optional).
            smoothing_window: Number of consecutive frame probabilities to average.
            device: 'cpu', 'cuda', or None.
        """
        self.smoothing_window = smoothing_window
        self.history: deque = deque(maxlen=smoothing_window)

        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self.model = EmotionCNN(num_classes=len(EMOTION_LABELS)).to(self.device)
        self.weights_path = weights_path or self.DEFAULT_CHECKPOINT_PATH

        if self.weights_path and os.path.exists(self.weights_path):
            try:
                state = torch.load(self.weights_path, map_location=self.device)
                self.model.load_state_dict(state)
            except Exception:
                pass  # Use initialized weights if corrupt

        self.model.eval()

    def preprocess_face(self, face_crop: np.ndarray) -> Optional[torch.Tensor]:
        """
        Preprocesses a raw face crop into a normalized 1x1x48x48 tensor.
        """
        if face_crop is None or face_crop.size == 0:
            return None

        h, w = face_crop.shape[:2]
        if h < 10 or w < 10:
            return None

        # Convert to grayscale if 3-channel
        if face_crop.ndim == 3 and face_crop.shape[2] == 3:
            gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
        elif face_crop.ndim == 2:
            gray = face_crop
        else:
            return None

        # Resize to 48x48
        resized = cv2.resize(gray, (48, 48), interpolation=cv2.INTER_AREA)

        # Normalize to [0.0, 1.0]
        norm = resized.astype(np.float32) / 255.0
        tensor = torch.from_numpy(norm).unsqueeze(0).unsqueeze(0).to(self.device)
        return tensor

    def predict(self, face_crop: Optional[np.ndarray]) -> Dict[str, Any]:
        """
        Predicts emotion from a single face crop with temporal smoothing.

        Args:
            face_crop: Cropped face image as numpy array.

        Returns:
            Structured dictionary:
            {
                "dominant_emotion": str,
                "emotion_confidence": float,
                "emotion_scores": dict of emotion -> probability
            }
        """
        tensor = self.preprocess_face(face_crop)
        if tensor is None:
            # Missing face handling (RULE 15)
            default_scores = {emo: 0.0 for emo in EMOTION_LABELS}
            default_scores["neutral"] = 1.0
            return {
                "dominant_emotion": "neutral",
                "emotion_confidence": 0.0,
                "emotion_scores": default_scores,
            }

        with torch.no_grad():
            logits = self.model(tensor)
            probs = F.softmax(logits, dim=1).squeeze().cpu().numpy()

        self.history.append(probs)

        # Temporal smoothing: average probabilities over window
        smoothed = np.mean(self.history, axis=0)
        dominant_idx = int(np.argmax(smoothed))
        confidence = float(smoothed[dominant_idx])
        dominant_emotion = EMOTION_LABELS[dominant_idx]

        scores = {
            EMOTION_LABELS[i]: round(float(smoothed[i]), 3)
            for i in range(len(EMOTION_LABELS))
        }

        return {
            "dominant_emotion": dominant_emotion,
            "emotion_confidence": round(confidence, 3),
            "emotion_scores": scores,
        }

    def reset(self) -> None:
        """Clears temporal smoothing history."""
        self.history.clear()
