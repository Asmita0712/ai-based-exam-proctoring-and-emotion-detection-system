"""
Visual pipeline: orchestrates face/person detection, multi-person tracking,
gaze estimation, and head-pose estimation over a video frame.

Adheres to:
- RULE 4: Clean reusable interface
- RULE 13: Avoids duplicate model runs (shared FaceLandmarkExtractor)
- RULE 14: Runs on CPU first
"""
from typing import Any, Dict, Optional
import numpy as np

from ml.models.face.person_detector import PersonDetector
from ml.models.face.multi_person_detector import MultiPersonTracker
from ml.models.face.landmarks import FaceLandmarkExtractor
from ml.models.gaze.gaze_estimator import GazeEstimator
from ml.models.head_pose.head_pose_estimator import HeadPoseEstimator


class VisualPipeline:
    """Orchestrates all visual proctoring modalities on a single video frame."""

    def __init__(
        self,
        yolo_model_path: str = "yolov8n.pt",
        person_conf: float = 0.4,
        yaw_threshold: float = 25.0,
        pitch_threshold: float = 20.0,
        device: Optional[str] = None,
    ) -> None:
        self.person_detector = PersonDetector(
            model_name_or_path=yolo_model_path,
            conf_threshold=person_conf,
            device=device,
        )
        self.multi_person_tracker = MultiPersonTracker()
        self.landmark_extractor = FaceLandmarkExtractor()
        self.gaze_estimator = GazeEstimator(landmark_extractor=self.landmark_extractor)
        self.head_pose_estimator = HeadPoseEstimator(
            landmark_extractor=self.landmark_extractor,
            yaw_threshold=yaw_threshold,
            pitch_threshold=pitch_threshold,
        )

    def process_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Runs visual modalities on a single video frame.

        Args:
            frame: Video frame as numpy BGR array.

        Returns:
            Structured dictionary of visual signals.
        """
        if frame is None or frame.size == 0:
            return {
                "person_count": 0,
                "boxes": [],
                "confidence": [],
                "multi_person_flag": False,
                "no_person_flag": True,
                "gaze": {"gaze_ratio": 0.5, "vertical_ratio": 0.5, "looking_away": False, "confidence": 0.0},
                "looking_away": False,
                "head_pose": {"yaw": 0.0, "pitch": 0.0, "roll": 0.0, "turned_away": False},
                "turned_away": False,
            }

        # 1. Person detection
        det = self.person_detector.detect(frame)

        # 2. Multi-person tracking debounce
        mp_status = self.multi_person_tracker.update(det)

        # 3. Extract landmarks once for both gaze and head pose
        landmarks = self.landmark_extractor.extract(frame)
        h, w = frame.shape[:2]

        # 4. Gaze & Head pose
        gaze_res = self.gaze_estimator.estimate_from_landmarks(landmarks)
        pose_res = self.head_pose_estimator.estimate_from_landmarks(landmarks, image_shape=(h, w))

        return {
            "person_count": det["person_count"],
            "boxes": det["boxes"],
            "confidence": det["confidence"],
            "multi_person_flag": mp_status["multi_person_flag"],
            "no_person_flag": mp_status["no_person_flag"],
            "gaze": gaze_res,
            "looking_away": gaze_res["looking_away"],
            "head_pose": pose_res,
            "turned_away": pose_res["turned_away"],
        }

    def reset(self) -> None:
        """Resets stateful trackers."""
        self.multi_person_tracker.reset()
        self.gaze_estimator.reset()


# Lazy-loaded default singleton instance for module-level calls
_DEFAULT_VISUAL_PIPELINE: Optional[VisualPipeline] = None


def get_visual_pipeline() -> VisualPipeline:
    global _DEFAULT_VISUAL_PIPELINE
    if _DEFAULT_VISUAL_PIPELINE is None:
        _DEFAULT_VISUAL_PIPELINE = VisualPipeline()
    return _DEFAULT_VISUAL_PIPELINE


def process_frame(frame: Any) -> Dict[str, Any]:
    """Module-level entrypoint for visual frame processing."""
    return get_visual_pipeline().process_frame(frame)
