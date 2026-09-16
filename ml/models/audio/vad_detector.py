"""
Voice Activity Detection (VAD) module using Silero VAD.

Adheres to:
- RULE 4: Clean reusable interface
- RULE 10: Configurable speech threshold, window size, sustained ratio
- RULE 13: Model loaded once during initialization
- RULE 14: Runs on CPU
- Outputs: speech_probability, sustained_talking
"""
from collections import deque
from typing import Any, Dict, Optional, Union
import numpy as np
import torch


class SileroVADDetector:
    """
    Detects voice activity and sustained speech in audio streams
    using Silero VAD over rolling windows.
    """

    SUPPORTED_SAMPLE_RATES = (8000, 16000)
    DEFAULT_CHUNK_SIZE = 512  # 512 samples @ 16kHz == 32ms

    def __init__(
        self,
        sample_rate: int = 16000,
        speech_threshold: float = 0.5,
        rolling_window_chunks: int = 30,  # ~1 second of chunks
        sustained_talking_ratio: float = 0.5,
    ) -> None:
        """
        Args:
            sample_rate: 16000 or 8000 Hz.
            speech_threshold: Probability threshold above which a chunk is classified as speech.
            rolling_window_chunks: Number of recent chunk probabilities to retain in memory.
            sustained_talking_ratio: Fraction of chunks in window that must be speech to flag sustained talking.
        """
        if sample_rate not in self.SUPPORTED_SAMPLE_RATES:
            raise ValueError(f"Sample rate must be one of {self.SUPPORTED_SAMPLE_RATES}, got {sample_rate}")

        self.sample_rate = sample_rate
        self.speech_threshold = speech_threshold
        self.sustained_ratio = sustained_talking_ratio
        self.history: deque = deque(maxlen=rolling_window_chunks)

        # Load Silero VAD model
        self.model, _ = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            force_reload=False,
            trust_repo=True,
        )
        self.model.eval()

    def process_chunk(self, chunk: Union[np.ndarray, torch.Tensor]) -> Dict[str, Any]:
        """
        Processes a single audio chunk (expected: 512 samples for 16kHz).

        Args:
            chunk: 1D numpy array or torch tensor of audio amplitudes normalized to [-1.0, 1.0].

        Returns:
            {
                "speech_probability": float,
                "sustained_talking": bool,
                "current_chunk_speech": bool
            }
        """
        if isinstance(chunk, np.ndarray):
            tensor = torch.from_numpy(chunk).float()
        else:
            tensor = chunk.float()

        # Ensure 1D
        if tensor.dim() > 1:
            tensor = tensor.squeeze()

        # If chunk is shorter than 512, pad with zeros
        if tensor.numel() < self.DEFAULT_CHUNK_SIZE:
            padded = torch.zeros(self.DEFAULT_CHUNK_SIZE, dtype=torch.float32)
            padded[: tensor.numel()] = tensor
            tensor = padded
        elif tensor.numel() > self.DEFAULT_CHUNK_SIZE:
            # truncate to chunk size if single chunk
            tensor = tensor[: self.DEFAULT_CHUNK_SIZE]

        with torch.no_grad():
            prob = float(self.model(tensor, self.sample_rate).item())

        self.history.append(prob)

        avg_prob = sum(self.history) / len(self.history)
        speech_chunks = sum(1 for p in self.history if p >= self.speech_threshold)
        sustained = (speech_chunks / len(self.history)) >= self.sustained_ratio

        return {
            "speech_probability": round(avg_prob, 3),
            "sustained_talking": bool(sustained),
            "current_chunk_speech": bool(prob >= self.speech_threshold),
        }

    def process_audio_buffer(self, buffer: Union[np.ndarray, torch.Tensor]) -> Dict[str, Any]:
        """
        Processes an arbitrary-length audio buffer by splitting it into 512-sample chunks.
        """
        if isinstance(buffer, torch.Tensor):
            arr = buffer.cpu().numpy()
        else:
            arr = np.array(buffer)

        if arr.ndim > 1:
            arr = arr.mean(axis=1)  # convert stereo to mono

        res = {"speech_probability": 0.0, "sustained_talking": False, "current_chunk_speech": False}
        for start in range(0, len(arr), self.DEFAULT_CHUNK_SIZE):
            chunk = arr[start : start + self.DEFAULT_CHUNK_SIZE]
            if len(chunk) > 0:
                res = self.process_chunk(chunk)

        return res

    def reset(self) -> None:
        """Clears audio history and internal model states."""
        self.history.clear()
        if hasattr(self.model, "reset_states"):
            self.model.reset_states()
