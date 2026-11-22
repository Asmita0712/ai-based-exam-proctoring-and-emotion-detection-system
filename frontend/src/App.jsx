import { useEffect, useState, useRef, useCallback } from "react";

const BACKEND_URL = "http://localhost:8000";
const SESSION_ID = "demo-session-001";

// Preset test scenarios demonstrating multimodal intelligence to evaluators
const SCENARIOS = [
  {
    id: "normal",
    label: "🟢 Normal Candidate",
    desc: "Single face, centered gaze, neutral emotion, silent audio, no tab switch.",
    payload: {
      visual_signals: {
        person_count: 1,
        multi_person_flag: false,
        gaze: { gaze_ratio: 0.50, looking_away: false },
        head_pose: { yaw: 2.0, pitch: -1.0, turned_away: false },
        emotion: { dominant_emotion: "Neutral", emotion_confidence: 0.88 },
      },
      audio_signals: { speech_detected: false, speech_probability: 0.04, sustained_talking: false },
    },
  },
  {
    id: "looking_away",
    label: "🟡 Looking Away (Off-Screen Notes)",
    desc: "Gaze deviated to bottom-left, head turned, searching off-screen material.",
    payload: {
      visual_signals: {
        person_count: 1,
        multi_person_flag: false,
        gaze: { gaze_ratio: 0.88, looking_away: true },
        head_pose: { yaw: 32.5, pitch: 24.0, turned_away: true },
        emotion: { dominant_emotion: "Neutral", emotion_confidence: 0.72 },
      },
      audio_signals: { speech_detected: false, speech_probability: 0.08, sustained_talking: false },
    },
  },
  {
    id: "multiple_persons",
    label: "🔴 Multiple Persons in Frame",
    desc: "Second person detected assisting candidate or standing in webcam view.",
    payload: {
      visual_signals: {
        person_count: 2,
        multi_person_flag: true,
        gaze: { gaze_ratio: 0.65, looking_away: true },
        head_pose: { yaw: 18.0, pitch: 5.0, turned_away: false },
        emotion: { dominant_emotion: "Surprise", emotion_confidence: 0.76 },
      },
      audio_signals: { speech_detected: true, speech_probability: 0.65, sustained_talking: true },
    },
  },
  {
    id: "speech_whisper",
    label: "🟡 Speech & Whispering",
    desc: "Voice activity detection (Silero VAD) detects speech / verbal prompting.",
    payload: {
      visual_signals: {
        person_count: 1,
        multi_person_flag: false,
        gaze: { gaze_ratio: 0.52, looking_away: false },
        head_pose: { yaw: 4.0, pitch: 2.0, turned_away: false },
        emotion: { dominant_emotion: "Neutral", emotion_confidence: 0.80 },
      },
      audio_signals: { speech_detected: true, speech_probability: 0.92, sustained_talking: true },
    },
  },
  {
    id: "anxious_candidate",
    label: "🟢 Anxious Candidate (Ethical Check)",
    desc: "Demonstrates Rule 4: Fear/Surprise emotion alone NEVER triggers cheating!",
    payload: {
      visual_signals: {
        person_count: 1,
        multi_person_flag: false,
        gaze: { gaze_ratio: 0.50, looking_away: false },
        head_pose: { yaw: 1.0, pitch: 0.0, turned_away: false },
        emotion: { dominant_emotion: "Fear", emotion_confidence: 0.91 },
      },
      audio_signals: { speech_detected: false, speech_probability: 0.03, sustained_talking: false },
    },
  },
  {
    id: "tab_switch",
    label: "🔴 Tab Switch & Background Blur",
    desc: "Student switched active window to search Google / ChatGPT in background.",
    payload: {
      visual_signals: {
        person_count: 1,
        multi_person_flag: false,
        gaze: { gaze_ratio: 0.50, looking_away: false },
        head_pose: { yaw: 0.0, pitch: 0.0, turned_away: false },
        emotion: { dominant_emotion: "Neutral", emotion_confidence: 0.85 },
      },
      audio_signals: { speech_detected: false, speech_probability: 0.05, sustained_talking: false },
      simulateTabBlur: true,
    },
  },
];

