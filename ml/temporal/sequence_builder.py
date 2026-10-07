"""
Sequence builder for BiLSTM temporal modeling (Phase 3, Part D).

Adheres to:
- Converts consecutive per-window feature vectors into [batch, sequence_length, feature_dim]
- Configurable sequence length (e.g. 30–60 windows)
- Provides streaming SequenceBuffer for real-time inference with zero-padding
"""
from collections import deque
from typing import Any, Dict, List, Optional, Union
import numpy as np

from ml.utils.feature_standardizer import FeatureStandardizer, FEATURE_DIM


def build_sequences(
    feature_windows: List[Union[Dict[str, Any], np.ndarray]],
    sequence_length: int = 30,
    step: int = 1,
) -> np.ndarray:
    """
    Constructs overlapping sequences of shape [num_sequences, sequence_length, feature_dim].

    Args:
        feature_windows: List of window dicts or 1D numpy arrays.
        sequence_length: Number of consecutive windows per sequence (default: 30).
        step: Stride between successive sequences.

    Returns:
        3D numpy array of shape [num_sequences, sequence_length, 24].
    """
    standardizer = FeatureStandardizer()
    if not feature_windows:
        return np.empty((0, sequence_length, FEATURE_DIM), dtype=np.float32)

    # Convert all windows to vectors
    vectors = []
    for w in feature_windows:
        if isinstance(w, dict):
            vectors.append(standardizer.vectorize(w))
        elif isinstance(w, np.ndarray):
            vectors.append(w.astype(np.float32))
        else:
            raise TypeError(f"Expected dict or np.ndarray, got {type(w)}")

    data = np.array(vectors, dtype=np.float32)

    # If shorter than sequence_length, pad leading windows with zeros
    if len(data) < sequence_length:
        pad_len = sequence_length - len(data)
        pad = np.zeros((pad_len, FEATURE_DIM), dtype=np.float32)
        padded_data = np.vstack([pad, data])
        return np.expand_dims(padded_data, axis=0)

    sequences = []
    for i in range(0, len(data) - sequence_length + 1, step):
        sequences.append(data[i : i + sequence_length])

    return np.array(sequences, dtype=np.float32)


class SequenceBuffer:
    """
    Streaming FIFO buffer maintaining the recent `sequence_length` windows
    for real-time BiLSTM inference.
    """

    def __init__(self, sequence_length: int = 30) -> None:
        self.sequence_length = sequence_length
        self.standardizer = FeatureStandardizer()
        self.buffer: deque = deque(maxlen=sequence_length)

    def add_window(self, window: Union[Dict[str, Any], np.ndarray]) -> None:
        """Appends a new window to the streaming buffer."""
        if isinstance(window, dict):
            vec = self.standardizer.vectorize(window)
        elif isinstance(window, np.ndarray):
            vec = window.astype(np.float32)
        else:
            raise TypeError(f"Expected dict or np.ndarray, got {type(window)}")

        self.buffer.append(vec)

    def get_sequence(self) -> np.ndarray:
        """
        Returns a single sequence tensor of shape (1, sequence_length, 24).
        If buffer has fewer items than sequence_length, pads leading steps with zeros.
        """
        items = list(self.buffer)
        if len(items) < self.sequence_length:
            pad_len = self.sequence_length - len(items)
            pad = [np.zeros(FEATURE_DIM, dtype=np.float32) for _ in range(pad_len)]
            full = pad + items
        else:
            full = items[-self.sequence_length :]

        arr = np.array(full, dtype=np.float32)
        return np.expand_dims(arr, axis=0)

    def reset(self) -> None:
        """Clears the temporal window buffer."""
        self.buffer.clear()
