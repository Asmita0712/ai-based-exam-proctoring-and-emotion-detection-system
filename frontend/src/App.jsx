import React, { useState, useEffect } from "react";
import examApi from "./services/examApi";
import StudentExamPortal from "./components/StudentExamPortal";
import TeacherPortal from "./components/TeacherPortal";
import DiagnosticLab from "./components/DiagnosticLab";
import LoginModal from "./components/LoginModal";

export default function App() {
  // activeTab: "student" | "teacher" | "lab"
  const [activeTab, setActiveTab] = useState("student");
  const [backendHealth, setBackendHealth] = useState(null);
  const [currentUser, setCurrentUser] = useState(examApi.getStoredUser());
  
  // Auth modal state
  const [loginModalOpen, setLoginModalOpen] = useState(false);
  const [pendingTab, setPendingTab] = useState(null);
  const [requiredRole, setRequiredRole] = useState("teacher");

  // Poll backend health
  useEffect(() => {
    const check = async () => {
      try {
        const data = await examApi.checkHealth();
        setBackendHealth(data);
      } catch (err) {
        console.warn("Backend health check failed:", err.message);
        setBackendHealth({ status: "offline" });
      }
    };
    check();
    const interval = setInterval(check, 10000);
    return () => clearInterval(interval);
  }, []);

  // Sync profile if token exists
  useEffect(() => {
    if (examApi.isStaffLoggedIn()) {
      examApi.getMe()
        .then((user) => {
          setCurrentUser(user);
          localStorage.setItem("sentinel_user", JSON.stringify(user));
        })
        .catch(() => {
          // Token expired or invalid
          examApi.logout();
          setCurrentUser(null);
        });
    }
  }, []);

  const handleTabSwitch = (targetTab) => {
    if (targetTab === "student") {
      setActiveTab("student");
      return;
    }

    if (targetTab === "teacher") {
      if (currentUser && (currentUser.role === "teacher" || currentUser.role === "admin")) {
        setActiveTab("teacher");
      } else {
        setPendingTab("teacher");
        setRequiredRole("teacher");
        setLoginModalOpen(true);
      }
      return;
    }

    if (targetTab === "lab") {
      if (currentUser && currentUser.role === "admin") {
        setActiveTab("lab");
      } else {
        setPendingTab("lab");
        setRequiredRole("admin");
        setLoginModalOpen(true);
      }
      return;
    }
  };

  const handleLoginSuccess = (user) => {
    setCurrentUser(user);
    if (pendingTab) {
      setActiveTab(pendingTab);
      setPendingTab(null);
    }
  };

  const handleLogout = async () => {
    await examApi.logout();
    setCurrentUser(null);
    setActiveTab("student");
  };

  const isOnline = backendHealth?.status === "ok" || backendHealth?.status === "healthy";

  return (
    <div
      style={{
        fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        backgroundColor: "#0b0f19",
        color: "#f8fafc",
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Top Main Navigation Header */}
      <header
        style={{
          backgroundColor: "#0f172a",
          borderBottom: "1px solid #1e293b",
          padding: "0.8rem 2rem",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "1rem",
          position: "sticky",
          top: 0,
          zIndex: 1000,
          boxShadow: "0 4px 20px rgba(0, 0, 0, 0.4)",
        }}
      >
        {/* Left: Brand Identity */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.9rem" }}>
          <div
            style={{
              width: "40px",
              height: "40px",
              borderRadius: "10px",
              background: "linear-gradient(135deg, #0284c7 0%, #38bdf8 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "1.4rem",
              boxShadow: "0 4px 10px rgba(56, 189, 248, 0.3)",
            }}
          >
            🛡️
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
              <span style={{ fontSize: "1.2rem", fontWeight: "800", color: "#f8fafc", letterSpacing: "-0.02em" }}>
                Sentinel<span style={{ color: "#38bdf8" }}>Proctor</span> AI
              </span>
              <span
                style={{
                  fontSize: "0.7rem",
                  backgroundColor: isOnline ? "#065f46" : "#7f1d1d",
                  color: isOnline ? "#34d399" : "#fca5a5",
                  border: `1px solid ${isOnline ? "#10b981" : "#ef4444"}`,
                  padding: "2px 8px",
                  borderRadius: "10px",
                  fontWeight: "700",
                }}
              >
                {isOnline ? "● API ONLINE" : "● CONNECTING..."}
              </span>
            </div>
            <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
              Enterprise Multimodal Examination & Proctoring Platform
            </div>
          </div>
        </div>

        {/* Center: Primary Role Navigation Switcher */}
        <nav
          style={{
            display: "flex",
            backgroundColor: "#1e293b",
            borderRadius: "10px",
            padding: "4px",
            border: "1px solid #334155",
            gap: "4px",
          }}
        >
          {/* Public Student Mode - OPEN ACCESS */}
          <button
            onClick={() => handleTabSwitch("student")}
            style={{
              padding: "0.6rem 1.2rem",
              borderRadius: "8px",
              border: "none",
              backgroundColor: activeTab === "student" ? "#0284c7" : "transparent",
              color: activeTab === "student" ? "white" : "#94a3b8",
              fontWeight: activeTab === "student" ? "700" : "500",
              fontSize: "0.9rem",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              transition: "all 0.15s ease",
            }}
          >
            <span>📝</span>
            <span>Student Exam Mode (Open)</span>
          </button>

          {/* Teacher Portal - AUTHENTICATION REQUIRED */}
          <button
            onClick={() => handleTabSwitch("teacher")}
            style={{
              padding: "0.6rem 1.2rem",
              borderRadius: "8px",
              border: "none",
              backgroundColor: activeTab === "teacher" ? "#0284c7" : "transparent",
              color: activeTab === "teacher" ? "white" : "#94a3b8",
              fontWeight: activeTab === "teacher" ? "700" : "500",
              fontSize: "0.9rem",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              transition: "all 0.15s ease",
            }}
          >
            <span>👨‍🏫</span>
            <span>Teacher Portal {currentUser ? "" : "🔒"}</span>
          </button>

          {/* Diagnostic Lab - ADMIN AUTHENTICATION REQUIRED */}
          <button
            onClick={() => handleTabSwitch("lab")}
            style={{
              padding: "0.6rem 1.2rem",
              borderRadius: "8px",
              border: "none",
              backgroundColor: activeTab === "lab" ? "#0284c7" : "transparent",
              color: activeTab === "lab" ? "white" : "#94a3b8",
              fontWeight: activeTab === "lab" ? "700" : "500",
              fontSize: "0.9rem",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              transition: "all 0.15s ease",
            }}
          >
            <span>🔬</span>
            <span>Diagnostic AI Lab {currentUser?.role === "admin" ? "" : "🔒"}</span>
          </button>
        </nav>

        {/* Right: Auth Profile / Login Button */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.8rem" }}>
          {currentUser ? (
            <div style={{ display: "flex", alignItems: "center", gap: "0.8rem" }}>
              <div style={{ textAlign: "right", fontSize: "0.78rem" }}>
                <div style={{ fontWeight: "700", color: "#f8fafc" }}>{currentUser.full_name}</div>
                <div style={{ color: currentUser.role === "admin" ? "#f43f5e" : "#38bdf8", textTransform: "uppercase", fontSize: "0.7rem", fontWeight: "700" }}>
                  {currentUser.role}
                </div>
              </div>
              <button
                onClick={handleLogout}
                style={{
                  padding: "0.4rem 0.8rem",
                  backgroundColor: "#334155",
                  color: "#cbd5e1",
                  border: "1px solid #475569",
                  borderRadius: "6px",
                  fontSize: "0.78rem",
                  cursor: "pointer",
                  fontWeight: "600",
                }}
              >
                Sign Out
              </button>
            </div>
          ) : (
            <button
              onClick={() => {
                setPendingTab("teacher");
                setRequiredRole("teacher");
                setLoginModalOpen(true);
              }}
              style={{
                padding: "0.5rem 1rem",
                backgroundColor: "#1e293b",
                color: "#38bdf8",
                border: "1px solid #334155",
                borderRadius: "8px",
                fontWeight: "700",
                fontSize: "0.85rem",
                cursor: "pointer",
              }}
            >
              Staff Login 🔑
            </button>
          )}

          <a
            href={`${examApi.getApiBaseUrl()}/docs`}
            target="_blank"
            rel="noreferrer"
            style={{
              padding: "0.5rem 0.8rem",
              backgroundColor: "#1e293b",
              color: "#94a3b8",
              border: "1px solid #334155",
              borderRadius: "8px",
              textDecoration: "none",
              fontWeight: "600",
              fontSize: "0.8rem",
              display: "flex",
              alignItems: "center",
              gap: "0.4rem",
            }}
          >
            <span>API Docs</span>
            <span>↗</span>
          </a>
        </div>
      </header>

      {/* Main Role-Specific Workspace Content */}
      <main style={{ flex: 1, padding: "2rem", maxWidth: "1600px", margin: "0 auto", width: "100%", boxSizing: "border-box" }}>
        {activeTab === "student" && <StudentExamPortal />}
        {activeTab === "teacher" && <TeacherPortal currentUser={currentUser} />}
        {activeTab === "lab" && <DiagnosticLab currentUser={currentUser} />}
      </main>

      {/* Footer */}
      <footer
        style={{
          backgroundColor: "#0f172a",
          borderTop: "1px solid #1e293b",
          padding: "1.2rem 2rem",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontSize: "0.8rem",
          color: "#64748b",
          flexWrap: "wrap",
          gap: "1rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
          <span>SentinelProctor AI v2.0 Enterprise</span>
          <span>•</span>
          <span>500-Concurrent-User Architecture</span>
          <span>•</span>
          <span>PostgreSQL & Multi-Worker Pipeline</span>
        </div>
        <div>
          Ethical Proctoring Standard: Emotion context non-punitive • Authoritative server timers active
        </div>
      </footer>

      {/* Authentication Modal */}
      <LoginModal
        isOpen={loginModalOpen}
        requiredRole={requiredRole}
        onClose={() => setLoginModalOpen(false)}
        onSuccess={handleLoginSuccess}
      />
    </div>
  );
}
