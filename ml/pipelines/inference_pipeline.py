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
from ml.temporal.sequence_builder import SequenceBuffer
from ml.utils.feature_standardizer import FeatureStandardizer

# Safe import for PyTorch / heavy neural models to support 512MB free-tier deployments
try:
    import torch
    from ml.fusion.learned_fusion import LearnedFusion
    from ml.fusion.modality_attention import compute_modality_importance
    from ml.temporal.bilstm import BiLSTMTemporalModel
    TORCH_AVAILABLE = True
except (ImportError, Exception):
    torch = None
    LearnedFusion = None
    compute_modality_importance = None
    BiLSTMTemporalModel = None
    TORCH_AVAILABLE = False


class InferencePipeline:
    """
    End-to-end inference orchestrator supporting:
    - 'baseline': Rule-based weighted scoring (Phase 1 baseline, 0 MB ML RAM overhead)
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
        self.rule_threshold = rule_threshold
        self.learned_threshold = learned_threshold
        self.standardizer = FeatureStandardizer()

        # Phase 1 baseline (always active, pure Python)
        self.rule_fusion = RuleBasedFusion(threshold=rule_threshold)

        # Phase 3 Part B & D: Learned fusion and BiLSTM (lazy/conditional on PyTorch availability)
        self.learned_fusion = None
        self.bilstm = None
        self.sequence_length = sequence_length
        self.session_buffers: Dict[str, SequenceBuffer] = {}

        if TORCH_AVAILABLE and self.mode in ("learned", "temporal"):
            try:
                self.learned_fusion = LearnedFusion(
                    model_type="mlp",
                    threshold=learned_threshold,
                    device=device,
                )
                self.bilstm = BiLSTMTemporalModel(
                    sequence_length=sequence_length,
                    threshold=learned_threshold,
                    device=device,
                )
            except Exception:
                self.learned_fusion = None
                self.bilstm = None

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

        # Automatic graceful fallback to baseline rule fusion if neural models or PyTorch are absent
        if active_mode in ("learned", "temporal"):
            if self.learned_fusion is None or (active_mode == "temporal" and self.bilstm is None):
                active_mode = "baseline"

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
            lstm_score = float(temporal_res["suspicion_probability"])

            # Compute instant learned MLP and rule-based fusion scores for frame-level responsiveness
            learned_res = self.learned_fusion.predict(vec)
            instant_learned = float(learned_res["suspicion_score"])
            instant_rule = float(rule_res["suspicion_score"])
            instant_score = max(instant_rule, instant_learned)

            # Responsive dual-branch calibration:
            # 1. Onset of suspicious activity: react instantly without waiting for 30-frame sequence fill
            if instant_score >= 0.35:
                suspicion_score = max(lstm_score, instant_score)
            # 2. Return to normal conduct: decay rapidly instead of staying stuck for 25 frames
            elif instant_score < 0.25 and lstm_score > 0.35:
                suspicion_score = (0.65 * instant_score) + (0.35 * lstm_score)
            else:
                suspicion_score = max(lstm_score, instant_score)

            flag = bool(suspicion_score >= self.learned_threshold)

            temporal_context = {
                "is_sustained": temporal_res["is_sustained"],
                "sequence_steps": len(buf.buffer),
            }
        else:
            raise ValueError(f"Unknown mode '{active_mode}'. Available: 'baseline', 'learned', 'temporal'.")

        # 4. Modality importance analysis (Phase 3 Part C)
        if compute_modality_importance is not None and self.learned_fusion is not None:
            importance = compute_modality_importance(self.learned_fusion)
        else:
            importance = {"visual": 0.40, "audio": 0.30, "browser": 0.30}

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
