"""
End-to-end inference pipeline: clean interface between backend/service layer and ML.

Adheres to:
- RULE 2: Backend calls ML via clean pipeline interface
- RULE 3: Inference logic decoupled from FastAPI route functions
- RULE 7: Suspicion decisions produced at fusion layer
"""
from typing import Any, Dict, Optional
from ml.fusion.baseline_fusion import RuleBasedFusion


class InferencePipeline:
    """End-to-end inference runner mapping window features to suspicion decisions."""

    def __init__(self, fusion_engine: Optional[RuleBasedFusion] = None) -> None:
        self.fusion = fusion_engine or RuleBasedFusion()

    def run_inference(self, session_id: str, feature_window: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs multimodal fusion on a per-window feature vector.

        Returns:
            {
                "session_id": str,
                "suspicion_score": float,
                "flag": bool,
                "contributors": list of str,
                "modality_scores": dict,
                "feature_window": dict
            }
        """
        fusion_result = self.fusion.fuse(feature_window)
        return {
            "session_id": session_id,
            "suspicion_score": fusion_result["suspicion_score"],
            "flag": fusion_result["flag"],
            "contributors": fusion_result["contributors"],
            "modality_scores": fusion_result["modality_scores"],
            "feature_window": feature_window,
        }


_DEFAULT_INFERENCE_PIPELINE = InferencePipeline()


def run_inference(session_id: str, feature_window: Dict[str, Any]) -> Dict[str, Any]:
    """Module-level entrypoint for proctoring inference."""
    return _DEFAULT_INFERENCE_PIPELINE.run_inference(session_id, feature_window)
