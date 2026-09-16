"""
Head pose estimation module using MediaPipe landmarks and OpenCV solvePnP.

Adheres to:
- RULE 4: Clean reusable interface (outputs: yaw, pitch, roll, turned_away)
- RULE 10: Configurable thresholds for yaw, pitch, roll
- RULE 13: Allows receiving pre-extracted landmarks to prevent duplicate inference
- RULE 15: Baseline implementation compatible with future SixDRepNet upgrade
"""
import math
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np

from ml.models.face.landmarks import FaceLandmarkExtractor


class HeadPoseEstimator:
    """
    Estimates 3D head pose (yaw, pitch, roll in degrees) using 3D-to-2D
    correspondences via OpenCV solvePnP.
    """

    # Canonical 3D face model points (in arbitrary world units)
    MODEL_POINTS = np.array(
        [
            (0.0, 0.0, 0.0),          # Nose tip (landmark 1)
            (0.0, -330.0, -65.0),      # Chin (landmark 152)
            (-225.0, 170.0, -135.0),   # Left eye outer corner (landmark 33)
            (225.0, 170.0, -135.0),    # Right eye outer corner (landmark 263)
            (-150.0, -150.0, -125.0),  # Left mouth corner (landmark 61)
            (150.0, -150.0, -125.0),   # Right mouth corner (landmark 291)
        ],
        dtype=np.float64,
    )

    LANDMARK_INDICES = [1, 152, 33, 263, 61, 291]

    def __init__(
        self,
        landmark_extractor: Optional[FaceLandmarkExtractor] = None,
        yaw_threshold: float = 25.0,
        pitch_threshold: float = 20.0,
        roll_threshold: float = 25.0,
    ) -> None:
        """
        Args:
            landmark_extractor: Shared FaceLandmarkExtractor instance (optional).
            yaw_threshold: Absolute yaw in degrees beyond which head is turned away.
            pitch_threshold: Absolute pitch in degrees beyond which head is turned away.
            roll_threshold: Absolute roll in degrees beyond which head is turned away.
        """
        self.landmark_extractor = landmark_extractor
        self.yaw_threshold = yaw_threshold
        self.pitch_threshold = pitch_threshold
        self.roll_threshold = roll_threshold

    def estimate_from_landmarks(
        self, landmarks: Optional[List[Any]], image_shape: Tuple[int, int] = (480, 640)
    ) -> Dict[str, Any]:
        """
        Estimates head pose angles given 478 MediaPipe landmarks and frame dimensions.

        Args:
            landmarks: List of NormalizedLandmark objects or None.
            image_shape: (height, width) of the image.

        Returns:
            {
                "yaw": float,
                "pitch": float,
                "roll": float,
                "turned_away": bool
            }
        """
        if landmarks is None or len(landmarks) < 478:
            return {
                "yaw": 0.0,
                "pitch": 0.0,
                "roll": 0.0,
                "turned_away": False,
            }

        h, w = image_shape
        image_points = []
        for idx in self.LANDMARK_INDICES:
            lm = landmarks[idx]
            image_points.append([lm.x * w, lm.y * h])

        image_points = np.array(image_points, dtype=np.float64)

        # Camera calibration approximation
        focal_length = w
        center = (w / 2.0, h / 2.0)
        camera_matrix = np.array(
            [[focal_length, 0, center[0]], [0, focal_length, center[1]], [0, 0, 1]],
            dtype=np.float64,
        )
        dist_coeffs = np.zeros((4, 1), dtype=np.float64)

        success, rvec, _ = cv2.solvePnP(
            self.MODEL_POINTS,
            image_points,
            camera_matrix,
            dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE,
        )

        if not success:
            return {
                "yaw": 0.0,
                "pitch": 0.0,
                "roll": 0.0,
                "turned_away": False,
            }

        rotation_matrix, _ = cv2.Rodrigues(rvec)
        # RQDecomp3x3 decomposes a 3x3 rotation matrix into Euler angles
        angles, _, _, _, _, _ = cv2.RQDecomp3x3(rotation_matrix)
        pitch = float(angles[0])
        yaw = float(angles[1])
        roll = float(angles[2])

        turned_away = (
            abs(yaw) > self.yaw_threshold
            or abs(pitch) > self.pitch_threshold
            or abs(roll) > self.roll_threshold
        )

        return {
            "yaw": round(yaw, 2),
            "pitch": round(pitch, 2),
            "roll": round(roll, 2),
            "turned_away": bool(turned_away),
        }

    def estimate(self, frame: np.ndarray) -> Dict[str, Any]:
        """Runs landmark extraction and estimates head pose from a video frame."""
        if frame is None or frame.size == 0:
            return {"yaw": 0.0, "pitch": 0.0, "roll": 0.0, "turned_away": False}

        if self.landmark_extractor is None:
            self.landmark_extractor = FaceLandmarkExtractor()

        landmarks = self.landmark_extractor.extract(frame)
        h, w = frame.shape[:2]
        return self.estimate_from_landmarks(landmarks, image_shape=(h, w))
