"""
Gaze estimation module using MediaPipe iris landmarks.

Adheres to:
- RULE 4: Clean reusable interface
- RULE 10: Configurable thresholds (away_threshold_low, away_threshold_high, smoothing_window)
- RULE 13: Allows receiving pre-extracted landmarks to prevent duplicate model runs
- RULE 15: Baseline implementation structured so L2CS-Net can replace it seamlessly
"""
from collections import deque
import math
from typing import Any, Dict, List, Optional
import numpy as np

from ml.models.face.landmarks import FaceLandmarkExtractor


class GazeEstimator:
    """
    Estimates gaze direction and whether the subject is looking away from the screen.
    Applies temporal smoothing over consecutive frames.
    """

    # Canonical MediaPipe 478 FaceMesh indices for eye and iris landmarks
    LEFT_EYE_INNER = 133
    LEFT_EYE_OUTER = 33
    LEFT_EYE_TOP = 159
    LEFT_EYE_BOTTOM = 145
    LEFT_IRIS_CENTER = 468

    RIGHT_EYE_INNER = 362
    RIGHT_EYE_OUTER = 263
    RIGHT_EYE_TOP = 386
    RIGHT_EYE_BOTTOM = 374
    RIGHT_IRIS_CENTER = 473

    def __init__(
        self,
        landmark_extractor: Optional[FaceLandmarkExtractor] = None,
        horizontal_threshold_low: float = 0.35,
        horizontal_threshold_high: float = 0.65,
        vertical_threshold_low: float = 0.25,
        vertical_threshold_high: float = 0.75,
        smoothing_window: int = 10,
    ) -> None:
        """
        Args:
            landmark_extractor: Shared FaceLandmarkExtractor (optional).
            horizontal_threshold_low: Ratio below which user is looking right.
            horizontal_threshold_high: Ratio above which user is looking left.
            vertical_threshold_low: Ratio below which user is looking up.
            vertical_threshold_high: Ratio above which user is looking down.
            smoothing_window: Number of frames to smooth over.
        """
        self.landmark_extractor = landmark_extractor
        self.h_low = horizontal_threshold_low
        self.h_high = horizontal_threshold_high
        self.v_low = vertical_threshold_low
        self.v_high = vertical_threshold_high
        self.history: deque = deque(maxlen=smoothing_window)

    def estimate_from_landmarks(
        self, landmarks: Optional[List[Any]]
    ) -> Dict[str, Any]:
        """
        Calculates gaze ratio from 478 face landmarks.

        Returns:
            {
                "gaze_ratio": float (0.5 = center),
                "vertical_ratio": float,
                "looking_away": bool,
                "confidence": float
            }
        """
        if landmarks is None or len(landmarks) < 478:
            return {
                "gaze_ratio": 0.5,
                "vertical_ratio": 0.5,
                "looking_away": False,
                "confidence": 0.0,
            }

        def _calc_eye_ratios(inner_idx, outer_idx, top_idx, bot_idx, iris_idx):
            inner = landmarks[inner_idx]
            outer = landmarks[outer_idx]
            top = landmarks[top_idx]
            bot = landmarks[bot_idx]
            iris = landmarks[iris_idx]

            d_inner = math.hypot(iris.x - inner.x, iris.y - inner.y)
            d_outer = math.hypot(iris.x - outer.x, iris.y - outer.y)
            h_ratio = d_inner / (d_inner + d_outer + 1e-6)

            d_top = abs(iris.y - top.y)
            d_bot = abs(bot.y - iris.y)
            v_ratio = d_top / (d_top + d_bot + 1e-6)

            return h_ratio, v_ratio

        left_h, left_v = _calc_eye_ratios(
            self.LEFT_EYE_INNER,
            self.LEFT_EYE_OUTER,
            self.LEFT_EYE_TOP,
            self.LEFT_EYE_BOTTOM,
            self.LEFT_IRIS_CENTER,
        )

        right_h, right_v = _calc_eye_ratios(
            self.RIGHT_EYE_INNER,
            self.RIGHT_EYE_OUTER,
            self.RIGHT_EYE_TOP,
            self.RIGHT_EYE_BOTTOM,
            self.RIGHT_IRIS_CENTER,
        )

        avg_h = float((left_h + right_h) / 2.0)
        avg_v = float((left_v + right_v) / 2.0)

        self.history.append((avg_h, avg_v))

        # Smoothed ratios
        smooth_h = sum(h for h, _ in self.history) / len(self.history)
        smooth_v = sum(v for _, v in self.history) / len(self.history)

        looking_away = (
            smooth_h < self.h_low
            or smooth_h > self.h_high
            or smooth_v < self.v_low
            or smooth_v > self.v_high
        )

        return {
            "gaze_ratio": round(smooth_h, 3),
            "vertical_ratio": round(smooth_v, 3),
            "looking_away": bool(looking_away),
            "confidence": 0.95,
        }

    def estimate(self, frame: np.ndarray) -> Dict[str, Any]:
        """Runs landmark extraction and estimates gaze from a video frame."""
        if self.landmark_extractor is None:
            self.landmark_extractor = FaceLandmarkExtractor()
        landmarks = self.landmark_extractor.extract(frame)
        return self.estimate_from_landmarks(landmarks)

    def reset(self) -> None:
        """Clears temporal smoothing history."""
        self.history.clear()
