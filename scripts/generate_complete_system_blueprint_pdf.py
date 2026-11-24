"""
Generates the Ultimate Master Architecture, Implementation & Reproduction Blueprint PDF
for the AI-Based Exam Proctoring, Emotion Detection, and Student-Teacher Exam Platform.

Designed so that any engineer or LLM can reconstruct the complete system from scratch.
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
            self.drawString(54, 750, "SentinelProctor AI — Master System Architecture & Implementation Blueprint")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)

        # Footer (All pages)
        self.setFont("Helvetica", 8)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 45, 558, 45)

        self.drawString(54, 32, "Confidential System Architecture & Complete LLM Reproduction Blueprint")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 32, page_str)
        self.restoreState()


def build_blueprint_pdf(filename="docs/AI_Exam_Proctoring_System_Master_Blueprint.pdf"):
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

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        fontName="Helvetica",
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#475569"),
        spaceAfter=15,
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=colors.HexColor("#0284c7"),
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "Heading2_Custom",
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True,
    )

    h3_style = ParagraphStyle(
        "Heading3_Custom",
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        fontName="Helvetica",
        fontSize=9,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6,
    )

    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        fontName="Helvetica",
        fontSize=9,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
        leftIndent=15,
        spaceAfter=3,
    )

    code_style = ParagraphStyle(
        "Code_Custom",
        fontName="Courier",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=4,
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1e293b"),
    )

    callout_style = ParagraphStyle(
        "Callout",
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor("#0369a1"),
    )

    story = []

    # =========================================================================
    # TITLE & METADATA
    # =========================================================================
    story.append(Paragraph("SentinelProctor AI: Master System Architecture & Full Engineering Blueprint", title_style))
    story.append(Paragraph("<b>End-to-End LLM Reconstruction Manual</b>: Multimodal AI Proctoring, BiLSTM Fusion, Student Exam Portal, Teacher MCQ Creator & Cheating Forensics Dashboard", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#0284c7"), spaceAfter=14))

    # Meta Table
    meta_data = [
        [
            Paragraph("<b>Author / System:</b> SentinelProctor Engineering Team", table_cell_style),
            Paragraph("<b>Target Stack:</b> FastAPI + React/Vite + PyTorch + MediaPipe + YOLOv8", table_cell_style),
        ],
        [
            Paragraph("<b>Architecture:</b> Decoupled 3-Tier Layered", table_cell_style),
            Paragraph("<b>Deployment Scope:</b> Production-Ready Localhost / Distributed", table_cell_style),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[250, 254])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # =========================================================================
    # EXECUTIVE SUMMARY & SYSTEM OVERVIEW
    # =========================================================================
    story.append(Paragraph("1. Executive Summary & Core Engineering Philosophy", h1_style))
    story.append(Paragraph(
        "SentinelProctor AI is a state-of-the-art multimodal automated examination proctoring and integrity assessment platform. "
        "Unlike legacy proctoring tools that rely on naive threshold rules or intrusive screen-recording software, this system merges "
        "computer vision (YOLOv8, MediaPipe Iris Mesh, solvePnP 3D Head Pose), acoustic signal processing (True RMS AudioContext / Silero VAD), "
        "affective context (7-Class Facial Emotion Recognition CNN), and temporal sequence fusion (Bidirectional LSTM). "
        "Furthermore, the platform integrates a complete <b>Student Examination Interface</b> and a <b>Teacher Management & Analytics Portal</b>, "
        "pairing real-time student MCQ submissions directly with forensic integrity scores, flagged percentages, and time-correlated violation breakdowns.",
        body_style
    ))
    story.append(Spacer(1, 6))

    # Callout Box
    callout_data = [[
        Paragraph(
            "<b>Engineering Rule of Clean Decoupling:</b><br/>"
            "1. <b>Backend API routes never load ML models directly:</b> All ML models are orchestrated via unified service boundaries (<code>proctoring_service.py</code> and <code>exam_service.py</code>).<br/>"
            "2. <b>Security-by-Design:</b> The Student API (<code>GET /exams/{id}</code>) completely strips answer keys to prevent browser DevTools inspection.<br/>"
            "3. <b>Zero Vendor Lock-in:</b> Runs natively on standard CPUs without GPU requirements using PyTorch TFLite / ONNX delegates and pure React frontend.",
            callout_style
        )
    ]]
    callout_table = Table(callout_data, colWidths=[504])
    callout_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0f9ff")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#0284c7")),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(callout_table)
    story.append(Spacer(1, 14))

    # =========================================================================
    # COMPLETE FILE TREE & MODULE MAP
    # =========================================================================
    story.append(Paragraph("2. Complete Repository Architecture & Directory Tree", h1_style))
    story.append(Paragraph(
        "Any LLM or developer reconstructing this project should create the exact directory structure below. "
        "Notice the clean separation between Backend Services, Machine Learning Pipelines, and the React Frontend:",
        body_style
    ))

    tree_text = (
        "ai-based-exam-proctoring-and-emotion-detection-system/<br/>"
        "├── backend/<br/>"
        "│   ├── app/<br/>"
        "│   │   ├── api/routes/<br/>"
        "│   │   │   ├── exam.py              # [NEW] MCQ creation, student view, submit & dashboard<br/>"
        "│   │   │   ├── proctoring.py        # Frame inference & window analysis routes<br/>"
        "│   │   │   ├── results.py           # Historical session summary retrieval<br/>"
        "│   │   │   └── session.py           # Session management & active tokens<br/>"
        "│   │   ├── core/<br/>"
        "│   │   │   ├── config.py            # App settings (Pydantic Settings)<br/>"
        "│   │   │   └── logging.py           # Structured logger configuration<br/>"
        "│   │   ├── schemas/<br/>"
        "│   │   │   ├── events.py            # BrowserEvent schemas (tab_hidden, window_blur)<br/>"
        "│   │   │   ├── exam.py              # [NEW] Exam, Question, Submission & Dashboard Pydantic models<br/>"
        "│   │   │   └── results.py           # ModalitySignals, SuspicionResult, ExamSummary schemas<br/>"
        "│   │   ├── services/<br/>"
        "│   │   │   ├── exam_service.py      # [NEW] In-memory exam store, grading & proctoring pairing<br/>"
        "│   │   │   └── proctoring_service.py# Seam connecting API layer to ML pipelines<br/>"
        "│   │   └── main.py                  # FastAPI application entrypoint with CORS<br/>"
        "│   └── requirements.txt             # Python dependencies (FastAPI, PyTorch, MediaPipe, OpenCV)<br/>"
        "├── ml/<br/>"
        "│   ├── fusion/<br/>"
        "│   │   ├── baseline_fusion.py       # Rule-based linear weighted combination<br/>"
        "│   │   ├── learned_fusion.py        # PyTorch MLP / Logistic learned classifier<br/>"
        "│   │   └── modality_attention.py    # Modality importance & explainability weighting<br/>"
        "│   ├── models/<br/>"
        "│   │   ├── emotion/                 # FER-2013 7-Class Emotion CNN<br/>"
        "│   │   ├── face/                    # YOLOv8 PersonDetector & MediaPipe FaceLandmarker<br/>"
        "│   │   ├── gaze/                    # Iris vector projection GazeEstimator<br/>"
        "│   │   └── head_pose/               # Perspective-n-Point (solvePnP) HeadPoseEstimator<br/>"
        "│   ├── pipelines/<br/>"
        "│   │   ├── feature_pipeline.py      # Combines visual, audio, browser signals into common window<br/>"
        "│   │   ├── inference_pipeline.py    # Dual-branch orchestrator (Rule + MLP + BiLSTM)<br/>"
        "│   │   └── visual_pipeline.py       # Decodes image frames, coordinates YOLO, Mesh, solvePnP, FER<br/>"
        "│   ├── temporal/<br/>"
        "│   │   ├── bilstm.py                # Bidirectional LSTM temporal model<br/>"
        "│   │   └── sequence_builder.py      # Sliding window temporal buffer (30 steps)<br/>"
        "│   └── utils/                       # FeatureStandardizer, TabTracker, audio utilities<br/>"
        "├── frontend/<br/>"
        "│   ├── src/<br/>"
        "│   │   ├── components/<br/>"
        "│   │   │   ├── DiagnosticLab.jsx    # [EXTRACTED] Telemetry & multi-scenario simulation lab<br/>"
        "│   │   │   ├── ProctoringReportModal.jsx # [NEW] Standalone audit report modal with PDF printing<br/>"
        "│   │   │   ├── StudentExamPortal.jsx# [NEW] Full student lobby, live exam with HUD, submission<br/>"
        "│   │   │   └── TeacherPortal.jsx    # [NEW] Exam builder & cheating analytics dashboard<br/>"
        "│   │   ├── App.jsx                  # Master app with top role-switching navigation bar<br/>"
        "│   │   └── main.jsx                 # React root mount<br/>"
        "│   └── package.json                 # React 18, Vite 5 frontend dependencies<br/>"
        "└── tests/<br/>"
        "    └── unit/<br/>"
        "        ├── test_exam_api.py         # [NEW] Unit tests for exam creation, grading & dashboard<br/>"
        "        └── test_proctoring_api.py   # Unit tests for multimodal proctoring pipelines"
    )

    tree_table = Table([[Paragraph(tree_text, code_style)]], colWidths=[504])
    tree_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#38bdf8")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#334155")),
        ("PADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(tree_table)
    story.append(Spacer(1, 14))

    # =========================================================================
    # MULTIMODAL AI PROCTORING PIPELINE (PHASES 1 TO 3)
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("3. Multimodal Machine Learning & Sensory Pipelines", h1_style))
    story.append(Paragraph(
        "The system processes multiple sensory channels asynchronously and synchronously. "
        "Here is the exact mathematical specification of every sensory detector in the platform:",
        body_style
    ))

    ml_table_data = [
        [
            Paragraph("<b>Modality / Engine</b>", table_header_style),
            Paragraph("<b>Underlying Algorithm & Model</b>", table_header_style),
            Paragraph("<b>Extracted Signals & Mathematical Basis</b>", table_header_style),
            Paragraph("<b>Violation Thresholds</b>", table_header_style),
        ],
        [
            Paragraph("<b>Person Detection & Tracking</b>", table_cell_style),
            Paragraph("YOLOv8 Nano (<code>yolov8n.pt</code>) + Temporal Debounce Filter", table_cell_style),
            Paragraph("Detects bounding boxes around humans. <code>MultiPersonTracker</code> uses a 15-frame deque history to prevent false single-frame glitches.", table_cell_style),
            Paragraph("<code>person_count == 0</code> (Absence)<br/><code>person_count > 1</code> (Multi-person, >50% buffer ratio)", table_cell_style),
        ],
        [
            Paragraph("<b>3D Head Pose Orientation</b>", table_cell_style),
            Paragraph("Perspective-n-Point (OpenCV <code>solvePnP</code>) + MediaPipe 478 Mesh", table_cell_style),
            Paragraph("Maps 6 canonical 3D facial points (Nose tip 1, Chin 199, Eye corners 33/263, Mouth corners 61/291) to 2D image coordinates. Computes rotation matrix & Euler angles.", table_cell_style),
            Paragraph("<b>Yaw</b>: |yaw| &gt; 38.0°<br/><b>Pitch</b>: pitch &gt; 30.0° or pitch &lt; -25.0°<br/><b>Roll</b>: |roll| &gt; 35.0°", table_cell_style),
        ],
        [
            Paragraph("<b>Iris Gaze Estimation</b>", table_cell_style),
            Paragraph("MediaPipe Iris Landmarks (468, 473) + Eyelid Corners (33, 133, 263, 362)", table_cell_style),
            Paragraph("Calculates normalized vector projection of iris centers along eye corner vectors (screen-left 0.0 to screen-right 1.0). Fuses with MediaPipe 52 facial blendshapes.", table_cell_style),
            Paragraph("<b>Horizontal</b>: ratio &lt; 0.36 (Left) or ratio &gt; 0.64 (Right)<br/><b>Vertical</b>: ratio &lt; 0.33 (Up) or ratio &gt; 0.67 (Down)", table_cell_style),
        ],
        [
            Paragraph("<b>Acoustic Voice VAD</b>", table_cell_style),
            Paragraph("Web Audio API True Float32 Time-Domain RMS + Silero VAD", table_cell_style),
            Paragraph("Computes root-mean-square over PCM sample buffer <code>[-1.0, 1.0]</code>. Tracks consecutive speech streak frames across 380ms capture cycles.", table_cell_style),
            Paragraph("RMS &gt;= 0.034 (Speech streak &gt;= 2 frames) or RMS &gt;= 0.052 (Loud utterance). Ambient typing &lt; 0.025 ignored.", table_cell_style),
        ],
        [
            Paragraph("<b>Browser Focus Security</b>", table_cell_style),
            Paragraph("HTML5 Page Visibility API + Window Blur Listener", table_cell_style),
            Paragraph("Monitors <code>document.hidden</code> and <code>window.onblur</code>. Increments tab switch counters and posts time-stamped audit events to backend.", table_cell_style),
            Paragraph("Any visibility change or loss of focus immediately flags suspicion score.", table_cell_style),
        ],
        [
            Paragraph("<b>Affective Context (FER)</b>", table_cell_style),
            Paragraph("7-Class Convolutional Neural Network (PyTorch)", table_cell_style),
            Paragraph("Input: 48x48 grayscale face crop. Classes: Anger, Disgust, Fear, Happiness, Sadness, Surprise, Neutral. <b>RULE 8:</b> Affective context only; non-punitive.", table_cell_style),
            Paragraph("Informs teacher of anxiety or stress, but does NOT penalize student marks.", table_cell_style),
        ],
        [
            Paragraph("<b>Temporal Fusion (BiLSTM)</b>", table_cell_style),
            Paragraph("Bidirectional LSTM (2-Layer, 64 Hidden Units, Dropout 0.3)", table_cell_style),
            Paragraph("Maintains a 30-step sliding sequence buffer. Processes forward and backward temporal patterns to distinguish brief accidental glances from sustained cheating.", table_cell_style),
            Paragraph("Dual-branch instant onset (threshold 0.35) combined with rapid clean conduct decay.", table_cell_style),
        ],
    ]

    ml_table = Table(ml_table_data, colWidths=[100, 120, 184, 100])
    ml_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(ml_table)
    story.append(Spacer(1, 14))

    # =========================================================================
    # THE COMPLETE STUDENT & TEACHER EXAM PLATFORM (THE BEST WAY)
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("4. The Complete Student & Teacher Examination Platform", h1_style))
    story.append(Paragraph(
        "To transform the raw AI proctoring laboratory into an end-to-end commercial-grade testing suite, "
        "we implemented a comprehensive examination architecture comprising secure schemas, exam services, "
        "student-teacher routes, interactive UI components, and real-time forensic linkage.",
        body_style
    ))

    story.append(Paragraph("4.1 Architecture & Data Flow Diagram", h2_style))

    flow_data = [
        [
            Paragraph(
                "<b>1. TEACHER PORTAL (TeacherPortal.jsx)</b><br/>"
                "• Teacher builds MCQ exam (Title, Duration, Questions, Options A–D, Points, Answer Key).<br/>"
                "• Sends <code>POST /exams/</code> to Backend Exam Service.<br/>"
                "• Exam is saved with full questions and answer keys.",
                table_cell_style
            ),
            Paragraph("➡️ <b>EXAM SERVICE</b><br/>Stores exam in memory repository (<code>_EXAMS</code>).", table_cell_style)
        ],
        [
            Paragraph(
                "<b>2. SECURE STUDENT VIEW (GET /exams/{id})</b><br/>"
                "• Student selects exam from Lobby.<br/>"
                "• Backend strips <code>correct_option_index</code> into <code>QuestionStudentView</code>.<br/>"
                "• Tech-savvy students inspecting Network tab cannot see answer keys.",
                table_cell_style
            ),
            Paragraph("➡️ <b>STUDENT PORTAL</b><br/>Renders interactive question cards with options A–D.", table_cell_style)
        ],
        [
            Paragraph(
                "<b>3. LIVE AI PROCTORING LOOP (StudentExamPortal.jsx)</b><br/>"
                "• Starts webcam and mic with auto-attaching video hook.<br/>"
                "• Generates unique session ID (e.g. <code>stu-alex-m4k9</code>).<br/>"
                "• Canvas captures 320x240 frame every 380ms $\\rightarrow$ <code>POST /proctoring/analyze-frame</code>.<br/>"
                "• AudioContext checks True RMS voice energy.<br/>"
                "• Page Visibility API checks tab switches and window blur.<br/>"
                "• Live HUD displays frame counter, gaze status, person count, and warning banners.",
                table_cell_style
            ),
            Paragraph("➡️ <b>PROCTORING SERVICE</b><br/>Maintains rolling inference history in <code>_SESSION_RESULTS[session_id]</code>.", table_cell_style)
        ],
        [
            Paragraph(
                "<b>4. EXAM SUBMISSION & FORENSIC BINDING (POST /exams/{id}/submit)</b><br/>"
                "• Student submits answers dictionary (<code>{q1: 1, q2: 0, ...}</code>).<br/>"
                "• Backend grades answers against answer keys $\\rightarrow$ calculates Test Marks & Percentage.<br/>"
                "• Calls <code>proctoring_service.get_session_summary(req.session_id)</code>.<br/>"
                "• Calculates Final Integrity Score %, Flagged Ratio, and Cheating Verdict.<br/>"
                "• Stores combined <code>SubmissionReport</code> in <code>_SUBMISSIONS[exam_id]</code>.",
                table_cell_style
            ),
            Paragraph("➡️ <b>DUAL REPORT</b><br/>Returns academic test grade + AI proctoring summary.", table_cell_style)
        ],
        [
            Paragraph(
                "<b>5. TEACHER CHEATING ANALYTICS DASHBOARD (TeacherPortal.jsx)</b><br/>"
                "• Teacher accesses <code>GET /exams/{id}/dashboard</code>.<br/>"
                "• Displays Summary Cards: Submissions, Class Avg Score, Flagged Cheaters Count, Integrity Avg.<br/>"
                "• Submissions Table lists candidate marks, AI Integrity %, and color-coded Verdict.<br/>"
                "• Teacher clicks <b>'🔍 Inspect Violations'</b> to open <code>ProctoringReportModal.jsx</code>.<br/>"
                "• Inspects multi-person frames, looking away duration, speech time, tab switches, and prints PDF.",
                table_cell_style
            ),
            Paragraph("➡️ <b>FORENSIC AUDIT</b><br/>Complete institutional defense evidence.", table_cell_style)
        ],
    ]

    flow_table = Table(flow_data, colWidths=[380, 124])
    flow_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#0284c7")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(flow_table)
    story.append(Spacer(1, 14))

    # =========================================================================
    # BACKEND DATA MODELS & SCHEMAS
    # =========================================================================
    story.append(Paragraph("4.2 Backend Data Models & Security Schemas (backend/app/schemas/exam.py)", h2_style))
    story.append(Paragraph(
        "Here are the exact Pydantic models powering the examination engine:",
        body_style
    ))

    schema_code = (
        "class Question(BaseModel):<br/>"
        "    id: str<br/>"
        "    question_text: str<br/>"
        "    options: List[str]<br/>"
        "    correct_option_index: int  # 0-indexed; only visible to teacher<br/>"
        "    points: int = 2<br/><br/>"
        "class QuestionStudentView(BaseModel):<br/>"
        "    id: str<br/>"
        "    question_text: str<br/>"
        "    options: List[str]<br/>"
        "    points: int = 2<br/>"
        "    # correct_option_index is intentionally excluded for security<br/><br/>"
        "class ExamCreateRequest(BaseModel):<br/>"
        "    title: str<br/>"
        "    description: Optional[str] = ''<br/>"
        "    duration_minutes: int = 15<br/>"
        "    questions: List[Question]<br/><br/>"
        "class ExamSubmitRequest(BaseModel):<br/>"
        "    student_name: str<br/>"
        "    student_id: Optional[str] = 'STU-001'<br/>"
        "    session_id: str<br/>"
        "    answers: Dict[str, int]  # question_id -> selected_option_index<br/><br/>"
        "class SubmissionReport(BaseModel):<br/>"
        "    submission_id: str<br/>"
        "    exam_id: str<br/>"
        "    student_name: str<br/>"
        "    student_id: str<br/>"
        "    session_id: str<br/>"
        "    score: int<br/>"
        "    total_points: int<br/>"
        "    percentage: float<br/>"
        "    submitted_at: str<br/>"
        "    integrity_score: float<br/>"
        "    verdict: str<br/>"
        "    verdict_label: str<br/>"
        "    verdict_color: str<br/>"
        "    proctoring_summary: Optional[ExamSummary] = None<br/>"
        "    question_results: Optional[List[Dict[str, Any]]] = None"
    )

    schema_box = Table([[Paragraph(schema_code, code_style)]], colWidths=[504])
    schema_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#38bdf8")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#334155")),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(schema_box)
    story.append(Spacer(1, 14))

    # =========================================================================
    # BACKEND EXAM SERVICE & GRADING LOGIC
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("4.3 Backend Exam Service & Automated Grading (backend/app/services/exam_service.py)", h2_style))
    story.append(Paragraph(
        "The service layer orchestrates exam storage, automated grading, and the critical binding to the live proctoring session summary:",
        body_style
    ))

    service_code = (
        "def submit_exam(exam_id: str, request: ExamSubmitRequest) -> Optional[SubmissionReport]:<br/>"
        "    exam = _EXAMS.get(exam_id)<br/>"
        "    if not exam: return None<br/><br/>"
        "    # 1. Automated Academic Grading<br/>"
        "    earned_score = 0<br/>"
        "    question_results = []<br/>"
        "    for q in exam.questions:<br/>"
        "        selected_idx = request.answers.get(q.id)<br/>"
        "        is_correct = (selected_idx == q.correct_option_index)<br/>"
        "        if is_correct: earned_score += q.points<br/>"
        "        question_results.append({<br/>"
        "            'question_id': q.id, 'question_text': q.question_text,<br/>"
        "            'selected_option_index': selected_idx, 'correct_option_index': q.correct_option_index,<br/>"
        "            'is_correct': is_correct, 'points_earned': q.points if is_correct else 0,<br/>"
        "            'max_points': q.points<br/>"
        "        })<br/>"
        "    percentage = round((earned_score / max(1, exam.total_points)) * 100, 1)<br/><br/>"
        "    # 2. Retrieve AI Proctoring Audit Summary for this session<br/>"
        "    proctor_summary = proctoring_service.get_session_summary(request.session_id)<br/><br/>"
        "    # 3. Assemble and persist final Submission Report<br/>"
        "    report = SubmissionReport(<br/>"
        "        submission_id=f'sub-{uuid.uuid4().hex[:8]}',<br/>"
        "        exam_id=exam_id, student_name=request.student_name, student_id=request.student_id,<br/>"
        "        session_id=request.session_id, score=earned_score, total_points=exam.total_points,<br/>"
        "        percentage=percentage, submitted_at=datetime.now(timezone.utc).isoformat(),<br/>"
        "        integrity_score=proctor_summary.integrity_score,<br/>"
        "        verdict=proctor_summary.verdict, verdict_label=proctor_summary.verdict_label,<br/>"
        "        verdict_color=proctor_summary.verdict_color,<br/>"
        "        proctoring_summary=proctor_summary, question_results=question_results<br/>"
        "    )<br/>"
        "    _SUBMISSIONS[exam_id].append(report)<br/>"
        "    return report"
    )

    service_box = Table([[Paragraph(service_code, code_style)]], colWidths=[504])
    service_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#38bdf8")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#334155")),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(service_box)
    story.append(Spacer(1, 14))

    # =========================================================================
    # FASTAPI ROUTE DEFINITIONS
    # =========================================================================
    story.append(Paragraph("4.4 Complete API Endpoint Specifications (backend/app/api/routes/exam.py)", h2_style))

    api_specs = [
        [
            Paragraph("<b>Endpoint Route & Method</b>", table_header_style),
            Paragraph("<b>Purpose & Security Scope</b>", table_header_style),
            Paragraph("<b>Request Payload</b>", table_header_style),
            Paragraph("<b>Response Payload</b>", table_header_style),
        ],
        [
            Paragraph("<code>POST /exams/</code>", table_cell_style),
            Paragraph("Teacher creates and publishes a new MCQ examination.", table_cell_style),
            Paragraph("<code>ExamCreateRequest</code> (title, duration, questions with answers)", table_cell_style),
            Paragraph("<code>ExamResponse</code> (complete exam with generated ID)", table_cell_style),
        ],
        [
            Paragraph("<code>GET /exams/</code>", table_cell_style),
            Paragraph("Lobby catalog of all available examinations.", table_cell_style),
            Paragraph("None (query params optional)", table_cell_style),
            Paragraph("<code>List[ExamResponse]</code> (catalog overview)", table_cell_style),
        ],
        [
            Paragraph("<code>GET /exams/{id}</code>", table_cell_style),
            Paragraph("<b>Student Secure Endpoint:</b> Returns questions with answer keys stripped.", table_cell_style),
            Paragraph("Path parameter: <code>exam_id</code>", table_cell_style),
            Paragraph("<code>ExamStudentView</code> (questions without <code>correct_option_index</code>)", table_cell_style),
        ],
        [
            Paragraph("<code>GET /exams/{id}/teacher</code>", table_cell_style),
            Paragraph("Teacher retrieval endpoint: Returns questions with answer keys.", table_cell_style),
            Paragraph("Path parameter: <code>exam_id</code>", table_cell_style),
            Paragraph("<code>ExamResponse</code> (includes full answer keys)", table_cell_style),
        ],
        [
            Paragraph("<code>POST /exams/{id}/submit</code>", table_cell_style),
            Paragraph("Student submission: Grades test and binds to live proctoring session.", table_cell_style),
            Paragraph("<code>ExamSubmitRequest</code> (student info, session ID, answers dict)", table_cell_style),
            Paragraph("<code>SubmissionReport</code> (marks + percentage + integrity score + summary)", table_cell_style),
        ],
        [
            Paragraph("<code>GET /exams/{id}/dashboard</code>", table_cell_style),
            Paragraph("Teacher Cheating Analytics: Aggregate class metrics and forensic table.", table_cell_style),
            Paragraph("Path parameter: <code>exam_id</code>", table_cell_style),
            Paragraph("<code>TeacherDashboardResponse</code> (class average, submissions list, flagged count)", table_cell_style),
        ],
    ]

    api_table = Table(api_specs, colWidths=[120, 130, 120, 134])
    api_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(api_table)
    story.append(Spacer(1, 14))

    # =========================================================================
    # FRONTEND COMPONENTS DEEP-DIVE
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("4.5 Frontend User Experience & UI Component Architecture", h2_style))
    story.append(Paragraph(
        "The React frontend was designed with seamless single-page application (SPA) role switching. "
        "Here are the core components and their specialized implementations:",
        body_style
    ))

    story.append(Paragraph("A. Master Application Switcher (frontend/src/App.jsx)", h3_style))
    story.append(Paragraph(
        "• Provides a persistent top navigation header with live API status check (<code>/health</code>).<br/>"
        "• Allows switching between three dedicated workspaces: <b>Student Exam Mode</b>, <b>Teacher & Analytics Portal</b>, and <b>Diagnostic AI Lab</b>.<br/>"
        "• Completely decouples the testing workflows from the diagnostic sensor testbed.",
        bullet_style
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("B. Student Exam Portal (frontend/src/components/StudentExamPortal.jsx)", h3_style))
    story.append(Paragraph(
        "• <b>Phase 1: Lobby</b> — Candidate enters Full Name and Student ID, selects an examination, reads the official proctoring protocols, and tests camera/mic readiness.<br/>"
        "• <b>Phase 2: Active Proctored Exam</b>:<br/>"
        "  - <i>Countdown Clock</i>: Live MM:SS timer; turns pulsing red when &lt; 3 minutes remain; automatically submits answers on timeout.<br/>"
        "  - <i>Question Palette</i>: Interactive badges (1 to N) indicating Answered (green) vs Unanswered (gray) questions.<br/>"
        "  - <i>Interactive MCQ Cards</i>: Cards A, B, C, D with clear selection and navigation.<br/>"
        "  - <i>Live AI Proctor HUD</i>: Picture-in-picture mirrored camera preview with real-time frame counter, gaze status, YOLO person count, and acoustic speech energy meter.<br/>"
        "  - <i>Auto-Attaching Stream Hook</i>: Automatically mounts media streams to the video player as soon as the active exam DOM is rendered.<br/>"
        "  - <i>Continuous Frame Inference</i>: Canvas captures 320x240 JPEG every 380ms and sends to <code>/proctoring/analyze-frame</code>.<br/>"
        "  - <i>Top Floating Warning Toast</i>: Alerts student immediately if they look away, speak, turn their head, or switch tabs.<br/>"
        "• <b>Phase 3: Results & Review</b>:<br/>"
        "  - Shows Academic Score (e.g. 8/10), Percentage (80.0%), Pass/Fail status.<br/>"
        "  - Displays AI Integrity Score (e.g. 91.5%) and Cheating Verdict Badge.<br/>"
        "  - Question-by-question review showing the candidate's chosen option and the correct answer.<br/>"
        "  - 'Inspect Full Proctoring Audit Report' button opening the forensic modal.",
        bullet_style
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("C. Teacher Portal & Cheating Analytics (frontend/src/components/TeacherPortal.jsx)", h3_style))
    story.append(Paragraph(
        "• <b>Sub-Tab 1: Create MCQ Exam</b>:<br/>"
        "  - Intuitive form for exam title, description, duration in minutes, and question builder.<br/>"
        "  - Options A, B, C, D with radio button answer key selector and custom point weights.<br/>"
        "  - 'Load Sample Questions' one-click helper to populate pre-tested computer vision & AI questions.<br/>"
        "  - 'Publish Exam' button sending <code>POST /exams/</code>.<br/>"
        "• <b>Sub-Tab 2: Submissions & Cheating Analytics Dashboard</b>:<br/>"
        "  - Summary Cards: Total Submissions, Class Average Score, Flagged Cheaters Count, Exam Integrity Average.<br/>"
        "  - Submissions Table: Candidate Name, ID, Submission Timestamp, Test Marks, AI Integrity %, and Cheating Verdict.<br/>"
        "  - 'Inspect Violations' button opening the comprehensive forensic modal for any student.",
        bullet_style
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("D. Standalone Proctoring Report Modal (frontend/src/components/ProctoringReportModal.jsx)", h3_style))
    story.append(Paragraph(
        "• Reusable forensic modal displaying Final Calculated Integrity Score %, Flagged Ratio, and Exam Duration.<br/>"
        "• Modality Violation Breakdown Cards: Multi-person events, looking away frames, head turned frames, speech frames, tab switches, and candidate absence.<br/>"
        "• Displays Dominant FER Emotion and Top Contributing Violations.<br/>"
        "• Built-in <b>'🖨 Print / Save Report'</b> button triggering browser print-to-PDF formatting for institutional archival.",
        bullet_style
    ))
    story.append(Spacer(1, 14))

    # =========================================================================
    # FORENSIC SCORING & CHEATING VERDICT FORMULA
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("5. AI Integrity Scoring & Cheating Verdict Mathematical Formulation", h1_style))
    story.append(Paragraph(
        "The post-exam audit calculation in <code>proctoring_service.get_session_summary()</code> adheres to a strictly "
        "weighted mathematical formula that rewards continuous compliant conduct and penalizes verified infractions proportionally:",
        body_style
    ))

    formula_text = (
        "<b>1. Flagged Ratio:</b><br/>"
        "$$R_{flagged} = \\frac{N_{flagged}}{N_{total}}$$ (where $N_{total}$ is total frames analyzed during the exam session)<br/><br/>"
        "<b>2. Weighted Modality Infraction Penalty:</b><br/>"
        "$$P_{total} = (0.25 \\times F_{multi\\_person}) + (0.15 \\times F_{absence}) + (0.08 \\times F_{looking\\_away}) + (0.08 \\times F_{head\\_turned}) + (0.07 \\times F_{speech}) + (0.12 \\times F_{tab\\_away})$$<br/>"
        "$$P_{norm} = \\min\\left(100.0, \\; \\frac{P_{total}}{\\max(1, N_{total})} \\times 100.0\\right)$$<br/><br/>"
        "<b>3. Final Integrity Score:</b><br/>"
        "$$\\text{Integrity Score} = \\max\\left(0.0, \\; 100.0 - (0.50 \\times R_{flagged} \\times 100.0) - (0.50 \\times P_{norm})\\right)$$<br/><br/>"
        "<b>4. Institutional Verdict Classification:</b><br/>"
        "• <b>Integrity Score &gt;= 85.0%</b>: <code>VERIFIED_CLEAN</code> (Clean Conduct — Verified Honest) [Green #10b981]<br/>"
        "• <b>70.0% &lt;= Score &lt; 85.0%</b>: <code>LOW_SUSPICION</code> (Low Suspicion — Candidate mostly compliant) [Blue #38bdf8]<br/>"
        "• <b>50.0% &lt;= Score &lt; 70.0%</b>: <code>MODERATE_SUSPICION</code> (Moderate Suspicion — Review Recommended) [Amber #f59e0b]<br/>"
        "• <b>Score &lt; 50.0%</b>: <code>HIGH_SUSPICION</code> (High Cheating Probability — Integrity Breach Flagged) [Red #ef4444]"
    )

    formula_box = Table([[Paragraph(formula_text, body_style)]], colWidths=[504])
    formula_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#0284c7")),
        ("PADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(formula_box)
    story.append(Spacer(1, 14))

    # =========================================================================
    # COMPLETE STEP-BY-STEP REPRODUCTION & RUN GUIDE
    # =========================================================================
    story.append(Paragraph("6. Step-by-Step Reproduction & Execution Guide for Any LLM", h1_style))
    story.append(Paragraph(
        "To run or recreate this entire system from scratch in any clean environment, execute the following commands:",
        body_style
    ))

    run_guide = (
        "<b>Step 1: Clone Repository & Setup Python Environment</b><br/>"
        "<code>git clone &lt;repo_url&gt;</code><br/>"
        "<code>cd ai-based-exam-proctoring-and-emotion-detection-system</code><br/>"
        "<code>python -m venv venv</code><br/>"
        "<code>.\\venv\\Scripts\\activate  # On Windows</code><br/>"
        "<code>pip install -r backend/requirements.txt</code><br/><br/>"
        "<b>Step 2: Start Backend Server</b><br/>"
        "<code>python -m uvicorn backend.app.main:app --reload --port 8000</code><br/>"
        "<i>Backend will load YOLOv8, MediaPipe FaceLandmarker, and BiLSTM, running on http://127.0.0.1:8000. Interactive Swagger API docs are accessible at http://127.0.0.1:8000/docs.</i><br/><br/>"
        "<b>Step 3: Setup & Run React Frontend</b><br/>"
        "<code>cd frontend</code><br/>"
        "<code>npm install</code><br/>"
        "<code>npm run dev</code><br/>"
        "<i>Frontend runs on http://localhost:5173 with Vite hot module replacement.</i><br/><br/>"
        "<b>Step 4: Execute Automated Unit & Regression Tests</b><br/>"
        "<code>pytest tests/unit/test_exam_api.py -v</code><br/>"
        "<code>pytest tests/unit/test_proctoring_api.py -v</code>"
    )

    run_box = Table([[Paragraph(run_guide, body_style)]], colWidths=[504])
    run_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#10b981")),
        ("PADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(run_box)
    story.append(Spacer(1, 14))

    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated Master Blueprint PDF at: {filename}")


if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "docs/AI_Exam_Proctoring_System_Master_Blueprint.pdf"
    build_blueprint_pdf(out_file)
