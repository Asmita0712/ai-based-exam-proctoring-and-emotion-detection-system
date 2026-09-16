"""
Phase 0 requirement: backend health endpoint must work.

Run with: pytest tests/unit/test_health.py
Requires: fastapi, httpx (see backend/requirements.txt)
"""
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


def test_health_check_has_version():
    response = client.get("/health")
    assert "version" in response.json()
