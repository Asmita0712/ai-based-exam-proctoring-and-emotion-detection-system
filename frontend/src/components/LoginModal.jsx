import React, { useState } from "react";
import examApi from "../services/examApi";

export default function LoginModal({ isOpen, onClose, onSuccess, requiredRole = "teacher" }) {
  const [email, setEmail] = useState(
    requiredRole === "admin" ? "admin@sentinelproctor.ai" : "teacher@sentinelproctor.ai"
  );
  const [password, setPassword] = useState(
    requiredRole === "admin" ? "Admin@Sentinel2026" : "Teacher@Sentinel2026"
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await examApi.login(email, password);
      if (requiredRole === "admin" && data.user.role !== "admin") {
        throw new Error("Access restricted: Administrator role required for this area.");
      }
      onSuccess(data.user);
      onClose();
    } catch (err) {
      setError(err.message || "Authentication failed.");
    } finally {
      setLoading(false);
    }
  };

  const fillCredentials = (role) => {
    if (role === "admin") {
      setEmail("admin@sentinelproctor.ai");
      setPassword("Admin@Sentinel2026");
    } else {
      setEmail("teacher@sentinelproctor.ai");
      setPassword("Teacher@Sentinel2026");
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(0, 0, 0, 0.75)",
        backdropFilter: "blur(6px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 9999,
        padding: "1rem",
      }}
    >
      <div
        style={{
          backgroundColor: "#0f172a",
          border: "1px solid #334155",
          borderRadius: "16px",
          width: "100%",
          maxWidth: "460px",
          padding: "2rem",
          boxShadow: "0 20px 40px rgba(0, 0, 0, 0.6)",
          color: "#f8fafc",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.2rem" }}>
          <div>
            <span
              style={{
                fontSize: "0.72rem",
                fontWeight: "800",
                color: requiredRole === "admin" ? "#f43f5e" : "#38bdf8",
                textTransform: "uppercase",
                letterSpacing: "0.5px",
              }}
            >
              {requiredRole === "admin" ? "🛡️ SYSTEM ADMINISTRATOR LOGIN" : "👨‍🏫 TEACHER PORTAL LOGIN"}
            </span>
            <h2 style={{ fontSize: "1.4rem", fontWeight: "800", margin: "0.3rem 0 0 0" }}>
              Staff Authentication
            </h2>
          </div>
          <button
            onClick={onClose}
            style={{
              background: "none",
              border: "none",
              color: "#94a3b8",
              fontSize: "1.4rem",
              cursor: "pointer",
            }}
          >
            ✕
          </button>
        </div>

        <p style={{ fontSize: "0.85rem", color: "#94a3b8", marginBottom: "1.5rem", lineHeight: "1.5" }}>
          {requiredRole === "admin"
            ? "Diagnostic AI Lab and internal model controls are restricted to authorized administrators."
            : "Examination authoring, student results, and forensic cheating reports are restricted to authorized teachers."}
        </p>

        {error && (
          <div
            style={{
              backgroundColor: "rgba(239, 68, 68, 0.15)",
              border: "1px solid #ef4444",
              borderRadius: "8px",
              padding: "10px 14px",
              fontSize: "0.85rem",
              color: "#fca5a5",
              marginBottom: "1.2rem",
            }}
          >
            ⚠️ {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div>
            <label style={{ display: "block", fontSize: "0.8rem", color: "#cbd5e1", marginBottom: "0.4rem", fontWeight: "600" }}>
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={{
                width: "100%",
                boxSizing: "border-box",
                backgroundColor: "#020617",
                border: "1px solid #334155",
                borderRadius: "8px",
                padding: "10px 14px",
                color: "#ffffff",
                fontSize: "0.9rem",
              }}
            />
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.8rem", color: "#cbd5e1", marginBottom: "0.4rem", fontWeight: "600" }}>
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{
                width: "100%",
                boxSizing: "border-box",
                backgroundColor: "#020617",
                border: "1px solid #334155",
                borderRadius: "8px",
                padding: "10px 14px",
                color: "#ffffff",
                fontSize: "0.9rem",
              }}
            />
          </div>

          {/* Quick Credential Presets */}
          <div style={{ display: "flex", gap: "8px", marginTop: "0.2rem" }}>
            <button
              type="button"
              onClick={() => fillCredentials("teacher")}
              style={{
                fontSize: "0.75rem",
                padding: "4px 8px",
                backgroundColor: "#1e293b",
                color: "#38bdf8",
                border: "1px solid #334155",
                borderRadius: "4px",
                cursor: "pointer",
              }}
            >
              Fill Teacher Demo
            </button>
            <button
              type="button"
              onClick={() => fillCredentials("admin")}
              style={{
                fontSize: "0.75rem",
                padding: "4px 8px",
                backgroundColor: "#1e293b",
                color: "#f43f5e",
                border: "1px solid #334155",
                borderRadius: "4px",
                cursor: "pointer",
              }}
            >
              Fill Admin Demo
            </button>
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              marginTop: "0.8rem",
              padding: "12px",
              backgroundColor: requiredRole === "admin" ? "#e11d48" : "#0284c7",
              color: "white",
              border: "none",
              borderRadius: "8px",
              fontWeight: "700",
              fontSize: "0.95rem",
              cursor: loading ? "wait" : "pointer",
              boxShadow: "0 4px 14px rgba(2, 132, 199, 0.4)",
            }}
          >
            {loading ? "Authenticating..." : "Sign In & Enter Workspace"}
          </button>
        </form>
      </div>
    </div>
  );
}
