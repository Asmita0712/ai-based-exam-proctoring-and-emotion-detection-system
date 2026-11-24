"""
Gaze estimation module using MediaPipe iris landmarks and face blendshapes.

Adheres to:
- RULE 4: Clean reusable interface
- RULE 10: Configurable thresholds (away_threshold_low, away_threshold_high, smoothing_window)
- RULE 13: Allows receiving pre-extracted landmarks to prevent duplicate model runs
- RULE 15: Baseline implementation structured so L2CS-Net can replace it seamlessly
"""
from collections import deque
from typing import Any, Dict, List, Optional
import numpy as np

from ml.models.face.landmarks import FaceLandmarkExtractor


class GazeEstimator:
    """
    Estimates gaze direction and whether the subject is looking away from the screen.
    Features:
    - Bounded to physical laptop screen geometry (accommodates normal on-screen reading)
    - Blink / Eye-Aspect-Ratio protection to prevent blink-induced false alarms
    - Dual confirmation with MediaPipe neural blendshapes (when available)
    - 2-frame consecutive debouncing to eliminate micro-saccade flicker
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
        horizontal_threshold_low: float = 0.30,
        horizontal_threshold_high: float = 0.70,
        vertical_threshold_low: float = 0.25,
        vertical_threshold_high: float = 0.78,
        smoothing_window: int = 4,
    ) -> None:
        """
        Args:
            landmark_extractor: Shared FaceLandmarkExtractor (optional).
            horizontal_threshold_low: Ratio below which user is looking left of laptop screen.
            horizontal_threshold_high: Ratio above which user is looking right of laptop screen.
            vertical_threshold_low: Ratio below which user is looking up above webcam.
            vertical_threshold_high: Ratio above which user is looking down past laptop screen into lap/phone.
            smoothing_window: Number of frames to smooth telemetry ratios over.
        """
        self.landmark_extractor = landmark_extractor
        self.h_low = horizontal_threshold_low
        self.h_high = horizontal_threshold_high
        self.v_low = vertical_threshold_low
        self.v_high = vertical_threshold_high
        self.history: deque = deque(maxlen=smoothing_window)
        self.last_valid_ratios = (0.50, 0.55)
        self.consecutive_away = 0

    def estimate_from_landmarks(
        self, landmarks: Optional[List[Any]]
    ) -> Dict[str, Any]:
        """
        Calculates gaze ratio from 478 face landmarks and optional blendshapes.

        Returns:
            {
                "gaze_ratio": float (0.5 = center),
                "vertical_ratio": float (0.5 = center),
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

        def _calc_eye(c1_idx, c2_idx, top_idx, bot_idx, iris_idx):
            c1 = landmarks[c1_idx]
            c2 = landmarks[c2_idx]
            top = landmarks[top_idx]
            bot = landmarks[bot_idx]
            iris = landmarks[iris_idx]

            x_min = min(c1.x, c2.x)
            x_max = max(c1.x, c2.x)
            eye_w = max(1e-5, x_max - x_min)

            y_min = min(top.y, bot.y)
            y_max = max(top.y, bot.y)
            eye_h = max(1e-5, y_max - y_min)

            # Eye Aspect Ratio to detect blinks / eyelid closure
            ear = eye_h / eye_w
            is_blink = ear < 0.14

            h_r = (iris.x - x_min) / eye_w
            v_r = (iris.y - y_min) / eye_h
            return max(0.0, min(1.0, h_r)), max(0.0, min(1.0, v_r)), is_blink

        l_h, l_v, l_blink = _calc_eye(
            self.LEFT_EYE_OUTER,
            self.LEFT_EYE_INNER,
            self.LEFT_EYE_TOP,
            self.LEFT_EYE_BOTTOM,
            self.LEFT_IRIS_CENTER,
        )
        r_h, r_v, r_blink = _calc_eye(
            self.RIGHT_EYE_INNER,
            self.RIGHT_EYE_OUTER,
            self.RIGHT_EYE_TOP,
            self.RIGHT_EYE_BOTTOM,
            self.RIGHT_IRIS_CENTER,
        )

        is_blinking = l_blink or r_blink

        # Extract MediaPipe FaceLandmarker blendshapes if available
        bs_away = False
        if hasattr(landmarks, "_blendshapes") and landmarks._blendshapes:
            try:
                bs = {cat.category_name: cat.score for cat in landmarks._blendshapes}
                blink_score = (bs.get("eyeBlinkLeft", 0.0) + bs.get("eyeBlinkRight", 0.0)) / 2.0
                if blink_score > 0.60:
                    is_blinking = True

                look_left = (bs.get("eyeLookOutLeft", 0.0) + bs.get("eyeLookInRight", 0.0)) / 2.0
                look_right = (bs.get("eyeLookInLeft", 0.0) + bs.get("eyeLookOutRight", 0.0)) / 2.0
                look_down = (bs.get("eyeLookDownLeft", 0.0) + bs.get("eyeLookDownRight", 0.0)) / 2.0
                look_up = (bs.get("eyeLookUpLeft", 0.0) + bs.get("eyeLookUpRight", 0.0)) / 2.0

                if look_left > 0.68 or look_right > 0.68 or look_down > 0.74 or look_up > 0.68:
                    bs_away = True
            except Exception:
                pass

        # Protect against blink-induced false positives: preserve last valid gaze during blinks
        if is_blinking:
            avg_h, avg_v = self.last_valid_ratios
        else:
            avg_h = float((l_h + r_h) / 2.0)
            avg_v = float((l_v + r_v) / 2.0)
            self.last_valid_ratios = (avg_h, avg_v)

        self.history.append((avg_h, avg_v))

        # Smoothed ratios for visual telemetry display
        smooth_h = sum(h for h, _ in self.history) / len(self.history)
        smooth_v = sum(v for _, v in self.history) / len(self.history)

        # Instantaneous threshold evaluation
        raw_away = (
            avg_h < self.h_low
            or avg_h > self.h_high
            or avg_v < self.v_low
            or avg_v > self.v_high
            or bs_away
        )

        # 2-frame debouncing: require 2 consecutive frames of off-screen gaze to flag violation
        if raw_away and not is_blinking:
            self.consecutive_away += 1
        else:
            self.consecutive_away = 0

        debounced_looking_away = bool(self.consecutive_away >= 2)

        return {
            "gaze_ratio": round(smooth_h, 3),
            "vertical_ratio": round(smooth_v, 3),
            "looking_away": debounced_looking_away,
            "confidence": 0.95,
        }

    def estimate(self, frame: np.ndarray) -> Dict[str, Any]:
        """Runs landmark extraction and estimates gaze from a video frame."""
        if self.landmark_extractor is None:
            self.landmark_extractor = FaceLandmarkExtractor()
        landmarks = self.landmark_extractor.extract(frame)
        return self.estimate_from_landmarks(landmarks)

    def reset(self) -> None:
        """Clears temporal smoothing history and debounce counters."""
        self.history.clear()
        self.last_valid_ratios = (0.50, 0.55)
        self.consecutive_away = 0
