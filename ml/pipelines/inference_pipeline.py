"""
End-to-end multimodal inference pipeline (Phase 3 Integration).

Adheres to:
- RULE 1 / 2: Backend calls ML via clean pipeline interface
- RULE 3: Inference logic decoupled from FastAPI route functions
- RULE 7: Suspicion decisions produced at fusion layer
- RULE 9: Preserves modality-level outputs and importance for explainability
- PART E: Compares baseline rule-based, learned fusion, and temporal BiLSTM
"""
from typing import Any, Dict, List, Optional
import numpy as np

from ml.fusion.baseline_fusion import RuleBasedFusion
from ml.fusion.learned_fusion import LearnedFusion
from ml.fusion.modality_attention import compute_modality_importance
from ml.temporal.sequence_builder import SequenceBuffer
from ml.temporal.bilstm import BiLSTMTemporalModel
from ml.utils.feature_standardizer import FeatureStandardizer


class InferencePipeline:
    """
    End-to-end inference orchestrator supporting:
    - 'baseline': Rule-based weighted scoring (Phase 1 baseline)
    - 'learned': PyTorch MLP / Logistic learned fusion (Phase 3 Part B)
    - 'temporal': Full architecture (Learned fusion + Sequence Builder + BiLSTM)
    """

    def __init__(
        self,
        mode: str = "temporal",
        rule_threshold: float = 0.45,
        learned_threshold: float = 0.5,
        sequence_length: int = 30,
        device: Optional[str] = None,
    ) -> None:
        """
        Args:
            mode: 'baseline', 'learned', or 'temporal' (default: 'temporal').
            rule_threshold: Threshold for rule-based decision.
            learned_threshold: Threshold for learned fusion and BiLSTM.
            sequence_length: Number of time windows in BiLSTM sequence.
            device: 'cpu', 'cuda', or None.
        """
        self.mode = mode.lower()
        self.standardizer = FeatureStandardizer()

        # Phase 1 baseline
        self.rule_fusion = RuleBasedFusion(threshold=rule_threshold)

        # Phase 3 Part B: Learned fusion
        self.learned_fusion = LearnedFusion(
            model_type="mlp",
            threshold=learned_threshold,
            device=device,
        )

        # Phase 3 Part D: Sequence buffer and BiLSTM
        self.sequence_length = sequence_length
        self.session_buffers: Dict[str, SequenceBuffer] = {}
        self.bilstm = BiLSTMTemporalModel(
            sequence_length=sequence_length,
            threshold=learned_threshold,
            device=device,
        )

    def _get_buffer(self, session_id: str) -> SequenceBuffer:
        """Retrieves or creates a SequenceBuffer for the given session ID."""
        if session_id not in self.session_buffers:
            self.session_buffers[session_id] = SequenceBuffer(self.sequence_length)
        return self.session_buffers[session_id]

    def run_inference(
        self,
        session_id: str,
        feature_window: Dict[str, Any],
        mode_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Runs multimodal inference on a single per-window feature representation.

        Args:
            session_id: Unique session identifier.
            feature_window: Dictionary of window signals.
            mode_override: Optional override for 'baseline', 'learned', or 'temporal'.

        Returns:
            Structured dictionary of suspicion scores, decisions, and explainability signals.
        """
        active_mode = (mode_override or self.mode).lower()

        # 1. Base rule-based fusion output (always available for baseline comparison / explainability)
        rule_res = self.rule_fusion.fuse(feature_window)

        # 2. Vectorize window for learned models
        vec = self.standardizer.vectorize(feature_window)

        # 3. Mode execution
        if active_mode == "baseline":
            suspicion_score = rule_res["suspicion_score"]
            flag = rule_res["flag"]
            temporal_context = {"is_sustained": False, "sequence_steps": 1}

        elif active_mode == "learned":
            learned_res = self.learned_fusion.predict(vec)
            suspicion_score = learned_res["suspicion_score"]
            flag = learned_res["flag"]
            temporal_context = {"is_sustained": False, "sequence_steps": 1}

        elif active_mode == "temporal":
            # Add to temporal sliding sequence buffer
            buf = self._get_buffer(session_id)
            buf.add_window(vec)
            seq = buf.get_sequence()

            temporal_res = self.bilstm.predict_sequence(seq)
            suspicion_score = temporal_res["suspicion_probability"]
            flag = temporal_res["flag"]
            temporal_context = {
                "is_sustained": temporal_res["is_sustained"],
                "sequence_steps": len(buf.buffer),
            }
        else:
            raise ValueError(f"Unknown mode '{active_mode}'. Available: 'baseline', 'learned', 'temporal'.")

        # 4. Modality importance analysis (Phase 3 Part C)
        importance = compute_modality_importance(self.learned_fusion)

        return {
            "session_id": session_id,
            "mode": active_mode,
            "suspicion_score": round(float(suspicion_score), 4),
            "flag": bool(flag),
            "contributors": rule_res["contributors"],
            "modality_scores": rule_res["modality_scores"],
            "modality_importance": importance,
            "temporal_context": temporal_context,
            "feature_window": feature_window,
        }

    def reset_session(self, session_id: str) -> None:
        """Resets temporal sequence buffer for a session."""
        if session_id in self.session_buffers:
            self.session_buffers[session_id].reset()


# Default singleton instance
_DEFAULT_INFERENCE_PIPELINE = InferencePipeline(mode="temporal")


def run_inference(
    session_id: str,
    feature_window: Dict[str, Any],
    mode: Optional[str] = None,
) -> Dict[str, Any]:
    """Module-level entrypoint for proctoring inference."""
    return _DEFAULT_INFERENCE_PIPELINE.run_inference(session_id, feature_window, mode_override=mode)
