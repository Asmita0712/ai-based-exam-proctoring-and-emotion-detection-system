# Architecture Overview

This mirrors the fixed architecture agreed for this project. Do not
diverge from this without an explicit decision to change it.

```
                    Exam Web Interface / Frontend
                                |
              +------------------+------------------+
              |                 |                  |
           Webcam           Microphone       Browser Events
              |                 |                  |
              v                 v                  v
        Visual Pipeline    Audio Pipeline    Tab Tracking
              |                 |                  |
              +------------------+------------------+
                                v
                    Feature Extraction Layer
                                |
             +------------------+------------------+
             |                  |                  |
          Gaze              Head Pose           Emotion
          Face             Multi-Person         Audio
             |                  |                  |
             +------------------+------------------+
                                v
                    Per-Window Feature Vector
                                |
                                v
                  Learned Multimodal Fusion
                                |
                                v
                       Suspicion Probability
                                |
                                v
                     Temporal Context Model (BiLSTM)
                                |
                                v
                 Final Suspicious Classification
                                |
                                v
                  Evidence + Explanation + Score
```

## Phase status

| Phase | Scope | Status |
|---|---|---|
| 0 | Project structure & environment | Complete |
| 1 | Basic multimodal proctoring model (rule-based) | Not started |
| 2 | Emotion detection differentiator | Not started |
| 3 | Learned fusion + temporal context | Not started |
| 4 | Dataset, training & evaluation | Not started |
