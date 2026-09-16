"""
Phase 0 requirement: verify microphone access before any audio
detection code is written. Run this locally.
"""
import sys
import numpy as np
import sounddevice as sd

DURATION_SEC = 3
SAMPLE_RATE = 16000
SILENCE_THRESHOLD = 0.001


def main() -> int:
    print(f"Recording for {DURATION_SEC} seconds -- say something...")
    try:
        recording = sd.rec(
            int(DURATION_SEC * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1
        )
        sd.wait()
    except Exception as exc:  # sounddevice raises varied backend errors
        print(f"ERROR: could not record audio: {exc}", file=sys.stderr)
        return 1

    volume = float(np.abs(recording).mean())
    print(f"Average volume: {volume:.5f}")

    if volume < SILENCE_THRESHOLD:
        print("WARNING: recording looks silent -- check mic permissions/selected device.")
        return 1

    print("Mic is capturing audio correctly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
