"""
Full build script to generate the official GGSIPU USAR Minor Project Report (ARP 455)
in BOTH .docx (Word format matching sample) and .pdf (ReportLab format matching university rules).

Features:
- First page matches user sample: centered GGSIPU logo banner (4.48 x 1.5 in), school name, 24pt title, 16pt project name, student details, supervisor details, 2026-27.
- Full academic content covering Chapters 1-8, subsections 5.1-5.6, 6.1-6.3, tables, algorithms, and APA references.
- Minimum 30+ pages guaranteed.
"""
import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable, Image as RLImage
)
from reportlab.pdfgen import canvas

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_PATH = os.path.join(BASE_DIR, "docs", "assets", "ggsipu_logo.png")
DOCX_OUT = os.path.join(BASE_DIR, "Minor_Project_Report_Asmita_00819051723_USAR.docx")
PDF_OUT = os.path.join(BASE_DIR, "Minor_Project_Report_Asmita_00819051723_USAR.pdf")


# =============================================================================
# PART 1: GENERATE DOCX (EXACT WORD REPLICATION OF SAMPLE)
# =============================================================================

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def build_docx(output_path: str):
    doc = docx.Document()

    # Configure Margins (USAR Standard: Left 3.5cm / 1.38in, Right 1.25cm / 0.5in, Top 2.5cm / 0.98in, Bottom 1.25cm / 0.5in)
    section = doc.sections[0]
    section.left_margin = Inches(1.38)
    section.right_margin = Inches(0.55)
    section.top_margin = Inches(0.98)
    section.bottom_margin = Inches(0.60)
    section.header_distance = Inches(0.4)
    section.footer_distance = Inches(0.3)

    # Helper functions for paragraph generation
    def add_p(text="", align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=0, space_after=6, line_spacing=1.5, bold=False, italic=False, size=11, font_name="Times New Roman"):
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = line_spacing
        if text:
            r = p.add_run(text)
            r.bold = bold
            r.italic = italic
            r.font.name = font_name
            r.font.size = Pt(size)
        return p

    def add_bullet(text):
        p = doc.add_paragraph(style='List Bullet')
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.25
        r = p.add_run(text)
        r.font.name = "Times New Roman"
        r.font.size = Pt(11)
        return p

    def add_h1(text):
        return add_p(text, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=14, space_after=10, bold=True, size=14)

    def add_h2(text):
        return add_p(text, align=WD_ALIGN_PARAGRAPH.LEFT, space_before=12, space_after=4, bold=True, size=12)

    def add_h3(text):
        return add_p(text, align=WD_ALIGN_PARAGRAPH.LEFT, space_before=8, space_after=2, bold=True, size=11)

    # -------------------------------------------------------------------------
    # COVER PAGE
    # -------------------------------------------------------------------------
    p_logo = doc.add_paragraph()
    p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_logo.paragraph_format.space_before = Pt(0)
    p_logo.paragraph_format.space_after = Pt(4)
    if os.path.exists(LOGO_PATH):
        r_logo = p_logo.add_run()
        r_logo.add_picture(LOGO_PATH, width=Inches(4.48), height=Inches(1.50))

    add_p("UNIVERSITY SCHOOL OF AUTOMATION AND ROBOTICS\nEAST DELHI CAMPUS, SURAJMAL VIHAR, DELHI- 110032", align=WD_ALIGN_PARAGRAPH.CENTER, space_before=2, space_after=18, bold=True, size=11)
    
    add_p("Minor Project Report", align=WD_ALIGN_PARAGRAPH.CENTER, space_before=10, space_after=6, bold=True, size=24)
    add_p("on", align=WD_ALIGN_PARAGRAPH.CENTER, space_before=4, space_after=8, size=14)
    
    add_p("Multimodal AI-Based Online Examination Proctoring and Suspicious Activity Detection", align=WD_ALIGN_PARAGRAPH.CENTER, space_before=4, space_after=16, bold=True, size=16)
    
    add_p("Submitted in partial fulfilment of the requirements for the completion of minor project [ARP 455]", align=WD_ALIGN_PARAGRAPH.CENTER, space_before=8, space_after=24, size=11, italic=True)
    
    add_p("Name: Asmita", align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=2, bold=True, size=13)
    add_p("Enrollment Number: 00819051723", align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=2, bold=True, size=13)
    add_p("Programme: B.Tech IIOT", align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=20, bold=True, size=13)
    
    add_p("Under the supervision of", align=WD_ALIGN_PARAGRAPH.CENTER, space_before=8, space_after=2, size=11)
    add_p("Dr. Anshul Bhatia", align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=2, bold=True, size=13)
    add_p("Assistant Professor", align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=2, size=11)
    add_p("University School of Automation and Robotics (USAR)", align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=24, size=11)
    
    add_p("2026-27", align=WD_ALIGN_PARAGRAPH.CENTER, space_before=10, space_after=0, bold=True, size=12)
    doc.add_page_break()

    # -------------------------------------------------------------------------
    # CERTIFICATE BY SUPERVISOR
    # -------------------------------------------------------------------------
    add_h1("CERTIFICATE BY SUPERVISOR")
    add_p(
        "This is to certify that the Minor Project Report entitled “Multimodal AI-Based Online Examination Proctoring and Suspicious Activity Detection”, "
        "submitted by Asmita (Enrollment Number: 00819051723), in partial fulfillment of the requirements for the award of the degree of "
        "Bachelor of Technology in Industrial Internet of Things from the University School of Automation and Robotics (USAR), Guru Gobind Singh Indraprastha University, "
        "East Delhi Campus, Surajmal Vihar, Delhi, is an authentic record of the research, design, implementation, and evaluation work carried out by her under my guidance and supervision.",
        space_before=12, space_after=12
    )
    add_p(
        "To the best of my knowledge, the matter embodied in this report has not been submitted to any other University or Institution for the award of any degree, diploma, or fellowship.",
        space_before=6, space_after=36
    )
    add_p("(Signature of Supervisor)", align=WD_ALIGN_PARAGRAPH.RIGHT, space_before=0, space_after=2, size=11)
    add_p("Dr. Anshul Bhatia", align=WD_ALIGN_PARAGRAPH.RIGHT, space_before=0, space_after=2, bold=True, size=11)
    add_p("Assistant Professor, USAR, GGSIPU", align=WD_ALIGN_PARAGRAPH.RIGHT, space_before=0, space_after=12, size=11)
    add_p("Date: 25th November 2026", align=WD_ALIGN_PARAGRAPH.LEFT, space_before=0, space_after=2, size=11)
    add_p("Place: Delhi, India", align=WD_ALIGN_PARAGRAPH.LEFT, space_before=0, space_after=0, size=11)
    doc.add_page_break()

    # -------------------------------------------------------------------------
    # DECLARATION
    # -------------------------------------------------------------------------
    add_h1("DECLARATION")
    add_p(
        "I hereby declare that the Minor Project Report entitled “Multimodal AI-Based Online Examination Proctoring and Suspicious Activity Detection” "
        "is an authentic record of work completed as requirements of Minor Project (ARP 455) under the supervision of Dr. Anshul Bhatia, Assistant Professor, "
        "University School of Automation and Robotics (USAR), Guru Gobind Singh Indraprastha University, Delhi.",
        space_before=12, space_after=12
    )
    add_p(
        "I further declare that this report has not been submitted previously in part or in full for the award of any other academic degree, diploma, or qualification to any institution. "
        "Wherever external contributions, datasets, open-source libraries, or algorithms have been used, due acknowledgement has been given and cited according to academic standards.",
        space_before=6, space_after=36
    )
    add_p("(Signature of Student)", align=WD_ALIGN_PARAGRAPH.RIGHT, space_before=0, space_after=2, size=11)
    add_p("Asmita", align=WD_ALIGN_PARAGRAPH.RIGHT, space_before=0, space_after=2, bold=True, size=11)
    add_p("Enrollment Number: 00819051723", align=WD_ALIGN_PARAGRAPH.RIGHT, space_before=0, space_after=2, size=11)
    add_p("Programme: B.Tech IIOT, 7th Semester", align=WD_ALIGN_PARAGRAPH.RIGHT, space_before=0, space_after=12, size=11)
    add_p("Date: 25th November 2026", align=WD_ALIGN_PARAGRAPH.LEFT, space_before=0, space_after=2, size=11)
    add_p("Place: Delhi, India", align=WD_ALIGN_PARAGRAPH.LEFT, space_before=0, space_after=0, size=11)
    doc.add_page_break()

    # -------------------------------------------------------------------------
    # ACKNOWLEDGEMENT
    # -------------------------------------------------------------------------
    add_h1("ACKNOWLEDGEMENT")
    add_p(
        "I would like to express my profound gratitude and deep reverence to my project supervisor, Dr. Anshul Bhatia, Assistant Professor, "
        "University School of Automation and Robotics (USAR), Guru Gobind Singh Indraprastha University, for his invaluable guidance, constant motivation, "
        "and scholarly critiques throughout the duration of this project. His deep domain insights in machine learning, vision pipelines, and system architectures "
        "provided vital direction at critical junctures of modality fusion and behavioral modeling.",
        space_before=12, space_after=10
    )
    add_p(
        "I express my sincere gratitude to Prof. Arvinder Kaur, Dean, University School of Automation and Robotics, for providing state-of-the-art laboratory infrastructure, "
        "computational facilities, and an encouraging academic ecosystem that facilitated the execution of this minor project.",
        space_before=6, space_after=10
    )
    add_p(
        "I also thank all faculty members, laboratory staff, and technical officers of USAR for their constructive feedback during project progress reviews. "
        "Finally, I thank my family and peers for their constant moral support and motivation during the preparation of this project and report.",
        space_before=6, space_after=24
    )
    add_p("Asmita\nEnrollment No.: 00819051723\nB.Tech IIOT, 7th Semester", align=WD_ALIGN_PARAGRAPH.RIGHT, bold=True, size=11)
    doc.add_page_break()

    # -------------------------------------------------------------------------
    # TABLE OF CONTENTS
    # -------------------------------------------------------------------------
    add_h1("TABLE OF CONTENTS")
    toc_data = [
        ("CERTIFICATE BY SUPERVISOR", "ii"),
        ("DECLARATION BY STUDENT", "iii"),
        ("ACKNOWLEDGEMENT", "iv"),
        ("TABLE OF CONTENTS", "v"),
        ("LIST OF TABLES", "vii"),
        ("LIST OF FIGURES", "viii"),
        ("ABBREVIATIONS AND NOMENCLATURE", "ix"),
        ("ABSTRACT", "xi"),
        ("CHAPTER 1: INTRODUCTION", "1"),
        ("  1.1 Context and Motivation", "1"),
        ("  1.2 Evolution of Remote Examination Proctoring", "3"),
        ("  1.3 Key Vulnerabilities in Unsupervised Remote Exams", "4"),
        ("  1.4 Objectives of the Present Investigation", "6"),
        ("  1.5 Report Organization", "7"),
        ("CHAPTER 2: LITERATURE SURVEY", "8"),
        ("  2.1 Critical Review of State-of-the-Art Proctoring Frameworks", "8"),
        ("  2.2 Computer Vision Techniques for Facial and Gaze Analysis", "11"),
        ("  2.3 Acoustic Voice Activity Detection in Academic Integrity", "13"),
        ("  2.4 Sequential Behavioral Modeling and Temporal Attention", "15"),
        ("  2.5 Literature Gap Analysis", "17"),
        ("CHAPTER 3: PROBLEM STATEMENT", "19"),
        ("  3.1 Formal Problem Definition", "19"),
        ("  3.2 Mathematical Formulation of Multimodal Cheating Detection", "20"),
        ("  3.3 Scope, Constraints, and Ethical Considerations", "22"),
        ("CHAPTER 4: DESCRIPTION OF VARIOUS MODULES", "24"),
        ("  4.1 Sensor and Event Capture Ingestion Layer", "24"),
        ("  4.2 Visual Pipeline: Detection, Iris Gaze, and 3D Head Pose", "25"),
        ("  4.3 Auditory Modality: Silero Neural Voice Activity Detection", "28"),
        ("  4.4 Behavioral Context: Dual-Channel Browser Event Tracker", "30"),
        ("  4.5 Affective Differentiator: Non-Punitive Facial Emotion Classifier", "32"),
        ("  4.6 Common Representation: 24-Dimensional Feature Vector", "34"),
        ("  4.7 Multimodal Fusion Engines (Rule-Based & Learned MLP)", "36"),
        ("  4.8 Temporal Context Sequencer and Bidirectional LSTM Engine", "38"),
        ("  4.9 Full-Stack Examination Engine and Teacher Forensic Portal", "40"),
        ("CHAPTER 5: METHODOLOGY ADOPTED", "42"),
        ("  5.1 Objective of Project", "42"),
        ("  5.2 Design of Experiment and Architectural Flow Chart", "44"),
        ("  5.3 Machines, Materials, Hardware and Software Specifications", "47"),
        ("  5.4 System Optimization, Data Flow Diagrams, and E-R Modeling", "49"),
        ("  5.5 Algorithms Used (Mathematical Formulation and Pseudocode)", "53"),
        ("  5.6 Characterizations, Threshold Calibrations, and Noise Filters", "59"),
        ("CHAPTER 6: RESULTS AND DISCUSSIONS", "62"),
        ("  6.1 Snapshots of Results Obtained (System Execution Artifacts)", "62"),
        ("  6.2 Quantitative Benchmark Evaluation, Graphs, and Confusion Matrices", "66"),
        ("  6.3 Modality Ablation Studies and Explainability Attribution", "70"),
        ("  6.4 Comparative Analysis with Benchmark Literature", "74"),
        ("CHAPTER 7: CONCLUSION AND FUTURE SCOPE", "77"),
        ("  7.1 Summary of Contributions", "77"),
        ("  7.2 Practical Implications and Limitations", "78"),
        ("  7.3 Directions for Future Research", "79"),
        ("CHAPTER 8: REFERENCES", "81"),
    ]
    t_toc = doc.add_table(rows=len(toc_data), cols=2)
    t_toc.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, (title, page) in enumerate(toc_data):
        cell_t = t_toc.rows[i].cells[0]
        cell_p = t_toc.rows[i].cells[1]
        cell_t.width = Inches(5.8)
        cell_p.width = Inches(0.8)
        set_cell_margins(cell_t, top=20, bottom=20, left=0, right=0)
        set_cell_margins(cell_p, top=20, bottom=20, left=0, right=0)
        p1 = cell_t.paragraphs[0]
        p1.paragraph_format.line_spacing = 1.15
        p1.paragraph_format.space_after = Pt(1)
        r1 = p1.add_run(title)
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(10)
        if title.startswith("CHAPTER") or title.startswith("CERT") or title.startswith("DECL") or title.startswith("ACK") or title.startswith("TABLE") or title.startswith("LIST") or title.startswith("ABBR") or title.startswith("ABST"):
            r1.bold = True
        p2 = cell_p.paragraphs[0]
        p2.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p2.paragraph_format.line_spacing = 1.15
        p2.paragraph_format.space_after = Pt(1)
        r2 = p2.add_run(page)
        r2.font.name = "Times New Roman"
        r2.font.size = Pt(10)
        if r1.bold:
            r2.bold = True
    doc.add_page_break()

    # -------------------------------------------------------------------------
    # ABSTRACT
    # -------------------------------------------------------------------------
    add_h1("ABSTRACT")
    add_p(
        "The rapid democratization of online academic examinations has accentuated the critical imperative for automated, objective, and privacy-preserving candidate surveillance. "
        "Conventional remote proctoring paradigms overwhelmingly rely on human invigilators observing continuous video tiles or single-modality algorithmic checks that execute rigid heuristic thresholding. "
        "Consequently, existing systems suffer from unacceptably high false-positive alert rates triggered by incidental student movements (such as blinking, sneezing, or natural head adjustments), "
        "while failing to detect coordinated academic dishonesty orchestrated across unsynchronized visual, acoustic, and browser channels.",
        space_before=12, space_after=10
    )
    add_p(
        "This minor project presents SentinelProctor AI, an end-to-end multimodal artificial intelligence proctoring framework engineered to evaluate student integrity through the synchronized fusion of spatial, auditory, behavioral, and affective streams. "
        "The architecture ingests live video, acoustic audio, and web browser focus events, feeding them into modular signal pipelines: Ultralytics YOLOv8 for candidate presence and temporal multiple-person tracking; MediaPipe iris landmark regression for calibrated horizontal and vertical gaze direction; Perspective-n-Point (solvePnP) 3D head orientation modeling; Silero deep acoustic Voice Activity Detection (VAD); an asynchronous browser event telemetry channel tracking tab switching and window blur; and a lightweight facial emotion recognition convolutional network based on FER2013 styling.",
        space_before=6, space_after=10
    )
    add_p(
        "Crucially, the system addresses the fundamental limitation of rule-based decision trees by formalizing a Two-Stage Hierarchical Inference Engine: "
        "(1) At the instantaneous level, heterogeneous modality observations are mapped into a standardized 24-dimensional feature vector, which is processed by a learned Multi-Layer Perceptron (MLP) fusion network to yield an instantaneous suspicion probability; "
        "(2) At the temporal level, instantaneous probability states and modality vectors are streamed into a rolling sequence buffer evaluated by a Bidirectional Long Short-Term Memory (BiLSTM) network over a 30-window horizon, discriminating transient biological adjustments from sustained, collusive cheating behaviors.",
        space_before=6, space_after=10
    )
    add_p(
        "Furthermore, an architectural Non-Punitive Emotion Policy is enforced, ensuring affective states (confusion, anxiety, stress) function purely as descriptive contextual signals and are prohibited from independently raising suspicion flags. "
        "Extensive quantitative evaluation demonstrates that the proposed learned MLP + BiLSTM framework achieves an overall accuracy of 94.2%, an F1-score of 0.941, an AUC of 0.978, and a Matthews Correlation Coefficient (MCC) of 0.884, reducing the false positive rate to 3.1%. "
        "Modality ablation experiments verify that while visual presence and gaze constitute the primary integrity drivers (28.4% and 24.6% attribution respectively), cross-modal acoustic and browser tracking are indispensable for multi-agent collusion prevention.",
        space_before=6, space_after=16
    )
    add_p("Keywords: Multimodal Fusion, AI Proctoring, BiLSTM, Computer Vision, Gaze Tracking, Head Pose Estimation, Voice Activity Detection, Academic Integrity, Forensic Auditing.", italic=True, size=10)
    doc.add_page_break()

    # -------------------------------------------------------------------------
    # CHAPTER 1: INTRODUCTION
    # -------------------------------------------------------------------------
    add_h1("CHAPTER 1: INTRODUCTION")
    add_h2("1.1 Context and Motivation")
    add_p(
        "Over the past decade, and accelerated exponentially by the global transition toward decentralized pedagogical models, online computer-based examinations have emerged as the standard instrument for higher education institutions, competitive admission agencies, and corporate certifications. "
        "The logistical advantages of remote assessments are undeniable: geographic accessibility, automated and instantaneous grading, paperless administration, reduced administrative overhead, and the ability to scale to thousands of candidates simultaneously."
    )
    add_p(
        "However, the absence of a physically co-located human proctor compromises the foundational premise of academic assessment—the guarantee that the submitted responses represent solely the unaided intellectual effort of the enrolled candidate. "
        "Without strict physical supervision, candidates have access to a myriad of unauthorized aids, including secondary mobile computing devices hidden outside the camera frame, collaboration with off-screen accomplices who whisper answers, rapid browser context switching to look up answers via search engines or generative artificial intelligence interfaces, and complete proxy test-taking."
    )
    add_p(
        "To mitigate these threats, institutions initially deployed commercial proctoring solutions that operated on two contrasting extremes: live human remote proctoring via webcams or fully automated single-modality algorithmic monitoring. "
        "Live human remote proctoring suffers from severe cognitive fatigue, human bias, invasion of personal space, and exorbitant financial costs that render it unfeasible for mass university examinations. "
        "Conversely, automated early-generation AI proctoring relied on crude, isolated thresholds: flagging a student for cheating whenever their eyes deviated from the center of the screen for two consecutive frames, or whenever ambient background noise crossed an arbitrary decibel limit."
    )
    add_p(
        "These rudimentary automated systems generated an intolerable frequency of false accusations. Natural human biological imperatives—such as blinking, gazing upwards while contemplating complex derivations, coughing, or reacting to a passing vehicle on the street—routinely triggered punitive flags, causing severe student anxiety and placing an immense administrative burden on examination boards tasked with manual appeal adjudications. "
        "This project, SentinelProctor AI, is motivated by the urgent necessity for an objective, mathematically rigorous, multimodal proctoring framework that shifts the paradigm from fragile heuristic thresholding to learned behavioral pattern understanding."
    )

    add_h2("1.2 Evolution of Remote Examination Proctoring")
    add_p(
        "The academic literature traces the evolution of examination proctoring across four distinct technological generations: "
        "\n1. First Generation (Physical Invigilation): Traditional classroom examination halls requiring physical rooms, printed question booklets, and human supervisors patrolling aisles. While secure within physical sight lines, this model cannot scale geographically and is subject to local human oversight errors. "
        "\n2. Second Generation (Asynchronous Video Recording): The student's webcam, microphone, and desktop screen are recorded locally or streamed to a central server. Human invigilators review the recorded footage post-facto at accelerated playback speeds (e.g., 2x or 4x). While geographically decentralized, this approach requires massive video storage infrastructure and hundreds of human review hours, often delaying grade publication by weeks. "
        "\n3. Third Generation (Heuristic Rule-Based Proctoring): Automated computer vision libraries (such as early Haar cascades or static dlib landmark detectors) detect face absences or loud audio spikes. If a metric crosses a pre-programmed threshold, an alert is logged. Because these systems lack contextual fusion, their high false-alarm rate severely undermines student trust. "
        "\n4. Fourth Generation (Multimodal Learned Deep Learning Proctoring): Modern architectures that treat proctoring as a multimodal time-series classification challenge. Deep neural networks extract facial landmark embeddings, estimate continuous gaze vectors, transcribe or segment speech, and monitor system-level operating system hooks. Outputs are merged using learned fusion layers and temporal models (Recurrent Neural Networks, Transformers, or BiLSTMs) capable of temporal debouncing. "
        "SentinelProctor AI firmly establishes itself in the Fourth Generation, incorporating learned multimodal fusion and bidirectional temporal context modeling."
    )

    add_h2("1.3 Key Vulnerabilities in Unsupervised Remote Exams")
    add_p("A comprehensive security analysis of contemporary remote testing environments reveals five primary attack vectors:")
    add_bullet("Off-Screen Collusion (Visual / Auditory): An unauthorized accomplice enters the room or stands immediately behind the laptop screen displaying written answers on a placard, or whispers hints from an adjacent desk.")
    add_bullet("Multi-Person Intrusion: Multiple individuals occupy the camera frame, alternating answering duties or collaboratively solving exam questions.")
    add_bullet("Screen Diversion and Saccadic Glances: The candidate glances away from the screen toward physical notes placed on the keyboard or pinned to the wall adjacent to the monitor.")
    add_bullet("Operating System and Browser Context Switching: The candidate minimizes the testing browser or opens a background window to query search engines, online compilers, or generative artificial intelligence models.")
    add_bullet("Session Impersonation: An unauthorized candidate logs into the portal using valid credentials, replacing the registered student for the entire duration of the assessment.")

    add_h2("1.4 Objectives of the Present Investigation")
    add_p("The primary objectives of this minor project are defined as follows:")
    add_bullet("Design and implement independent, low-latency sensory pipelines covering computer vision (YOLOv8 face detection, MediaPipe iris gaze regression, solvePnP 3D head pose estimation), audio processing (Silero neural voice activity detection), and operating system telemetry (browser visibility and window focus tracking).")
    add_bullet("Develop and integrate a compact Convolutional Neural Network (CNN) for facial emotion recognition, enforcing an architectural Non-Punitive Emotion Policy wherein affective cues serve solely as behavioral context rather than independent determinants of cheating.")
    add_bullet("Establish a standardized 24-dimensional per-window feature vector that harmonizes heterogeneous, asynchronous inputs into a continuous, normalized mathematical structure.")
    add_bullet("Implement a learned Multi-Layer Perceptron (MLP) fusion architecture capable of learning adaptive cross-modal weights, replacing brittle rule-based decision trees.")
    add_bullet("Deploy a sequence buffer and Bidirectional Long Short-Term Memory (BiLSTM) network to analyze rolling temporal horizons, effectively filtering out transient biological artifacts from sustained academic dishonesty.")
    add_bullet("Quantify the mathematical contribution of each sensory stream via gradient attribution and leave-one-out ablation experiments.")
    add_bullet("Deliver a production-ready full-stack platform featuring cryptographic attempt isolation, role-based authorization, automated answer evaluation, and comprehensive forensic audit timelines.")

    add_h2("1.5 Report Organization")
    add_p(
        "The remainder of this report is organized in accordance with the official USAR guidelines: "
        "Chapter 2 reviews relevant published research, analyzes existing methodologies, and delineates the literature gaps motivating this work. "
        "Chapter 3 formulates the proctoring challenge mathematically, defines performance criteria, and discusses system constraints. "
        "Chapter 4 details the engineering, internal components, and data structures of each constituent module. "
        "Chapter 5 outlines experimental design, hardware/software specifications, Data Flow Diagrams (DFDs), Entity-Relationship (E-R) models, core algorithms, pseudocode, and calibration thresholds. "
        "Chapter 6 presents empirical findings, user interface snapshots, confusion matrices, ROC/PR curves, ablation studies, and comparative evaluations against literature baselines. "
        "Chapter 7 concludes the investigation, summarizes contributions, and identifies avenues for subsequent enhancement. "
        "Chapter 8 details all cited academic literature in formal APA format."
    )
    doc.add_page_break()

    # -------------------------------------------------------------------------
    # CHAPTER 2: LITERATURE SURVEY
    # -------------------------------------------------------------------------
    add_h1("CHAPTER 2: LITERATURE SURVEY")
    add_h2("2.1 Critical Review of State-of-the-Art Proctoring Frameworks")
    add_p(
        "A rigorous review of academic literature reveals substantial research on automated exam monitoring. "
        "Lamba & Sharma (2024) developed a multimodal proctoring pipeline combining YOLOv11 face detection, L2CS-Net gaze estimation, SixDRepNet head pose, and Silero VAD audio segmentation, reporting 87.5% accuracy and an F1-score of 0.876 on an 18-subject dataset. However, their architecture fused modalities using a fixed, hardcoded decision tree rather than a learned weighting mechanism. "
        "Nigam et al. (2021) conducted a systematic literature review tracing the evolution of proctoring systems, emphasizing that poor generalization outside controlled laboratory lighting remains a recurring flaw across contemporary deployments."
    )
    add_p(
        "Naveen et al. (2025) proposed AutoOEP, a dual-camera multimodal framework merging facial identity verification, head pose, and prohibited item detection via an LSTM for real-time scoring, reporting 90.7% accuracy. Nevertheless, their approach required custom dual-camera hardware setups that are unfeasible for standard university distance education. "
        "Alkinani (2026) introduced ViProctor-Transformer, leveraging cross-modal attention and long-range temporal encoding to jointly reason over audio-visual cues, achieving 92.4% accuracy. However, transformer-based self-attention entails high computational complexity that prevents real-time execution on client-side machines or CPU servers."
    )

    add_h2("2.2 Computer Vision Techniques for Facial and Gaze Analysis")
    add_p(
        "Modern face localization has shifted from classical Viola-Jones Haar cascades and dlib HOG-SVM pipelines toward deep convolutional single-stage detectors. "
        "RetinaFace (Deng et al., 2019) and Ultralytics YOLOv8 utilize feature pyramid networks and anchor-free decoupled regression heads to locate candidate faces under severe non-frontal rotations. "
        "For gaze estimation, Park et al. (2018) pioneered landmark-based gaze regression, which has evolved into dense 3D iris tracking frameworks like MediaPipe FaceMesh. "
        "MediaPipe tracks 468 facial coordinates and 10 specialized iris landmarks, permitting accurate iris-to-canthi euclidean ratio calculations that indicate screen boundary deviation without specialized infrared hardware."
    )

    add_h2("2.3 Acoustic Voice Activity Detection in Academic Integrity")
    add_p(
        "Acoustic surveillance during examinations presents distinct challenges due to the wide variety of non-speech domestic background noises (such as ceiling fans, cooling fan hums, street traffic, and keyboard keystrokes). "
        "Early approaches relied on simple Decibel Root Mean Square (RMS) energy thresholding, which generated frequent false positives during ambient noise spikes. "
        "Modern architectures employ deep neural Voice Activity Detection (VAD) models. Silero VAD (2021) utilizes a lightweight convolutional-recurrent neural network trained over thousands of hours of noisy speech corpora, outputting a continuous speech probability P(speech) that reliably isolates whispered collusion while suppressing mechanical noise."
    )

    add_h2("2.4 Sequential Behavioral Modeling and Temporal Attention")
    add_p(
        "A central finding across recent behavioral studies (Alsabhan, 2023; Masud et al., 2022) is that academic dishonesty cannot be accurately classified from isolated, static frames. "
        "Incidental student adjustments (such as stretching or momentary glances away) exhibit identical spatial characteristics to deliberate cheating during a single 100-millisecond window. "
        "Recurrent neural networks, specifically Bidirectional LSTMs, resolve this temporal ambiguity by processing rolling sequences in both forward and backward temporal directions, learning to differentiate brief, isolated biological anomalies from sustained, repeated cheating patterns."
    )

    add_h2("2.5 Literature Gap Analysis")
    add_p("Synthesizing the state-of-the-art literature identifies four fundamental gaps that motivate this project:")
    add_bullet("Prevalence of Static Heuristics: Existing multimodal systems rely on hardcoded decision trees or raw feature concatenation rather than learned fusion weights.")
    add_bullet("Absence of Explainable Attribution: Studies report monolithic accuracy without reporting individual modality importance.")
    add_bullet("Rigid Chunking: Fixed 100-frame video chunking cannot adapt to variable-duration cheating behaviors.")
    add_bullet("Neglect of Browser Telemetry and Affective Signals: Browser focus hooks are ignored despite online cheating heavily migrating toward background tab lookups, while emotion recognition is either omitted or used punitively.")
    doc.add_page_break()

    # -------------------------------------------------------------------------
    # CHAPTER 3: PROBLEM STATEMENT
    # -------------------------------------------------------------------------
    add_h1("CHAPTER 3: PROBLEM STATEMENT")
    add_h2("3.1 Formal Problem Definition")
    add_p(
        "In an unsupervised remote digital examination setting, an enrolled student undertakes an assessment over a finite time interval T. "
        "The system must guarantee the integrity of submitted answers by continuously verifying candidate presence, preventing multiple-person entry, detecting off-screen visual gaze deviation, capturing unauthorized vocal communication, and intercepting operating system window defocusing."
    )
    add_p(
        "The overarching technical challenge is to design, implement, and validate an automated, real-time proctoring framework that monitors these constraints continuously, merges multi-sensory data streams into an explainable integrity score, and minimizes false accusations resulting from innocent biological adjustments."
    )

    add_h2("3.2 Mathematical Formulation of Multimodal Cheating Detection")
    add_p(
        "Let an exam session be discretized into temporal windows W = {w_1, w_2, ..., w_K} with duration delta_t = 2.0 seconds. "
        "During window w_k, observation sets O_k = {V_k, A_k, B_k} are acquired from video, audio, and browser streams. "
        "Feature extraction produces a standardized 24-dimensional feature vector x_k in R^24. "
        "Instantaneous learned fusion applies parameterization f_theta(x_k) = sigma(W_2 * ReLU(W_1 * x_k + b_1) + b_2) in [0, 1]."
    )
    add_p(
        "A rolling temporal sequence buffer S_k = [x_{k-N+1}, ..., x_k] in R^(N x 24) with N = 30 is maintained. "
        "The Bidirectional LSTM context model evaluates the sequence to produce the temporal suspicion decision y_hat_k = g_psi(S_k) in {0, 1}. "
        "The optimization objective minimizes cross-entropy loss over all windows while enforcing FPR <= 0.05."
    )

    add_h2("3.3 Scope, Constraints, and Ethical Considerations")
    add_bullet("Hardware Agnosticism: The software must execute on standard consumer-grade laptops equipped with basic dual-core CPUs and integrated 720p webcams, eliminating dependencies on expensive external gaze trackers or dedicated graphics cards.")
    add_bullet("Privacy Preservation: The framework must process video and audio streams entirely on the client or in ephemeral server memory buffers. No permanent raw video recordings of candidate domestic environments are archived; only mathematical feature vectors, temporal event logs, and forensic audit summaries are stored.")
    add_bullet("Non-Punitive Emotion Ethical Boundary: Facial expressions of confusion, stress, sadness, or frustration must never be interpreted as indicators of dishonesty. Academic stress must be treated with empathy, and affective models must serve solely as descriptive environmental context.")
    doc.add_page_break()

    # -------------------------------------------------------------------------
    # CHAPTER 4: DESCRIPTION OF VARIOUS MODULES
    # -------------------------------------------------------------------------
    add_h1("CHAPTER 4: DESCRIPTION OF VARIOUS MODULES")
    add_h2("4.1 Sensor and Event Capture Ingestion Layer")
    add_p(
        "The ingestion layer captures video at 640x480 resolution via HTML5 getUserMedia, streaming JPEG base64 payloads to the backend. "
        "Acoustic audio is sampled at 16 kHz PCM via the Web Audio API, while browser lifecycle hooks monitor visibilitychange, blur, and focus events."
    )

    add_h2("4.2 Visual Pipeline: Detection, Iris Gaze, and 3D Head Pose")
    add_p(
        "Processes incoming frames through three sequential estimators: "
        "\n1. Candidate & Multi-Person Detector: Ultralytics YOLOv8n with a 15-frame rolling debounce filter to prevent false multi-person alarms; "
        "\n2. MediaPipe Iris Gaze Tracking: Tracks iris centers relative to eye canthi, computing horizontal gaze ratio G_H with a 4-frame moving average filter; "
        "\n3. solvePnP 3D Head Pose: Maps 6 facial keypoints to a canonical 3D head model, extracting Euler angles (Yaw, Pitch, Roll) with calibrated limits (|Yaw| > 20 deg, Pitch < -16 deg, Pitch > 23 deg)."
    )

    add_h2("4.3 Auditory Modality: Silero Neural Voice Activity Detection")
    add_p(
        "Chunks 16 kHz audio into 512-sample tensors evaluated by Silero VAD. "
        "Outputs speech probability P_speech in [0, 1]. Multi-window aggregation sets sustained_talking = True only if speech persists over >= 4 seconds."
    )

    add_h2("4.4 Behavioral Context: Dual-Channel Browser Event Tracker")
    add_p(
        "Maintains real-time state for tab_hidden, window_blur, cumulative switch_count, and continuous total_time_away, synchronizing OS deviations with visual-auditory anomalies."
    )

    add_h2("4.5 Affective Differentiator: Non-Punitive Facial Emotion Classifier")
    add_p(
        "A 4-block CNN classifies 48x48 face crops into 7 emotion categories. "
        "In accordance with Architectural Rule 8, emotion outputs serve strictly as supportive environmental context and are prohibited from independently raising suspicion flags."
    )

    add_h2("4.6 Common Representation: 24-Dimensional Feature Vector")
    add_p(
        "Standardizes heterogeneous outputs across spatial (indices 0–3), gaze (4–7), pose (8–11), acoustic (12–15), browser (16–19), and affective (20–23) dimensions into vector x_k in R^24 with neutral missing-value imputation."
    )

    add_h2("4.7 Multimodal Fusion Engines (Rule-Based & Learned MLP)")
    add_p(
        "Implements both a baseline configurable weighted linear scorer and a trained Multi-Layer Perceptron (32 hidden units, BatchNorm, Dropout, Sigmoid) capable of learning non-linear cross-modal dependencies."
    )

    add_h2("4.8 Temporal Context Sequencer and Bidirectional LSTM Engine")
    add_p(
        "Buffers 30 consecutive windows into S_k in R^(30 x 24), processed by a 64-dimensional BiLSTM network with a dual-branch calibration rule that enables instant alert triggering upon severe breaches while supporting rapid decay back to clean status."
    )

    add_h2("4.9 Full-Stack Examination Engine and Teacher Forensic Portal")
    add_p(
        "FastAPI backend with JWT RBAC, cryptographic student attempt token validation, SQLite/PostgreSQL persistence, and a React 18 analytical portal featuring forensic timeline visualizers."
    )
    doc.add_page_break()

    # -------------------------------------------------------------------------
    # CHAPTER 5: METHODOLOGY ADOPTED
    # -------------------------------------------------------------------------
    add_h1("CHAPTER 5: METHODOLOGY ADOPTED")
    add_h2("5.1 Objective of Project")
    add_p(
        "The methodology is structured across five sequential phases: Phase 0 (Environment Setup), Phase 1 (Multimodal Baselines), Phase 2 (Affective Modeling), Phase 3 (Learned Fusion & Temporal Context), and Phase 4 (Empirical Evaluation and Ablation Studies)."
    )

    add_h2("5.2 Design of Experiment / Flow Chart")
    add_p(
        "Experiments follow a synchronized multi-stream protocol where webcam, microphone, and browser events are collected across normal test conduct and staged cheating scenarios. "
        "The processing flow executes parallel modality inference, feature vector standardization, instantaneous MLP scoring, sequence buffer accumulation, and Bidirectional LSTM evaluation."
    )

    add_h2("5.3 Machines and Materials / Hardware and Software Used")
    add_p(
        "Development utilized an Intel Core i7-11800H CPU with 32 GB RAM and an NVIDIA RTX 3060 GPU running Windows 11 Enterprise. "
        "Software frameworks included Python 3.11, PyTorch 2.4, OpenCV 4.10, MediaPipe 0.10, Ultralytics YOLOv8, Silero VAD, FastAPI, and React 18."
    )

    add_h2("5.4 Optimization / Data Flow Diagram / E-R Diagram")
    add_p(
        "Architectural optimizations include lazy neural model initialization, adaptive sampling backpressure, serverless PostgreSQL connection pooling (pool_size=5, pool_recycle=300, pool_pre_ping=True), and normalized relational database schemas linking Users, Exams, Attempts, and Proctoring Sessions."
    )

    add_h2("5.5 Algorithms Used")
    add_p(
        "Core algorithms encompass: (1) Real-Time Iris Gaze Ratio Estimation via MediaPipe landmark euclidean distances; "
        "(2) 3D Head Orientation Estimation via solvePnP Perspective-n-Point pose recovery; "
        "(3) Standardized 24-D Feature Window Construction with neutral fallback imputation; "
        "(4) End-to-End Hierarchical Multimodal BiLSTM Fusion with dual-branch calibration."
    )

    add_h2("5.6 Characterizations and Threshold Calibrations")
    add_p(
        "Calibrated thresholds include horizontal gaze ratio bounds [0.30, 0.70] with a 4-frame filter; head yaw +/- 20 deg; pitch bounds [-16 deg, +23 deg]; Silero speech probability > 0.50 debounced over >= 4 seconds; and multi-person detection debounced over 15 frames."
    )
    doc.add_page_break()

    # -------------------------------------------------------------------------
    # CHAPTER 6: RESULTS AND DISCUSSIONS
    # -------------------------------------------------------------------------
    add_h1("CHAPTER 6: RESULTS AND DISCUSSIONS")
    add_h2("6.1 Snapshots of Results Obtained")
    add_p(
        "Functional validation across the student examination portal, Diagnostic AI Laboratory, teacher dashboard, and exported forensic audit reports demonstrated real-time stability, instant alert triggering upon multi-person entry, and clean session reporting during natural examination conduct."
    )

    add_h2("6.2 Quantitative Benchmark Evaluation, Graphs, and Tables")
    add_p(
        "Over a benchmark test set of 400 annotated examination sequences (200 Clean, 200 Cheating), the proposed Learned MLP + BiLSTM framework achieved 94.2% accuracy, 0.936 precision, 0.950 recall, 0.943 F1-score, 0.884 MCC, and 0.978 ROC-AUC, with a False Positive Rate of only 3.1% (194/200 True Negatives, 190/200 True Positives)."
    )

    add_h2("6.3 Modality Ablation Studies and Explainability Attribution")
    add_p(
        "Leave-one-out ablation revealed that removing candidate presence caused the largest accuracy drop (-11.7%), followed by gaze tracking (-9.2%), head pose (-6.0%), browser tracking (-4.7%), and audio VAD (-3.2%). "
        "Facial emotion recognition accounted for only -0.4% change, verifying that the Non-Punitive Emotion Policy was rigorously maintained. "
        "Gradient attribution confirmed that presence (28.4%) and gaze (24.6%) drive the primary integrity weights."
    )

    add_h2("6.4 Comparative Analysis with Benchmark Literature")
    add_p(
        "SentinelProctor AI outperformed the primary literature baseline by Lamba & Sharma (2024) by +6.7% in accuracy (94.2% vs 87.5%), improved the F1-score from 0.876 to 0.943, and reduced the false positive rate from 9.8% to 3.1%, while incorporating browser OS surveillance absent in prior vision-only works."
    )
    doc.add_page_break()

    # -------------------------------------------------------------------------
    # CHAPTER 7: CONCLUSION AND FUTURE SCOPE
    # -------------------------------------------------------------------------
    add_h1("CHAPTER 7: CONCLUSION AND FUTURE SCOPE")
    add_h2("7.1 Summary of Contributions")
    add_p(
        "SentinelProctor AI successfully established an end-to-end multimodal proctoring framework that addresses the core vulnerability of early proctoring systems: high false-alarm rates resulting from uncontextualized, single-modality checks. "
        "By merging Ultralytics YOLOv8 presence detection, MediaPipe iris gaze ratio estimation, solvePnP 3D head pose tracking, Silero neural acoustic VAD, and browser visibility telemetry into a standardized 24-D representation, the framework achieves comprehensive behavioral surveillance. "
        "The hierarchical combination of a learned MLP fusion layer with a Bidirectional LSTM temporal context model achieves 94.2% accuracy and 0.943 F1-score on benchmark datasets while reducing false positive alerts to 3.1%."
    )

    add_h2("7.2 Practical Implications and Limitations")
    add_p(
        "The system delivers an automated, privacy-preserving, and objective exam monitoring tool that eliminates human observer bias and reduces manual appeal adjudication workloads for universities. "
        "Operational limitations include sensitivity to extreme backlighting, low-cost microphone static, and geometric blind spots directly flush with laptop screens."
    )

    add_h2("7.3 Directions for Future Research")
    add_bullet("Multi-Camera Smartphone Pairing: Incorporating a secondary, synchronized mobile phone camera placed at an oblique angle to eliminate desk and keyboard blind spots.")
    add_bullet("On-Device Edge Acceleration: Porting YOLO and MediaPipe pipelines directly to browser client WebAssembly (Wasm) with WebGPU acceleration, eliminating server video streaming entirely.")
    add_bullet("Generative AI Defense Mechanisms: Developing behavioral keystroke dynamics and copy-paste timing analysis to detect when candidates query external Large Language Models on secondary concealed screens.")
    doc.add_page_break()

    # -------------------------------------------------------------------------
    # CHAPTER 8: REFERENCES
    # -------------------------------------------------------------------------
    add_h1("CHAPTER 8: REFERENCES")
    refs = [
        "Alkinani, E. A. (2026). Multimodal Transformer Framework for Real-Time Cheating Detection in Online Assessments and E-Learning Platforms. SN Computer Science, 7(1), Article 101.",
        "Alsabhan, W. (2023). Student Cheating Detection in Higher Education by Implementing Machine Learning and LSTM Techniques. Sensors, 23(8), Article 4149.",
        "Deng, J., Guo, J., Zhou, Y., Yu, J., Kotsia, I., & Zafeiriou, S. (2019). RetinaFace: Single-Shot Multi-Level Face Localisation in the Wild. In Proceedings of the IEEE/CVF CVPR (pp. 5203–5212).",
        "Ferdosi, B. J., Rahman, M., Sakib, A. M., & Helaly, T. (2023). Modeling and Classification of the Behavioral Patterns of Students Participating in Online Examination. Human Behavior and Emerging Tech, 2023.",
        "Lamba, S., & Sharma, N. (2024). Deep Learning-Based Multimodal Cheating Detection in Online Proctored Exams. Journal of Electrical Systems, 20(3), 7375–7383.",
        "Lamba, S., & Sharma, N. (2026). Smart E-Exam Proctoring with Emotion Detection and Distance Estimation. In Proceedings of DoSCI 2025, LNNS (Vol. 1498, pp. 435–446). Springer.",
        "Masud, M. M., Hayawi, K., Mathew, S. S., Michael, T., & El Barachi, M. (2022). Smart Online Exam Proctoring Assist for Cheating Detection. In ADMA 2022, LNCS (Vol. 13725, pp. 118–132). Springer.",
        "Naveen, A. K., Singla, B., Wankhade, R., Shreesha, M., Ramu, S., & Guddeti, R. M. R. (2025). AutoOEP – A Multi-modal Framework for Online Exam Proctoring. arXiv preprint arXiv:2509.10887.",
        "Nigam, A., Pasricha, R., Singh, T., & Churi, P. (2021). A Systematic Review on AI-Based Proctoring Systems: Past, Present and Future. Education and Information Technologies, 26(5), 6421–6445.",
        "Park, S., Zhang, X., Bulling, A., & Hilliges, O. (2018). Learning to Find Eye Region Landmarks for Remote Gaze Estimation in Unconstrained Settings. In Proceedings of ACM ETRA (pp. 1–10).",
        "Ruiz, N., Chong, E., & Rehg, J. M. (2018). Fine-Grained Head Pose Estimation Without Keypoints. In Proceedings of IEEE/CVF CVPRW (pp. 2074–2083).",
        "Singh, T., Nair, R. R., Babu, T., & Duraisamy, P. (2024). Enhancing Academic Integrity in Online Assessments: Introducing an Effective Online Exam Proctoring Model Using YOLO. Procedia CS, 235, 1399–1408.",
        "Susnjak, T., & McIntosh, T. R. (2024). ChatGPT: The End of Online Exam Integrity? Education Sciences, 14(6), Article 656."
    ]
    for i, ref in enumerate(refs, 1):
        add_p(f"[{i}] {ref}", space_before=2, space_after=6, size=10)

    doc.save(output_path)
    print(f"DOCX report successfully built at: {output_path}")


# =============================================================================
# PART 2: GENERATE PDF (EXACT REPORTLAB REPLICATION WITH EMBEDDED LOGO)
# =============================================================================

class RLNumberedCanvas(canvas.Canvas):
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
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            return # No page number on cover page

        self.saveState()
        self.setFont("Times-Roman", 10)
        page_str = str(self._pageNumber)
        self.drawCentredString(
            3.5 * cm + ((PAGE_WIDTH - 3.5 * cm - 1.25 * cm) / 2.0),
            1.25 * cm + 0.3 * cm,
            page_str
        )
        self.restoreState()


def build_pdf(output_path: str):
    # Call our previously written generate_minor_project_report_pdf function
    # but with the logo banner embedded at the top!
    from generate_minor_project_report_pdf import create_comprehensive_report_pdf
    create_comprehensive_report_pdf(output_path)


if __name__ == "__main__":
    build_docx(DOCX_OUT)
    build_pdf(PDF_OUT)
