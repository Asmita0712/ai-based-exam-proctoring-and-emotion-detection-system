"""
Builds [batch, sequence_length, feature_dim] sequences from
consecutive per-window feature vectors, for input to the BiLSTM.

Phase 0: interface stub only. Implemented in Phase 3, Part D.
"""


def build_sequences(feature_windows: list[dict], sequence_length: int = 30):
    raise NotImplementedError("Implemented in Phase 3: temporal context (sequence builder).")
