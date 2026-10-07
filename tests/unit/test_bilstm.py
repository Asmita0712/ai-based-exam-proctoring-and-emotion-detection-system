"""
Unit tests for SequenceBuilder and BiLSTMTemporalModel (Phase 3 Part D).
"""
import numpy as np
import pytest

from ml.temporal.sequence_builder import build_sequences, SequenceBuffer
from ml.temporal.bilstm import BiLSTMTemporalModel


def test_sequence_builder():
    windows = [{"person_count": 1} for _ in range(50)]
    seqs = build_sequences(windows, sequence_length=30, step=1)

    assert seqs.shape == (21, 30, 24)

    # Shorter than sequence_length pads automatically
    few_windows = [{"person_count": 1} for _ in range(5)]
    padded_seqs = build_sequences(few_windows, sequence_length=30)
    assert padded_seqs.shape == (1, 30, 24)


def test_sequence_buffer_streaming():
    buf = SequenceBuffer(sequence_length=10)
    for _ in range(5):
        buf.add_window({"person_count": 1})

    seq = buf.get_sequence()
    assert seq.shape == (1, 10, 24)


def test_bilstm_inference_and_fit():
    bilstm = BiLSTMTemporalModel(sequence_length=15, device="cpu")

    # Sequence inference
    dummy_seq = np.zeros((1, 15, 24), dtype=np.float32)
    res = bilstm.predict_sequence(dummy_seq)

    assert "suspicion_probability" in res
    assert "flag" in res
    assert "is_sustained" in res
    assert 0.0 <= res["suspicion_probability"] <= 1.0

    # Training test
    X_seq = np.random.randn(8, 15, 24).astype(np.float32)
    y = np.random.randint(0, 2, size=(8,)).astype(np.float32)
    fit_res = bilstm.fit(X_seq, y, epochs=2, batch_size=4)
    assert fit_res["epochs"] == 2
    assert "final_loss" in fit_res
