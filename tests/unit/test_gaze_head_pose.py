"""
Unit tests for GazeEstimator and HeadPoseEstimator.
"""
import numpy as np
import pytest
from ml.models.gaze.gaze_estimator import GazeEstimator
from ml.models.head_pose.head_pose_estimator import HeadPoseEstimator


def test_gaze_estimator_none_landmarks():
    gaze = GazeEstimator(smoothing_window=5)
    res = gaze.estimate_from_landmarks(None)

    assert "gaze_ratio" in res
    assert "vertical_ratio" in res
    assert "looking_away" in res
    assert "confidence" in res
    assert res["looking_away"] is False
    assert res["confidence"] == 0.0


def test_head_pose_estimator_none_landmarks():
    pose = HeadPoseEstimator(yaw_threshold=25.0, pitch_threshold=20.0)
    res = pose.estimate_from_landmarks(None)

    assert "yaw" in res
    assert "pitch" in res
    assert "roll" in res
    assert "turned_away" in res
    assert res["turned_away"] is False
    assert res["yaw"] == 0.0


def test_gaze_and_head_pose_empty_frame():
    gaze = GazeEstimator()
    pose = HeadPoseEstimator()

    empty_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    gaze_res = gaze.estimate(empty_frame)
    pose_res = pose.estimate(empty_frame)

    assert gaze_res["looking_away"] is False
    assert pose_res["turned_away"] is False
