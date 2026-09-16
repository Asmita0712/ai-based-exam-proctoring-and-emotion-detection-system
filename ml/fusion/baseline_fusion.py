"""
Rule-based baseline multimodal fusion module.

Adheres to:
- RULE 4: Clean reusable interface
- RULE 7: Suspicion decision made at fusion layer, not inside individual modalities
- RULE 8: Emotion is NOT independently determining suspicion
- RULE 9: Preserves modality-level contributors for explainability
- RULE 10: All weights and thresholds are configurable
"""
from typing import Any, Dict, List, Optional


class RuleBasedFusion:
    """
    Baseline multimodal fusion combining visual, audio, and browser signals
    using configurable weighted linear combination.
    """

    DEFAULT_WEIGHTS = {
        "multi_person": 0.30,
        "no_person": 0.25,
        "gaze_away": 0.20,
        "head_turned": 0.20,
        "sustained_talking": 0.15,
        "tab_away": 0.15,
    }

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        threshold: float = 0.45,
    ) -> None:
        """
        Args:
            weights: Dictionary mapping signal names to positive weights.
            threshold: Suspicion score threshold [0.0 - 1.0] to trigger `flag = True`.
        """
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        self.threshold = threshold

    def fuse(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combines modality signals into an overall suspicion score.

        Expected keys in signals (missing keys handled gracefully):
        - person_count: int
        - multi_person_flag: bool
        - looking_away: bool
        - turned_away: bool
        - sustained_talking: bool
        - speech_probability: float
        - tab_hidden: bool
        - window_blur: bool

        Returns:
            {
                "suspicion_score": float [0.0, 1.0],
                "flag": bool,
                "contributors": list of str descriptions,
                "modality_scores": dict of individual weighted scores
            }
        """
        contributors: List[str] = []
        modality_scores: Dict[str, float] = {}

        # 1. Multi-person presence
        if signals.get("multi_person_flag", False) or signals.get("person_count", 1) > 1:
            score = self.weights.get("multi_person", 0.30)
            modality_scores["multi_person"] = score
            contributors.append("multiple_persons_detected")
        else:
            modality_scores["multi_person"] = 0.0

        # 2. Absence of person
        if signals.get("person_count") == 0 or signals.get("no_person_flag", False):
            score = self.weights.get("no_person", 0.25)
            modality_scores["no_person"] = score
            contributors.append("no_person_detected")
        else:
            modality_scores["no_person"] = 0.0

        # 3. Gaze looking away
        if signals.get("looking_away", False):
            score = self.weights.get("gaze_away", 0.20)
            modality_scores["gaze"] = score
            contributors.append("gaze_looking_away")
        else:
            modality_scores["gaze"] = 0.0

        # 4. Head turned away
        if signals.get("turned_away", False):
            score = self.weights.get("head_turned", 0.20)
            modality_scores["head_pose"] = score
            contributors.append("head_turned_away")
        else:
            modality_scores["head_pose"] = 0.0

        # 5. Audio / sustained talking
        if signals.get("sustained_talking", False) or signals.get("speech_probability", 0.0) > 0.6:
            score = self.weights.get("sustained_talking", 0.15)
            modality_scores["audio"] = score
            contributors.append("speech_detected")
        else:
            modality_scores["audio"] = 0.0

        # 6. Tab / window away
        if signals.get("tab_hidden", False) or signals.get("window_blur", False) or signals.get("is_away", False):
            score = self.weights.get("tab_away", 0.15)
            modality_scores["browser"] = score
            contributors.append("browser_focus_lost")
        else:
            modality_scores["browser"] = 0.0

        raw_score = sum(modality_scores.values())
        # Clamp score to [0.0, 1.0]
        suspicion_score = min(1.0, max(0.0, raw_score))
        flag = suspicion_score >= self.threshold

        return {
            "suspicion_score": round(suspicion_score, 3),
            "flag": bool(flag),
            "contributors": contributors,
            "modality_scores": modality_scores,
        }


# Convenience module-level fuse function for backward compatibility
_DEFAULT_FUSION = RuleBasedFusion()


def fuse(signals: Dict[str, Any]) -> Dict[str, Any]:
    """Module-level entry point using default rule-based fusion weights."""
    return _DEFAULT_FUSION.fuse(signals)
