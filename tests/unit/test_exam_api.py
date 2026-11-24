"""
Level 1 Unit tests for Exam API, Open Student Flow, Security Boundaries, and Grading.
"""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_auth_login_and_roles(client: TestClient):
    # 1. Invalid login
    bad_resp = client.post(
        "/auth/login",
        json={"email": "teacher@sentinelproctor.ai", "password": "WrongPassword"},
    )
    assert bad_resp.status_code == 401

    # 2. Valid teacher login
    t_resp = client.post(
        "/auth/login",
        json={"email": "teacher@sentinelproctor.ai", "password": "Teacher@Sentinel2026"},
    )
    assert t_resp.status_code == 200
    assert t_resp.json()["user"]["role"] == "teacher"
    t_token = t_resp.json()["access_token"]

    # 3. Access me endpoint
    me_resp = client.get("/auth/me", headers={"Authorization": f"Bearer {t_token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "teacher@sentinelproctor.ai"


@pytest.mark.unit
def test_list_and_get_default_exam(client: TestClient, teacher_auth_headers: dict):
    # 1. Public list exams (open for students)
    resp = client.get("/exams/")
    assert resp.status_code == 200
    exams = resp.json()
    assert len(exams) >= 1

    exam_id = exams[0]["id"]
    # Security boundary: questions and correct_option_index are completely omitted from public listing
    assert "questions" not in exams[0]

    # 2. Public student view (questions included, but answers stripped)
    stu_resp = client.get(f"/exams/{exam_id}")
    assert stu_resp.status_code == 200
    stu_exam = stu_resp.json()
    assert stu_exam["id"] == exam_id
    assert len(stu_exam["questions"]) >= 1
    # Security boundary: correct_option_index is stripped from student view
    assert "correct_option_index" not in stu_exam["questions"][0]

    # 3. Unauthenticated access to teacher view must fail (401)
    client.cookies.clear()
    unauth_resp = client.get(f"/exams/{exam_id}/teacher")
    assert unauth_resp.status_code == 401

    # 4. Authenticated Teacher view (answers included)
    teach_resp = client.get(f"/exams/{exam_id}/teacher", headers=teacher_auth_headers)
    assert teach_resp.status_code == 200
    teach_exam = teach_resp.json()
    assert "correct_option_index" in teach_exam["questions"][0]

    # 5. Authenticated Teacher list
    teach_list_resp = client.get("/exams/teacher/list", headers=teacher_auth_headers)
    assert teach_list_resp.status_code == 200
    assert "questions" in teach_list_resp.json()[0]


@pytest.mark.unit
def test_open_student_flow_and_autosave(client: TestClient, teacher_auth_headers: dict):
    # 1. Teacher creates exam
    create_payload = {
        "title": "Computer Networks Quiz",
        "description": "Networking basics",
        "duration_minutes": 15,
        "is_published": True,
        "questions": [
            {
                "id": "q1",
                "question_text": "What protocol operates at the Transport layer?",
                "options": ["IP", "TCP", "HTTP", "Ethernet"],
                "correct_option_index": 1,
                "points": 5,
            },
            {
                "id": "q2",
                "question_text": "Which port does HTTPS use by default?",
                "options": ["80", "22", "443", "53"],
                "correct_option_index": 2,
                "points": 5,
            },
        ],
    }
    create_resp = client.post("/exams/", json=create_payload, headers=teacher_auth_headers)
    assert create_resp.status_code == 201
    new_exam = create_resp.json()
    exam_id = new_exam["id"]
    q1_id = new_exam["questions"][0]["id"]
    q2_id = new_exam["questions"][1]["id"]

    # 2. OPEN ACCESS: Student starts exam attempt WITHOUT registering an account
    start_resp = client.post(
        f"/exams/{exam_id}/start",
        json={"student_name": "Rohan Verma", "student_id": "STU-202"},
    )
    assert start_resp.status_code == 200
    start_data = start_resp.json()
    attempt_id = start_data["attempt_id"]
    attempt_token = start_data["attempt_token"]
    session_id = start_data["session_id"]
    assert attempt_id is not None
    assert attempt_token is not None
    assert start_data["remaining_seconds"] > 0

    # 3. Autosave answer
    save_resp = client.post(
        f"/exams/{exam_id}/autosave",
        json={"question_id": q1_id, "selected_option": 1},
        headers={"X-Attempt-Token": attempt_token},
    )
    assert save_resp.status_code == 200
    assert save_resp.json()["success"] is True

    # 4. Final submit without attempt token MUST FAIL (401)
    submit_payload = {
        "student_name": "Rohan Verma",
        "student_id": "STU-202",
        "session_id": session_id,
        "answers": {q1_id: 1, q2_id: 2},
    }
    client.cookies.clear()
    unauth_sub_resp = client.post(f"/exams/{exam_id}/submit", json=submit_payload)
    assert unauth_sub_resp.status_code == 401

    # 5. Final submit with valid attempt token succeeds (200)
    sub_resp = client.post(
        f"/exams/{exam_id}/submit",
        json=submit_payload,
        headers={"X-Attempt-Token": attempt_token},
    )
    assert sub_resp.status_code == 200
    sub_data = sub_resp.json()
    assert sub_data["score"] == 10
    assert sub_data["percentage"] == 100.0

    # 6. Re-submitting already completed attempt MUST FAIL (400)
    resub_resp = client.post(
        f"/exams/{exam_id}/submit",
        json=submit_payload,
        headers={"X-Attempt-Token": attempt_token},
    )
    assert resub_resp.status_code == 400

    # 7. Teacher inspects dashboard
    dash_resp = client.get(f"/exams/{exam_id}/dashboard", headers=teacher_auth_headers)
    assert dash_resp.status_code == 200
    dash_data = dash_resp.json()
    assert dash_data["total_submissions"] >= 1


@pytest.mark.unit
def test_cross_student_attempt_isolation(client: TestClient, teacher_auth_headers: dict):
    """
    SECURITY BOUNDARY: Verifies complete isolation between student attempts:
    - Student A cannot be modified or submitted by Student B.
    - Token B cannot operate on Attempt A.
    """
    # 1. Fetch public exam
    resp = client.get("/exams/")
    exam_id = resp.json()[0]["id"]

    # 2. Student A starts attempt
    start_a = client.post(
        f"/exams/{exam_id}/start",
        json={"student_name": "Student Alpha", "student_id": "STU-ALPHA"},
    )
    assert start_a.status_code == 200
    token_a = start_a.json()["attempt_token"]
    att_a_id = start_a.json()["attempt_id"]

    # 3. Student B starts attempt
    start_b = client.post(
        f"/exams/{exam_id}/start",
        json={"student_name": "Student Beta", "student_id": "STU-BETA"},
    )
    assert start_b.status_code == 200
    token_b = start_b.json()["attempt_token"]
    att_b_id = start_b.json()["attempt_id"]
    assert att_a_id != att_b_id

    # 4. Student B tries to submit using Student A's student_id with Token B
    # Server extracts student identity from the cryptographic token, so spoofing fails
    b_spoof_submit = client.post(
        f"/exams/{exam_id}/submit",
        json={
            "student_name": "Student Alpha",
            "student_id": "STU-ALPHA",
            "session_id": start_b.json()["session_id"],
            "answers": {},
        },
        headers={"X-Attempt-Token": token_b},
    )
    assert b_spoof_submit.status_code == 200
    # The server graded Student B's attempt, not Student A's
    assert b_spoof_submit.json()["student_id"] == "STU-BETA"
    assert b_spoof_submit.json()["student_name"] == "Student Beta"

    # 5. Student A's attempt remains active and unsubmitted
    save_a = client.post(
        f"/exams/{exam_id}/autosave",
        json={"question_id": "q1", "selected_option": 0},
        headers={"X-Attempt-Token": token_a},
    )
    assert save_a.status_code == 200
    assert save_a.json()["success"] is True
