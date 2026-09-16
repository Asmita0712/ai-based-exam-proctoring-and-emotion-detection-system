# Multimodal AI-Based Online Examination Proctoring and Suspicious Activity Detection

Academic project implementing a multimodal exam-proctoring system that
fuses webcam signals (face, gaze, head-pose), audio activity, browser
behavior, and facial emotion into a suspicion score, benchmarked
against the Lamba & Sharma CNN-BiLSTM baseline (87.5% accuracy).

Built phase by phase. See `docs/architecture/overview.md` for the full
architecture and current phase status.

## Project structure

```
proctoring-system/
├── frontend/     React + Vite exam interface
├── backend/      FastAPI service (routes -> services -> ml/pipelines)
├── ml/           models, pipelines, fusion, temporal modeling
├── data/         raw/processed/features/labels/splits (not committed)
├── evaluation/   metrics, ablation, baseline comparison
├── notebooks/    exploration and experiments
├── models/       trained checkpoints (not committed)
├── scripts/      CLI entrypoints (collect_data, preprocess, train, evaluate)
├── tests/        unit / integration / evaluation tests
└── docs/         architecture and experiment notes
```

## Backend setup

```bash
cd backend
python3 -m venv ../venv
source ../venv/bin/activate      # Windows: ..\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Health check: `GET http://localhost:8000/health`

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Runs at `http://localhost:5173`, proxies `/api` to the backend.

## ML / scripts environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Linux note for the mic test

`sounddevice` needs the system PortAudio library on Linux:

```bash
sudo apt install portaudio19-dev
```

(Not required on Windows/macOS — sounddevice ships PortAudio for those.)

## Phase 0 verification

```bash
python scripts/test_camera.py   # requires a real webcam + display
python scripts/test_mic.py      # requires a real microphone
pytest tests/unit/test_health.py -v
```

## Phase 1 verification

Run all modality unit and pipeline integration tests:

```bash
pytest tests/ -v
```
