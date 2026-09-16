"""
Shared Face Landmark extractor using MediaPipe FaceLandmarker.

Adheres to:
- RULE 4: Clean, reusable interface
- RULE 10/11: Configurable model path and confidence
- RULE 13: Single model load shared between gaze and head-pose
- RULE 14: CPU execution first
"""
import os
import urllib.request
from typing import Any, Dict, List, Optional
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


DEFAULT_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task"
DEFAULT_MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "models", "checkpoints", "face_landmarker.task"
)


class FaceLandmarkExtractor:
    """Extracts 478 3D facial landmarks from frames for gaze and head-pose modules."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        min_face_detection_confidence: float = 0.5,
        min_face_presence_confidence: float = 0.5,
    ) -> None:
        self.model_path = os.path.abspath(model_path or DEFAULT_MODEL_PATH)
        self._ensure_model_exists()

        base_options = python.BaseOptions(model_asset_path=self.model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=True,
            output_facial_transformation_matrixes=True,
            min_face_detection_confidence=min_face_detection_confidence,
            min_face_presence_confidence=min_face_presence_confidence,
            num_faces=1,
        )
        self.landmarker = vision.FaceLandmarker.create_from_options(options)

    def _ensure_model_exists(self) -> None:
        """Downloads the model bundle if not present on disk."""
        if not os.path.exists(self.model_path):
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            urllib.request.urlretrieve(DEFAULT_MODEL_URL, self.model_path)

    def extract(self, frame: np.ndarray) -> Optional[List[Any]]:
        """
        Extracts 478 face landmarks from a BGR/RGB image frame.

        Args:
            frame: Numpy BGR or RGB array (H, W, 3).

        Returns:
            List of 478 NormalizedLandmark objects for the first face, or None if no face.
        """
        if frame is None or frame.size == 0:
            return None

        # MediaPipe expects RGB
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            rgb_frame = frame[:, :, ::-1].copy() if frame.dtype == np.uint8 else frame
        else:
            return None

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        result = self.landmarker.detect(mp_image)

        if result.face_landmarks and len(result.face_landmarks) > 0:
            return result.face_landmarks[0]

        return None
