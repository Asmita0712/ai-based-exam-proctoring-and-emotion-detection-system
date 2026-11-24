import React, { useState, useEffect, useMemo } from "react";
import examApi from "../services/examApi";
import ProctoringReportModal from "./ProctoringReportModal";

export default function TeacherPortal({ initialTab = "dashboard" }) {
  // Navigation tabs: 'dashboard', 'exams', 'create', 'analytics'
  const [activeTab, setActiveTab] = useState(initialTab);

  // Global state
  const [systemOverview, setSystemOverview] = useState(null);
  const [exams, setExams] = useState([]);
  const [selectedExamId, setSelectedExamId] = useState("");
  const [dashboard, setDashboard] = useState(null);
  const [loadingDashboard, setLoadingDashboard] = useState(false);
  const [loadingOverview, setLoadingOverview] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);

  // Modal inspection states
  const [selectedAuditReport, setSelectedAuditReport] = useState(null);
  const [inspectingSubmission, setInspectingSubmission] = useState(null);

  // Exam Management Drilldown state
  const [viewingExamDetails, setViewingExamDetails] = useState(null);
  const [examDetailSubTab, setExamDetailSubTab] = useState("overview"); // 'overview', 'questions', 'submissions'

  // Submissions filter & search
  const [searchQuery, setSearchQuery] = useState("");
  const [verdictFilter, setVerdictFilter] = useState("ALL"); // ALL, CLEAN, REVIEW_NEEDED, HIGH_SUSPICION
  const [sortBy, setSortBy] = useState("DATE_DESC"); // DATE_DESC, SCORE_DESC, SCORE_ASC, INTEGRITY_ASC

  // Exam Builder State
  const [builderStep, setBuilderStep] = useState(1); // 1: Details, 2: Questions, 3: Preview, 4: Review
  const [previewShowAnswers, setPreviewShowAnswers] = useState(false);
  const [examTitle, setExamTitle] = useState("");
  const [examDesc, setExamDesc] = useState("");
  const [examInstructions, setExamInstructions] = useState(
    "1. Webcam and microphone must remain active throughout the test.\n2. Do not switch tabs or minimize the window.\n3. Keep your face centered in the camera frame.\n4. All questions are mandatory."
  );
  const [examDuration, setExamDuration] = useState(15);
  const [examIsPublished, setExamIsPublished] = useState(true);
  const [questions, setQuestions] = useState([
    {
      id: "q_1",
      question_text: "",
      options: ["", "", "", ""],
      correct_option_index: 0,
      points: 2,
    },
  ]);
  const [creating, setCreating] = useState(false);
  const [publishedExamResult, setPublishedExamResult] = useState(null);

  const showToast = (msg, duration = 3000) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), duration);
  };

  // 1. Fetch system-wide overview
  const loadSystemOverview = async () => {
    try {
      setLoadingOverview(true);
      const data = await examApi.getSystemOverview();
      setSystemOverview(data);
    } catch (err) {
      console.error("Failed to load system overview:", err);
    } finally {
      setLoadingOverview(false);
    }
  };

  // 2. Fetch all exams
  const loadExams = async () => {
    try {
      const data = await examApi.getExams(false);
      setExams(data);
      if (data.length > 0 && !selectedExamId) {
        setSelectedExamId(data[0].id);
      }
    } catch (err) {
      console.error("Failed to load exams:", err);
    }
  };

  // 3. Fetch specific exam submissions dashboard
  const loadExamDashboard = async (examId) => {
    if (!examId) return;
    try {
      setLoadingDashboard(true);
      const data = await examApi.getTeacherDashboard(examId);
      setDashboard(data);
    } catch (err) {
      console.error("Failed to load exam dashboard:", err);
    } finally {
      setLoadingDashboard(false);
    }
  };

  useEffect(() => {
    loadSystemOverview();
    loadExams();
  }, []);

  useEffect(() => {
    if (selectedExamId) {
      loadExamDashboard(selectedExamId);
    }
  }, [selectedExamId]);

  // Toggle publish state
  const handleTogglePublish = async (examId, currentState, e) => {
    if (e) e.stopPropagation();
    try {
      const updated = await examApi.togglePublishExam(examId, !currentState);
      showToast(`Exam "${updated.title}" ${updated.is_published ? "Published" : "Unpublished"}`);
      loadExams();
      loadSystemOverview();
      if (viewingExamDetails && viewingExamDetails.id === examId) {
        setViewingExamDetails(updated);
      }
    } catch (err) {
      alert("Failed to update status: " + err.message);
    }
  };

  // Question builder helpers
  const handleAddQuestion = () => {
    const nextIdx = questions.length + 1;
    setQuestions([
      ...questions,
      {
        id: `q_${nextIdx}_${Date.now().toString(36)}`,
        question_text: "",
        options: ["", "", "", ""],
        correct_option_index: 0,
        points: 2,
      },
    ]);
  };

  const handleDuplicateQuestion = (idx) => {
    const target = questions[idx];
    const duplicated = {
      ...target,
      id: `q_${questions.length + 1}_${Date.now().toString(36)}`,
      options: [...target.options],
    };
    const updated = [...questions];
    updated.splice(idx + 1, 0, duplicated);
    setQuestions(updated);
    showToast(`Duplicated Question #${idx + 1}`);
  };

  const handleRemoveQuestion = (idx) => {
    if (questions.length <= 1) {
      alert("An examination must contain at least one question.");
      return;
    }
    setQuestions(questions.filter((_, i) => i !== idx));
  };

  const handleQuestionChange = (idx, field, value) => {
    const updated = [...questions];
    updated[idx][field] = value;
    setQuestions(updated);
  };

  const handleOptionChange = (qIdx, optIdx, val) => {
    const updated = [...questions];
    updated[qIdx].options[optIdx] = val;
    setQuestions(updated);
  };

  const handleLoadSample = () => {
    setExamTitle("Computer Science & Applied AI Examination");
    setExamDesc("Comprehensive assessment covering computer vision, neural temporal networks, and ethical AI systems.");
    setExamInstructions(
      "1. Ensure your webcam and microphone remain active throughout the examination.\n2. Do not switch tabs or minimize the browser window.\n3. Keep your face centered in the camera view with adequate lighting.\n4. All questions are mandatory."
    );
    setExamDuration(15);
    setExamIsPublished(true);
    setQuestions([
      {
        id: "q_1",
        question_text: "Which neural network architecture is explicitly designed for temporal sequence modeling across consecutive video windows?",
        options: [
          "Convolutional Neural Network (CNN)",
          "Bidirectional Long Short-Term Memory (BiLSTM)",
          "Principal Component Analysis (PCA)",
          "Support Vector Machine (SVM)",
        ],
        correct_option_index: 1,
        points: 2,
      },
      {
        id: "q_2",
        question_text: "In computer vision proctoring, what 3D spatial properties are estimated by Perspective-n-Point (solvePnP)?",
        options: [
          "Pupil diameter & dilation rate",
          "Head pose orientation angles (Yaw, Pitch, Roll)",
          "Candidate facial emotion category",
          "Audio fundamental frequency (F0)",
        ],
        correct_option_index: 1,
        points: 2,
      },
      {
        id: "q_3",
        question_text: "Why does SentinelProctor AI utilize Multimodal Fusion rather than relying on a single camera stream?",
        options: [
          "It reduces server memory consumption to zero",
          "It cross-correlates audio, visual landmarks, and browser signals to minimize false positive accusations",
          "It disables the need for webcam permissions",
          "It automatically solves questions for the student",
        ],
        correct_option_index: 1,
        points: 2,
      },
      {
        id: "q_4",
        question_text: "Under the ethical Affective Integrity Rule, how does elevated facial anxiety or fear influence student integrity scores?",
        options: [
          "It directly deducts marks from the student's exam score",
          "It immediately triggers an automatic cheating disqualification",
          "It acts as context only and NEVER independently penalizes an anxious student",
          "It overrides the camera stream",
        ],
        correct_option_index: 2,
        points: 2,
      },
      {
        id: "q_5",
        question_text: "Which time-domain metric is calculated over PCM Float32 audio samples to detect student voice activity?",
        options: [
          "Root-Mean-Square (RMS) amplitude",
          "Fast Fourier Transform (FFT) peak bin",
          "Mel-Frequency Cepstral Coefficients (MFCC)",
          "WAV header byte offset",
        ],
        correct_option_index: 0,
        points: 2,
      },
    ]);
    showToast("Loaded sample exam template!");
  };

  // Validate builder
  const validateExam = () => {
    if (!examTitle.trim()) return "Exam Title is required.";
    if (examDuration < 1) return "Duration must be at least 1 minute.";
    if (questions.length === 0) return "At least one question is required.";

    for (let i = 0; i < questions.length; i++) {
      if (!questions[i].question_text.trim()) {
        return `Question #${i + 1} is missing its question prompt text.`;
      }
      for (let j = 0; j < 4; j++) {
        if (!questions[i].options[j].trim()) {
          return `Question #${i + 1}, Option ${String.fromCharCode(65 + j)} is empty.`;
        }
      }
    }
    return null;
  };

  // Publish exam handler
  const handlePublishExam = async () => {
    const error = validateExam();
    if (error) {
      alert(error);
      return;
    }

    try {
      setCreating(true);
      const payload = {
        title: examTitle.trim(),
        description: examDesc.trim(),
        instructions: examInstructions.trim(),
        duration_minutes: Number(examDuration),
        is_published: Boolean(examIsPublished),
        questions: questions.map((q, idx) => ({
          id: q.id || `q_${idx + 1}`,
          question_text: q.question_text.trim(),
          options: q.options.map((opt) => opt.trim()),
          correct_option_index: Number(q.correct_option_index),
          points: Number(q.points) || 1,
        })),
      };

      const created = await examApi.createExam(payload);
      setPublishedExamResult(created);
      await loadExams();
      await loadSystemOverview();
      setSelectedExamId(created.id);
      showToast("Exam successfully created and registered!");
    } catch (err) {
      console.error("Error creating exam:", err);
      alert("Failed to publish exam: " + err.message);
    } finally {
      setCreating(false);
    }
  };

  // Filtered & sorted submissions
  const filteredSubmissions = useMemo(() => {
    if (!dashboard || !dashboard.submissions) return [];
    let list = [...dashboard.submissions];

    // Search query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      list = list.filter(
        (s) =>
          s.student_name.toLowerCase().includes(q) ||
          s.student_id.toLowerCase().includes(q) ||
          s.submission_id.toLowerCase().includes(q)
      );
    }

    // Verdict filter
    if (verdictFilter === "CLEAN") {
      list = list.filter((s) => s.verdict === "VERIFIED_CLEAN");
    } else if (verdictFilter === "REVIEW_NEEDED") {
      list = list.filter((s) => s.verdict === "SUSPICIOUS_REVIEW_NEEDED" || s.verdict === "CHEATING_FLAGGED");
    } else if (verdictFilter === "HIGH_SUSPICION") {
      list = list.filter((s) => s.verdict === "CHEATING_FLAGGED");
    }

    // Sorting
    list.sort((a, b) => {
      if (sortBy === "DATE_DESC") return new Date(b.submitted_at) - new Date(a.submitted_at);
      if (sortBy === "SCORE_DESC") return b.score - a.score;
      if (sortBy === "SCORE_ASC") return a.score - b.score;
      if (sortBy === "INTEGRITY_ASC") return a.integrity_score - b.integrity_score;
      return 0;
    });

    return list;
  }, [dashboard, searchQuery, verdictFilter, sortBy]);

  // Total marks calculation in builder
  const totalBuilderPoints = useMemo(() => {
    return questions.reduce((sum, q) => sum + (Number(q.points) || 0), 0);
  }, [questions]);

  // Color helper for verdict
  const getVerdictBadge = (verdict, label) => {
    if (verdict === "VERIFIED_CLEAN") {
      return {
        bg: "rgba(16, 185, 129, 0.15)",
        border: "#10b981",
        color: "#34d399",
        text: label || "Verified Clean",
      };
    }
    if (verdict === "SUSPICIOUS_REVIEW_NEEDED") {
      return {
        bg: "rgba(245, 158, 11, 0.15)",
        border: "#f59e0b",
        color: "#fbbf24",
        text: label || "Review Needed",
      };
    }
    return {
      bg: "rgba(239, 68, 68, 0.15)",
      border: "#ef4444",
      color: "#f87171",
      text: label || "Cheating Flagged",
    };
  };

  return (
    <div style={{ color: "#f8fafc", width: "100%", maxWidth: "1280px", margin: "0 auto", paddingBottom: "3rem" }}>
      {/* Toast notification banner */}
      {toastMessage && (
        <div
          style={{
            position: "fixed",
            bottom: "24px",
            right: "24px",
            backgroundColor: "#0284c7",
            color: "#ffffff",
            padding: "12px 20px",
            borderRadius: "10px",
            boxShadow: "0 10px 25px -5px rgba(2, 132, 199, 0.5)",
            zIndex: 10000,
            fontSize: "0.9rem",
            fontWeight: "600",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <span>✓</span>
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Top Workspace Navigation Bar */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          borderBottom: "1px solid #1e293b",
          paddingBottom: "1.2rem",
          marginBottom: "1.8rem",
          flexWrap: "wrap",
          gap: "1rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <div
            style={{
              width: "42px",
              height: "42px",
              borderRadius: "10px",
              background: "linear-gradient(135deg, #2563eb, #0284c7)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "1.4rem",
              boxShadow: "0 4px 14px rgba(37,99,235,0.3)",
            }}
          >
            👨‍🏫
          </div>
          <div>
            <h1 style={{ fontSize: "1.45rem", fontWeight: "800", margin: 0, letterSpacing: "-0.02em" }}>
              Teacher Examination Control Hub
            </h1>
            <p style={{ margin: 0, fontSize: "0.82rem", color: "#94a3b8" }}>
              Author examinations, manage submissions, and review real-time multimodal AI proctoring audits.
            </p>
          </div>
        </div>

        {/* Workspace Sub-tabs */}
        <div
          style={{
            display: "flex",
            backgroundColor: "#0f172a",
            padding: "4px",
            borderRadius: "10px",
            border: "1px solid #1e293b",
            gap: "4px",
          }}
        >
          <button
            onClick={() => {
              setActiveTab("dashboard");
              loadSystemOverview();
            }}
            style={{
              padding: "8px 16px",
              borderRadius: "7px",
              border: "none",
              backgroundColor: activeTab === "dashboard" ? "#1e293b" : "transparent",
              color: activeTab === "dashboard" ? "#38bdf8" : "#94a3b8",
              fontWeight: activeTab === "dashboard" ? "700" : "500",
              cursor: "pointer",
              fontSize: "0.85rem",
              transition: "all 0.15s ease",
            }}
          >
            📊 System Overview
          </button>
          <button
            onClick={() => {
              setActiveTab("exams");
              loadExams();
            }}
            style={{
              padding: "8px 16px",
              borderRadius: "7px",
              border: "none",
              backgroundColor: activeTab === "exams" ? "#1e293b" : "transparent",
              color: activeTab === "exams" ? "#38bdf8" : "#94a3b8",
              fontWeight: activeTab === "exams" ? "700" : "500",
              cursor: "pointer",
              fontSize: "0.85rem",
              transition: "all 0.15s ease",
            }}
          >
            📚 Manage Exams ({exams.length})
          </button>
          <button
            onClick={() => setActiveTab("create")}
            style={{
              padding: "8px 16px",
              borderRadius: "7px",
              border: "none",
              backgroundColor: activeTab === "create" ? "#0284c7" : "transparent",
              color: activeTab === "create" ? "#ffffff" : "#94a3b8",
              fontWeight: activeTab === "create" ? "700" : "500",
              cursor: "pointer",
              fontSize: "0.85rem",
              transition: "all 0.15s ease",
            }}
          >
            ✍️ Exam Builder
          </button>
          <button
            onClick={() => {
              setActiveTab("analytics");
              if (selectedExamId) loadExamDashboard(selectedExamId);
            }}
            style={{
              padding: "8px 16px",
              borderRadius: "7px",
              border: "none",
              backgroundColor: activeTab === "analytics" ? "#1e293b" : "transparent",
              color: activeTab === "analytics" ? "#38bdf8" : "#94a3b8",
              fontWeight: activeTab === "analytics" ? "700" : "500",
              cursor: "pointer",
              fontSize: "0.85rem",
              transition: "all 0.15s ease",
            }}
          >
            🎯 Submissions & AI Audit
          </button>
        </div>
      </div>

      {/* ---------------------------------------------------- */}
      {/* TAB 1: SYSTEM OVERVIEW DASHBOARD */}
      {/* ---------------------------------------------------- */}
      {activeTab === "dashboard" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.8rem" }}>
          {/* Key Metric Cards */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))",
              gap: "1rem",
            }}
          >
            <div
              style={{
                backgroundColor: "#0f172a",
                border: "1px solid #1e293b",
                borderRadius: "12px",
                padding: "1.2rem",
                position: "relative",
                overflow: "hidden",
              }}
            >
              <div style={{ fontSize: "0.75rem", color: "#94a3b8", fontWeight: "600", textTransform: "uppercase" }}>
                Total Examinations
              </div>
              <div style={{ fontSize: "2rem", fontWeight: "800", color: "#38bdf8", marginTop: "0.4rem" }}>
                {systemOverview ? systemOverview.total_exams : exams.length}
              </div>
              <div style={{ fontSize: "0.78rem", color: "#64748b", marginTop: "0.2rem" }}>
                {systemOverview ? systemOverview.published_exams : 0} currently active
              </div>
            </div>

            <div
              style={{
                backgroundColor: "#0f172a",
                border: "1px solid #1e293b",
                borderRadius: "12px",
                padding: "1.2rem",
              }}
            >
              <div style={{ fontSize: "0.75rem", color: "#94a3b8", fontWeight: "600", textTransform: "uppercase" }}>
                Total Submissions
              </div>
              <div style={{ fontSize: "2rem", fontWeight: "800", color: "#f8fafc", marginTop: "0.4rem" }}>
                {systemOverview ? systemOverview.total_submissions : 0}
              </div>
              <div style={{ fontSize: "0.78rem", color: "#64748b", marginTop: "0.2rem" }}>
                Across all created exams
              </div>
            </div>

            <div
              style={{
                backgroundColor: "#0f172a",
                border: "1px solid #1e293b",
                borderRadius: "12px",
                padding: "1.2rem",
              }}
            >
              <div style={{ fontSize: "0.75rem", color: "#94a3b8", fontWeight: "600", textTransform: "uppercase" }}>
                Class Academic Avg
              </div>
              <div style={{ fontSize: "2rem", fontWeight: "800", color: "#10b981", marginTop: "0.4rem" }}>
                {systemOverview ? `${systemOverview.class_average}%` : "—"}
              </div>
              <div style={{ fontSize: "0.78rem", color: "#64748b", marginTop: "0.2rem" }}>
                MCQ graded performance
              </div>
            </div>

            <div
              style={{
                backgroundColor: "#0f172a",
                border: "1px solid #1e293b",
                borderRadius: "12px",
                padding: "1.2rem",
              }}
            >
              <div style={{ fontSize: "0.75rem", color: "#94a3b8", fontWeight: "600", textTransform: "uppercase" }}>
                Avg AI Integrity
              </div>
              <div style={{ fontSize: "2rem", fontWeight: "800", color: "#818cf8", marginTop: "0.4rem" }}>
                {systemOverview ? `${systemOverview.average_integrity}%` : "100%"}
              </div>
              <div style={{ fontSize: "0.78rem", color: "#64748b", marginTop: "0.2rem" }}>
                Multimodal fusion confidence
              </div>
            </div>

            <div
              style={{
                backgroundColor: "#0f172a",
                border:
                  systemOverview && systemOverview.flagged_students_count > 0
                    ? "1px solid rgba(239, 68, 68, 0.4)"
                    : "1px solid #1e293b",
                borderRadius: "12px",
                padding: "1.2rem",
                background:
                  systemOverview && systemOverview.flagged_students_count > 0
                    ? "linear-gradient(180deg, #0f172a 0%, rgba(239,68,68,0.06) 100%)"
                    : "#0f172a",
              }}
            >
              <div style={{ fontSize: "0.75rem", color: "#94a3b8", fontWeight: "600", textTransform: "uppercase" }}>
                Manual Reviews Needed
              </div>
              <div
                style={{
                  fontSize: "2rem",
                  fontWeight: "800",
                  color: systemOverview && systemOverview.flagged_students_count > 0 ? "#f87171" : "#10b981",
                  marginTop: "0.4rem",
                }}
              >
                {systemOverview ? systemOverview.flagged_students_count : 0}
              </div>
              <div style={{ fontSize: "0.78rem", color: "#64748b", marginTop: "0.2rem" }}>
                Candidate flagged sessions
              </div>
            </div>
          </div>

          {/* Quick Actions Panel */}
          <div
            style={{
              backgroundColor: "#0f172a",
              borderRadius: "12px",
              border: "1px solid #1e293b",
              padding: "1.2rem 1.5rem",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "1rem",
            }}
          >
            <div>
              <div style={{ fontWeight: "700", fontSize: "1rem", color: "#f8fafc" }}>
                Examination Operations
              </div>
              <div style={{ fontSize: "0.82rem", color: "#94a3b8" }}>
                Draft new question banks or inspect recent student attempts.
              </div>
            </div>
            <div style={{ display: "flex", gap: "0.8rem", flexWrap: "wrap" }}>
              <button
                onClick={() => setActiveTab("create")}
                style={{
                  backgroundColor: "#0284c7",
                  color: "#ffffff",
                  border: "none",
                  borderRadius: "8px",
                  padding: "9px 18px",
                  fontSize: "0.85rem",
                  fontWeight: "700",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  boxShadow: "0 2px 8px rgba(2,132,199,0.3)",
                }}
              >
                <span>➕</span> Create New Examination
              </button>
              <button
                onClick={() => setActiveTab("exams")}
                style={{
                  backgroundColor: "#1e293b",
                  color: "#e2e8f0",
                  border: "1px solid #334155",
                  borderRadius: "8px",
                  padding: "9px 16px",
                  fontSize: "0.85rem",
                  fontWeight: "600",
                  cursor: "pointer",
                }}
              >
                Browse All Exams
              </button>
            </div>
          </div>

          {/* Recent Examinations Table */}
          <div
            style={{
              backgroundColor: "#0f172a",
              borderRadius: "12px",
              border: "1px solid #1e293b",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                padding: "1.2rem 1.5rem",
                borderBottom: "1px solid #1e293b",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <div>
                <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: "700" }}>Recent Examinations</h3>
                <p style={{ margin: 0, fontSize: "0.8rem", color: "#94a3b8" }}>
                  Live assessment statuses and student submission counts
                </p>
              </div>
              <button
                onClick={loadSystemOverview}
                style={{
                  backgroundColor: "transparent",
                  color: "#38bdf8",
                  border: "1px solid #334155",
                  borderRadius: "6px",
                  padding: "6px 12px",
                  fontSize: "0.8rem",
                  cursor: "pointer",
                }}
              >
                🔄 Refresh Metrics
              </button>
            </div>

            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.88rem" }}>
                <thead>
                  <tr style={{ backgroundColor: "#090d16", color: "#64748b", borderBottom: "1px solid #1e293b" }}>
                    <th style={{ padding: "12px 16px", fontWeight: "600" }}>EXAMINATION TITLE</th>
                    <th style={{ padding: "12px 16px", fontWeight: "600" }}>QUESTIONS</th>
                    <th style={{ padding: "12px 16px", fontWeight: "600" }}>DURATION</th>
                    <th style={{ padding: "12px 16px", fontWeight: "600" }}>STATUS</th>
                    <th style={{ padding: "12px 16px", fontWeight: "600" }}>SUBMISSIONS</th>
                    <th style={{ padding: "12px 16px", fontWeight: "600" }}>CREATED</th>
                    <th style={{ padding: "12px 16px", fontWeight: "600", textAlign: "right" }}>ACTIONS</th>
                  </tr>
                </thead>
                <tbody>
                  {(systemOverview?.recent_exams || exams).map((exam) => (
                    <tr
                      key={exam.id}
                      style={{
                        borderBottom: "1px solid #1e293b",
                        transition: "background-color 0.15s ease",
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "rgba(30, 41, 59, 0.4)")}
                      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
                    >
                      <td style={{ padding: "14px 16px" }}>
                        <div style={{ fontWeight: "700", color: "#f8fafc" }}>{exam.title}</div>
                        <div style={{ fontSize: "0.75rem", color: "#64748b", fontFamily: "monospace" }}>
                          ID: {exam.id}
                        </div>
                      </td>
                      <td style={{ padding: "14px 16px", color: "#94a3b8" }}>
                        {exam.questions_count} MCQs ({exam.total_points} pts)
                      </td>
                      <td style={{ padding: "14px 16px", color: "#94a3b8" }}>{exam.duration_minutes} mins</td>
                      <td style={{ padding: "14px 16px" }}>
                        <button
                          onClick={(e) => handleTogglePublish(exam.id, exam.is_published, e)}
                          title="Click to toggle status"
                          style={{
                            padding: "4px 10px",
                            borderRadius: "12px",
                            fontSize: "0.75rem",
                            fontWeight: "700",
                            border: exam.is_published ? "1px solid #10b981" : "1px solid #64748b",
                            backgroundColor: exam.is_published ? "rgba(16, 185, 129, 0.12)" : "rgba(100, 116, 139, 0.12)",
                            color: exam.is_published ? "#34d399" : "#94a3b8",
                            cursor: "pointer",
                          }}
                        >
                          {exam.is_published ? "● Published" : "○ Draft"}
                        </button>
                      </td>
                      <td style={{ padding: "14px 16px" }}>
                        <span
                          style={{
                            backgroundColor: "#1e293b",
                            padding: "4px 10px",
                            borderRadius: "6px",
                            fontWeight: "700",
                            color: "#38bdf8",
                          }}
                        >
                          {exam.submissions_count || 0}
                        </span>
                      </td>
                      <td style={{ padding: "14px 16px", color: "#64748b", fontSize: "0.8rem" }}>
                        {new Date(exam.created_at).toLocaleDateString()}
                      </td>
                      <td style={{ padding: "14px 16px", textAlign: "right" }}>
                        <div style={{ display: "flex", justifyContent: "flex-end", gap: "6px" }}>
                          <button
                            onClick={() => {
                              setSelectedExamId(exam.id);
                              setActiveTab("analytics");
                            }}
                            style={{
                              backgroundColor: "#0284c7",
                              color: "#ffffff",
                              border: "none",
                              borderRadius: "6px",
                              padding: "6px 12px",
                              fontSize: "0.8rem",
                              fontWeight: "600",
                              cursor: "pointer",
                            }}
                          >
                            Submissions
                          </button>
                          <button
                            onClick={() => {
                              setViewingExamDetails(exam);
                              setActiveTab("exams");
                            }}
                            style={{
                              backgroundColor: "#1e293b",
                              color: "#e2e8f0",
                              border: "1px solid #334155",
                              borderRadius: "6px",
                              padding: "6px 10px",
                              fontSize: "0.8rem",
                              cursor: "pointer",
                            }}
                          >
                            Details
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                  {(systemOverview?.recent_exams || exams).length === 0 && (
                    <tr>
                      <td colSpan="7" style={{ padding: "2.5rem", textAlign: "center", color: "#64748b" }}>
                        No examinations created yet. Use the <strong>Exam Builder</strong> to author your first assessment!
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ---------------------------------------------------- */}
      {/* TAB 2: MANAGE EXAMINATIONS */}
      {/* ---------------------------------------------------- */}
      {activeTab === "exams" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          {viewingExamDetails ? (
            /* Detailed Single Exam Inspection */
            <div
              style={{
                backgroundColor: "#0f172a",
                borderRadius: "12px",
                border: "1px solid #1e293b",
                padding: "1.8rem",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "flex-start",
                  borderBottom: "1px solid #1e293b",
                  paddingBottom: "1.2rem",
                  marginBottom: "1.5rem",
                  flexWrap: "wrap",
                  gap: "1rem",
                }}
              >
                <div>
                  <button
                    onClick={() => setViewingExamDetails(null)}
                    style={{
                      background: "none",
                      border: "none",
                      color: "#38bdf8",
                      fontSize: "0.85rem",
                      cursor: "pointer",
                      padding: 0,
                      marginBottom: "0.5rem",
                      fontWeight: "600",
                    }}
                  >
                    ← Back to All Examinations
                  </button>
                  <h2 style={{ margin: 0, fontSize: "1.5rem", fontWeight: "800" }}>{viewingExamDetails.title}</h2>
                  <p style={{ margin: "0.3rem 0 0 0", color: "#94a3b8", fontSize: "0.88rem" }}>
                    {viewingExamDetails.description}
                  </p>
                </div>
                <div style={{ display: "flex", gap: "0.8rem", alignItems: "center" }}>
                  <button
                    onClick={(e) =>
                      handleTogglePublish(viewingExamDetails.id, viewingExamDetails.is_published, e)
                    }
                    style={{
                      padding: "8px 16px",
                      borderRadius: "8px",
                      fontSize: "0.85rem",
                      fontWeight: "700",
                      border: viewingExamDetails.is_published ? "1px solid #10b981" : "1px solid #64748b",
                      backgroundColor: viewingExamDetails.is_published
                        ? "rgba(16, 185, 129, 0.15)"
                        : "rgba(100, 116, 139, 0.15)",
                      color: viewingExamDetails.is_published ? "#34d399" : "#94a3b8",
                      cursor: "pointer",
                    }}
                  >
                    {viewingExamDetails.is_published ? "● Active (Published)" : "○ Inactive (Draft)"}
                  </button>
                  <button
                    onClick={() => {
                      setSelectedExamId(viewingExamDetails.id);
                      setActiveTab("analytics");
                    }}
                    style={{
                      backgroundColor: "#0284c7",
                      color: "#ffffff",
                      border: "none",
                      borderRadius: "8px",
                      padding: "8px 16px",
                      fontSize: "0.85rem",
                      fontWeight: "700",
                      cursor: "pointer",
                    }}
                  >
                    View Submissions
                  </button>
                </div>
              </div>

              {/* Sub-navigation inside Exam Details */}
              <div style={{ display: "flex", gap: "1rem", borderBottom: "1px solid #1e293b", marginBottom: "1.5rem" }}>
                <button
                  onClick={() => setExamDetailSubTab("overview")}
                  style={{
                    padding: "8px 14px",
                    background: "none",
                    border: "none",
                    borderBottom: examDetailSubTab === "overview" ? "2px solid #0284c7" : "2px solid transparent",
                    color: examDetailSubTab === "overview" ? "#38bdf8" : "#94a3b8",
                    fontWeight: examDetailSubTab === "overview" ? "700" : "500",
                    cursor: "pointer",
                    fontSize: "0.9rem",
                  }}
                >
                  Overview & Configuration
                </button>
                <button
                  onClick={() => setExamDetailSubTab("questions")}
                  style={{
                    padding: "8px 14px",
                    background: "none",
                    border: "none",
                    borderBottom: examDetailSubTab === "questions" ? "2px solid #0284c7" : "2px solid transparent",
                    color: examDetailSubTab === "questions" ? "#38bdf8" : "#94a3b8",
                    fontWeight: examDetailSubTab === "questions" ? "700" : "500",
                    cursor: "pointer",
                    fontSize: "0.9rem",
                  }}
                >
                  Question Bank ({viewingExamDetails.questions?.length || viewingExamDetails.questions_count})
                </button>
              </div>

              {/* Exam Sub-tab Content */}
              {examDetailSubTab === "overview" && (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
                  <div
                    style={{
                      backgroundColor: "#090d16",
                      border: "1px solid #1e293b",
                      borderRadius: "10px",
                      padding: "1.2rem",
                    }}
                  >
                    <div style={{ fontSize: "0.78rem", fontWeight: "700", color: "#64748b", textTransform: "uppercase" }}>
                      Examination Parameters
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.8rem", marginTop: "1rem" }}>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span style={{ color: "#94a3b8" }}>Exam ID:</span>
                        <span style={{ fontFamily: "monospace", color: "#e2e8f0" }}>{viewingExamDetails.id}</span>
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span style={{ color: "#94a3b8" }}>Allocated Duration:</span>
                        <span style={{ fontWeight: "700", color: "#e2e8f0" }}>
                          {viewingExamDetails.duration_minutes} Minutes
                        </span>
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span style={{ color: "#94a3b8" }}>Total Questions:</span>
                        <span style={{ fontWeight: "700", color: "#e2e8f0" }}>
                          {viewingExamDetails.questions?.length || viewingExamDetails.questions_count} MCQs
                        </span>
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span style={{ color: "#94a3b8" }}>Total Max Marks:</span>
                        <span style={{ fontWeight: "700", color: "#10b981" }}>
                          {viewingExamDetails.total_points} Points
                        </span>
                      </div>
                    </div>
                  </div>

                  <div
                    style={{
                      backgroundColor: "#090d16",
                      border: "1px solid #1e293b",
                      borderRadius: "10px",
                      padding: "1.2rem",
                    }}
                  >
                    <div style={{ fontSize: "0.78rem", fontWeight: "700", color: "#64748b", textTransform: "uppercase" }}>
                      Proctoring & Student Instructions
                    </div>
                    <div
                      style={{
                        marginTop: "1rem",
                        fontSize: "0.85rem",
                        color: "#cbd5e1",
                        lineHeight: "1.6",
                        whiteSpace: "pre-line",
                      }}
                    >
                      {viewingExamDetails.instructions ||
                        "Standard AI Multimodal Proctoring guidelines apply. Webcam and microphone required."}
                    </div>
                  </div>
                </div>
              )}

              {examDetailSubTab === "questions" && (
                <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                  {(viewingExamDetails.questions || []).map((q, idx) => (
                    <div
                      key={q.id || idx}
                      style={{
                        backgroundColor: "#090d16",
                        border: "1px solid #1e293b",
                        borderRadius: "10px",
                        padding: "1.2rem",
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          marginBottom: "0.8rem",
                        }}
                      >
                        <span style={{ fontWeight: "700", color: "#38bdf8", fontSize: "0.95rem" }}>
                          Question #{idx + 1}
                        </span>
                        <span
                          style={{
                            backgroundColor: "rgba(2, 132, 199, 0.15)",
                            color: "#38bdf8",
                            padding: "3px 8px",
                            borderRadius: "6px",
                            fontSize: "0.75rem",
                            fontWeight: "700",
                          }}
                        >
                          {q.points} Points
                        </span>
                      </div>

                      <div style={{ fontSize: "0.95rem", color: "#f8fafc", marginBottom: "1rem" }}>
                        {q.question_text}
                      </div>

                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.6rem" }}>
                        {q.options.map((opt, optIdx) => {
                          const isCorrect = optIdx === q.correct_option_index;
                          return (
                            <div
                              key={optIdx}
                              style={{
                                padding: "8px 12px",
                                borderRadius: "6px",
                                fontSize: "0.85rem",
                                border: isCorrect ? "1px solid #10b981" : "1px solid #1e293b",
                                backgroundColor: isCorrect ? "rgba(16, 185, 129, 0.12)" : "#0f172a",
                                color: isCorrect ? "#34d399" : "#94a3b8",
                                display: "flex",
                                alignItems: "center",
                                gap: "8px",
                              }}
                            >
                              <span style={{ fontWeight: "700" }}>{String.fromCharCode(65 + optIdx)}.</span>
                              <span style={{ flex: 1 }}>{opt}</span>
                              {isCorrect && (
                                <span style={{ fontSize: "0.7rem", fontWeight: "700", color: "#10b981" }}>
                                  ✓ ANSWER KEY
                                </span>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            /* Examinations Catalog Grid */
            <div>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "1.2rem",
                }}
              >
                <div>
                  <h2 style={{ margin: 0, fontSize: "1.3rem", fontWeight: "700" }}>All Registered Examinations</h2>
                  <p style={{ margin: 0, fontSize: "0.82rem", color: "#94a3b8" }}>
                    Select an exam to view its question bank, adjust publish status, or review analytics.
                  </p>
                </div>
                <button
                  onClick={() => setActiveTab("create")}
                  style={{
                    backgroundColor: "#0284c7",
                    color: "#ffffff",
                    border: "none",
                    borderRadius: "8px",
                    padding: "8px 16px",
                    fontSize: "0.85rem",
                    fontWeight: "700",
                    cursor: "pointer",
                  }}
                >
                  ➕ Author New Exam
                </button>
              </div>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))",
                  gap: "1.2rem",
                }}
              >
                {exams.map((ex) => (
                  <div
                    key={ex.id}
                    style={{
                      backgroundColor: "#0f172a",
                      border: "1px solid #1e293b",
                      borderRadius: "12px",
                      padding: "1.4rem",
                      display: "flex",
                      flexDirection: "column",
                      justifyContent: "space-between",
                      transition: "transform 0.15s ease, border-color 0.15s ease",
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.borderColor = "#38bdf8")}
                    onMouseLeave={(e) => (e.currentTarget.style.borderColor = "#1e293b")}
                  >
                    <div>
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "flex-start",
                          marginBottom: "0.8rem",
                        }}
                      >
                        <span
                          style={{
                            padding: "3px 8px",
                            borderRadius: "12px",
                            fontSize: "0.72rem",
                            fontWeight: "700",
                            border: ex.is_published ? "1px solid #10b981" : "1px solid #64748b",
                            backgroundColor: ex.is_published
                              ? "rgba(16, 185, 129, 0.12)"
                              : "rgba(100, 116, 139, 0.12)",
                            color: ex.is_published ? "#34d399" : "#94a3b8",
                          }}
                        >
                          {ex.is_published ? "● Published" : "○ Draft"}
                        </span>
                        <span style={{ fontSize: "0.75rem", color: "#64748b", fontFamily: "monospace" }}>
                          {ex.id}
                        </span>
                      </div>

                      <h3 style={{ margin: "0 0 0.4rem 0", fontSize: "1.1rem", fontWeight: "700", color: "#f8fafc" }}>
                        {ex.title}
                      </h3>
                      <p
                        style={{
                          margin: 0,
                          fontSize: "0.82rem",
                          color: "#94a3b8",
                          lineHeight: "1.5",
                          minHeight: "2.4rem",
                        }}
                      >
                        {ex.description || "Standard MCQ examination."}
                      </p>

                      <div
                        style={{
                          display: "flex",
                          gap: "1rem",
                          marginTop: "1.2rem",
                          paddingTop: "0.8rem",
                          borderTop: "1px solid #1e293b",
                          fontSize: "0.8rem",
                          color: "#64748b",
                        }}
                      >
                        <div>
                          ⏱️ <strong style={{ color: "#e2e8f0" }}>{ex.duration_minutes}</strong> mins
                        </div>
                        <div>
                          ❓ <strong style={{ color: "#e2e8f0" }}>{ex.questions_count}</strong> MCQs
                        </div>
                        <div>
                          🏆 <strong style={{ color: "#10b981" }}>{ex.total_points}</strong> pts
                        </div>
                      </div>
                    </div>

                    <div
                      style={{
                        display: "flex",
                        gap: "0.6rem",
                        marginTop: "1.2rem",
                        borderTop: "1px solid #1e293b",
                        paddingTop: "0.8rem",
                      }}
                    >
                      <button
                        onClick={() => setViewingExamDetails(ex)}
                        style={{
                          flex: 1,
                          backgroundColor: "#1e293b",
                          color: "#e2e8f0",
                          border: "1px solid #334155",
                          borderRadius: "7px",
                          padding: "8px",
                          fontSize: "0.82rem",
                          fontWeight: "600",
                          cursor: "pointer",
                        }}
                      >
                        Inspect Details
                      </button>
                      <button
                        onClick={() => {
                          setSelectedExamId(ex.id);
                          setActiveTab("analytics");
                        }}
                        style={{
                          flex: 1,
                          backgroundColor: "#0284c7",
                          color: "#ffffff",
                          border: "none",
                          borderRadius: "7px",
                          padding: "8px",
                          fontSize: "0.82rem",
                          fontWeight: "700",
                          cursor: "pointer",
                        }}
                      >
                        Submissions
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ---------------------------------------------------- */}
      {/* TAB 3: COMPLETE EXAMINATION BUILDER */}
      {/* ---------------------------------------------------- */}
      {activeTab === "create" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          {/* Builder Step Header */}
          <div
            style={{
              backgroundColor: "#0f172a",
              border: "1px solid #1e293b",
              borderRadius: "12px",
              padding: "1.2rem 1.6rem",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "1rem",
            }}
          >
            <div>
              <h2 style={{ margin: 0, fontSize: "1.25rem", fontWeight: "800" }}>Examination Creator Studio</h2>
              <p style={{ margin: 0, fontSize: "0.82rem", color: "#94a3b8" }}>
                Step {builderStep} of 4 — {builderStep === 1 && "Basic Configuration & Rules"}
                {builderStep === 2 && "Question Builder & Answer Keys"}
                {builderStep === 3 && "Student Interface Preview"}
                {builderStep === 4 && "Final Review & Publish"}
              </p>
            </div>

            {/* Stepper pills */}
            <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
              {[
                { step: 1, label: "1. Config" },
                { step: 2, label: "2. Questions" },
                { step: 3, label: "3. Preview" },
                { step: 4, label: "4. Publish" },
              ].map((s) => (
                <button
                  key={s.step}
                  onClick={() => setBuilderStep(s.step)}
                  style={{
                    backgroundColor: builderStep === s.step ? "#0284c7" : "#1e293b",
                    color: builderStep === s.step ? "#ffffff" : "#94a3b8",
                    border: "none",
                    borderRadius: "20px",
                    padding: "6px 14px",
                    fontSize: "0.8rem",
                    fontWeight: "700",
                    cursor: "pointer",
                  }}
                >
                  {s.label}
                </button>
              ))}
              <button
                onClick={handleLoadSample}
                style={{
                  backgroundColor: "rgba(16, 185, 129, 0.15)",
                  color: "#34d399",
                  border: "1px solid #10b981",
                  borderRadius: "20px",
                  padding: "6px 14px",
                  fontSize: "0.8rem",
                  fontWeight: "700",
                  cursor: "pointer",
                  marginLeft: "8px",
                }}
              >
                ⚡ Load Sample Exam
              </button>
            </div>
          </div>

          {/* Builder Step 1: Basic Information */}
          {builderStep === 1 && (
            <div
              style={{
                backgroundColor: "#0f172a",
                border: "1px solid #1e293b",
                borderRadius: "12px",
                padding: "2rem",
                display: "flex",
                flexDirection: "column",
                gap: "1.5rem",
              }}
            >
              <div>
                <label style={{ display: "block", fontSize: "0.88rem", fontWeight: "700", marginBottom: "0.5rem" }}>
                  Examination Title <span style={{ color: "#f87171" }}>*</span>
                </label>
                <input
                  type="text"
                  value={examTitle}
                  onChange={(e) => setExamTitle(e.target.value)}
                  placeholder="e.g. Machine Learning & Deep Learning Midterm Examination"
                  style={{
                    width: "100%",
                    backgroundColor: "#090d16",
                    border: "1px solid #334155",
                    borderRadius: "8px",
                    padding: "10px 14px",
                    color: "#f8fafc",
                    fontSize: "0.95rem",
                    boxSizing: "border-box",
                  }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.88rem", fontWeight: "700", marginBottom: "0.5rem" }}>
                  Description / Topic Scope
                </label>
                <input
                  type="text"
                  value={examDesc}
                  onChange={(e) => setExamDesc(e.target.value)}
                  placeholder="e.g. Official multiple choice assessment covering computer vision, temporal networks, and ethics."
                  style={{
                    width: "100%",
                    backgroundColor: "#090d16",
                    border: "1px solid #334155",
                    borderRadius: "8px",
                    padding: "10px 14px",
                    color: "#f8fafc",
                    fontSize: "0.95rem",
                    boxSizing: "border-box",
                  }}
                />
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
                <div>
                  <label style={{ display: "block", fontSize: "0.88rem", fontWeight: "700", marginBottom: "0.5rem" }}>
                    Duration (Minutes)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="180"
                    value={examDuration}
                    onChange={(e) => setExamDuration(e.target.value)}
                    style={{
                      width: "100%",
                      backgroundColor: "#090d16",
                      border: "1px solid #334155",
                      borderRadius: "8px",
                      padding: "10px 14px",
                      color: "#f8fafc",
                      fontSize: "0.95rem",
                      boxSizing: "border-box",
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: "block", fontSize: "0.88rem", fontWeight: "700", marginBottom: "0.5rem" }}>
                    Publication Visibility
                  </label>
                  <div
                    onClick={() => setExamIsPublished(!examIsPublished)}
                    style={{
                      backgroundColor: "#090d16",
                      border: "1px solid #334155",
                      borderRadius: "8px",
                      padding: "10px 14px",
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: "10px",
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={examIsPublished}
                      onChange={(e) => setExamIsPublished(e.target.checked)}
                      style={{ cursor: "pointer" }}
                    />
                    <span style={{ fontSize: "0.9rem", color: examIsPublished ? "#34d399" : "#94a3b8" }}>
                      {examIsPublished ? "Publish immediately to Student Lobby" : "Save as Draft (hidden from students)"}
                    </span>
                  </div>
                </div>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.88rem", fontWeight: "700", marginBottom: "0.5rem" }}>
                  Examination Instructions for Students
                </label>
                <textarea
                  rows="4"
                  value={examInstructions}
                  onChange={(e) => setExamInstructions(e.target.value)}
                  style={{
                    width: "100%",
                    backgroundColor: "#090d16",
                    border: "1px solid #334155",
                    borderRadius: "8px",
                    padding: "10px 14px",
                    color: "#f8fafc",
                    fontSize: "0.9rem",
                    lineHeight: "1.5",
                    boxSizing: "border-box",
                  }}
                />
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end" }}>
                <button
                  onClick={() => setBuilderStep(2)}
                  style={{
                    backgroundColor: "#0284c7",
                    color: "#ffffff",
                    border: "none",
                    borderRadius: "8px",
                    padding: "10px 24px",
                    fontSize: "0.9rem",
                    fontWeight: "700",
                    cursor: "pointer",
                  }}
                >
                  Proceed to Question Builder →
                </button>
              </div>
            </div>
          )}

          {/* Builder Step 2: Question Builder */}
          {builderStep === 2 && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              {/* Question Summary Bar */}
              <div
                style={{
                  backgroundColor: "#0f172a",
                  border: "1px solid #1e293b",
                  borderRadius: "10px",
                  padding: "1rem 1.4rem",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  flexWrap: "wrap",
                  gap: "1rem",
                }}
              >
                <div style={{ display: "flex", gap: "1.5rem", alignItems: "center" }}>
                  <div>
                    <span style={{ fontSize: "0.78rem", color: "#64748b" }}>TOTAL QUESTIONS: </span>
                    <strong style={{ color: "#38bdf8", fontSize: "1.1rem" }}>{questions.length}</strong>
                  </div>
                  <div>
                    <span style={{ fontSize: "0.78rem", color: "#64748b" }}>TOTAL POINTS: </span>
                    <strong style={{ color: "#10b981", fontSize: "1.1rem" }}>{totalBuilderPoints} pts</strong>
                  </div>
                  <div>
                    <span style={{ fontSize: "0.78rem", color: "#64748b" }}>EST. TIME: </span>
                    <strong style={{ color: "#e2e8f0", fontSize: "1.1rem" }}>{examDuration} mins</strong>
                  </div>
                </div>

                <button
                  onClick={handleAddQuestion}
                  style={{
                    backgroundColor: "#0284c7",
                    color: "#ffffff",
                    border: "none",
                    borderRadius: "7px",
                    padding: "8px 16px",
                    fontSize: "0.85rem",
                    fontWeight: "700",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                  }}
                >
                  <span>➕</span> Add New Question
                </button>
              </div>

              {/* Questions List */}
              {questions.map((q, qIdx) => (
                <div
                  key={q.id || qIdx}
                  style={{
                    backgroundColor: "#0f172a",
                    border: "1px solid #1e293b",
                    borderRadius: "12px",
                    padding: "1.5rem",
                  }}
                >
                  {/* Question Header */}
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      borderBottom: "1px solid #1e293b",
                      paddingBottom: "0.8rem",
                      marginBottom: "1rem",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <span
                        style={{
                          backgroundColor: "#0284c7",
                          color: "#ffffff",
                          width: "28px",
                          height: "28px",
                          borderRadius: "50%",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          fontWeight: "800",
                          fontSize: "0.85rem",
                        }}
                      >
                        {qIdx + 1}
                      </span>
                      <span style={{ fontWeight: "700", color: "#f8fafc", fontSize: "0.95rem" }}>
                        Question #{qIdx + 1}
                      </span>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        <span style={{ fontSize: "0.8rem", color: "#94a3b8" }}>Marks:</span>
                        <input
                          type="number"
                          min="1"
                          max="20"
                          value={q.points}
                          onChange={(e) => handleQuestionChange(qIdx, "points", Number(e.target.value))}
                          style={{
                            width: "55px",
                            backgroundColor: "#090d16",
                            border: "1px solid #334155",
                            borderRadius: "6px",
                            padding: "4px 8px",
                            color: "#10b981",
                            fontWeight: "700",
                            fontSize: "0.85rem",
                            textAlign: "center",
                          }}
                        />
                      </div>
                      <button
                        onClick={() => handleDuplicateQuestion(qIdx)}
                        title="Duplicate question"
                        style={{
                          backgroundColor: "#1e293b",
                          color: "#94a3b8",
                          border: "1px solid #334155",
                          borderRadius: "6px",
                          padding: "4px 8px",
                          fontSize: "0.75rem",
                          cursor: "pointer",
                        }}
                      >
                        📋 Duplicate
                      </button>
                      <button
                        onClick={() => handleRemoveQuestion(qIdx)}
                        title="Delete question"
                        style={{
                          backgroundColor: "rgba(239, 68, 68, 0.15)",
                          color: "#f87171",
                          border: "1px solid #ef4444",
                          borderRadius: "6px",
                          padding: "4px 8px",
                          fontSize: "0.75rem",
                          cursor: "pointer",
                        }}
                      >
                        ✕ Delete
                      </button>
                    </div>
                  </div>

                  {/* Question Prompt Input */}
                  <div style={{ marginBottom: "1.2rem" }}>
                    <label style={{ display: "block", fontSize: "0.8rem", color: "#94a3b8", marginBottom: "0.3rem" }}>
                      QUESTION PROMPT:
                    </label>
                    <textarea
                      rows="2"
                      value={q.question_text}
                      onChange={(e) => handleQuestionChange(qIdx, "question_text", e.target.value)}
                      placeholder="Enter the question text here..."
                      style={{
                        width: "100%",
                        backgroundColor: "#090d16",
                        border: "1px solid #334155",
                        borderRadius: "8px",
                        padding: "10px 14px",
                        color: "#f8fafc",
                        fontSize: "0.95rem",
                        boxSizing: "border-box",
                      }}
                    />
                  </div>

                  {/* 4 MCQ Options */}
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.8rem" }}>
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        flexWrap: "wrap",
                        gap: "0.6rem",
                        backgroundColor: "#090d16",
                        border: "1px solid #1e293b",
                        borderRadius: "8px",
                        padding: "8px 12px",
                      }}
                    >
                      <div>
                        <span style={{ fontSize: "0.8rem", color: "#38bdf8", fontWeight: "700" }}>
                          SELECT CORRECT ANSWER KEY:
                        </span>
                        <div style={{ fontSize: "0.72rem", color: "#64748b" }}>
                          Choose which option (A, B, C, or D) is the correct answer for student evaluation.
                        </div>
                      </div>
                      <div style={{ display: "flex", gap: "6px" }}>
                        {["A", "B", "C", "D"].map((letter, optIdx) => {
                          const isSelected = q.correct_option_index === optIdx;
                          return (
                            <button
                              key={letter}
                              type="button"
                              onClick={() => handleQuestionChange(qIdx, "correct_option_index", optIdx)}
                              style={{
                                padding: "6px 14px",
                                borderRadius: "6px",
                                border: isSelected ? "2px solid #10b981" : "1px solid #334155",
                                backgroundColor: isSelected ? "#10b981" : "#0f172a",
                                color: isSelected ? "#ffffff" : "#94a3b8",
                                fontWeight: "800",
                                fontSize: "0.82rem",
                                cursor: "pointer",
                                boxShadow: isSelected ? "0 0 10px rgba(16, 185, 129, 0.4)" : "none",
                                transition: "all 0.15s ease",
                              }}
                            >
                              {isSelected ? `✓ Option ${letter}` : `Option ${letter}`}
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    {q.options.map((opt, optIdx) => {
                      const isCorrect = q.correct_option_index === optIdx;
                      return (
                        <div
                          key={optIdx}
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "10px",
                            backgroundColor: isCorrect ? "rgba(16, 185, 129, 0.08)" : "#090d16",
                            border: isCorrect ? "1px solid #10b981" : "1px solid #1e293b",
                            borderRadius: "8px",
                            padding: "8px 12px",
                            transition: "all 0.15s ease",
                          }}
                        >
                          <input
                            type="radio"
                            name={`correct_opt_${qIdx}`}
                            checked={isCorrect}
                            onChange={() => handleQuestionChange(qIdx, "correct_option_index", optIdx)}
                            style={{ cursor: "pointer", width: "18px", height: "18px", accentColor: "#10b981" }}
                          />
                          <button
                            type="button"
                            onClick={() => handleQuestionChange(qIdx, "correct_option_index", optIdx)}
                            title="Click to set this option as the correct answer key"
                            style={{
                              background: isCorrect ? "#10b981" : "#1e293b",
                              border: isCorrect ? "1px solid #10b981" : "1px solid #334155",
                              color: isCorrect ? "#ffffff" : "#94a3b8",
                              borderRadius: "4px",
                              padding: "2px 8px",
                              fontWeight: "800",
                              fontSize: "0.82rem",
                              cursor: "pointer",
                            }}
                          >
                            {String.fromCharCode(65 + optIdx)}.
                          </button>
                          <input
                            type="text"
                            value={opt}
                            onChange={(e) => handleOptionChange(qIdx, optIdx, e.target.value)}
                            placeholder={`Option ${String.fromCharCode(65 + optIdx)} text...`}
                            style={{
                              flex: 1,
                              backgroundColor: "transparent",
                              border: "none",
                              color: isCorrect ? "#34d399" : "#e2e8f0",
                              fontSize: "0.9rem",
                              outline: "none",
                            }}
                          />
                          {isCorrect ? (
                            <span
                              style={{
                                backgroundColor: "rgba(16, 185, 129, 0.2)",
                                color: "#10b981",
                                fontSize: "0.72rem",
                                fontWeight: "800",
                                padding: "4px 10px",
                                borderRadius: "4px",
                                border: "1px solid rgba(16, 185, 129, 0.4)",
                              }}
                            >
                              ✓ CORRECT ANSWER KEY
                            </span>
                          ) : (
                            <button
                              type="button"
                              onClick={() => handleQuestionChange(qIdx, "correct_option_index", optIdx)}
                              style={{
                                backgroundColor: "transparent",
                                color: "#64748b",
                                border: "1px dashed #334155",
                                borderRadius: "4px",
                                padding: "3px 8px",
                                fontSize: "0.72rem",
                                cursor: "pointer",
                              }}
                              onMouseEnter={(e) => {
                                e.currentTarget.style.color = "#38bdf8";
                                e.currentTarget.style.borderColor = "#38bdf8";
                              }}
                              onMouseLeave={(e) => {
                                e.currentTarget.style.color = "#64748b";
                                e.currentTarget.style.borderColor = "#334155";
                              }}
                            >
                              Set as Correct
                            </button>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <button
                  onClick={handleAddQuestion}
                  style={{
                    backgroundColor: "#1e293b",
                    color: "#38bdf8",
                    border: "1px solid #334155",
                    borderRadius: "8px",
                    padding: "10px 20px",
                    fontSize: "0.9rem",
                    fontWeight: "700",
                    cursor: "pointer",
                  }}
                >
                  ➕ Add Another Question
                </button>

                <div style={{ display: "flex", gap: "10px" }}>
                  <button
                    onClick={() => setBuilderStep(1)}
                    style={{
                      backgroundColor: "transparent",
                      color: "#94a3b8",
                      border: "1px solid #334155",
                      borderRadius: "8px",
                      padding: "10px 18px",
                      fontSize: "0.9rem",
                      cursor: "pointer",
                    }}
                  >
                    ← Back to Config
                  </button>
                  <button
                    onClick={() => setBuilderStep(3)}
                    style={{
                      backgroundColor: "#0284c7",
                      color: "#ffffff",
                      border: "none",
                      borderRadius: "8px",
                      padding: "10px 24px",
                      fontSize: "0.9rem",
                      fontWeight: "700",
                      cursor: "pointer",
                    }}
                  >
                    Preview Examination →
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Builder Step 3: Student Preview Mode */}
          {builderStep === 3 && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              <div
                style={{
                  backgroundColor: "#0f172a",
                  border: "1px solid #1e293b",
                  borderRadius: "12px",
                  padding: "1.2rem 1.6rem",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <div>
                  <h3 style={{ margin: 0, fontSize: "1.1rem", fontWeight: "700" }}>Student Examination View Preview</h3>
                  <p style={{ margin: 0, fontSize: "0.82rem", color: "#94a3b8" }}>
                    This accurately simulates how students will perceive the assessment layout.
                  </p>
                </div>
                <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
                  <label
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                      fontSize: "0.85rem",
                      color: "#94a3b8",
                      cursor: "pointer",
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={previewShowAnswers}
                      onChange={(e) => setPreviewShowAnswers(e.target.checked)}
                    />
                    Highlight Teacher Answer Keys
                  </label>
                  <button
                    onClick={() => setBuilderStep(4)}
                    style={{
                      backgroundColor: "#0284c7",
                      color: "#ffffff",
                      border: "none",
                      borderRadius: "8px",
                      padding: "8px 18px",
                      fontSize: "0.85rem",
                      fontWeight: "700",
                      cursor: "pointer",
                    }}
                  >
                    Proceed to Publish →
                  </button>
                </div>
              </div>

              {/* Simulated Student Exam Container */}
              <div
                style={{
                  backgroundColor: "#020617",
                  border: "2px dashed #334155",
                  borderRadius: "14px",
                  padding: "2rem",
                }}
              >
                <div
                  style={{
                    borderBottom: "1px solid #1e293b",
                    paddingBottom: "1rem",
                    marginBottom: "1.5rem",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                      <span
                        style={{
                          backgroundColor: "#0284c7",
                          color: "#ffffff",
                          fontSize: "0.72rem",
                          fontWeight: "800",
                          padding: "3px 8px",
                          borderRadius: "4px",
                        }}
                      >
                        AI-MONITORED EXAMINATION
                      </span>
                      <h2 style={{ margin: "0.5rem 0 0 0", fontSize: "1.4rem" }}>
                        {examTitle || "Untitled Examination"}
                      </h2>
                    </div>
                    <div
                      style={{
                        backgroundColor: "#0f172a",
                        border: "1px solid #1e293b",
                        borderRadius: "8px",
                        padding: "8px 14px",
                        fontFamily: "monospace",
                        color: "#38bdf8",
                        fontWeight: "700",
                      }}
                    >
                      ⏱️ {examDuration}:00 Remaining
                    </div>
                  </div>
                </div>

                {/* Questions Preview List */}
                <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
                  {questions.map((q, idx) => (
                    <div
                      key={idx}
                      style={{
                        backgroundColor: "#0f172a",
                        border: "1px solid #1e293b",
                        borderRadius: "10px",
                        padding: "1.4rem",
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          marginBottom: "0.8rem",
                        }}
                      >
                        <span style={{ color: "#38bdf8", fontWeight: "700", fontSize: "0.9rem" }}>
                          Question {idx + 1} of {questions.length}
                        </span>
                        <span style={{ color: "#94a3b8", fontSize: "0.8rem" }}>{q.points} Points</span>
                      </div>

                      <div style={{ fontSize: "1rem", fontWeight: "600", marginBottom: "1.2rem" }}>
                        {q.question_text || <em>[No question text provided]</em>}
                      </div>

                      <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
                        {q.options.map((opt, optIdx) => {
                          const isKey = previewShowAnswers && optIdx === q.correct_option_index;
                          return (
                            <div
                              key={optIdx}
                              style={{
                                padding: "12px 16px",
                                borderRadius: "8px",
                                border: isKey ? "1px solid #10b981" : "1px solid #334155",
                                backgroundColor: isKey ? "rgba(16, 185, 129, 0.12)" : "#090d16",
                                color: isKey ? "#34d399" : "#e2e8f0",
                                display: "flex",
                                alignItems: "center",
                                gap: "12px",
                              }}
                            >
                              <div
                                style={{
                                  width: "20px",
                                  height: "20px",
                                  borderRadius: "50%",
                                  border: "2px solid #64748b",
                                }}
                              />
                              <span style={{ fontWeight: "700" }}>{String.fromCharCode(65 + optIdx)}.</span>
                              <span style={{ flex: 1 }}>{opt || <em>[Empty option]</em>}</span>
                              {isKey && (
                                <span style={{ fontSize: "0.75rem", fontWeight: "800", color: "#10b981" }}>
                                  ✓ ANSWER KEY
                                </span>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <button
                  onClick={() => setBuilderStep(2)}
                  style={{
                    backgroundColor: "transparent",
                    color: "#94a3b8",
                    border: "1px solid #334155",
                    borderRadius: "8px",
                    padding: "10px 20px",
                    fontSize: "0.9rem",
                    cursor: "pointer",
                  }}
                >
                  ← Back to Editor
                </button>
                <button
                  onClick={() => setBuilderStep(4)}
                  style={{
                    backgroundColor: "#0284c7",
                    color: "#ffffff",
                    border: "none",
                    borderRadius: "8px",
                    padding: "10px 26px",
                    fontSize: "0.9rem",
                    fontWeight: "700",
                    cursor: "pointer",
                  }}
                >
                  Confirm & Review Final Assessment →
                </button>
              </div>
            </div>
          )}

          {/* Builder Step 4: Final Review & Publish */}
          {builderStep === 4 && (
            <div
              style={{
                backgroundColor: "#0f172a",
                border: "1px solid #1e293b",
                borderRadius: "12px",
                padding: "2rem",
                display: "flex",
                flexDirection: "column",
                gap: "1.8rem",
              }}
            >
              <div>
                <h3 style={{ margin: 0, fontSize: "1.25rem", fontWeight: "800" }}>Final Examination Verification</h3>
                <p style={{ margin: "0.2rem 0 0 0", color: "#94a3b8", fontSize: "0.85rem" }}>
                  Verify that all questions have assigned answer keys and points before publishing to the student lobby.
                </p>
              </div>

              <div
                style={{
                  backgroundColor: "#090d16",
                  border: "1px solid #1e293b",
                  borderRadius: "10px",
                  padding: "1.4rem",
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                  gap: "1.2rem",
                }}
              >
                <div>
                  <div style={{ fontSize: "0.75rem", color: "#64748b", textTransform: "uppercase" }}>EXAM TITLE</div>
                  <div style={{ fontWeight: "700", fontSize: "1.1rem", color: "#f8fafc", marginTop: "0.2rem" }}>
                    {examTitle || "—"}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: "0.75rem", color: "#64748b", textTransform: "uppercase" }}>TOTAL QUESTIONS</div>
                  <div style={{ fontWeight: "700", fontSize: "1.1rem", color: "#38bdf8", marginTop: "0.2rem" }}>
                    {questions.length} MCQs
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: "0.75rem", color: "#64748b", textTransform: "uppercase" }}>TOTAL POINTS</div>
                  <div style={{ fontWeight: "700", fontSize: "1.1rem", color: "#10b981", marginTop: "0.2rem" }}>
                    {totalBuilderPoints} Points
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: "0.75rem", color: "#64748b", textTransform: "uppercase" }}>DURATION</div>
                  <div style={{ fontWeight: "700", fontSize: "1.1rem", color: "#e2e8f0", marginTop: "0.2rem" }}>
                    {examDuration} Minutes
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: "0.75rem", color: "#64748b", textTransform: "uppercase" }}>LOBBY VISIBILITY</div>
                  <div
                    style={{
                      fontWeight: "700",
                      fontSize: "1.1rem",
                      color: examIsPublished ? "#34d399" : "#f59e0b",
                      marginTop: "0.2rem",
                    }}
                  >
                    {examIsPublished ? "Published (Visible)" : "Draft (Hidden)"}
                  </div>
                </div>
              </div>

              {/* Publish Result Success Card */}
              {publishedExamResult && (
                <div
                  style={{
                    backgroundColor: "rgba(16, 185, 129, 0.12)",
                    border: "1px solid #10b981",
                    borderRadius: "10px",
                    padding: "1.5rem",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    flexWrap: "wrap",
                    gap: "1rem",
                  }}
                >
                  <div>
                    <div style={{ fontWeight: "800", color: "#34d399", fontSize: "1.1rem" }}>
                      ✓ Examination Published Successfully!
                    </div>
                    <div style={{ fontSize: "0.85rem", color: "#e2e8f0", marginTop: "0.3rem" }}>
                      Unique Examination ID:{" "}
                      <code style={{ backgroundColor: "#020617", padding: "2px 8px", borderRadius: "4px" }}>
                        {publishedExamResult.id}
                      </code>
                    </div>
                  </div>
                  <div style={{ display: "flex", gap: "10px" }}>
                    <button
                      onClick={() => {
                        setSelectedExamId(publishedExamResult.id);
                        setActiveTab("analytics");
                        setPublishedExamResult(null);
                      }}
                      style={{
                        backgroundColor: "#0284c7",
                        color: "#ffffff",
                        border: "none",
                        borderRadius: "7px",
                        padding: "8px 16px",
                        fontSize: "0.85rem",
                        fontWeight: "700",
                        cursor: "pointer",
                      }}
                    >
                      View Live Analytics
                    </button>
                    <button
                      onClick={() => {
                        setPublishedExamResult(null);
                        setExamTitle("");
                        setExamDesc("");
                        setQuestions([
                          {
                            id: "q_1",
                            question_text: "",
                            options: ["", "", "", ""],
                            correct_option_index: 0,
                            points: 2,
                          },
                        ]);
                        setBuilderStep(1);
                      }}
                      style={{
                        backgroundColor: "#1e293b",
                        color: "#e2e8f0",
                        border: "1px solid #334155",
                        borderRadius: "7px",
                        padding: "8px 14px",
                        fontSize: "0.85rem",
                        cursor: "pointer",
                      }}
                    >
                      Create Another
                    </button>
                  </div>
                </div>
              )}

              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <button
                  onClick={() => setBuilderStep(3)}
                  disabled={creating}
                  style={{
                    backgroundColor: "transparent",
                    color: "#94a3b8",
                    border: "1px solid #334155",
                    borderRadius: "8px",
                    padding: "10px 20px",
                    fontSize: "0.9rem",
                    cursor: "pointer",
                  }}
                >
                  ← Back to Preview
                </button>
                <button
                  onClick={handlePublishExam}
                  disabled={creating}
                  style={{
                    backgroundColor: creating ? "#0284c7" : "#10b981",
                    color: "#ffffff",
                    border: "none",
                    borderRadius: "8px",
                    padding: "12px 32px",
                    fontSize: "1rem",
                    fontWeight: "800",
                    cursor: creating ? "wait" : "pointer",
                    boxShadow: "0 4px 14px rgba(16, 185, 129, 0.4)",
                  }}
                >
                  {creating ? "Publishing Examination..." : "🚀 Publish Examination to Backend"}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ---------------------------------------------------- */}
      {/* TAB 4: SUBMISSION ANALYTICS & AI AUDIT TABLE */}
      {/* ---------------------------------------------------- */}
      {activeTab === "analytics" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          {/* Exam Selector & Context Header */}
          <div
            style={{
              backgroundColor: "#0f172a",
              border: "1px solid #1e293b",
              borderRadius: "12px",
              padding: "1.2rem 1.6rem",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "1rem",
            }}
          >
            <div>
              <span style={{ fontSize: "0.75rem", textTransform: "uppercase", color: "#94a3b8", fontWeight: "700" }}>
                Target Examination Audit
              </span>
              <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginTop: "0.3rem" }}>
                <select
                  value={selectedExamId}
                  onChange={(e) => setSelectedExamId(e.target.value)}
                  style={{
                    backgroundColor: "#090d16",
                    color: "#38bdf8",
                    border: "1px solid #334155",
                    borderRadius: "8px",
                    padding: "8px 14px",
                    fontSize: "0.95rem",
                    fontWeight: "700",
                    cursor: "pointer",
                    minWidth: "260px",
                  }}
                >
                  {exams.map((ex) => (
                    <option key={ex.id} value={ex.id}>
                      {ex.title} ({ex.duration_minutes}m, {ex.questions_count} MCQs)
                    </option>
                  ))}
                </select>
                <button
                  onClick={() => loadExamDashboard(selectedExamId)}
                  style={{
                    backgroundColor: "#1e293b",
                    color: "#e2e8f0",
                    border: "1px solid #334155",
                    borderRadius: "7px",
                    padding: "8px 12px",
                    fontSize: "0.85rem",
                    cursor: "pointer",
                  }}
                >
                  🔄 Refresh
                </button>
              </div>
            </div>

            {/* Quick Summary Pill */}
            {dashboard && (
              <div style={{ display: "flex", gap: "1rem" }}>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: "0.75rem", color: "#64748b" }}>TOTAL ATTEMPTS</div>
                  <div style={{ fontSize: "1.2rem", fontWeight: "800", color: "#f8fafc" }}>
                    {dashboard.total_submissions}
                  </div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: "0.75rem", color: "#64748b" }}>AVG SCORE</div>
                  <div style={{ fontSize: "1.2rem", fontWeight: "800", color: "#10b981" }}>
                    {dashboard.average_score}%
                  </div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: "0.75rem", color: "#64748b" }}>SUSPICIOUS SESSIONS</div>
                  <div
                    style={{
                      fontSize: "1.2rem",
                      fontWeight: "800",
                      color: dashboard.flagged_students_count > 0 ? "#f87171" : "#34d399",
                    }}
                  >
                    {dashboard.flagged_students_count}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Submissions Search, Filter & Sort Controls */}
          <div
            style={{
              backgroundColor: "#0f172a",
              border: "1px solid #1e293b",
              borderRadius: "12px",
              padding: "1rem 1.4rem",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "1rem",
            }}
          >
            {/* Search Input */}
            <div style={{ flex: 1, minWidth: "240px" }}>
              <input
                type="text"
                placeholder="Search by student name, ID, or submission reference..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  width: "100%",
                  backgroundColor: "#090d16",
                  border: "1px solid #334155",
                  borderRadius: "8px",
                  padding: "8px 14px",
                  color: "#f8fafc",
                  fontSize: "0.88rem",
                  boxSizing: "border-box",
                }}
              />
            </div>

            {/* Filter Tabs */}
            <div style={{ display: "flex", gap: "6px" }}>
              {[
                { id: "ALL", label: "All Submissions" },
                { id: "CLEAN", label: "Verified Clean" },
                { id: "REVIEW_NEEDED", label: "Review Needed" },
                { id: "HIGH_SUSPICION", label: "Cheating Flagged" },
              ].map((f) => (
                <button
                  key={f.id}
                  onClick={() => setVerdictFilter(f.id)}
                  style={{
                    backgroundColor: verdictFilter === f.id ? "#0284c7" : "#090d16",
                    color: verdictFilter === f.id ? "#ffffff" : "#94a3b8",
                    border: "1px solid #334155",
                    borderRadius: "6px",
                    padding: "6px 12px",
                    fontSize: "0.8rem",
                    fontWeight: "600",
                    cursor: "pointer",
                  }}
                >
                  {f.label}
                </button>
              ))}
            </div>

            {/* Sort Dropdown */}
            <div>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                style={{
                  backgroundColor: "#090d16",
                  color: "#e2e8f0",
                  border: "1px solid #334155",
                  borderRadius: "6px",
                  padding: "6px 12px",
                  fontSize: "0.8rem",
                  cursor: "pointer",
                }}
              >
                <option value="DATE_DESC">Newest Submissions</option>
                <option value="SCORE_DESC">Highest Academic Score</option>
                <option value="SCORE_ASC">Lowest Academic Score</option>
                <option value="INTEGRITY_ASC">Lowest Integrity (Most Suspicious)</option>
              </select>
            </div>
          </div>

          {/* Submissions Table */}
          <div
            style={{
              backgroundColor: "#0f172a",
              borderRadius: "12px",
              border: "1px solid #1e293b",
              overflow: "hidden",
            }}
          >
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.88rem" }}>
                <thead>
                  <tr style={{ backgroundColor: "#090d16", color: "#64748b", borderBottom: "1px solid #1e293b" }}>
                    <th style={{ padding: "12px 16px", fontWeight: "600" }}>STUDENT</th>
                    <th style={{ padding: "12px 16px", fontWeight: "600" }}>STUDENT ID</th>
                    <th style={{ padding: "12px 16px", fontWeight: "600" }}>SCORE</th>
                    <th style={{ padding: "12px 16px", fontWeight: "600" }}>PERCENTAGE</th>
                    <th style={{ padding: "12px 16px", fontWeight: "600" }}>AI INTEGRITY</th>
                    <th style={{ padding: "12px 16px", fontWeight: "600" }}>VERDICT</th>
                    <th style={{ padding: "12px 16px", fontWeight: "600" }}>SUBMITTED AT</th>
                    <th style={{ padding: "12px 16px", fontWeight: "600", textAlign: "right" }}>ACTIONS</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredSubmissions.map((sub) => {
                    const badge = getVerdictBadge(sub.verdict, sub.verdict_label);
                    return (
                      <tr
                        key={sub.submission_id}
                        style={{
                          borderBottom: "1px solid #1e293b",
                          transition: "background-color 0.15s ease",
                        }}
                        onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "rgba(30, 41, 59, 0.4)")}
                        onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
                      >
                        <td style={{ padding: "14px 16px" }}>
                          <div style={{ fontWeight: "700", color: "#f8fafc" }}>{sub.student_name}</div>
                          <div style={{ fontSize: "0.75rem", color: "#64748b", fontFamily: "monospace" }}>
                            {sub.submission_id}
                          </div>
                        </td>
                        <td style={{ padding: "14px 16px", color: "#94a3b8", fontFamily: "monospace" }}>
                          {sub.student_id}
                        </td>
                        <td style={{ padding: "14px 16px", fontWeight: "700", color: "#f8fafc" }}>
                          {sub.score} / {sub.total_points}
                        </td>
                        <td style={{ padding: "14px 16px" }}>
                          <span
                            style={{
                              backgroundColor:
                                sub.percentage >= 70
                                  ? "rgba(16, 185, 129, 0.15)"
                                  : sub.percentage >= 40
                                  ? "rgba(245, 158, 11, 0.15)"
                                  : "rgba(239, 68, 68, 0.15)",
                              color: sub.percentage >= 70 ? "#34d399" : sub.percentage >= 40 ? "#fbbf24" : "#f87171",
                              padding: "4px 8px",
                              borderRadius: "6px",
                              fontWeight: "700",
                            }}
                          >
                            {sub.percentage}%
                          </span>
                        </td>
                        <td style={{ padding: "14px 16px" }}>
                          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                            <div
                              style={{
                                width: "60px",
                                height: "6px",
                                backgroundColor: "#1e293b",
                                borderRadius: "3px",
                                overflow: "hidden",
                              }}
                            >
                              <div
                                style={{
                                  width: `${sub.integrity_score}%`,
                                  height: "100%",
                                  backgroundColor:
                                    sub.integrity_score >= 80
                                      ? "#10b981"
                                      : sub.integrity_score >= 60
                                      ? "#f59e0b"
                                      : "#ef4444",
                                }}
                              />
                            </div>
                            <span
                              style={{
                                fontWeight: "700",
                                color:
                                  sub.integrity_score >= 80
                                    ? "#10b981"
                                    : sub.integrity_score >= 60
                                    ? "#f59e0b"
                                    : "#ef4444",
                              }}
                            >
                              {sub.integrity_score}%
                            </span>
                          </div>
                        </td>
                        <td style={{ padding: "14px 16px" }}>
                          <span
                            style={{
                              backgroundColor: badge.bg,
                              border: `1px solid ${badge.border}`,
                              color: badge.color,
                              padding: "4px 10px",
                              borderRadius: "12px",
                              fontSize: "0.75rem",
                              fontWeight: "700",
                            }}
                          >
                            {badge.text}
                          </span>
                        </td>
                        <td style={{ padding: "14px 16px", color: "#64748b", fontSize: "0.8rem" }}>
                          {new Date(sub.submitted_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        </td>
                        <td style={{ padding: "14px 16px", textAlign: "right" }}>
                          <div style={{ display: "flex", justifyContent: "flex-end", gap: "6px" }}>
                            <button
                              onClick={() => setInspectingSubmission(sub)}
                              style={{
                                backgroundColor: "#0284c7",
                                color: "#ffffff",
                                border: "none",
                                borderRadius: "6px",
                                padding: "6px 12px",
                                fontSize: "0.8rem",
                                fontWeight: "600",
                                cursor: "pointer",
                              }}
                            >
                              Inspect Answers
                            </button>
                            {sub.proctoring_summary && (
                              <button
                                onClick={() => setSelectedAuditReport(sub.proctoring_summary)}
                                style={{
                                  backgroundColor: "#1e293b",
                                  color: "#38bdf8",
                                  border: "1px solid #334155",
                                  borderRadius: "6px",
                                  padding: "6px 10px",
                                  fontSize: "0.8rem",
                                  fontWeight: "600",
                                  cursor: "pointer",
                                }}
                              >
                                AI Report
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                  {filteredSubmissions.length === 0 && (
                    <tr>
                      <td colSpan="8" style={{ padding: "3rem", textAlign: "center", color: "#64748b" }}>
                        {searchQuery || verdictFilter !== "ALL"
                          ? "No submissions matched your search or verdict filter."
                          : "No student submissions have been recorded for this examination yet."}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ---------------------------------------------------- */}
      {/* STUDENT SUBMISSION DRILLDOWN MODAL */}
      {/* ---------------------------------------------------- */}
      {inspectingSubmission && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.8)",
            backdropFilter: "blur(6px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 9990,
            padding: "1rem",
          }}
        >
          <div
            style={{
              backgroundColor: "#0f172a",
              border: "1px solid #334155",
              borderRadius: "16px",
              width: "100%",
              maxWidth: "760px",
              maxHeight: "90vh",
              overflowY: "auto",
              padding: "2rem",
              boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.8)",
            }}
          >
            {/* Modal Header */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
                borderBottom: "1px solid #1e293b",
                paddingBottom: "1rem",
                marginBottom: "1.5rem",
              }}
            >
              <div>
                <span
                  style={{
                    fontSize: "0.75rem",
                    textTransform: "uppercase",
                    letterSpacing: "1px",
                    color: "#94a3b8",
                    fontWeight: "700",
                  }}
                >
                  Candidate Submission Audit
                </span>
                <h2 style={{ fontSize: "1.4rem", margin: "0.2rem 0 0 0", color: "#f8fafc" }}>
                  {inspectingSubmission.student_name} ({inspectingSubmission.student_id})
                </h2>
                <div style={{ fontSize: "0.8rem", color: "#64748b", fontFamily: "monospace" }}>
                  Session ID: {inspectingSubmission.session_id}
                </div>
              </div>
              <button
                onClick={() => setInspectingSubmission(null)}
                style={{
                  background: "none",
                  border: "none",
                  color: "#94a3b8",
                  fontSize: "1.5rem",
                  cursor: "pointer",
                }}
              >
                ✕
              </button>
            </div>

            {/* High-Level Score Banner */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr 1fr",
                gap: "1rem",
                backgroundColor: "#090d16",
                border: "1px solid #1e293b",
                borderRadius: "10px",
                padding: "1rem",
                marginBottom: "1.5rem",
              }}
            >
              <div>
                <div style={{ fontSize: "0.72rem", color: "#64748b" }}>ACADEMIC SCORE</div>
                <div style={{ fontSize: "1.3rem", fontWeight: "800", color: "#10b981" }}>
                  {inspectingSubmission.score} / {inspectingSubmission.total_points} ({inspectingSubmission.percentage}%)
                </div>
              </div>
              <div>
                <div style={{ fontSize: "0.72rem", color: "#64748b" }}>AI INTEGRITY</div>
                <div
                  style={{
                    fontSize: "1.3rem",
                    fontWeight: "800",
                    color: inspectingSubmission.integrity_score >= 80 ? "#10b981" : "#f87171",
                  }}
                >
                  {inspectingSubmission.integrity_score}%
                </div>
              </div>
              <div>
                <div style={{ fontSize: "0.72rem", color: "#64748b" }}>AI VERDICT</div>
                <div style={{ fontSize: "1rem", fontWeight: "800", color: inspectingSubmission.verdict_color }}>
                  {inspectingSubmission.verdict_label}
                </div>
              </div>
            </div>

            {/* Question-by-Question Breakdown */}
            <h4 style={{ margin: "0 0 0.8rem 0", fontSize: "1rem", color: "#f8fafc" }}>
              Question Responses & Marking Sheet
            </h4>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.8rem", marginBottom: "1.5rem" }}>
              {(inspectingSubmission.question_results || []).map((qr, idx) => (
                <div
                  key={idx}
                  style={{
                    backgroundColor: "#090d16",
                    border: qr.is_correct ? "1px solid rgba(16, 185, 129, 0.4)" : "1px solid rgba(239, 68, 68, 0.4)",
                    borderRadius: "8px",
                    padding: "1rem",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      marginBottom: "0.4rem",
                    }}
                  >
                    <span style={{ fontWeight: "700", color: "#38bdf8", fontSize: "0.85rem" }}>
                      Q{idx + 1}. {qr.question_text}
                    </span>
                    <span
                      style={{
                        fontSize: "0.78rem",
                        fontWeight: "700",
                        color: qr.is_correct ? "#10b981" : "#f87171",
                      }}
                    >
                      {qr.is_correct ? `+${qr.points_earned} pts` : `0 / ${qr.max_points} pts`}
                    </span>
                  </div>

                  <div style={{ display: "flex", gap: "1.5rem", fontSize: "0.82rem", marginTop: "0.4rem" }}>
                    <div>
                      <span style={{ color: "#64748b" }}>Student Answer: </span>
                      <strong style={{ color: qr.is_correct ? "#34d399" : "#f87171" }}>
                        {qr.selected_option_index !== null && qr.selected_option_index !== undefined
                          ? `Option ${String.fromCharCode(65 + qr.selected_option_index)}`
                          : "Unanswered"}
                      </strong>
                    </div>
                    {!qr.is_correct && (
                      <div>
                        <span style={{ color: "#64748b" }}>Correct Answer: </span>
                        <strong style={{ color: "#34d399" }}>
                          Option {String.fromCharCode(65 + qr.correct_option_index)}
                        </strong>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Modal Actions */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                borderTop: "1px solid #1e293b",
                paddingTop: "1.2rem",
              }}
            >
              {inspectingSubmission.proctoring_summary ? (
                <button
                  onClick={() => {
                    setSelectedAuditReport(inspectingSubmission.proctoring_summary);
                  }}
                  style={{
                    backgroundColor: "#0284c7",
                    color: "#ffffff",
                    border: "none",
                    borderRadius: "8px",
                    padding: "10px 18px",
                    fontSize: "0.85rem",
                    fontWeight: "700",
                    cursor: "pointer",
                  }}
                >
                  🔍 Open Full Multimodal AI Proctoring Report
                </button>
              ) : (
                <span style={{ fontSize: "0.82rem", color: "#64748b" }}>No AI proctoring audit recorded.</span>
              )}
              <button
                onClick={() => setInspectingSubmission(null)}
                style={{
                  backgroundColor: "#1e293b",
                  color: "#e2e8f0",
                  border: "1px solid #334155",
                  borderRadius: "8px",
                  padding: "10px 18px",
                  fontSize: "0.85rem",
                  cursor: "pointer",
                }}
              >
                Close Inspection
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Official AI Forensic Audit Modal */}
      {selectedAuditReport && (
        <ProctoringReportModal
          summary={selectedAuditReport}
          onClose={() => setSelectedAuditReport(null)}
          onReset={() => {
            setSelectedAuditReport(null);
            if (selectedExamId) loadExamDashboard(selectedExamId);
          }}
        />
      )}
    </div>
  );
}
