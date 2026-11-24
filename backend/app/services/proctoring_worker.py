"""
Decoupled AI Inference Worker & Adaptive Queue Architecture.
Handles high-concurrency (500 users) frame ingestion, backpressure, and async processing.
"""
import asyncio
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import os
import time
from typing import Any, Dict, Optional
import numpy as np

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("proctoring_worker")
settings = get_settings()


class InferenceQueueManager:
    """
    Manages bounded frame ingestion, adaptive sampling intervals,
    and thread/process pool worker offloading.
    """

    def __init__(self, max_workers: int = 4, max_queue_depth: int = 1500):
        self.max_workers = max_workers
        self.max_queue_depth = max_queue_depth
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="ai-inference")
        
        # Per-session tracking for adaptive backpressure
        self.session_last_frame_time: Dict[str, float] = defaultdict(float)
        self.session_in_flight: Dict[str, int] = defaultdict(int)
        self.total_processed_frames = 0
        self.total_throttled_frames = 0

    def calculate_sampling_interval_ms(self, active_session_count: int) -> int:
        """
        Dynamically calculates recommended client frame sampling interval
        based on active cluster concurrency.
        """
        if active_session_count <= 25:
            return 500   # 2 frames/sec (low load)
        elif active_session_count <= 100:
            return 1000  # 1 frame/sec (medium load)
        elif active_session_count <= 250:
            return 1800  # ~0.55 frame/sec (high load)
        else:
            return 2500  # ~0.4 frame/sec (500 peak load: total cluster fps ~200)

    def should_sample_frame(self, session_id: str, active_session_count: int = 1) -> bool:
        """
        Evaluates backpressure: prevents frame flooding if a worker is already busy
        with a session's frame or if the client is exceeding its sampling interval.
        """
        now = time.time()
        target_interval_sec = self.calculate_sampling_interval_ms(active_session_count) / 1000.0

        # Backpressure condition 1: A frame is already actively being processed for this session
        if self.session_in_flight[session_id] >= 1:
            self.total_throttled_frames += 1
            return False

        # Backpressure condition 2: Frame arrived faster than target interval
        last_time = self.session_last_frame_time.get(session_id, 0.0)
        if (now - last_time) < (target_interval_sec * 0.75):
            self.total_throttled_frames += 1
            return False

        self.session_last_frame_time[session_id] = now
        return True

    def mark_in_flight_start(self, session_id: str) -> None:
        self.session_in_flight[session_id] += 1

    def mark_in_flight_end(self, session_id: str) -> None:
        self.session_in_flight[session_id] = max(0, self.session_in_flight[session_id] - 1)
        self.total_processed_frames += 1


_QUEUE_MANAGER: Optional[InferenceQueueManager] = None


def get_queue_manager() -> InferenceQueueManager:
    global _QUEUE_MANAGER
    if _QUEUE_MANAGER is None:
        # Scale worker threads based on available CPU cores
        cpu_count = os.cpu_count() or 4
        workers = max(2, min(8, cpu_count))
        _QUEUE_MANAGER = InferenceQueueManager(max_workers=workers)
        logger.info("Initialized InferenceQueueManager with %d worker threads", workers)
    return _QUEUE_MANAGER
