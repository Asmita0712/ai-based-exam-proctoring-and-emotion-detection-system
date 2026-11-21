"""
Unit test for backend proctoring routes and inference service.
"""
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_submit_event_and_analyze_window():
    sess_id = "test_eval_session"

    # 1. Post browser event
    evt_resp = client.post(
        "/proctoring/events",
        json={
            "session_id": sess_id,
            "type": "tab_hidden",
            "timestamp": "2026-11-21T12:00:00Z"
        }
    )
    assert evt_resp.status_code == 200
    assert evt_resp.json()["received"] is True

    # 2. Analyze window
    ana_resp = client.post(
        "/proctoring/analyze-window",
        json={
            "session_id": sess_id,
            "visual_signals": {
                "person_count": 2,
                "multi_person_flag": True,
                "looking_away": True
            },
            "mode": "temporal"
        }
    )
    assert ana_resp.status_code == 200
    data = ana_resp.json()
    assert data["session_id"] == sess_id
    assert "suspicion_score" in data
    assert "flag" in data
    assert "signals" in data

    # 3. Retrieve results list
    res_resp = client.get(f"/results/{sess_id}")
    assert res_resp.status_code == 200
    res_list = res_resp.json()
    assert len(res_list) >= 1
    assert res_list[0]["session_id"] == sess_id
