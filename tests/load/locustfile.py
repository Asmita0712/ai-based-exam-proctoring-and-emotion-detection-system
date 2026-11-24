"""
Locust Load Testing Suite for SentinelProctor AI: 500 Concurrent Active Examination Sessions.
Simulates real student examination lifecycles:
1. Lobby browsing & public exam retrieval
2. Open-access examination attempt initialization (JWT generation)
3. Periodic answer autosaving with server-authoritative timer validation
4. High-frequency AI proctoring event streaming with backpressure-adapted intervals
5. Final exam submission and forensic integrity report generation
6. Teacher dashboard polling under concurrent student load
"""
import random
import time
import uuid
from locust import HttpUser, between, events, tag, task


class ExamStudentUser(HttpUser):
    wait_time = between(2, 5)  # Natural human reading pause between questions

    def on_start(self):
        """Student entry flow: Open access, no password registration required."""
        self.student_id = f"STU-{uuid.uuid4().hex[:6]}"
        self.student_name = f"Student {self.student_id}"
        self.exam_id = "exam-demo-001"
        self.attempt_id = None
        self.attempt_token = None
        self.session_id = None
        self.questions = []
        self.sampling_interval_s = 1.0

        # 1. Fetch available exams from public lobby
        with self.client.get("/exams/", catch_response=True) as resp:
            if resp.status_code == 200 and len(resp.json()) > 0:
                self.exam_id = resp.json()[0]["id"]
                resp.success()
            else:
                resp.failure(f"Failed to fetch public exams: {resp.status_code}")
                return

        # 2. Open exam details (student view - answers stripped)
        with self.client.get(f"/exams/{self.exam_id}", catch_response=True) as resp:
            if resp.status_code == 200:
                data = resp.json()
                self.questions = data.get("questions", [])
                resp.success()
            else:
                resp.failure(f"Failed to fetch exam details: {resp.status_code}")
                return

        # 3. Start Exam Attempt
        start_payload = {
            "student_name": self.student_name,
            "student_id": self.student_id,
        }
        with self.client.post(
            f"/exams/{self.exam_id}/start", json=start_payload, catch_response=True
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                self.attempt_id = data["attempt_id"]
                self.attempt_token = data["attempt_token"]
                self.session_id = data["session_id"]
                resp.success()
            else:
                resp.failure(f"Failed to start exam attempt: {resp.status_code}")

    @task(4)
    @tag("autosave")
    def autosave_answer(self):
        """Simulates periodic student answer selection with server timer enforcement."""
        if not self.attempt_token or not self.questions:
            return

        q = random.choice(self.questions)
        selected_opt = random.randint(0, len(q.get("options", [0, 1])) - 1)

        payload = {
            "question_id": q["id"],
            "selected_option": selected_opt,
        }
        headers = {"X-Attempt-Token": self.attempt_token}

        with self.client.post(
            f"/exams/{self.exam_id}/autosave",
            json=payload,
            headers=headers,
            catch_response=True,
        ) as resp:
            if resp.status_code == 200 and resp.json().get("success"):
                resp.success()
            else:
                resp.failure(f"Autosave failed: {resp.status_code}")

    @task(6)
    @tag("proctoring")
    def stream_proctoring_event(self):
        """Simulates webcam telemetry & inference event streaming."""
        if not self.session_id:
            return

        # Telemetry payload simulating multimodal sensors
        event_payload = {
            "session_id": self.session_id,
            "event_type": random.choice(["gaze_deviation", "head_turn", "normal", "speech_detected"]),
            "confidence": round(random.uniform(0.7, 0.98), 2),
            "details": {
                "yaw": round(random.uniform(-15.0, 15.0), 1),
                "pitch": round(random.uniform(-10.0, 10.0), 1),
                "vad_speech": random.random() < 0.1,
            },
        }

        with self.client.post(
            "/proctoring/events", json=event_payload, catch_response=True
        ) as resp:
            if resp.status_code in (200, 201):
                # Check adaptive backpressure sampling interval header
                adaptive_interval = resp.headers.get("X-Sampling-Interval-Ms")
                if adaptive_interval:
                    self.sampling_interval_s = float(adaptive_interval) / 1000.0
                resp.success()
            else:
                resp.failure(f"Proctoring event rejected: {resp.status_code}")

    @task(1)
    @tag("submission")
    def finalize_submission(self):
        """Simulates end-of-exam submission and forensic result generation."""
        if not self.attempt_token or not self.questions:
            return

        answers = {q["id"]: random.randint(0, len(q["options"]) - 1) for q in self.questions}
        payload = {
            "student_name": self.student_name,
            "student_id": self.student_id,
            "session_id": self.session_id,
            "answers": answers,
        }

        with self.client.post(
            f"/exams/{self.exam_id}/submit", json=payload, catch_response=True
        ) as resp:
            if resp.status_code == 200:
                report = resp.json()
                if "score" in report and "integrity_score" in report:
                    resp.success()
                else:
                    resp.failure("Missing score or integrity_score in report")
                # Stop this student's lifecycle after submission
                self.environment.runner.quit()
            else:
                resp.failure(f"Submission failed: {resp.status_code}")


class TeacherMonitoringUser(HttpUser):
    wait_time = between(5, 10)

    def on_start(self):
        """Logs in as Teacher and obtains staff JWT."""
        self.auth_token = None
        login_payload = {
            "email": "teacher@sentinelproctor.ai",
            "password": "Teacher@Sentinel2026",
        }
        with self.client.post("/auth/login", json=login_payload, catch_response=True) as resp:
            if resp.status_code == 200:
                self.auth_token = resp.json().get("access_token")
                resp.success()
            else:
                resp.failure("Teacher authentication failed.")

    @task
    @tag("dashboard")
    def poll_teacher_dashboard(self):
        """Polls live metrics and student submission integrity scores."""
        if not self.auth_token:
            return
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        with self.client.get(
            "/exams/teacher/dashboard", headers=headers, catch_response=True
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"Teacher dashboard query failed: {resp.status_code}")
