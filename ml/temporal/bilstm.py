"""
BiLSTM temporal context model (Phase 3, Part D).

Consumes sequences from sequence_builder.py, sitting after learned
fusion in the architecture:

    Per-window features -> Learned Fusion -> Sequence Builder -> BiLSTM -> Classifier

Not implemented in Phase 0/1 -- torch is a listed dependency for this
project but no temporal modeling code should exist before Phase 3.
"""


class BiLSTMTemporalModel:
    def __init__(self, *args, **kwargs):
        raise NotImplementedError("Implemented in Phase 3: temporal context (BiLSTM).")
