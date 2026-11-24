/**
 * SentinelProctor AI - Centralized Exam, Auth & Proctoring API Client
 *
 * Implements:
 * - JWT token persistence for Staff (Teachers / Admins)
 * - Attempt token persistence for Students (Open Access flow)
 * - Automatic Authorization header injection
 * - Server-authoritative timer synchronization and autosave
 */

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").trim().replace(/\/+$/, "") || "http://localhost:8000";

// Token storage keys
const STAFF_TOKEN_KEY = "sentinel_staff_token";
const ATTEMPT_TOKEN_KEY = "sentinel_attempt_token";

/**
 * Standard fetch helper with error normalization and auth injection
 */
async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  // Inject Staff JWT if logged in
  const staffToken = localStorage.getItem(STAFF_TOKEN_KEY);
  if (staffToken && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${staffToken}`;
  }

  // Inject Student Attempt Token if taking an exam
  const attemptToken = sessionStorage.getItem(ATTEMPT_TOKEN_KEY);
  if (attemptToken && !headers["X-Attempt-Token"]) {
    headers["X-Attempt-Token"] = attemptToken;
  }

  const config = {
    ...options,
    credentials: "include", // Include HttpOnly cookies
    headers,
  };

  try {
    const res = await fetch(url, config);
    if (!res.ok) {
      let errorDetail = `HTTP ${res.status} ${res.statusText}`;
      try {
        const errorJson = await res.json();
        if (errorJson && errorJson.detail) {
          errorDetail =
            typeof errorJson.detail === "string"
              ? errorJson.detail
              : JSON.stringify(errorJson.detail);
        }
      } catch {
        // Fallback to HTTP text
      }
      const error = new Error(errorDetail);
      error.status = res.status;
      throw error;
    }
    return await res.json();
  } catch (err) {
    console.error(`[API Error] ${options.method || "GET"} ${endpoint}:`, err);
    throw err;
  }
}

export const examApi = {
  // ===================================================================
  // AUTHENTICATION & STAFF ACCESS
  // ===================================================================

  /** Authenticate staff member (Teacher or Admin) */
  async login(email, password) {
    const data = await request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    if (data.access_token) {
      localStorage.setItem(STAFF_TOKEN_KEY, data.access_token);
      localStorage.setItem("sentinel_user", JSON.stringify(data.user));
    }
    return data;
  },

  /** Log out staff member */
  async logout() {
    try {
      await request("/auth/logout", { method: "POST" });
    } catch (_) {}
    localStorage.removeItem(STAFF_TOKEN_KEY);
    localStorage.removeItem("sentinel_user");
  },

  /** Get current authenticated staff user profile */
  async getMe() {
    return request("/auth/me");
  },

  /** Retrieve currently saved staff user */
  getStoredUser() {
    try {
      const u = localStorage.getItem("sentinel_user");
      return u ? JSON.parse(u) : null;
    } catch (_) {
      return null;
    }
  },

  /** Check if teacher/admin is logged in */
  isStaffLoggedIn() {
    return Boolean(localStorage.getItem(STAFF_TOKEN_KEY));
  },

  // ===================================================================
  // HEALTH & MONITORING
  // ===================================================================

  async checkHealth() {
    return request("/health");
  },

  async checkReadiness() {
    return request("/health/ready");
  },

  // ===================================================================
  // EXAMINATIONS & STUDENT WORKFLOW
  // ===================================================================

  /** Public list of published exams for student lobby */
  async getExams(publishedOnly = true) {
    return request(`/exams/?published_only=${Boolean(publishedOnly)}`);
  },

  /** Public student question inspection (answers stripped) */
  async getExamForStudent(examId) {
    return request(`/exams/${encodeURIComponent(examId)}`);
  },

  /**
   * OPEN ACCESS: Student starts exam attempt without account registration
   * Receives server timer, clean questions, and signed attempt_token.
   */
  async startExamAttempt(examId, { student_name, student_id, access_code }) {
    const data = await request(`/exams/${encodeURIComponent(examId)}/start`, {
      method: "POST",
      body: JSON.stringify({ student_name, student_id, access_code }),
    });
    if (data.attempt_token) {
      sessionStorage.setItem(ATTEMPT_TOKEN_KEY, data.attempt_token);
    }
    return data;
  },

  /** Idempotent answer autosave during active exam */
  async autosaveAnswer(examId, questionId, selectedOption) {
    return request(`/exams/${encodeURIComponent(examId)}/autosave`, {
      method: "POST",
      body: JSON.stringify({
        question_id: questionId,
        selected_option: selectedOption,
      }),
    });
  },

  /** Final submission of exam answers */
  async submitExam(examId, payload) {
    const res = await request(`/exams/${encodeURIComponent(examId)}/submit`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    // Clear attempt token after final submission
    sessionStorage.removeItem(ATTEMPT_TOKEN_KEY);
    return res;
  },

  // ===================================================================
  // TEACHER PORTAL & ANALYTICS
  // ===================================================================

  /** Full exam definition with answer keys (Teacher/Admin only) */
  async getExamForTeacher(examId) {
    return request(`/exams/${encodeURIComponent(examId)}/teacher`);
  },

  /** Create new MCQ exam (Teacher/Admin only) */
  async createExam(examData) {
    return request("/exams/", {
      method: "POST",
      body: JSON.stringify(examData),
    });
  },

  /** Toggle exam publication (Teacher/Admin only) */
  async togglePublishExam(examId, isPublished) {
    return request(`/exams/${encodeURIComponent(examId)}/publish?is_published=${Boolean(isPublished)}`, {
      method: "PATCH",
    });
  },

  /** Teacher dashboard and submission reports for an exam */
  async getTeacherDashboard(examId) {
    return request(`/exams/${encodeURIComponent(examId)}/dashboard`);
  },

  /** System-wide overview metrics across all exams */
  async getSystemOverview() {
    return request("/exams/analytics/summary");
  },

  // ===================================================================
  // PROCTORING & INFERENCE
  // ===================================================================

  /** Stream webcam frame to AI proctoring pipeline */
  async sendProctoringFrame(framePayload) {
    return request("/proctoring/analyze-frame", {
      method: "POST",
      body: JSON.stringify(framePayload),
    });
  },

  /** Run simulated sensor scenario (Admin / Diagnostic Lab only) */
  async sendProctoringWindow(windowPayload) {
    return request("/proctoring/analyze-window", {
      method: "POST",
      body: JSON.stringify(windowPayload),
    });
  },

  /** Log student browser focus / blur events */
  async logBrowserEvent(browserEventPayload) {
    return request("/proctoring/events", {
      method: "POST",
      body: JSON.stringify(browserEventPayload),
    });
  },

  /** Retrieve full session audit report */
  async getSessionSummary(sessionId) {
    return request(`/results/${encodeURIComponent(sessionId)}/summary`);
  },

  /** Reset a proctoring session (Admin / Diagnostic Lab only) */
  async resetSession(sessionId) {
    return request(`/proctoring/session/reset`, {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId }),
    });
  },

  /** Retrieves base API URL for external links (e.g. Swagger docs) */
  getApiBaseUrl() {
    return API_BASE;
  },

  /** Backend health probe */
  async getHealth() {
    return request("/health");
  },
};

export default examApi;
