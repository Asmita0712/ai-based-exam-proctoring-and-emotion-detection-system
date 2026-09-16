"""
Phase 0 requirement: verify camera access before any detection code
is written. Run this locally (it needs a real display + webcam --
it will not run headlessly in a CI/sandbox environment).
"""
import sys
import time
import cv2


def main() -> int:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: could not open webcam at index 0. Try index 1 or 2, "
              "or check OS camera permissions.", file=sys.stderr)
        return 1

    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    print(f"Resolution: {width:.0f} x {height:.0f}")

    frame_count = 0
    start = time.time()

    while True:
        ok, frame = cap.read()
        if not ok:
            print("ERROR: failed to read frame from webcam.", file=sys.stderr)
            break
        frame_count += 1
        cv2.imshow("camera test - press q to quit", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    elapsed = time.time() - start
    if elapsed > 0:
        print(f"Measured FPS: {frame_count / elapsed:.1f}")

    cap.release()
    cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    sys.exit(main())