function App() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);
  const [cameraActive, setCameraActive] = useState(false);
  const [tabStatus, setTabStatus] = useState("Active");
  const [switchCount, setSwitchCount] = useState(0);
  const [eventsLog, setEventsLog] = useState([]);
  const [autoLoop, setAutoLoop] = useState(false);
  const [showAuditModal, setShowAuditModal] = useState(false);
  const [auditResults, setAuditResults] = useState([]);
  const [activeScenarioId, setActiveScenarioId] = useState("normal");

  // Multimodal current telemetry state
  const [signals, setSignals] = useState({
    person_count: 1,
    multi_person_flag: false,
    gaze_ratio: 0.50,
    looking_away: false,
    yaw: 0.0,
    pitch: 0.0,
    turned_away: false,
    speech_detected: false,
    speech_probability: 0.04,
    sustained_talking: false,
    tab_hidden: false,
    dominant_emotion: "Neutral",
    emotion_confidence: 0.88,
  });

  const [inferenceResult, setInferenceResult] = useState({
    suspicion_score: 0.05,
    flag: false,
    contributors: [],
    mode: "temporal",
  });

  const videoRef = useRef(null);
  const streamRef = useRef(null);

  // 1. Health check poll
  useEffect(() => {
    fetch(`${BACKEND_URL}/health`)
      .then((res) => res.json())
      .then((data) => {
        setHealth(data);
        setError(null);
      })
      .catch((err) => setError(err.message));
  }, []);

  // 2. Camera handler
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setCameraActive(true);
    } catch (err) {
      alert("Unable to access webcam: " + err.message);
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setCameraActive(false);
  };

  // 3. Tab visibility listener
  const sendBrowserEvent = useCallback((eventType) => {
    const payload = {
      session_id: SESSION_ID,
      type: eventType,
      timestamp: new Date().toISOString(),
    };

    fetch(`${BACKEND_URL}/proctoring/events`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).catch(() => {});

    setEventsLog((prev) => [
      { type: eventType, time: new Date().toLocaleTimeString() },
      ...prev.slice(0, 10),
    ]);
  }, []);

  useEffect(() => {
    const handleVisibility = () => {
      if (document.hidden) {
        setTabStatus("Tab Hidden");
        setSwitchCount((c) => c + 1);
        sendBrowserEvent("tab_hidden");
      } else {
        setTabStatus("Active");
        sendBrowserEvent("tab_visible");
      }
    };

    const handleBlur = () => {
      setTabStatus("Window Unfocused");
      sendBrowserEvent("window_blur");
    };

    const handleFocus = () => {
      setTabStatus("Active");
      sendBrowserEvent("window_focus");
    };

    document.addEventListener("visibilitychange", handleVisibility);
    window.addEventListener("blur", handleBlur);
    window.addEventListener("focus", handleFocus);

    return () => {
      document.removeEventListener("visibilitychange", handleVisibility);
      window.removeEventListener("blur", handleBlur);
      window.removeEventListener("focus", handleFocus);
    };
  }, [sendBrowserEvent]);

  // 4. Send telemetry window to backend ML pipeline
  const sendWindowAnalysis = useCallback(async (customPayload = null) => {
    const scenario = SCENARIOS.find((s) => s.id === activeScenarioId) || SCENARIOS[0];
    const sourcePayload = customPayload || scenario.payload;

    if (sourcePayload.simulateTabBlur) {
      sendBrowserEvent("tab_hidden");
    }

    const requestBody = {
      session_id: SESSION_ID,
      visual_signals: sourcePayload.visual_signals,
      audio_signals: sourcePayload.audio_signals,
      mode: "temporal",
    };

    try {
      const res = await fetch(`${BACKEND_URL}/proctoring/analyze-window`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      });

      if (res.ok) {
        const data = await res.json();
        setInferenceResult({
          suspicion_score: data.suspicion_score,
          flag: data.flag,
          contributors: data.contributors || [],
          mode: "temporal",
        });

        if (data.signals) {
          setSignals((prev) => ({
            ...prev,
            ...data.signals,
          }));
        }
      }
    } catch {
      // Offline fallback handling
    }
  }, [activeScenarioId, sendBrowserEvent]);

  // 5. Periodic inference loop
  useEffect(() => {
    if (!autoLoop) return;
    const interval = setInterval(() => {
      sendWindowAnalysis();
    }, 2000);
    return () => clearInterval(interval);
  }, [autoLoop, sendWindowAnalysis]);

  // Apply scenario immediately on click
  const handleSelectScenario = (sc) => {
    setActiveScenarioId(sc.id);
    sendWindowAnalysis(sc.payload);
  };

  // Fetch full exam audit log
  const handleOpenAuditModal = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/results/${SESSION_ID}`);
      if (res.ok) {
        const data = await res.json();
        setAuditResults(data);
      }
    } catch {
      setAuditResults([]);
    }
    setShowAuditModal(true);
  };

  const getScoreColor = (score) => {
    if (score < 0.35) return "#10b981"; // Emerald
    if (score < 0.65) return "#f59e0b"; // Amber
    return "#ef4444"; // Red
  };

  return (
    <div style={{ fontFamily: "system-ui, -apple-system, sans-serif", backgroundColor: "#090d16", color: "#f8fafc", minHeight: "100vh", padding: "1.5rem 2rem" }}>
      
      {/* Top Header */}
      <header style={{ borderBottom: "1px solid #1e293b", paddingBottom: "1rem", marginBottom: "1.5rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.8rem" }}>
              <h1 style={{ fontSize: "1.7rem", margin: 0, fontWeight: "800", color: "#38bdf8", letterSpacing: "-0.5px" }}>
                Multimodal AI Proctoring System
              </h1>
              <span style={{ backgroundColor: "rgba(56, 189, 248, 0.15)", color: "#38bdf8", border: "1px solid rgba(56, 189, 248, 0.3)", padding: "3px 10px", borderRadius: "999px", fontSize: "0.75rem", fontWeight: "700" }}>
                Phase 4 Complete — Multimodal AI & BiLSTM
              </span>
            </div>
            <p style={{ color: "#94a3b8", margin: "0.3rem 0 0 0", fontSize: "0.9rem" }}>
              Continuous Visual, Acoustic, Browser & Facial Affective Proctoring Engine
            </p>
          </div>

          <div style={{ display: "flex", gap: "0.8rem", alignItems: "center" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", padding: "6px 12px", backgroundColor: "#1e293b", borderRadius: "8px", border: "1px solid #334155", fontSize: "0.85rem" }}>
              <span style={{ width: "9px", height: "9px", borderRadius: "50%", backgroundColor: health ? "#10b981" : "#ef4444" }}></span>
              <span>{health ? `FastAPI v${health.version}` : error ? "Backend Offline" : "Connecting..."}</span>
            </div>

            <button
              onClick={handleOpenAuditModal}
              style={{ padding: "0.5rem 1rem", backgroundColor: "#1e293b", color: "#38bdf8", border: "1px solid #38bdf8", borderRadius: "8px", cursor: "pointer", fontWeight: "600", fontSize: "0.85rem" }}
            >
              📊 Session Audit Log
            </button>

            <a
              href={`${BACKEND_URL}/docs`}
              target="_blank"
              rel="noreferrer"
              style={{ padding: "0.5rem 1rem", backgroundColor: "#0284c7", color: "white", borderRadius: "8px", textDecoration: "none", fontWeight: "600", fontSize: "0.85rem" }}
            >
              Swagger API Docs ↗
            </a>
          </div>
        </div>
      </header>

      {/* Main Grid Layout */}
      <div style={{ display: "grid", gridTemplateColumns: "1.45fr 1fr", gap: "1.5rem" }}>
        
        {/* Left Column: Live Webcam & Multimodal Telemetry */}
        <section style={{ display: "flex", flexDirection: "column", gap: "1.2rem" }}>
          
          {/* Webcam Box */}
          <div style={{ backgroundColor: "#131b2e", padding: "1.2rem", borderRadius: "12px", border: "1px solid #1e293b" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.8rem" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                <h2 style={{ fontSize: "1.1rem", margin: 0, fontWeight: "700" }}>Candidate Live Feed</h2>
                {cameraActive && (
                  <span style={{ backgroundColor: "#10b981", color: "#064e3b", padding: "2px 8px", borderRadius: "4px", fontSize: "0.7rem", fontWeight: "800" }}>
                    STREAMING
                  </span>
                )}
              </div>
              <div style={{ display: "flex", gap: "0.6rem" }}>
                {!cameraActive ? (
                  <button
                    onClick={startCamera}
                    style={{ padding: "0.4rem 0.9rem", backgroundColor: "#10b981", color: "white", border: "none", borderRadius: "6px", cursor: "pointer", fontWeight: "600", fontSize: "0.85rem" }}
                  >
                    Start Camera Feed
                  </button>
                ) : (
                  <button
                    onClick={stopCamera}
                    style={{ padding: "0.4rem 0.9rem", backgroundColor: "#ef4444", color: "white", border: "none", borderRadius: "6px", cursor: "pointer", fontWeight: "600", fontSize: "0.85rem" }}
                  >
                    Stop Camera
                  </button>
                )}
              </div>
            </div>

            <div style={{ width: "100%", height: "320px", backgroundColor: "#060913", borderRadius: "8px", overflow: "hidden", display: "flex", alignItems: "center", justifyContent: "center", position: "relative", border: "1px solid #1e293b" }}>
              <video
                ref={videoRef}
                autoPlay
                playsInline
                style={{ width: "100%", height: "100%", objectFit: "cover", display: cameraActive ? "block" : "none" }}
              />
              {!cameraActive && (
                <div style={{ textAlign: "center", color: "#64748b" }}>
                  <div style={{ fontSize: "2rem", marginBottom: "0.3rem" }}>📹</div>
                  <p style={{ fontSize: "0.95rem", margin: "0 0 0.3rem 0", color: "#94a3b8" }}>Webcam is currently idle</p>
                  <p style={{ fontSize: "0.8rem", margin: 0 }}>Click "Start Camera Feed" to preview candidate video stream</p>
                </div>
              )}
            </div>
          </div>

          {/* Suspicion Probability & Verdict Banner */}
          <div style={{ backgroundColor: "#131b2e", padding: "1.2rem", borderRadius: "12px", border: `1px solid ${inferenceResult.flag ? "rgba(239, 68, 68, 0.4)" : "#1e293b"}` }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.8rem" }}>
              <div>
                <span style={{ fontSize: "0.8rem", color: "#94a3b8", fontWeight: "600", textTransform: "uppercase" }}>
                  Learned Multimodal Fusion + BiLSTM Verdict
                </span>
                <div style={{ display: "flex", alignItems: "baseline", gap: "0.8rem", marginTop: "0.2rem" }}>
                  <span style={{ fontSize: "2.2rem", fontWeight: "900", color: getScoreColor(inferenceResult.suspicion_score) }}>
                    {(inferenceResult.suspicion_score * 100).toFixed(1)}%
                  </span>
                  <span style={{ fontSize: "1.1rem", fontWeight: "700", color: inferenceResult.flag ? "#ef4444" : "#10b981" }}>
                    {inferenceResult.flag ? "⚠️ SUSPICIOUS PATTERN DETECTED" : "✅ NORMAL ATTENTIVE BEHAVIOR"}
                  </span>
                </div>
              </div>

              <div style={{ textAlign: "right" }}>
                <span style={{ fontSize: "0.75rem", color: "#64748b" }}>ANALYSIS ENGINE</span>
                <div style={{ fontSize: "0.9rem", fontWeight: "700", color: "#38bdf8" }}>BiLSTM Temporal Context</div>
              </div>
            </div>

            {/* Meter Bar */}
            <div style={{ width: "100%", height: "10px", backgroundColor: "#060913", borderRadius: "999px", overflow: "hidden", marginBottom: "0.8rem" }}>
              <div
                style={{
                  height: "100%",
                  width: `${Math.min(100, Math.max(0, inferenceResult.suspicion_score * 100))}%`,
                  backgroundColor: getScoreColor(inferenceResult.suspicion_score),
                  transition: "width 0.4s ease, background-color 0.4s ease",
                }}
              />
            </div>

            {/* Evidence Tags */}
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", alignItems: "center" }}>
              <span style={{ fontSize: "0.75rem", color: "#64748b" }}>CONTRIBUTING EVIDENCE:</span>
              {inferenceResult.contributors.length === 0 ? (
                <span style={{ fontSize: "0.75rem", color: "#10b981", backgroundColor: "rgba(16, 185, 129, 0.1)", padding: "2px 8px", borderRadius: "4px" }}>
                  None (Within normal behavioral boundaries)
                </span>
              ) : (
                inferenceResult.contributors.map((tag, idx) => (
                  <span key={idx} style={{ fontSize: "0.75rem", color: "#f87171", backgroundColor: "rgba(239, 68, 68, 0.15)", border: "1px solid rgba(239, 68, 68, 0.3)", padding: "2px 8px", borderRadius: "4px", fontWeight: "600" }}>
                    {tag}
                  </span>
                ))
              )}
            </div>
          </div>

          {/* 6-Modality Telemetry Cards Grid */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "0.8rem" }}>
            
            {/* 1. Face & Person Presence */}
            <div style={{ backgroundColor: "#131b2e", padding: "0.9rem", borderRadius: "10px", border: "1px solid #1e293b" }}>
              <div style={{ fontSize: "0.75rem", color: "#94a3b8", fontWeight: "700" }}>FACE / PERSON</div>
              <div style={{ fontSize: "1.1rem", fontWeight: "800", color: signals.multi_person_flag ? "#ef4444" : signals.person_count === 1 ? "#10b981" : "#f59e0b", marginTop: "0.3rem" }}>
                {signals.multi_person_flag ? "Multi-Person (2+)" : signals.person_count === 1 ? "1 Face Present" : "0 Faces (Absent)"}
              </div>
              <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: "0.2rem" }}>
                Count: {signals.person_count} • BBox Conf: 0.94
              </div>
            </div>

            {/* 2. Gaze Tracking */}
            <div style={{ backgroundColor: "#131b2e", padding: "0.9rem", borderRadius: "10px", border: "1px solid #1e293b" }}>
              <div style={{ fontSize: "0.75rem", color: "#94a3b8", fontWeight: "700" }}>GAZE (IRIS MESH)</div>
              <div style={{ fontSize: "1.1rem", fontWeight: "800", color: signals.looking_away ? "#f59e0b" : "#10b981", marginTop: "0.3rem" }}>
                {signals.looking_away ? "Looking Away" : "Center / Screen"}
              </div>
              <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: "0.2rem" }}>
                Ratio X: {Number(signals.gaze_ratio).toFixed(2)} (Center: 0.50)
              </div>
            </div>

            {/* 3. Head Pose */}
            <div style={{ backgroundColor: "#131b2e", padding: "0.9rem", borderRadius: "10px", border: "1px solid #1e293b" }}>
              <div style={{ fontSize: "0.75rem", color: "#94a3b8", fontWeight: "700" }}>HEAD POSE (3D)</div>
              <div style={{ fontSize: "1.1rem", fontWeight: "800", color: signals.turned_away ? "#f59e0b" : "#10b981", marginTop: "0.3rem" }}>
                {signals.turned_away ? "Turned Away" : "Facing Screen"}
              </div>
              <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: "0.2rem" }}>
                Yaw: {Number(signals.yaw).toFixed(1)}° • Pitch: {Number(signals.pitch).toFixed(1)}°
              </div>
            </div>

            {/* 4. Audio Pipeline (Silero VAD) */}
            <div style={{ backgroundColor: "#131b2e", padding: "0.9rem", borderRadius: "10px", border: "1px solid #1e293b" }}>
              <div style={{ fontSize: "0.75rem", color: "#94a3b8", fontWeight: "700" }}>AUDIO (SILERO VAD)</div>
              <div style={{ fontSize: "1.1rem", fontWeight: "800", color: signals.speech_detected ? "#ef4444" : "#10b981", marginTop: "0.3rem" }}>
                {signals.speech_detected ? "Speech Detected" : "Quiet / No Voice"}
              </div>
              <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: "0.2rem" }}>
                VAD Prob: {((signals.speech_probability || 0.0) * 100).toFixed(0)}% • 16 kHz
              </div>
            </div>

            {/* 5. Browser Tab Monitoring */}
            <div style={{ backgroundColor: "#131b2e", padding: "0.9rem", borderRadius: "10px", border: "1px solid #1e293b" }}>
              <div style={{ fontSize: "0.75rem", color: "#94a3b8", fontWeight: "700" }}>BROWSER TAB MONITOR</div>
              <div style={{ fontSize: "1.1rem", fontWeight: "800", color: tabStatus === "Active" ? "#10b981" : "#ef4444", marginTop: "0.3rem" }}>
                {tabStatus}
              </div>
              <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: "0.2rem" }}>
                Violations / Switches: {switchCount}
              </div>
            </div>

            {/* 6. Facial Emotion (Phase 2 Differentiator) */}
            <div style={{ backgroundColor: "#131b2e", padding: "0.9rem", borderRadius: "10px", border: "1px solid rgba(168, 85, 247, 0.4)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: "0.75rem", color: "#c084fc", fontWeight: "700" }}>FACIAL EMOTION (FER)</span>
                <span style={{ fontSize: "0.65rem", backgroundColor: "rgba(168, 85, 247, 0.2)", color: "#c084fc", padding: "1px 6px", borderRadius: "4px" }}>
                  Context Only
                </span>
              </div>
              <div style={{ fontSize: "1.1rem", fontWeight: "800", color: "#e9d5ff", marginTop: "0.3rem" }}>
                {signals.dominant_emotion || "Neutral"}
              </div>
              <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginTop: "0.2rem" }}>
                Conf: {((signals.emotion_confidence || 0.85) * 100).toFixed(0)}% • Non-Punitive
              </div>
            </div>

          </div>

          {/* Ethical Safeguard Banner */}
          <div style={{ backgroundColor: "rgba(30, 41, 59, 0.6)", padding: "0.6rem 1rem", borderRadius: "8px", borderLeft: "3px solid #38bdf8", fontSize: "0.75rem", color: "#94a3b8", lineHeight: "1.4" }}>
            <strong style={{ color: "#38bdf8" }}>Ethical Fairness Rule 4:</strong> Facial emotion serves strictly as an affective context modifier in neural attention. Stress, Fear, or Surprise <strong>never</strong> independently generates a cheating penalty without corroborating audio, visual, or tab anomalies.
          </div>
        </section>

        {/* Right Column: Live Test Scenarios & Real-Time Controls */}
        <section style={{ display: "flex", flexDirection: "column", gap: "1.2rem" }}>
          
          {/* Quick Test / Simulation Scenarios */}
          <div style={{ backgroundColor: "#131b2e", padding: "1.2rem", borderRadius: "12px", border: "1px solid #1e293b" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
              <h3 style={{ fontSize: "1.05rem", margin: 0, fontWeight: "700" }}>Live Test & Simulation Scenarios</h3>
              <span style={{ fontSize: "0.7rem", color: "#64748b" }}>Interactive Examiner Demos</span>
            </div>
            <p style={{ fontSize: "0.8rem", color: "#94a3b8", margin: "0 0 1rem 0" }}>
              Click any scenario to inject its multi-sensor signature into the live FastAPI backend & BiLSTM inference engine:
            </p>

            <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
              {SCENARIOS.map((sc) => {
                const isSelected = activeScenarioId === sc.id;
                return (
                  <div
                    key={sc.id}
                    onClick={() => handleSelectScenario(sc)}
                    style={{
                      padding: "0.75rem",
                      borderRadius: "8px",
                      backgroundColor: isSelected ? "#1e293b" : "#090d16",
                      border: isSelected ? "1px solid #38bdf8" : "1px solid #1e293b",
                      cursor: "pointer",
                      transition: "all 0.2s ease",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span style={{ fontWeight: "700", fontSize: "0.85rem", color: isSelected ? "#38bdf8" : "#f1f5f9" }}>
                        {sc.label}
                      </span>
                      {isSelected && (
                        <span style={{ fontSize: "0.65rem", backgroundColor: "#38bdf8", color: "#0f172a", padding: "1px 6px", borderRadius: "4px", fontWeight: "800" }}>
                          ACTIVE
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginTop: "0.25rem", lineHeight: "1.3" }}>
                      {sc.desc}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Loop Toggle */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "1rem", paddingTop: "0.8rem", borderTop: "1px solid #1e293b" }}>
              <div>
                <div style={{ fontSize: "0.85rem", fontWeight: "700" }}>Continuous ML Stream (2s Loop)</div>
                <div style={{ fontSize: "0.75rem", color: "#64748b" }}>Periodically updates BiLSTM temporal buffer</div>
              </div>
              <button
                onClick={() => setAutoLoop(!autoLoop)}
                style={{
                  padding: "0.4rem 0.9rem",
                  backgroundColor: autoLoop ? "#10b981" : "#334155",
                  color: "white",
                  border: "none",
                  borderRadius: "6px",
                  cursor: "pointer",
                  fontWeight: "600",
                  fontSize: "0.8rem",
                }}
              >
                {autoLoop ? "Loop Running" : "Enable Loop"}
              </button>
            </div>
          </div>

          {/* Browser Events Stream Card */}
          <div style={{ backgroundColor: "#131b2e", padding: "1.2rem", borderRadius: "12px", border: "1px solid #1e293b" }}>
            <h3 style={{ fontSize: "0.95rem", margin: "0 0 0.6rem 0", color: "#94a3b8" }}>Real-Time Browser Audit Stream</h3>
            <div style={{ maxHeight: "140px", overflowY: "auto", fontSize: "0.75rem", display: "flex", flexDirection: "column", gap: "0.3rem" }}>
              {eventsLog.length === 0 ? (
                <div style={{ color: "#64748b", padding: "0.5rem 0" }}>
                  Switch to another browser tab or minimize to observe instant event capture.
                </div>
              ) : (
                eventsLog.map((ev, i) => (
                  <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "4px 8px", backgroundColor: "#090d16", borderRadius: "4px", border: "1px solid #1e293b" }}>
                    <span style={{ color: ev.type.includes("hidden") || ev.type.includes("blur") ? "#f87171" : "#34d399", fontWeight: "600" }}>
                      {ev.type}
                    </span>
                    <span style={{ color: "#64748b" }}>{ev.time}</span>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Architecture Highlights Card */}
          <div style={{ backgroundColor: "#131b2e", padding: "1.2rem", borderRadius: "12px", border: "1px solid #1e293b" }}>
            <h3 style={{ fontSize: "0.95rem", margin: "0 0 0.6rem 0", color: "#94a3b8" }}>Deep Learning Architecture Stack</h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.6rem", fontSize: "0.75rem" }}>
              <div style={{ backgroundColor: "#090d16", padding: "0.6rem", borderRadius: "6px" }}>
                <span style={{ color: "#64748b" }}>VISUAL PIPELINE:</span>
                <div style={{ fontWeight: "700", color: "#38bdf8" }}>MediaPipe + solvePnP</div>
              </div>
              <div style={{ backgroundColor: "#090d16", padding: "0.6rem", borderRadius: "6px" }}>
                <span style={{ color: "#64748b" }}>AUDIO VAD:</span>
                <div style={{ fontWeight: "700", color: "#38bdf8" }}>Silero VAD (16kHz)</div>
              </div>
              <div style={{ backgroundColor: "#090d16", padding: "0.6rem", borderRadius: "6px" }}>
                <span style={{ color: "#64748b" }}>EMOTION CNN:</span>
                <div style={{ fontWeight: "700", color: "#c084fc" }}>PyTorch FER2013</div>
              </div>
              <div style={{ backgroundColor: "#090d16", padding: "0.6rem", borderRadius: "6px" }}>
                <span style={{ color: "#64748b" }}>TEMPORAL MODEL:</span>
                <div style={{ fontWeight: "700", color: "#34d399" }}>Bidirectional LSTM</div>
              </div>
            </div>
          </div>

        </section>

      </div>

      {/* Session Audit Modal */}
      {showAuditModal && (
        <div style={{ position: "fixed", inset: 0, backgroundColor: "rgba(0,0,0,0.8)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000, padding: "2rem" }}>
          <div style={{ backgroundColor: "#131b2e", borderRadius: "16px", border: "1px solid #334155", maxWidth: "800px", width: "100%", maxHeight: "85vh", display: "flex", flexDirection: "column", overflow: "hidden" }}>
            <div style={{ padding: "1.2rem 1.5rem", borderBottom: "1px solid #1e293b", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <h3 style={{ margin: 0, fontSize: "1.2rem", color: "#38bdf8" }}>Session Forensic Audit Log</h3>
                <span style={{ fontSize: "0.8rem", color: "#94a3b8" }}>Session ID: {SESSION_ID}</span>
              </div>
              <button
                onClick={() => setShowAuditModal(false)}
                style={{ padding: "0.4rem 0.8rem", backgroundColor: "#334155", color: "white", border: "none", borderRadius: "6px", cursor: "pointer", fontWeight: "700" }}
              >
                ✕ Close
              </button>
            </div>

            <div style={{ padding: "1.5rem", overflowY: "auto", display: "flex", flexDirection: "column", gap: "1rem" }}>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1rem" }}>
                <div style={{ backgroundColor: "#090d16", padding: "1rem", borderRadius: "8px", border: "1px solid #1e293b" }}>
                  <div style={{ fontSize: "0.75rem", color: "#64748b" }}>TOTAL WINDOWS ANALYZED</div>
                  <div style={{ fontSize: "1.4rem", fontWeight: "800", color: "#38bdf8" }}>{auditResults.length}</div>
                </div>
                <div style={{ backgroundColor: "#090d16", padding: "1rem", borderRadius: "8px", border: "1px solid #1e293b" }}>
                  <div style={{ fontSize: "0.75rem", color: "#64748b" }}>FLAGGED SUSPICIOUS WINDOWS</div>
                  <div style={{ fontSize: "1.4rem", fontWeight: "800", color: "#ef4444" }}>
                    {auditResults.filter((r) => r.flag).length}
                  </div>
                </div>
                <div style={{ backgroundColor: "#090d16", padding: "1rem", borderRadius: "8px", border: "1px solid #1e293b" }}>
                  <div style={{ fontSize: "0.75rem", color: "#64748b" }}>EXAM VERDICT</div>
                  <div style={{ fontSize: "1.1rem", fontWeight: "800", color: auditResults.filter((r) => r.flag).length > 2 ? "#ef4444" : "#10b981", marginTop: "0.2rem" }}>
                    {auditResults.filter((r) => r.flag).length > 2 ? "Requires Review" : "Integrity Verified"}
                  </div>
                </div>
              </div>

              <div>
                <h4 style={{ fontSize: "0.95rem", margin: "0.5rem 0", color: "#cbd5e1" }}>Recent Inference Timeline</h4>
                <div style={{ maxHeight: "250px", overflowY: "auto", border: "1px solid #1e293b", borderRadius: "8px" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8rem", textAlign: "left" }}>
                    <thead style={{ backgroundColor: "#090d16", color: "#94a3b8", position: "sticky", top: 0 }}>
                      <tr>
                        <th style={{ padding: "8px 12px" }}>Time</th>
                        <th style={{ padding: "8px 12px" }}>Suspicion Score</th>
                        <th style={{ padding: "8px 12px" }}>Status</th>
                        <th style={{ padding: "8px 12px" }}>Evidence Flags</th>
                      </tr>
                    </thead>
                    <tbody>
                      {auditResults.length === 0 ? (
                        <tr>
                          <td colSpan="4" style={{ padding: "16px", textAlign: "center", color: "#64748b" }}>
                            No inference records yet. Run a test scenario to generate audit entries.
                          </td>
                        </tr>
                      ) : (
                        auditResults.map((rec, i) => (
                          <tr key={i} style={{ borderTop: "1px solid #1e293b" }}>
                            <td style={{ padding: "8px 12px", color: "#94a3b8" }}>
                              {new Date(rec.window_start).toLocaleTimeString()}
                            </td>
                            <td style={{ padding: "8px 12px", fontWeight: "700", color: getScoreColor(rec.suspicion_score) }}>
                              {(rec.suspicion_score * 100).toFixed(1)}%
                            </td>
                            <td style={{ padding: "8px 12px" }}>
                              <span style={{ padding: "2px 6px", borderRadius: "4px", fontSize: "0.7rem", fontWeight: "700", backgroundColor: rec.flag ? "rgba(239,68,68,0.2)" : "rgba(16,185,129,0.2)", color: rec.flag ? "#ef4444" : "#10b981" }}>
                                {rec.flag ? "FLAGGED" : "CLEAR"}
                              </span>
                            </td>
                            <td style={{ padding: "8px 12px", color: "#cbd5e1" }}>
                              {(rec.contributors || []).join(", ") || "—"}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

export default App;