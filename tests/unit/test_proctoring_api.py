"""
Level 2 Integration tests for backend proctoring routes, RBAC protection, and forensic records.
"""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_submit_event_and_analyze_window_with_auth(client: TestClient, admin_auth_headers: dict):
    sess_id = "test_eval_session"

    # 1. Post browser event (public for student active exam)
    evt_resp = client.post(
        "/proctoring/events",
        json={
            "session_id": sess_id,
            "type": "tab_hidden",
            "timestamp": "2026-11-21T12:00:00Z",
        },
    )
    assert evt_resp.status_code == 200
    assert evt_resp.json()["received"] is True

    # 2. Unauthenticated call to /proctoring/analyze-window must be rejected (401)
    unauth_resp = client.post(
        "/proctoring/analyze-window",
        json={
            "session_id": sess_id,
            "visual_signals": {"person_count": 2, "multi_person_flag": True},
            "mode": "temporal",
        },
    )
    assert unauth_resp.status_code == 401

    # 3. Authenticated Admin calls /proctoring/analyze-window
    ana_resp = client.post(
        "/proctoring/analyze-window",
        json={
            "session_id": sess_id,
            "visual_signals": {
                "person_count": 2,
                "multi_person_flag": True,
                "looking_away": True,
            },
            "mode": "temporal",
        },
        headers=admin_auth_headers,
    )
    assert ana_resp.status_code == 200
    data = ana_resp.json()
    assert data["session_id"] == sess_id
    assert "suspicion_score" in data
    assert "flag" in data
    assert "signals" in data

    # 4. Retrieve results list
    res_resp = client.get(f"/results/{sess_id}")
    assert res_resp.status_code == 200
    res_list = res_resp.json()
    assert len(res_list) >= 1
    assert res_list[0]["session_id"] == sess_id

    # 5. Retrieve session summary and integrity score
    sum_resp = client.get(f"/results/{sess_id}/summary")
    assert sum_resp.status_code == 200
    summary = sum_resp.json()
    assert summary["session_id"] == sess_id
    assert "integrity_score" in summary
    assert "verdict" in summary
    assert "violations_summary" in summary


@pytest.mark.integration
def test_free_tier_health_and_proctoring_resilience(client: TestClient, admin_auth_headers: dict):
    # 1. Health check probes
    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    health_data = health_resp.json()
    assert health_data["status"] == "ok"
    assert "heavy_ai_enabled" in health_data

    ready_resp = client.get("/health/ready")
    assert ready_resp.status_code == 200
    assert ready_resp.json()["database"] == "connected"

    # 2. Frame inference under free tier defaults (honest status, no fake detections)
    sess_id = "test_free_tier_sess"
    # Small 1x1 transparent/black PNG base64
    dummy_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
    frame_resp = client.post(
        "/proctoring/analyze-frame",
        json={
            "session_id": sess_id,
            "image_base64": dummy_b64,
            "mode": "temporal",
            "browser_signals": {"tab_hidden": True, "window_blur": True},
        },
    )
    assert frame_resp.status_code == 200
    frame_data = frame_resp.json()
    assert frame_data["session_id"] == sess_id
    assert frame_data["inference_status"] in ("FREE_TIER_CPU_ONLY", "ACTIVE")
    # Tab violation must be captured truthfully
    assert frame_data["signals"]["tab_hidden"] is True
    # In free-tier mode, visual signals are not fabricated
    if frame_data["inference_status"] == "FREE_TIER_CPU_ONLY":
        assert frame_data["signals"]["gaze_ratio"] is None
        assert frame_data["signals"]["looking_away"] is None
