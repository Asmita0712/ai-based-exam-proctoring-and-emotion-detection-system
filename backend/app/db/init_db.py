"""
Database initialization and idempotent seed routines.
Creates tables and ensures baseline admin, teacher, and sample exam records exist.
"""
from datetime import datetime, timezone
import json
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.security import hash_password
from app.db.models import Base, Exam, Question, User
from app.db.session import SessionLocal, engine

logger = get_logger("init_db")
settings = get_settings()


def init_db(db: Session = None) -> None:
    """Creates tables and provisions initial users and demonstration exam."""
    Base.metadata.create_all(bind=engine)

    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        # 1. Provision Default Admin
        admin = db.query(User).filter(User.email == settings.admin_email).first()
        if not admin:
            admin = User(
                email=settings.admin_email,
                hashed_password=hash_password(settings.admin_password),
                full_name="System Administrator",
                role="admin",
                is_active=True,
            )
            db.add(admin)
            db.commit()
            logger.info("Provisioned default admin: %s", settings.admin_email)

        # 2. Provision Default Teacher
        teacher = db.query(User).filter(User.email == settings.teacher_email).first()
        if not teacher:
            teacher = User(
                email=settings.teacher_email,
                hashed_password=hash_password(settings.teacher_password),
                full_name="Prof. Alan Turing",
                role="teacher",
                is_active=True,
            )
            db.add(teacher)
            db.commit()
            logger.info("Provisioned default teacher: %s", settings.teacher_email)

        # 3. Provision Default Published Exam
        default_exam_id = "exam-demo-001"
        existing_exam = db.query(Exam).filter(Exam.id == default_exam_id).first()
        if not existing_exam:
            teacher_ref = db.query(User).filter(User.role == "teacher").first()
            exam = Exam(
                id=default_exam_id,
                title="AI & Computer Vision Certification Exam",
                description="Official Online MCQ Assessment — Monitored by Multimodal AI Proctoring Engine",
                duration_minutes=30,
                instructions="1. Ensure camera and microphone are centered.\n2. Do not switch tabs or minimize browser.\n3. Answer all multiple-choice questions before the timer expires.",
                is_published=True,
                teacher_id=teacher_ref.id if teacher_ref else None,
            )
            db.add(exam)
            db.commit()

            sample_questions = [
                (
                    "q1",
                    "Which of the following neural network architectures is primarily designed for sequential temporal data?",
                    ["Convolutional Neural Network (CNN)", "Bidirectional Long Short-Term Memory (BiLSTM)", "Principal Component Analysis (PCA)", "Support Vector Machine (SVM)"],
                    1,
                    2,
                    0,
                ),
                (
                    "q2",
                    "In computer vision, what does solvePnP (Perspective-n-Point) estimate from 2D facial landmarks?",
                    ["Iris pupil diameter", "3D Head Pose Orientation (Yaw, Pitch, Roll)", "Facial emotion probability", "Acoustic frequency spectrum"],
                    1,
                    2,
                    1,
                ),
                (
                    "q3",
                    "Why is Multimodal Fusion preferred over single-modality proctoring in online exams?",
                    ["It consumes zero CPU power", "It cross-verifies multiple sensory streams, drastically reducing false positive accusations", "It requires no webcam or microphone", "It only checks browser history"],
                    1,
                    2,
                    2,
                ),
                (
                    "q4",
                    "Under the ethical Affective Integrity Rule, how should facial emotion affect student suspicion scores?",
                    ["Fear or anxiety directly penalizes the student", "Emotion is the primary deciding factor for cheating", "Emotion acts as context only and NEVER independently penalizes an anxious student", "Only happy students are allowed to pass"],
                    2,
                    2,
                    3,
                ),
                (
                    "q5",
                    "What is the time-domain metric used in this system to measure microphone audio levels and speech presence?",
                    ["Root-Mean-Square (RMS) over Float32 PCM samples", "Fast Fourier Transform (FFT) Decibel Peak", "Keyboard Scancode Frequency", "HTTP Packet Header Size"],
                    0,
                    2,
                    4,
                ),
            ]

            for q_id, q_text, opts, correct_idx, pts, ord_idx in sample_questions:
                q = Question(
                    id=q_id,
                    exam_id=default_exam_id,
                    question_text=q_text,
                    options_json=json.dumps(opts),
                    correct_option_index=correct_idx,
                    points=pts,
                    order=ord_idx,
                )
                db.add(q)
            db.commit()
            logger.info("Provisioned default certification examination: %s", default_exam_id)

    finally:
        if close_session:
            db.close()


if __name__ == "__main__":
    init_db()
    print("Database initialization and provisioning complete.")
