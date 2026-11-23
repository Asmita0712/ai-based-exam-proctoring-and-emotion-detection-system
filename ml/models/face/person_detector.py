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
        conf_threshold: float = 0.50,
        device: Optional[str] = None,
    ) -> None:
        """
        Args:
            model_name_or_path: Path to weights or YOLO model name (e.g. 'yolov8n.pt').
            conf_threshold: Minimum detection confidence threshold [0.0 - 1.0].
            device: 'cpu', 'cuda', or None (auto-detect).
        """
        import os
        os.environ.setdefault("YOLO_CONFIG_DIR", os.path.join(os.path.dirname(__file__), ".yolo"))
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

        # Deduplicate overlapping boxes and filter background noise/shoulders
        if len(boxes) > 1:
            combined = sorted(zip(boxes, confidences), key=lambda x: x[1], reverse=True)
            filtered_boxes: List[List[float]] = []
            filtered_confs: List[float] = []
            img_area = float(frame.shape[0] * frame.shape[1])

            for b, c in combined:
                b_area = (b[2] - b[0]) * (b[3] - b[1])
                # Primary person can be any reasonable size, but secondary persons must be substantial
                min_area_ratio = 0.025 if len(filtered_boxes) == 0 else 0.065
                min_conf = self.conf_threshold if len(filtered_boxes) == 0 else max(self.conf_threshold, 0.58)

                if b_area < min_area_ratio * img_area or c < min_conf:
                    continue

                # Check overlap / containment with already accepted person boxes
                duplicate = False
                for existing in filtered_boxes:
                    ix1 = max(b[0], existing[0])
                    iy1 = max(b[1], existing[1])
                    ix2 = min(b[2], existing[2])
                    iy2 = min(b[3], existing[3])
                    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
                    if inter > 0:
                        ex_area = (existing[2] - existing[0]) * (existing[3] - existing[1])
                        min_a = min(b_area, ex_area)
                        union = b_area + ex_area - inter
                        iou = inter / union if union > 0 else 0.0
                        # If boxes overlap or one contains > 40% of the other, it's the same person's body/arm
                        if iou > 0.25 or (min_a > 0 and (inter / min_a) > 0.40):
                            duplicate = True
                            break

                if not duplicate:
                    filtered_boxes.append(b)
                    filtered_confs.append(c)

            boxes = filtered_boxes
            confidences = filtered_confs

        return {
            "person_count": len(boxes),
            "boxes": boxes,
            "confidence": confidences,
        }
