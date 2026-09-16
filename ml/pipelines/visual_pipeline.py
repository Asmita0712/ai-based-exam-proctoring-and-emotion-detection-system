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
from ml.models.emotion.emotion_classifier import EmotionClassifier


class VisualPipeline:
    """Orchestrates all visual proctoring modalities on a single video frame."""

    def __init__(
        self,
        yolo_model_path: str = "yolov8n.pt",
        person_conf: float = 0.4,
        yaw_threshold: float = 25.0,
        pitch_threshold: float = 20.0,
        emotion_weights_path: Optional[str] = None,
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
        self.emotion_classifier = EmotionClassifier(
            weights_path=emotion_weights_path,
            device=device,
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
                "emotion": self.emotion_classifier.predict(None),
            }

        # 1. Person detection
        det = self.person_detector.detect(frame)

        # 2. Multi-person tracking debounce
        mp_status = self.multi_person_tracker.update(det)

        # 3. Extract landmarks once for gaze, head pose, and precise face crop
        landmarks = self.landmark_extractor.extract(frame)
        h, w = frame.shape[:2]

        # 4. Gaze & Head pose
        gaze_res = self.gaze_estimator.estimate_from_landmarks(landmarks)
        pose_res = self.head_pose_estimator.estimate_from_landmarks(landmarks, image_shape=(h, w))

        # 5. Extract face crop for emotion classification (RULE 13: reuse detections)
        face_crop = None
        if landmarks and len(landmarks) >= 478:
            xs = [lm.x * w for lm in landmarks]
            ys = [lm.y * h for lm in landmarks]
            pad_x = (max(xs) - min(xs)) * 0.15
            pad_y = (max(ys) - min(ys)) * 0.15
            x1 = max(0, int(min(xs) - pad_x))
            x2 = min(w, int(max(xs) + pad_x))
            y1 = max(0, int(min(ys) - pad_y))
            y2 = min(h, int(max(ys) + pad_y))
            if x2 > x1 and y2 > y1:
                face_crop = frame[y1:y2, x1:x2]
        elif det["boxes"]:
            # Fallback to upper region of primary detected person box
            b = det["boxes"][0]
            bx1, by1, bx2, by2 = int(b[0]), int(b[1]), int(b[2]), int(b[3])
            head_h = max(20, int((by2 - by1) * 0.35))
            face_crop = frame[max(0, by1) : min(h, by1 + head_h), max(0, bx1) : min(w, bx2)]

        emotion_res = self.emotion_classifier.predict(face_crop)

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
            "emotion": emotion_res,
        }

    def reset(self) -> None:
        """Resets stateful trackers."""
        self.multi_person_tracker.reset()
        self.gaze_estimator.reset()
        self.emotion_classifier.reset()


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
