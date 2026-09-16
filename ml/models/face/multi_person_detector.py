"""
Multiple-person detection and temporal debounce module.

Adheres to:
- Reuse detector output (no duplicate inference, RULE 13)
- Temporal smoothing/debounce so momentary detection/flicker does not trigger alerts
- RULE 4: Clean reusable interface
- RULE 10: Configurable debounce threshold and window size
"""
from collections import deque
from typing import Any, Dict, List, Optional


class MultiPersonTracker:
    """
    Applies temporal smoothing/debounce on top of PersonDetector outputs
    to robustly detect multiple-person events without momentary flicker.
    """

    def __init__(
        self,
        history_len: int = 15,
        multi_person_ratio_threshold: float = 0.4,
    ) -> None:
        """
        Args:
            history_len: Number of recent frames to retain in sliding window.
            multi_person_ratio_threshold: Fraction of recent frames that must have >1
                                         person to trigger multi_person_flag.
        """
        self.history_len = history_len
        self.ratio_threshold = multi_person_ratio_threshold
        self.history: deque = deque(maxlen=history_len)

    def update(self, person_detection: Dict[str, Any]) -> Dict[str, Any]:
        """
        Updates tracker with the latest frame's person detection.

        Args:
            person_detection: Dict containing "person_count", "boxes", "confidence".

        Returns:
            Structured dictionary:
            {
                "person_count": int (current frame person count),
                "multi_person_flag": bool (debounced flag),
                "multi_person_ratio": float (fraction of history with >1 person),
                "no_person_flag": bool (true if 0 persons detected consistently)
            }
        """
        current_count = int(person_detection.get("person_count", 0))
        self.history.append(current_count)

        if not self.history:
            return {
                "person_count": current_count,
                "multi_person_flag": False,
                "multi_person_ratio": 0.0,
                "no_person_flag": current_count == 0,
            }

        multi_person_frames = sum(1 for c in self.history if c > 1)
        ratio = multi_person_frames / len(self.history)
        multi_flag = ratio >= self.ratio_threshold

        zero_person_frames = sum(1 for c in self.history if c == 0)
        no_person_flag = (zero_person_frames / len(self.history)) >= self.ratio_threshold

        return {
            "person_count": current_count,
            "multi_person_flag": multi_flag,
            "multi_person_ratio": round(ratio, 3),
            "no_person_flag": no_person_flag,
        }

    def reset(self) -> None:
        """Clears the history window."""
        self.history.clear()
