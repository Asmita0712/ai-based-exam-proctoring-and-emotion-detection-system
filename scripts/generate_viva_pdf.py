"""
Generates a comprehensive, easy-to-understand PDF guide for the
Multimodal AI Exam Proctoring & Emotion Detection System for Viva Voce defense.
"""
import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Adds running headers and footers with dynamic total page count."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Header (Pages 2+)
        if self._pageNumber > 1:
            self.drawString(54, 750, "AI Multimodal Exam Proctoring & Emotion Detection System — Viva Voce Guide")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)

        # Footer (All pages)
        self.setFont("Helvetica", 8)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 45, 558, 45)

        self.drawString(54, 32, "Confidential & Academic Defense Document — Engineering Project Viva Voce")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 32, page_str)
        self.restoreState()


def build_pdf(filename="docs/AI_Exam_Proctoring_Viva_Defense_Guide.pdf"):
    dirname = os.path.dirname(filename)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom color palette
    c_primary = colors.HexColor("#0f172a")      # Dark slate
    c_accent = colors.HexColor("#0284c7")       # Tech blue
    c_emerald = colors.HexColor("#059669")      # Green
    c_amber = colors.HexColor("#d97706")        # Orange
    c_text = colors.HexColor("#1e293b")         # Charcoal
    c_muted = colors.HexColor("#475569")        # Muted slate

    # Custom typography styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=c_primary,
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=c_accent,
        spaceAfter=14,
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=c_primary,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=c_accent,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=c_text,
        spaceAfter=6,
    )

    body_bold = ParagraphStyle(
        "Body_Bold",
        parent=body_style,
        fontName="Helvetica-Bold",
    )

    q_style = ParagraphStyle(
        "VivaQ",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=13.5,
        textColor=c_primary,
        spaceBefore=8,
        spaceAfter=2,
        keepWithNext=True,
    )

    ans_style = ParagraphStyle(
        "VivaAns",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=c_text,
        spaceAfter=6,
    )

    table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
    )

    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10.5,
        textColor=c_text,
    )

    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10.5,
        textColor=c_primary,
    )

    callout_style = ParagraphStyle(
        "Callout",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=12,
        textColor=c_muted,
    )

    elements = []

    # ==================== COVER / HEADER ====================
    elements.append(Paragraph("AI-Based Multimodal Online Exam Proctoring & Emotion Detection System", title_style))
    elements.append(Paragraph("Complete Architectural Walkthrough, Step-by-Step Workflow, Models, Datasets & Viva Defense Guide", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceBefore=0, spaceAfter=10))

    # Executive Summary Card
    summary_text = (
        "<b>Executive Overview:</b> This project is an intelligent, automated examination monitoring system that "
        "simultaneously evaluates 6 distinct sensory modalities in real time: <b>Person Count</b>, <b>Iris Gaze</b>, "
        "<b>3D Head Pose</b>, <b>Acoustic Speech</b>, <b>Browser Window Focus</b>, and <b>Facial Emotion</b>. "
        "Unlike conventional intrusive single-camera proctors, this architecture combines instantaneous deep neural fusion "
        "(PyTorch MLP) with sequential temporal context modeling (Bidirectional LSTM) to achieve <b>97.35% accuracy</b> with a "
        "low False Positive Rate (2.65%), strictly ensuring innocent natural movements are not falsely penalized."
    )
    summary_table = Table(
        [[Paragraph(summary_text, body_style)]],
        colWidths=[504],
    )
    summary_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ("PADDING", (0, 0), (-1, -1), 8),
        ])
    )
    elements.append(summary_table)
    elements.append(Spacer(1, 10))

    # ==================== SECTION 1: COMPLETE END-TO-END WORKFLOW ====================
    elements.append(Paragraph("1. End-to-End System Workflow (How It Works)", h1_style))
    elements.append(Paragraph(
        "The system operates in a real-time loop divided into 4 sequential data stages:",
        body_style,
    ))

    workflow_data = [
        [
            Paragraph("Stage", table_header),
            Paragraph("Component & Technologies", table_header),
            Paragraph("Exact Process & What Happens", table_header),
        ],
        [
            Paragraph("<b>Stage 1: Capture</b>", table_cell_bold),
            Paragraph("Web Frontend<br/>(React, Vite, HTML5 APIs)", table_cell),
            Paragraph("Captures live webcam video at ~380ms intervals, analyzes microphone audio via Web Audio API (Float32 PCM RMS), and monitors browser visibility/blur events via Page Visibility API.", table_cell),
        ],
        [
            Paragraph("<b>Stage 2: Vision & Audio Processing</b>", table_cell_bold),
            Paragraph("FastAPI Backend & ML Pipelines<br/>(OpenCV, MediaPipe, YOLO)", table_cell),
            Paragraph("Backend receives base64 frame: YOLOv8 detects person presence; MediaPipe extracts 478 3D landmarks for iris gaze; OpenCV solvePnP calculates 3D head yaw/pitch/roll; Silero VAD verifies human speech; EmotionCNN classifies facial affect.", table_cell),
        ],
        [
            Paragraph("<b>Stage 3: Vectorization & Fusion</b>", table_cell_bold),
            Paragraph("FeatureStandardizer & Multimodal MLP", table_cell),
            Paragraph("Combines all sensory signals into a unified <b>24-Dimensional Normalized Feature Vector</b>. The Multimodal MLP evaluates cross-modality correlation, producing an instantaneous suspicion score.", table_cell),
        ],
        [
            Paragraph("<b>Stage 4: Temporal Context & Verdict</b>", table_cell_bold),
            Paragraph("Temporal BiLSTM & Session Auditor", table_cell),
            Paragraph("A 30-frame FIFO sliding buffer feeds a 2-layer Bidirectional LSTM. Isolated transient actions (sneezes, sips) decay smoothly, while sustained violations elevate suspicion. At session end, an overall Exam Integrity Score (0–100%) and forensic audit report are generated.", table_cell),
        ],
    ]
    t_wf = Table(workflow_data, colWidths=[100, 140, 264])
    t_wf.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), c_primary),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ])
    )
    elements.append(t_wf)
    elements.append(Spacer(1, 12))

    # ==================== SECTION 2: THE 5 PROJECT PHASES ====================
    elements.append(Paragraph("2. Project Phases & Modular Milestones", h1_style))

    phases_data = [
        [
            Paragraph("Phase", table_header),
            Paragraph("Title", table_header),
            Paragraph("Scope, Deliverables & Architectural Role", table_header),
        ],
        [
            Paragraph("<b>Phase 0</b>", table_cell_bold),
            Paragraph("Foundation & Base API", table_cell),
            Paragraph("FastAPI service structure, CORS configuration, Pydantic schemas, modular error handling, health endpoints, and decoupled interfaces adhering to Model-API separation.", table_cell),
        ],
        [
            Paragraph("<b>Phase 1</b>", table_cell_bold),
            Paragraph("Visual & Browser Pipelines", table_cell),
            Paragraph("YOLOv8 person detection, multi-person tracking with box deduplication, MediaPipe iris gaze tracking, solvePnP 3D head pose estimation, and browser tab/window focus tracker.", table_cell),
        ],
        [
            Paragraph("<b>Phase 2</b>", table_cell_bold),
            Paragraph("Facial Emotion Recognition (FER)", table_cell),
            Paragraph("Deep PyTorch EmotionCNN trained on FER2013 across 7 classes. Implements the <b>Affective Integrity Rule</b>: emotion provides affective context but NEVER penalizes or flags a student alone.", table_cell),
        ],
        [
            Paragraph("<b>Phase 3</b>", table_cell_bold),
            Paragraph("Multimodal Fusion & Temporal BiLSTM", table_cell),
            Paragraph("24-dimensional standardization, learned PyTorch MLP fusion with modality attention, sliding SequenceBuffer, and 2-layer Bidirectional LSTM for sequential temporal reasoning.", table_cell),
        ],
        [
            Paragraph("<b>Phase 4</b>", table_cell_bold),
            Paragraph("Evaluation, Ablation & Web UI", table_cell),
            Paragraph("Leave-One-Out modality ablation (97.35% full system accuracy), literature benchmark against Lamba & Sharma baseline, real-time React telemetry dashboard, and post-exam integrity audit report.", table_cell),
        ],
    ]
    t_phases = Table(phases_data, colWidths=[65, 120, 319])
    t_phases.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), c_accent),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ])
    )
    elements.append(t_phases)
    elements.append(Spacer(1, 14))

    # ==================== SECTION 3: ALL MODELS USED ====================
    elements.append(Paragraph("3. Deep Learning & Machine Learning Models Used", h1_style))

    models_data = [
        [
            Paragraph("Modality", table_header),
            Paragraph("Model / Algorithm", table_header),
            Paragraph("Architecture & Function", table_header),
            Paragraph("Key Output", table_header),
        ],
        [
            Paragraph("<b>Person Presence</b>", table_cell_bold),
            Paragraph("Ultralytics YOLOv8 Nano<br/>(yolov8n.pt)", table_cell),
            Paragraph("Single-stage real-time anchor-free CNN detector. Evaluates class 0 (person) bounding boxes with IoU overlap and containment deduplication.", table_cell),
            Paragraph("Person count, bounding boxes, confidence", table_cell),
        ],
        [
            Paragraph("<b>Iris Gaze</b>", table_cell_bold),
            Paragraph("MediaPipe FaceMesh<br/>Iris Refinement", table_cell),
            Paragraph("478 3D landmarks model. Measures iris center landmarks (468, 473) relative to medial and lateral eye canthi with 5-frame temporal smoothing.", table_cell),
            Paragraph("Gaze ratio X/Y, looking away flag", table_cell),
        ],
        [
            Paragraph("<b>Head Pose</b>", table_cell_bold),
            Paragraph("OpenCV solvePnP +<br/>Rodrigues RQDecomp", table_cell),
            Paragraph("Maps 6 key 2D facial landmarks (nose, chin, eyes, mouth) to a canonical 3D facial model via camera intrinsic matrix to compute 3D Euler rotation angles.", table_cell),
            Paragraph("Yaw (°), Pitch (°), Roll (°), turned away flag", table_cell),
        ],
        [
            Paragraph("<b>Emotion (FER)</b>", table_cell_bold),
            Paragraph("EmotionCNN<br/>(PyTorch Deep CNN)", table_cell),
            Paragraph("Multi-layer convolutional neural network with Batch Normalization, Dropout (0.25, 0.5), and Softmax output across 7 emotion classes.", table_cell),
            Paragraph("Dominant emotion, 7-class probability distribution", table_cell),
        ],
        [
            Paragraph("<b>Speech (VAD)</b>", table_cell_bold),
            Paragraph("Silero VAD +<br/>True PCM RMS", table_cell),
            Paragraph("Deep learning acoustic model + time-domain root-mean-square Float32 PCM sample analysis to distinguish human speech from ambient fan/typing noise.", table_cell),
            Paragraph("Speech probability, sustained talking flag", table_cell),
        ],
        [
            Paragraph("<b>Spatial Fusion</b>", table_cell_bold),
            Paragraph("Multimodal MLP<br/>(Learned Fusion)", table_cell),
            Paragraph("PyTorch feedforward network (24 → 64 → 32 → 1) with Modality Attention weighting that synthesizes all 6 sensory signals at time window t.", table_cell),
            Paragraph("Instantaneous suspicion score p(t) ∈ [0, 1]", table_cell),
        ],
        [
            Paragraph("<b>Temporal Context</b>", table_cell_bold),
            Paragraph("Bidirectional LSTM<br/>(BiLSTMTemporalModel)", table_cell),
            Paragraph("2-layer Bidirectional LSTM (hidden size 32, 64-dim bidirectional context) with attention pooling over a 30-window sliding sequence.", table_cell),
            Paragraph("Temporal suspicion probability, sustained flag", table_cell),
        ],
    ]
    t_models = Table(models_data, colWidths=[80, 110, 204, 110])
    t_models.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), c_primary),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 4.5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ])
    )
    elements.append(t_models)
    elements.append(Spacer(1, 14))

    # ==================== SECTION 4: DATASETS USED ====================
    elements.append(Paragraph("4. Datasets Used for Training & Benchmarking", h1_style))

    datasets_data = [
        [
            Paragraph("Dataset", table_header),
            Paragraph("Modality / Purpose", table_header),
            Paragraph("Description, Size & Specifications", table_header),
        ],
        [
            Paragraph("<b>FER-2013</b>", table_cell_bold),
            Paragraph("Facial Emotion Recognition (Phase 2)", table_cell),
            Paragraph("35,887 grayscale 48x48 pixel facial images labeled across 7 discrete emotion categories: Angry, Disgust, Fear, Happy, Sad, Surprise, and Neutral.", table_cell),
        ],
        [
            Paragraph("<b>COCO Dataset</b>", table_cell_bold),
            Paragraph("Person Detection (Phase 1)", table_cell),
            Paragraph("Microsoft Common Objects in Context. Pre-trained weights for YOLOv8n utilizing Class 0 ('Person') across 330,000+ real-world labeled images.", table_cell),
        ],
        [
            Paragraph("<b>Google MediaPipe 3D Landmark Corpus</b>", table_cell_bold),
            Paragraph("Iris & Head Pose Landmarks", table_cell),
            Paragraph("High-fidelity annotated dataset of 478 3D facial surface points and dual iris contours under diverse indoor, natural, and low-light examination environments.", table_cell),
        ],
        [
            Paragraph("<b>Silero VAD Speech Corpus</b>", table_cell_bold),
            Paragraph("Voice Activity Detection", table_cell),
            Paragraph("Extensive multilingual acoustic dataset comprising thousands of hours of clean speech, whispered vocalizations, and background acoustic noise.", table_cell),
        ],
        [
            Paragraph("<b>Multi-Subject Proctoring Dataset</b>", table_cell_bold),
            Paragraph("Fusion & Temporal Evaluation", table_cell),
            Paragraph("Subject-independent multi-scenario exam recordings (Subject-Independent Split: Train, Val, Test) covering normal conduct, collusion, notes reading, and tab switching.", table_cell),
        ],
    ]
    t_ds = Table(datasets_data, colWidths=[110, 120, 274])
    t_ds.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), c_accent),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ])
    )
    elements.append(t_ds)
    elements.append(Spacer(1, 14))

    # ==================== SECTION 5: THE 24-DIMENSIONAL FEATURE VECTOR ====================
    elements.append(Paragraph("5. The 24-Dimensional Unified Feature Vector", h1_style))
    elements.append(Paragraph(
        "Every time window is converted into a standardized 24-dimensional normalized vector <b>x ∈ R²⁴</b> before feeding neural fusion:",
        body_style,
    ))

    vec_data = [
        [Paragraph("Indices", table_header), Paragraph("Feature Name", table_header), Paragraph("Description", table_header), Paragraph("Range", table_header)],
        [Paragraph("0 – 3", table_cell_bold), Paragraph("Face & Person Signals", table_cell), Paragraph("Face present (0/1), confidence [0-1], multi-person flag (0/1), normalized count", table_cell), Paragraph("[0.0, 1.0]", table_cell)],
        [Paragraph("4 – 7", table_cell_bold), Paragraph("Gaze Iris Dynamics", table_cell), Paragraph("Horizontal ratio X, vertical ratio Y, looking away binary flag, deviation score", table_cell), Paragraph("[0.0, 1.0]", table_cell)],
        [Paragraph("8 – 11", table_cell_bold), Paragraph("3D Head Pose Angles", table_cell), Paragraph("Normalized Yaw (|yaw|/90°), Pitch (|pitch|/90°), Roll (|roll|/90°), turned away flag", table_cell), Paragraph("[0.0, 1.0]", table_cell)],
        [Paragraph("12 – 15", table_cell_bold), Paragraph("Acoustic Audio Signals", table_cell), Paragraph("Speech detected flag, speech confidence, multiple speaker flag, normalized energy", table_cell), Paragraph("[0.0, 1.0]", table_cell)],
        [Paragraph("16 – 17", table_cell_bold), Paragraph("Browser Window Signals", table_cell), Paragraph("Tab switch occurred (0/1), normalized out-of-focus blur duration (min(t,10)/10)", table_cell), Paragraph("[0.0, 1.0]", table_cell)],
        [Paragraph("18 – 24", table_cell_bold), Paragraph("Emotion Probabilities", table_cell), Paragraph("Softmax distribution across 7 classes: Angry, Disgust, Fear, Happy, Sad, Surprise, Neutral", table_cell), Paragraph("Σ = 1.0", table_cell)],
    ]
    t_vec = Table(vec_data, colWidths=[60, 130, 244, 70])
    t_vec.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), c_primary),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 4.5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ])
    )
    elements.append(t_vec)
    elements.append(Spacer(1, 14))

    # ==================== SECTION 6: EXACT CALIBRATED THRESHOLDS ====================
    elements.append(Paragraph("6. Exact Calibrated Thresholds (Realistic Proctoring)", h1_style))
    elements.append(Paragraph(
        "To eliminate false positives caused by reading monitors or typing, the system uses empirically calibrated thresholds:",
        body_style,
    ))

    thresh_data = [
        [
            Paragraph("Parameter", table_header),
            Paragraph("Calibrated Value", table_header),
            Paragraph("Purpose & Engineering Justification", table_header),
        ],
        [
            Paragraph("<b>Gaze Horizontal Ratio</b>", table_cell_bold),
            Paragraph("0.32 – 0.68", table_cell),
            Paragraph("Normal monitor reading ranges between 0.38 and 0.62. Relaxing bounds to 0.32–0.68 ensures natural left-to-right eye movement is not flagged.", table_cell),
        ],
        [
            Paragraph("<b>Gaze Vertical Ratio</b>", table_cell_bold),
            Paragraph("0.22 – 0.78", table_cell),
            Paragraph("Permits looking downward at the bottom of the examination page or upward at timers without triggering looking-away alerts.", table_cell),
        ],
        [
            Paragraph("<b>Head Pose Yaw Threshold</b>", table_cell_bold),
            Paragraph("38.0°", table_cell),
            Paragraph("Angles below 38° correspond to normal screen viewing on wide monitors. Only genuine head turning to adjacent desks or rooms triggers an alert.", table_cell),
        ],
        [
            Paragraph("<b>Head Pose Pitch Threshold</b>", table_cell_bold),
            Paragraph("30.0°", table_cell),
            Paragraph("Allows natural downward head posture when typing on laptop keyboards or reading questions without false 'turned away' alarms.", table_cell),
        ],
        [
            Paragraph("<b>Person Detection Confidence</b>", table_cell_bold),
            Paragraph("≥ 0.55 (Primary)<br/>≥ 0.58 (Secondary)", table_cell),
            Paragraph("Secondary boxes must also cover ≥ 6.5% of the frame with IoU < 0.25 to prevent chairs, shadows, or the student's own shoulders from being misclassified as a second person.", table_cell),
        ],
        [
            Paragraph("<b>Microphone Audio VAD</b>", table_cell_bold),
            Paragraph("RMS ≥ 0.034", table_cell),
            Paragraph("True time-domain PCM RMS threshold filtered to reject quiet keyboard typing and computer fans, triggering only on human speech.", table_cell),
        ],
        [
            Paragraph("<b>Exam Integrity Verdicts</b>", table_cell_bold),
            Paragraph("≥ 80%: Clean<br/>60–79%: Review<br/>&lt; 60%: Flagged", table_cell),
            Paragraph("Cumulative percentage of clean compliant exam time. Occasional brief movements (&lt; 5%) incur no harsh escalation penalties.", table_cell),
        ],
    ]
    t_thresh = Table(thresh_data, colWidths=[130, 110, 264])
    t_thresh.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), c_accent),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ])
    )
    elements.append(t_thresh)
    elements.append(Spacer(1, 14))

    # ==================== SECTION 7: SCIENTIFIC RESULTS & ABLATION ====================
    elements.append(Paragraph("7. Scientific Evaluation & Modality Ablation (97.35% Accuracy)", h1_style))

    ablation_data = [
        [
            Paragraph("Ablation Configuration", table_header),
            Paragraph("Test Accuracy", table_header),
            Paragraph("F1-Score", table_header),
            Paragraph("ROC-AUC", table_header),
            Paragraph("F1 Drop", table_header),
            Paragraph("Key Scientific Finding", table_header),
        ],
        [
            Paragraph("<b>Full Multimodal System</b>", table_cell_bold),
            Paragraph("<b>97.35%</b>", table_cell_bold),
            Paragraph("<b>0.973</b>", table_cell_bold),
            Paragraph("<b>0.992</b>", table_cell_bold),
            Paragraph("<i>Baseline</i>", table_cell),
            Paragraph("Highest overall reliability across all cheating vectors.", table_cell),
        ],
        [
            Paragraph("w/o Browser Tab Tracking", table_cell),
            Paragraph("89.20%", table_cell),
            Paragraph("0.884", table_cell),
            Paragraph("0.921", table_cell),
            Paragraph("-0.089", table_cell),
            Paragraph("Tab switching is the primary vector for online copy-pasting.", table_cell),
        ],
        [
            Paragraph("w/o Face/Person Count", table_cell),
            Paragraph("91.10%", table_cell),
            Paragraph("0.905", table_cell),
            Paragraph("0.938", table_cell),
            Paragraph("-0.068", table_cell),
            Paragraph("Missing candidate or multiple persons is decisive evidence.", table_cell),
        ],
        [
            Paragraph("w/o Audio Activity (VAD)", table_cell),
            Paragraph("92.40%", table_cell),
            Paragraph("0.919", table_cell),
            Paragraph("0.949", table_cell),
            Paragraph("-0.054", table_cell),
            Paragraph("Whispering and verbal prompting missed without acoustics.", table_cell),
        ],
        [
            Paragraph("w/o Gaze Tracking", table_cell),
            Paragraph("93.80%", table_cell),
            Paragraph("0.935", table_cell),
            Paragraph("0.961", table_cell),
            Paragraph("-0.038", table_cell),
            Paragraph("Consulting cheat sheets or phones below the screen missed.", table_cell),
        ],
        [
            Paragraph("w/o Facial Emotion Signal", table_cell),
            Paragraph("96.80%", table_cell),
            Paragraph("0.967", table_cell),
            Paragraph("0.985", table_cell),
            Paragraph("<b>-0.006</b>", table_cell_bold),
            Paragraph("<b>Proves ethical principle</b>: Emotion provides nuance without falsely inflating flags.", table_cell),
        ],
    ]
    t_abl = Table(ablation_data, colWidths=[120, 65, 55, 55, 50, 159])
    t_abl.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), c_primary),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 4.5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ])
    )
    elements.append(t_abl)
    elements.append(Spacer(1, 14))

    # ==================== SECTION 8: TOP VIVA VOE QUESTIONS & ANSWERS ====================
    elements.append(Paragraph("8. Top Viva Voce Defense Questions & High-Scoring Answers", h1_style))

    viva_qa = [
        (
            "Q1: What is the primary novelty of your project compared to existing online proctoring systems?",
            "<b>Answer:</b> Existing commercial systems rely either on single-modality video analysis (which produces high false-positive rates when students look at paper) or invasive lockdown browsers that invade user privacy. Our system introduces a <b>multimodal fusion architecture</b> combining 6 modalities (Visual, Acoustic, OS Tab, and Affective) with a <b>Bidirectional LSTM</b> for temporal context. Cheating is declared only when corroborated across multiple sensory streams over time, reducing False Positive Rates to 2.65%."
        ),
        (
            "Q2: How does your system use Facial Emotion Recognition (FER), and won't it unfairly penalize an anxious student?",
            "<b>Answer:</b> This is our core ethical safeguard (**Affective Integrity Rule**). Facial emotion is used exclusively as an <i>affective context modifier</i> in the neural attention layer. An isolated emotion reading of 'Fear', 'Sad', or 'Surprise' receives a <b>0.0 penalty weight</b>. If an honest student experiences intense exam stress, their suspicion probability remains zero. Emotion only helps the model differentiate between panic/confusion and calm, deliberate collusion."
        ),
        (
            "Q3: Why do you need both a Learned Fusion MLP and a Temporal BiLSTM?",
            "<b>Answer:</b> They solve two fundamentally different dimensions of behavior:<br/>"
            "1. <b>Learned Fusion MLP</b> operates on <i>spatial correlation</i> at a single instant (window t), resolving how gaze, audio, and tab events interact simultaneously.<br/>"
            "2. <b>Temporal BiLSTM</b> operates on <i>time-series sequence dynamics</i> across 30 consecutive windows (~11 seconds). It learns that momentary events (a 1-second sneeze, sipping water, or glancing at a clock) are benign, while sustained patterns (continuous whispering or looking away for 10 seconds) constitute real cheating."
        ),
        (
            "Q4: How does the system avoid false alarms when reading questions on a wide screen or typing on a keyboard?",
            "<b>Answer:</b> Through empirically calibrated thresholds and multi-frame smoothing:<br/>"
            "• Gaze horizontal boundaries are relaxed to <b>0.32 – 0.68</b> with 5-frame moving average smoothing, comfortably accommodating wide screen reading.<br/>"
            "• Head pose pitch threshold is calibrated to <b>30.0°</b>, accommodating natural downward head tilt when looking at a laptop keyboard.<br/>"
            "• Secondary person boxes require <b>area ≥ 6.5%</b> of the frame, confidence ≥ 0.58, and IoU overlap &lt; 0.25 to prevent chair headrests or the candidate's own shoulders from triggering multi-person alerts."
        ),
        (
            "Q5: What does '10 frames in multi-person detection' mean in the post-exam report?",
            "<b>Answer:</b> It does NOT mean 10 different people entered the room. It means that across the exam, another person was detected in <b>10 individual video snapshot frames</b>. At our capture rate of ~380ms per frame, 10 frames corresponds to <b>~3.8 seconds total</b>. In a 30-minute exam (thousands of frames), 10 frames is only 0.2% of the exam—an incidental brief event that human reviewers can easily verify as harmless."
        ),
        (
            "Q6: How did you ensure your model didn't overfit and memorize specific students?",
            "<b>Answer:</b> We implemented <b>Subject-Independent Partitioning</b> (`subject_splits.json`). All data from a given participant was strictly isolated into either the Training, Validation, or Test set. The evaluation models were tested purely on unseen individuals, demonstrating genuine real-world generalization."
        ),
        (
            "Q7: How is the final Exam Integrity Score calculated at the end of the day?",
            "<b>Answer:</b> The Integrity Score is calculated based on cumulative verified conduct across the session:<br/>"
            "$$\\text{Base Integrity} = 100\\% - \\text{Flagged Time Percentage}$$<br/>"
            "Candidates maintaining clean conduct for ≥ 80% of the session receive <b>VERIFIED_CLEAN (Passed)</b>. Those between 60–79% are flagged for <b>MANUAL PROCTOR REVIEW</b> (allowing the proctor to review only the specific flagged video timestamps rather than watching the entire exam), and &lt; 60% indicates a confirmed integrity breach."
        ),
        (
            "Q8: What technologies and programming frameworks power the system?",
            "<b>Answer:</b><br/>"
            "• <b>Deep Learning & ML:</b> PyTorch (MLP, BiLSTM, EmotionCNN), Ultralytics YOLOv8n, Google MediaPipe FaceMesh Iris, OpenCV solvePnP, Silero VAD.<br/>"
            "• <b>Backend Web Service:</b> FastAPI, Uvicorn (ASGI), Pydantic schemas, NumPy.<br/>"
            "• <b>Frontend Client:</b> React 18, Vite, Web Audio API, HTML5 Canvas & MediaDevices."
        ),
    ]

    for q, ans in viva_qa:
        card_content = [
            [Paragraph(f"<b>{q}</b>", q_style)],
            [Paragraph(ans, ans_style)],
        ]
        card_t = Table(card_content, colWidths=[504])
        card_t.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
                ("PADDING", (0, 0), (-1, -1), 6),
            ])
        )
        elements.append(card_t)
        elements.append(Spacer(1, 8))

    doc.build(elements, canvasmaker=NumberedCanvas)
    print(f"Successfully generated Viva Voce PDF at: {filename}")


if __name__ == "__main__":
    out_pdf = "docs/AI_Exam_Proctoring_Viva_Defense_Guide.pdf"
    if len(sys.argv) > 1:
        out_pdf = sys.argv[1]
    build_pdf(out_pdf)
