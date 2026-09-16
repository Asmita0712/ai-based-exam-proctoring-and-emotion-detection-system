"""
Person detection module using Ultralytics YOLO.

Adheres to:
- RULE 4: Clean reusable interface (input: frame, output: structured feature dict)
- RULE 10/11: Configurable confidence threshold and model path
- RULE 13: Model loaded once during initialization
- RULE 14: CPU first with GPU support if available
"""
from typing import Any, Dict, List, Optional
import numpy as np


class PersonDetector:
    """Detects human presence and bounding boxes in video frames using YOLO."""

    PERSON_CLASS_ID = 0  # COCO class 0 is 'person'

    def __init__(
        self,
        model_name_or_path: str = "yolov8n.pt",
        conf_threshold: float = 0.4,
        device: Optional[str] = None,
    ) -> None:
        """
        Args:
            model_name_or_path: Path to weights or YOLO model name (e.g. 'yolov8n.pt').
            conf_threshold: Minimum detection confidence threshold [0.0 - 1.0].
            device: 'cpu', 'cuda', or None (auto-detect).
        """
        from ultralytics import YOLO
        import torch

        self.conf_threshold = conf_threshold
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self.model_path = model_name_or_path
        self.model = YOLO(model_name_or_path)

    def detect(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Runs person detection on a single image frame.

        Args:
            frame: Video frame as a numpy BGR or RGB array.

        Returns:
            Structured dictionary:
            {
                "person_count": int,
                "boxes": list of [x1, y1, x2, y2],
                "confidence": list of float confidences
            }
        """
        if frame is None or frame.size == 0:
            return {"person_count": 0, "boxes": [], "confidence": []}

        # Run inference (classes=[0] filters to only 'person')
        results = self.model.predict(
            source=frame,
            classes=[self.PERSON_CLASS_ID],
            conf=self.conf_threshold,
            device=self.device,
            verbose=False,
        )

        boxes: List[List[float]] = []
        confidences: List[float] = []

        if results and len(results) > 0:
            det = results[0].boxes
            if det is not None and len(det) > 0:
                boxes_xyxy = det.xyxy.cpu().numpy()
                confs = det.conf.cpu().numpy()
                for box, conf in zip(boxes_xyxy, confs):
                    boxes.append([float(coord) for coord in box])
                    confidences.append(float(conf))

        return {
            "person_count": len(boxes),
            "boxes": boxes,
            "confidence": confidences,
        }
