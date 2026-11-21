"""
Data collection script (Phase 4).

Records or generates synchronized multi-subject exam sessions:
- Normal (compliant) sessions
- Suspicious sessions (looking away, head turned, multi-person presence, speech, tab switching)
Saves raw session data into data/raw/ with subject_id, session_id, and timestamps.
"""
import argparse
import json
import os
import time
from typing import Any, Dict, List
import numpy as np


def generate_synthetic_session(
    subject_id: str,
    session_id: str,
    duration_windows: int = 60,
    is_suspicious: bool = False,
) -> Dict[str, Any]:
    """
    Generates a synchronized session record with multi-modal behavioral signals.
    Adheres to realistic temporal patterns (normal vs. staged cheating actions).
    """
    windows: List[Dict[str, Any]] = []
    base_ts = time.time() - (duration_windows * 1.0)

    for i in range(duration_windows):
        ts = base_ts + i * 1.0
        # Normal baseline conditions
        looking_away = False
        gaze_ratio = float(np.random.normal(0.5, 0.04))
        vert_ratio = float(np.random.normal(0.5, 0.04))
        yaw = float(np.random.normal(0.0, 4.0))
        pitch = float(np.random.normal(0.0, 3.0))
        person_count = 1
        multi_person_flag = False
        speech_prob = float(np.random.uniform(0.01, 0.08))
        sustained_talking = False
        tab_hidden = False
        dom_emo = "neutral"
        emo_conf = float(np.random.uniform(0.65, 0.9))
        emo_scores = {
            "neutral": emo_conf,
            "happy": 0.05,
            "sad": 0.03,
            "surprise": 0.02,
            "fear": 0.02,
            "angry": 0.01,
            "disgust": 0.01,
        }

        # If suspicious session, inject sustained or repeated violation behaviors in middle intervals
        if is_suspicious and (15 <= i <= 40):
            behavior_type = (hash(subject_id) + i // 8) % 4
            if behavior_type == 0:
                # Gaze & Head pose shift (looking away at notes/phone)
                looking_away = True
                gaze_ratio = 0.78
                yaw = 35.0
                emo_scores["fear"] = 0.45
                emo_scores["neutral"] = 0.35
                dom_emo = "fear"
            elif behavior_type == 1:
                # Talking / Whispering to external collaborator
                speech_prob = 0.82
                sustained_talking = True
            elif behavior_type == 2:
                # Multi-person presence
                person_count = 2
                multi_person_flag = True
            elif behavior_type == 3:
                # Tab switching
                tab_hidden = True

        window_record = {
            "window_index": i,
            "timestamp": round(ts, 3),
            "person_count": person_count,
            "multi_person_flag": multi_person_flag,
            "no_person_flag": person_count == 0,
            "gaze": {
                "gaze_ratio": round(gaze_ratio, 3),
                "vertical_ratio": round(vert_ratio, 3),
                "looking_away": looking_away,
                "confidence": 0.95,
            },
            "looking_away": looking_away,
            "head_pose": {
                "yaw": round(yaw, 2),
                "pitch": round(pitch, 2),
                "roll": 0.0,
                "turned_away": abs(yaw) > 25.0,
            },
            "turned_away": abs(yaw) > 25.0,
            "audio": {
                "speech_probability": round(speech_prob, 3),
                "sustained_talking": sustained_talking,
            },
            "speech_probability": round(speech_prob, 3),
            "sustained_talking": sustained_talking,
            "tab_hidden": tab_hidden,
            "window_blur": tab_hidden,
            "is_away": tab_hidden,
            "emotion": {
                "dominant_emotion": dom_emo,
                "emotion_confidence": round(emo_conf, 3),
                "emotion_scores": {k: round(v, 3) for k, v in emo_scores.items()},
            },
        }
        windows.append(window_record)

    return {
        "subject_id": subject_id,
        "session_id": session_id,
        "label": 1 if is_suspicious else 0,
        "label_name": "suspicious" if is_suspicious else "compliant",
        "duration_windows": duration_windows,
        "windows": windows,
    }


def collect_dataset(
    output_dir: str = "data/raw",
    num_subjects: int = 12,
    windows_per_session: int = 40,
) -> List[str]:
    """
    Generates and saves multi-subject exam sessions with realistic normal and suspicious cases.
    """
    os.makedirs(output_dir, exist_ok=True)
    session_files = []

    for subj_idx in range(1, num_subjects + 1):
        subj_id = f"SUBJ_{subj_idx:03d}"
        # For each subject, record 1 normal session and 1 staged suspicious session
        for is_susp in [False, True]:
            sess_id = f"SESS_{subj_id}_{'SUSP' if is_susp else 'NORM'}"
            session_data = generate_synthetic_session(
                subject_id=subj_id,
                session_id=sess_id,
                duration_windows=windows_per_session,
                is_suspicious=is_susp,
            )
            file_path = os.path.join(output_dir, f"{sess_id}.json")
            with open(file_path, "w") as f:
                json.dump(session_data, f, indent=2)
            session_files.append(file_path)

    return session_files


def main():
    parser = argparse.ArgumentParser(description="Collect / generate examination session recordings.")
    parser.add_argument("--output_dir", default="data/raw", help="Path to raw data output directory.")
    parser.add_argument("--subjects", type=int, default=12, help="Number of distinct test subjects.")
    parser.add_argument("--windows", type=int, default=40, help="Number of windows per session.")
    args = parser.parse_args()

    print(f"Collecting sessions for {args.subjects} subjects into '{args.output_dir}'...")
    files = collect_dataset(args.output_dir, args.subjects, args.windows)
    print(f"Collection complete: {len(files)} session files saved.")


if __name__ == "__main__":
    main()
