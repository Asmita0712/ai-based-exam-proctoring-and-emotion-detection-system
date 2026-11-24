import React from "react";

export default function ProctoringReportModal({ summary, onClose, onReset }) {
  if (!summary) return null;

  return (
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
        zIndex: 9999,
        padding: "1rem",
      }}
    >
      <div
        style={{
          backgroundColor: "#1e293b",
          borderRadius: "16px",
          border: "1px solid #475569",
          width: "100%",
          maxWidth: "680px",
          maxHeight: "90vh",
          overflowY: "auto",
          padding: "2rem",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.75)",
          color: "#f8fafc",
        }}
      >
        {/* Header */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            marginBottom: "1.5rem",
            borderBottom: "1px solid #334155",
            paddingBottom: "1rem",
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
              Official Session Audit Record
            </span>
            <h2 style={{ fontSize: "1.5rem", margin: "0.2rem 0 0 0", color: "#f8fafc" }}>
              Exam Proctoring & Integrity Report
            </h2>
            <div style={{ fontSize: "0.85rem", color: "#64748b", marginTop: "4px" }}>
              Session ID: <code style={{ color: "#38bdf8" }}>{summary.session_id}</code>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              backgroundColor: "transparent",
              border: "none",
              color: "#94a3b8",
              fontSize: "1.5rem",
              cursor: "pointer",
              padding: "0 6px",
            }}
          >
            ✕
          </button>
        </div>

        {/* Score & Verdict Banner */}
        <div
          style={{
            backgroundColor: "#0f172a",
            borderRadius: "12px",
            border: `2px solid ${summary.verdict_color || "#38bdf8"}`,
            padding: "1.5rem",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "1rem",
            marginBottom: "1.5rem",
          }}
        >
          <div>
            <div
              style={{
                fontSize: "0.85rem",
                color: "#94a3b8",
                textTransform: "uppercase",
                fontWeight: "600",
              }}
            >
              Final Calculated Integrity Score:
            </div>
            <div
              style={{
                fontSize: "2.8rem",
                fontWeight: "900",
                color: summary.verdict_color || "#38bdf8",
                lineHeight: "1.1",
              }}
            >
              {summary.integrity_score}%
            </div>
            <div style={{ marginTop: "0.4rem", fontSize: "0.85rem", color: "#cbd5e1" }}>
              Flagged Ratio: <strong>{summary.flagged_percentage}%</strong> (
              {summary.flagged_frames_count} of {summary.total_frames_analyzed} frames)
            </div>
          </div>

          <div style={{ textAlign: "right" }}>
            <span
              style={{
                backgroundColor: (summary.verdict_color || "#38bdf8") + "22",
                color: summary.verdict_color || "#38bdf8",
                border: `1px solid ${summary.verdict_color || "#38bdf8"}`,
                padding: "6px 14px",
                borderRadius: "8px",
                fontWeight: "800",
                fontSize: "0.95rem",
                display: "inline-block",
              }}
            >
              {summary.verdict_label}
            </span>
            <div style={{ fontSize: "0.8rem", color: "#64748b", marginTop: "0.5rem" }}>
              Exam Duration: <strong>{summary.exam_duration_seconds}s</strong>
            </div>
          </div>
        </div>

        {/* Forensic Violations Breakdown */}
        {summary.violations_summary && (
          <div style={{ marginBottom: "1.5rem" }}>
            <h4 style={{ fontSize: "0.95rem", color: "#cbd5e1", margin: "0 0 0.8rem 0" }}>
              Forensic Modality Violations Breakdown:
            </h4>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))",
                gap: "0.8rem",
              }}
            >
              {[
                {
                  label: "Multi-Person Presence",
                  val: summary.violations_summary.multi_person || 0,
                  alert: (summary.violations_summary.multi_person || 0) > 0,
                },
                {
                  label: "Looking Away",
                  val: summary.violations_summary.looking_away || 0,
                  alert: (summary.violations_summary.looking_away || 0) > 5,
                },
                {
                  label: "Head Turned Away",
                  val: summary.violations_summary.head_turned || 0,
                  alert: (summary.violations_summary.head_turned || 0) > 5,
                },
                {
                  label: "Speech / Talking",
                  val: summary.violations_summary.speech_detected || 0,
                  alert: (summary.violations_summary.speech_detected || 0) > 3,
                },
                {
                  label: "Browser Tab Hidden / Away",
                  val: summary.violations_summary.tab_unfocused || 0,
                  alert: (summary.violations_summary.tab_unfocused || 0) > 0,
                },
                {
                  label: "Candidate Absence",
                  val: summary.violations_summary.absence || 0,
                  alert: (summary.violations_summary.absence || 0) > 0,
                },
              ].map((item, idx) => (
                <div
                  key={idx}
                  style={{
                    backgroundColor: "#0f172a",
                    border: `1px solid ${item.alert ? "#ef444466" : "#334155"}`,
                    borderRadius: "8px",
                    padding: "0.8rem",
                  }}
                >
                  <div style={{ fontSize: "0.72rem", color: "#94a3b8" }}>{item.label}</div>
                  <div
                    style={{
                      fontSize: "1.1rem",
                      fontWeight: "800",
                      color: item.alert ? "#f87171" : "#34d399",
                      marginTop: "4px",
                    }}
                  >
                    {item.val} frames {item.alert ? "⚠️" : "✓"}
                  </div>
                  <div style={{ fontSize: "0.7rem", color: "#64748b", marginTop: "2px" }}>
                    ≈ {(item.val * 0.38).toFixed(1)}s duration
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Emotional State & Top Contributors */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "1rem",
            marginBottom: "1.5rem",
          }}
        >
          <div
            style={{
              backgroundColor: "#0f172a",
              padding: "1rem",
              borderRadius: "8px",
              border: "1px solid #334155",
            }}
          >
            <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>DOMINANT EMOTION (FER)</div>
            <div
              style={{
                fontSize: "1.1rem",
                fontWeight: "700",
                color: "#38bdf8",
                textTransform: "capitalize",
                marginTop: "4px",
              }}
            >
              {summary.dominant_emotion || "Neutral"}
            </div>
            <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: "2px" }}>
              Affective context only — zero penalty
            </div>
          </div>

          <div
            style={{
              backgroundColor: "#0f172a",
              padding: "1rem",
              borderRadius: "8px",
              border: "1px solid #334155",
            }}
          >
            <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>PRIMARY CONTRIBUTORS</div>
            <div style={{ display: "flex", gap: "4px", flexWrap: "wrap", marginTop: "6px" }}>
              {(!summary.top_contributors || summary.top_contributors.length === 0) ? (
                <span style={{ color: "#34d399", fontSize: "0.85rem", fontWeight: "600" }}>
                  None (Clean conduct)
                </span>
              ) : (
                summary.top_contributors.map((c, i) => (
                  <span
                    key={i}
                    style={{
                      backgroundColor: "#ef444422",
                      color: "#f87171",
                      border: "1px solid #ef444455",
                      padding: "2px 6px",
                      borderRadius: "4px",
                      fontSize: "0.7rem",
                      fontWeight: "600",
                    }}
                  >
                    {c.replace(/_/g, " ")}
                  </span>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Actions */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            paddingTop: "1rem",
            borderTop: "1px solid #334155",
          }}
        >
          {onReset && (
            <button
              onClick={onReset}
              style={{
                padding: "0.6rem 1.2rem",
                backgroundColor: "#334155",
                color: "#f87171",
                border: "1px solid #ef444455",
                borderRadius: "6px",
                cursor: "pointer",
                fontWeight: "600",
                fontSize: "0.85rem",
              }}
            >
              🗑 Reset Audit Session
            </button>
          )}

          <div style={{ display: "flex", gap: "0.8rem", marginLeft: "auto" }}>
            <button
              onClick={() => window.print()}
              style={{
                padding: "0.6rem 1.2rem",
                backgroundColor: "#0284c7",
                color: "white",
                border: "none",
                borderRadius: "6px",
                cursor: "pointer",
                fontWeight: "700",
                fontSize: "0.85rem",
              }}
            >
              🖨 Print / Save PDF
            </button>
            <button
              onClick={onClose}
              style={{
                padding: "0.6rem 1.2rem",
                backgroundColor: "#10b981",
                color: "white",
                border: "none",
                borderRadius: "6px",
                cursor: "pointer",
                fontWeight: "700",
                fontSize: "0.85rem",
              }}
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
