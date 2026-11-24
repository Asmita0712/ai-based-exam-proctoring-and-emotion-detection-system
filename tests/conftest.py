"""
Pytest configuration and session-scoped fixtures.
Implements:
- Session-scoped TestClient and DB initialization (avoids re-creating on every test)
- Pre-generated staff authentication tokens (Teacher & Admin)
- Shared ML model fixtures (loads PyTorch/YOLO/BiLSTM once per test session)
"""
from typing import Dict, Generator
from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.core.security import create_access_token


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """Shared TestClient instance across the entire test session."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def teacher_auth_headers(client: TestClient) -> Dict[str, str]:
    """Pre-computed authentication headers for an authorized Teacher."""
    from app.db.session import SessionLocal
    from app.db.models import User
    db = SessionLocal()
    teacher = db.query(User).filter(User.email == "teacher@sentinelproctor.ai").first()
    teacher_id = teacher.id if teacher else "test-teacher-id"
    db.close()
    token = create_access_token(
        data={"sub": teacher_id, "email": "teacher@sentinelproctor.ai", "role": "teacher"}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def admin_auth_headers(client: TestClient) -> Dict[str, str]:
    """Pre-computed authentication headers for an authorized Admin."""
    from app.db.session import SessionLocal
    from app.db.models import User
    db = SessionLocal()
    admin = db.query(User).filter(User.email == "admin@sentinelproctor.ai").first()
    admin_id = admin.id if admin else "test-admin-id"
    db.close()
    token = create_access_token(
        data={"sub": admin_id, "email": "admin@sentinelproctor.ai", "role": "admin"}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def shared_bilstm():
    """Session-scoped BiLSTM model to prevent reloading weights repeatedly."""
    from ml.temporal.bilstm import BiLSTMTemporalModel
    return BiLSTMTemporalModel(sequence_length=30, threshold=0.5)


@pytest.fixture(scope="session")
def shared_learned_fusion():
    """Session-scoped LearnedFusion model to prevent reloading weights repeatedly."""
    from ml.fusion.learned_fusion import LearnedFusion
    return LearnedFusion(model_type="mlp", threshold=0.5)
