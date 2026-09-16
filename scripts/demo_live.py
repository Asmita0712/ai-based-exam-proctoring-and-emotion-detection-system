"""
Phase 1 Live Demo: Real-time visual proctoring using your webcam.

Displays in real-time:
- Person detection bounding boxes (YOLO)
- Multiple person alerts
- Gaze tracking & looking away indicator (MediaPipe)
- Head pose Euler angles (yaw, pitch, roll) & turned away alert (solvePnP)
- Live Rule-based Suspicion Score and active contributors

Run with:
    .\\venv\\Scripts\\python scripts/demo_live.py
Press 'q' to exit.
"""
import sys
import time
import cv2
import numpy as np

from ml.pipelines.visual_pipeline import VisualPipeline
from ml.fusion.baseline_fusion import RuleBasedFusion


def draw_hud(frame, visual_res, fusion_res, fps):
    h, w = frame.shape[:2]

    # 1. Draw bounding boxes
    boxes = visual_res.get("boxes", [])
    for box in boxes:
        x1, y1, x2, y2 = [int(v) for v in box]
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(
            frame,
            "Person",
            (x1, max(20, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )

    # 2. Semi-transparent overlay panel on top-left
    overlay = frame.copy()
    panel_w, panel_h = 390, 270
    cv2.rectangle(overlay, (10, 10), (10 + panel_w, 10 + panel_h), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

    # 3. Text statuses
    y = 35
    cv2.putText(frame, f"AI Proctoring Live Monitor (FPS: {fps:.1f})", (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

    # Person count & multi-person
    y += 26
    p_count = visual_res.get("person_count", 0)
    mp_flag = visual_res.get("multi_person_flag", False)
    p_color = (0, 0, 255) if mp_flag or p_count == 0 else (0, 255, 0)
    cv2.putText(frame, f"Persons: {p_count} {'[ALERT: Multi-person!]' if mp_flag else ''}", (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, p_color, 2)

    # Gaze
    y += 24
    gaze = visual_res.get("gaze", {})
    gaze_away = visual_res.get("looking_away", False)
    g_ratio = gaze.get("gaze_ratio", 0.5)
    g_color = (0, 0, 255) if gaze_away else (0, 255, 0)
    cv2.putText(frame, f"Gaze: {g_ratio:.2f} {'[LOOKING AWAY]' if gaze_away else '[ON SCREEN]'}", (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, g_color, 2)

    # Head Pose
    y += 24
    pose = visual_res.get("head_pose", {})
    turned_away = visual_res.get("turned_away", False)
    yaw, pitch = pose.get("yaw", 0.0), pose.get("pitch", 0.0)
    hp_color = (0, 0, 255) if turned_away else (0, 255, 0)
    cv2.putText(frame, f"Head Pose: Y:{yaw:.0f} P:{pitch:.0f} {'[TURNED AWAY]' if turned_away else '[FORWARD]'}", (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, hp_color, 2)

    # Emotion (Phase 2 Differentiator)
    y += 24
    emotion = visual_res.get("emotion", {})
    dom_emo = emotion.get("dominant_emotion", "neutral")
    emo_conf = emotion.get("emotion_confidence", 0.0)
    cv2.putText(frame, f"Emotion: {dom_emo.upper()} ({emo_conf:.2f}) [Behavioral Signal]", (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 100), 2)

    # Suspicion Score Bar
    y += 28
    score = fusion_res.get("suspicion_score", 0.0)
    is_flagged = fusion_res.get("flag", False)
    bar_color = (0, 0, 255) if is_flagged else (0, 255, 255) if score > 0.2 else (0, 255, 0)

    cv2.putText(frame, f"Suspicion Score: {score:.2f}", (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, bar_color, 2)

    # Draw score progress bar
    y += 10
    bar_x, bar_w, bar_h = 20, 220, 14
    cv2.rectangle(frame, (bar_x, y), (bar_x + bar_w, y + bar_h), (80, 80, 80), -1)
    fill_w = int(bar_w * min(1.0, max(0.0, score)))
    cv2.rectangle(frame, (bar_x, y), (bar_x + fill_w, y + bar_h), bar_color, -1)

    # Contributors
    y += 28
    contributors = fusion_res.get("contributors", [])
    if contributors:
        cv2.putText(frame, f"Alerts: {', '.join(contributors[:2])}", (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 140, 255), 1)
    else:
        cv2.putText(frame, "Alerts: None (Candidate Normal)", (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)

    return frame


def main():
    print("Initializing Phase 1 AI Models (YOLOv8 + MediaPipe + solvePnP + Fusion)...")
    pipeline = VisualPipeline()
    fusion = RuleBasedFusion(threshold=0.40)

    print("Opening webcam (press 'q' in the camera window to quit)...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Could not access webcam. Check camera permissions or index.")
        return 1

    prev_time = time.time()

    while True:
        ok, frame = cap.read()
        if not ok:
            print("Failed to grab frame from webcam.")
            break

        cur_time = time.time()
        fps = 1.0 / max(1e-5, (cur_time - prev_time))
        prev_time = cur_time

        # 1. Run visual pipeline
        visual_res = pipeline.process_frame(frame)

        # 2. Run baseline fusion
        fusion_res = fusion.fuse({
            "person_count": visual_res.get("person_count", 0),
            "multi_person_flag": visual_res.get("multi_person_flag", False),
            "no_person_flag": visual_res.get("no_person_flag", False),
            "looking_away": visual_res.get("looking_away", False),
            "turned_away": visual_res.get("turned_away", False),
        })

        # 3. Draw annotations on frame
        annotated_frame = draw_hud(frame, visual_res, fusion_res, fps)

        cv2.imshow("Multimodal Proctoring System - Phase 1 Live Demo", annotated_frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    sys.exit(main())
