"""
Phase 0 requirement: backend health and readiness endpoints.
"""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


@pytest.mark.unit
def test_health_check_has_version(client: TestClient):
    response = client.get("/health")
    assert "version" in response.json()


@pytest.mark.unit
def test_readiness_check(client: TestClient):
    response = client.get("/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert "database" in body
    assert body["status"] == "ready"
