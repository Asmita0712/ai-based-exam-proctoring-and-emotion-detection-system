import { useEffect, useState, useRef } from "react";
import examApi from "../services/examApi";

export default function DiagnosticLab() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);
  const [cameraActive, setCameraActive] = useState(false);
  const [tabStatus, setTabStatus] = useState("Active");
  const [switchCount, setSwitchCount] = useState(0);
  const [eventsLog, setEventsLog] = useState([]);
  const [inferenceMode, setInferenceMode] = useState("temporal");
  const [inferenceResult, setInferenceResult] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [selectedScenario, setSelectedScenario] = useState("live");
  const [realtimeInferring, setRealtimeInferring] = useState(false);
  const [lastLatency, setLastLatency] = useState(null);
  const [micActive, setMicActive] = useState(false);
  const [micLevel, setMicLevel] = useState(0);
  const [examSummary, setExamSummary] = useState(null);
  const [showReportModal, setShowReportModal] = useState(false);
  const [loadingReport, setLoadingReport] = useState(false);

  const fetchExamSummary = async () => {
    try {
      setLoadingReport(true);
      const data = await examApi.getSessionSummary("demo-session-001");
      setExamSummary(data);
      setShowReportModal(true);
    } catch (e) {
      console.error("Failed to fetch exam summary:", e);
    } finally {
      setLoadingReport(false);
    }
  };

  const handleEndExam = () => {
    stopCamera();
    fetchExamSummary();
  };

  const handleResetSession = async () => {
    try {
      await examApi.resetSession("demo-session-001");
      setSwitchCount(0);
      setEventsLog([]);
      setInferenceResult(null);
      setExamSummary(null);
      setShowReportModal(false);
    } catch (e) {
      console.error("Failed to reset session:", e);
    }
  };

  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const isAwayRef = useRef(false);
  const isInferringFrameRef = useRef(false);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const audioDataRef = useRef(null);
  const speechStreakRef = useRef(0);

  // 1. Health check poll
  useEffect(() => {
    examApi.getHealth()
      .then((data) => {
        setHealth(data);
        setError(null);
      })
      .catch((err) => setError(err.message));
  }, []);

  // 2. Camera & Microphone feed handler
  const startCamera = async () => {
    // Clean-slate reset of session history so new exam session starts at 0 frames
    try {
      await examApi.resetSession("demo-session-001");
      setSwitchCount(0);
      setEventsLog([]);
      setInferenceResult(null);
      setExamSummary(null);
    } catch (_) {}

    try {
      let stream = null;
      let hasAudio = false;

      // Attempt to acquire both video and audio
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480 },
          audio: true,
        });
        hasAudio = true;
      } catch (audioErr) {
        console.warn("Audio/Mic permission not granted, falling back to video only:", audioErr);
        stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480 },
          audio: false,
        });
      }

      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.muted = true;
      }

      // Initialize Web Audio API Analyser for real-time voice VAD
      if (hasAudio && stream.getAudioTracks().length > 0) {
        try {
          const AudioContextClass = window.AudioContext || window.webkitAudioContext;
          const audioCtx = new AudioContextClass();
          const source = audioCtx.createMediaStreamSource(stream);
          const analyser = audioCtx.createAnalyser();
          analyser.fftSize = 512;
          analyser.smoothingTimeConstant = 0.3;
          source.connect(analyser);

          audioContextRef.current = audioCtx;
          analyserRef.current = analyser;
          audioDataRef.current = new Float32Array(analyser.fftSize);
          speechStreakRef.current = 0;
          setMicActive(true);
        } catch (e) {
          console.warn("AudioContext setup failed:", e);
        }
      }

      setCameraActive(true);
      setSelectedScenario("live");
    } catch (err) {
      alert("Unable to access webcam or microphone: " + err.message);
    }
  };

  const stopCamera = () => {
    if (audioContextRef.current) {
      try {
        audioContextRef.current.close();
      } catch (e) {}
      audioContextRef.current = null;
    }
    analyserRef.current = null;
    audioDataRef.current = null;
    setMicActive(false);
    setMicLevel(0);

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setCameraActive(false);
  };

  // 3. Real-Time Camera Frame & Audio Processing Loop
  useEffect(() => {
    if (!cameraActive) return;

    const canvas = document.createElement("canvas");
    canvas.width = 320;
    canvas.height = 240;
    const ctx = canvas.getContext("2d");

    const interval = setInterval(async () => {
      if (!videoRef.current || isInferringFrameRef.current) return;
      if (videoRef.current.readyState < 2) return; // Need ready video data

      try {
        isInferringFrameRef.current = true;
        setRealtimeInferring(true);
        const t0 = performance.now();

        ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
        const imageBase64 = canvas.toDataURL("image/jpeg", 0.6);

        // Real-Time Audio Energy Analysis (True Float32 Time-Domain RMS)
        let speechProbability = 0.0;
        let sustainedTalking = false;
        let avgLevel = 0;

        if (analyserRef.current && audioDataRef.current) {
          analyserRef.current.getFloatTimeDomainData(audioDataRef.current);

          // Compute True RMS over PCM sample buffer [-1.0, 1.0]
          let sumSquares = 0;
          const pcm = audioDataRef.current;
          for (let i = 0; i < pcm.length; i++) {
            sumSquares += pcm[i] * pcm[i];
          }
          const rms = Math.sqrt(sumSquares / pcm.length);
          // Scale RMS to 0..100 for visual telemetry meter (rms typically 0.005 to 0.25)
          avgLevel = Math.round(Math.min(100, rms * 550));
          setMicLevel(avgLevel);

          // Calibrated speech threshold (+10% additional sensitivity, rms >= 0.034):
          // Room ambient silence / keyboard typing is rms < 0.025
          // Human vocal talking into microphone is rms >= 0.034
          if (rms >= 0.034) {
            speechStreakRef.current = Math.min(10, speechStreakRef.current + 1);
          } else {
            speechStreakRef.current = Math.max(0, speechStreakRef.current - 1);
          }

          // Sustained speech or clear vocal utterance
          if (speechStreakRef.current >= 2 || (speechStreakRef.current >= 1 && rms >= 0.052)) {
            sustainedTalking = true;
            speechProbability = Math.min(1.0, Math.max(0.60, (rms - 0.020) / 0.075));
          } else if (speechStreakRef.current === 1) {
            speechProbability = Math.min(0.50, Math.max(0.25, (rms - 0.020) / 0.075));
          }
        }

        // Live browser focus verification at frame capture time
        const isCurrentlyHidden = document.hidden;
        const isCurrentlyFocused = typeof document.hasFocus === "function" ? document.hasFocus() : true;
        const isCurrentlyAway = isCurrentlyHidden || !isCurrentlyFocused;

        const data = await examApi.sendProctoringFrame({
          session_id: "demo-session-001",
          image_base64: imageBase64,
          mode: inferenceMode,
          audio_signals: {
            speech_probability: speechProbability,
            sustained_talking: sustainedTalking,
            audio_level: Math.round(avgLevel),
          },
          browser_signals: {
            tab_hidden: isCurrentlyHidden,
            window_blur: !isCurrentlyFocused,
            is_away: isCurrentlyAway,
          },
        });

        if (data) {
          setInferenceResult(data);
          setLastLatency(Math.round(performance.now() - t0));
        }
      } catch (err) {
        console.error("Real-time frame error:", err);
      } finally {
        isInferringFrameRef.current = false;
        setRealtimeInferring(false);
      }
    }, 380);

    return () => clearInterval(interval);
  }, [cameraActive, inferenceMode]);

  // 4. Browser tab/window event tracking
  const sendBrowserEvent = (eventType) => {
    const payload = {
      session_id: "demo-session-001",
      type: eventType,
      timestamp: new Date().toISOString(),
    };

    examApi.logBrowserEvent(payload).catch(() => {});

    setEventsLog((prev) => [
      { type: eventType, time: new Date().toLocaleTimeString() },
      ...prev.slice(0, 8),
    ]);
  };

  useEffect(() => {
    const markAway = (status, eventType) => {
      setTabStatus(status);
      sendBrowserEvent(eventType);
      if (!isAwayRef.current) {
        isAwayRef.current = true;
        setSwitchCount((c) => c + 1);
      }
    };

    const markActive = (eventType) => {
      sendBrowserEvent(eventType);
      const isVisible = !document.hidden;
      const isFocused = typeof document.hasFocus === "function" ? document.hasFocus() : true;

      if (isVisible && isFocused) {
        isAwayRef.current = false;
        setTabStatus("Active");
      } else if (!isVisible) {
        setTabStatus("Tab Hidden");
      } else {
        setTabStatus("Window Unfocused");
      }
    };

    let blurTimeout = null;

    const handleVisibility = () => {
      if (document.hidden) {
        markAway("Tab Hidden", "tab_hidden");
      } else {
        markActive("tab_visible");
      }
    };

    const handleBlur = () => {
      // Debounce window blur to avoid false alarms from camera permission prompts or system tooltips
      if (blurTimeout) clearTimeout(blurTimeout);
      blurTimeout = setTimeout(() => {
        const isFocused = typeof document.hasFocus === "function" ? document.hasFocus() : true;
        if (!isFocused && !document.hidden) {
          markAway("Window Unfocused", "window_blur");
        }
      }, 700);
    };

    const handleFocus = () => {
      if (blurTimeout) clearTimeout(blurTimeout);
      markActive("window_focus");
    };

    const syncActiveState = () => {
      if (blurTimeout) clearTimeout(blurTimeout);
      if (!document.hidden) {
        const isFocused = typeof document.hasFocus === "function" ? document.hasFocus() : true;
        if (isFocused && (isAwayRef.current || tabStatus !== "Active")) {
          markActive("window_focus");
        }
      }
    };

    document.addEventListener("visibilitychange", handleVisibility);
    window.addEventListener("blur", handleBlur);
    window.addEventListener("focus", handleFocus);
    window.addEventListener("pointerdown", syncActiveState);
    window.addEventListener("click", syncActiveState);

    return () => {
      if (blurTimeout) clearTimeout(blurTimeout);
      document.removeEventListener("visibilitychange", handleVisibility);
      window.removeEventListener("blur", handleBlur);
      window.removeEventListener("focus", handleFocus);
      window.removeEventListener("pointerdown", syncActiveState);
      window.removeEventListener("click", syncActiveState);
    };
  }, []);

  // 5. Manual Scenario Runner (Optional when camera is idle)
  const runWindowAnalysis = async (scenario = selectedScenario, targetMode = inferenceMode) => {
    setAnalyzing(true);
    let visualSignals = {
      person_count: 1,
      multi_person_flag: false,
      looking_away: false,
      gaze: { gaze_ratio: 0.15 },
      head_pose: { yaw: 2.1, pitch: -3.4 },
      turned_away: false,
      emotion: { dominant_emotion: "neutral", emotion_confidence: 0.92 },
    };

    let audioSignals = {
      speech_probability: 0.05,
      sustained_talking: false,
    };

    if (scenario === "multi_person") {
      visualSignals.person_count = 2;
      visualSignals.multi_person_flag = true;
      visualSignals.emotion = { dominant_emotion: "surprise", emotion_confidence: 0.81 };
    } else if (scenario === "looking_away") {
      visualSignals.looking_away = true;
      visualSignals.turned_away = true;
      visualSignals.head_pose = { yaw: 38.5, pitch: 12.0 };
      visualSignals.gaze = { gaze_ratio: 0.48 };
      visualSignals.emotion = { dominant_emotion: "fear", emotion_confidence: 0.76 };
    } else if (scenario === "talking") {
      audioSignals.speech_probability = 0.88;
      audioSignals.sustained_talking = true;
      visualSignals.emotion = { dominant_emotion: "neutral", emotion_confidence: 0.85 };
    } else if (scenario === "tab_cheat") {
      visualSignals.looking_away = true;
      audioSignals.speech_probability = 0.65;
      audioSignals.sustained_talking = true;
      visualSignals.emotion = { dominant_emotion: "fear", emotion_confidence: 0.89 };
    }

    if (tabStatus !== "Active") {
      visualSignals.looking_away = true;
    }

    try {
      // In temporal mode, send 4 consecutive frames so the sequence buffer registers sustained status
      const iters = targetMode === "temporal" ? 4 : 1;
      let lastData = null;
      for (let i = 0; i < iters; i++) {
        const data = await examApi.sendProctoringWindow({
          session_id: "simulation-preview-session",
          visual_signals: visualSignals,
          audio_signals: audioSignals,
          mode: targetMode,
        });
        if (data) {
          lastData = data;
        }
      }
      if (lastData) {
        setInferenceResult(lastData);
      }
    } catch (e) {
      console.error("Inference request failed", e);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleModeChange = (newMode) => {
    setInferenceMode(newMode);
    if (!cameraActive) {
      runWindowAnalysis(selectedScenario, newMode);
    }
  };

  // Run initial baseline if camera is not on
  useEffect(() => {
    if (!cameraActive) {
      runWindowAnalysis(selectedScenario);
    }
  }, [inferenceMode]);

  const signals = inferenceResult?.signals || {};

  return (
    <div style={{ fontFamily: "system-ui, -apple-system, sans-serif", backgroundColor: "#0f172a", color: "#f8fafc", minHeight: "100vh", padding: "2rem" }}>
      {/* Header */}
      <header style={{ borderBottom: "1px solid #334155", paddingBottom: "1.5rem", marginBottom: "2rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.8rem", marginBottom: "0.4rem" }}>
              <h1 style={{ fontSize: "1.8rem", margin: 0, fontWeight: "700", color: "#38bdf8" }}>
                AI Multimodal Exam Proctoring & Suspicious Activity Detection
              </h1>
              <span style={{ backgroundColor: "#065f46", color: "#34d399", padding: "3px 10px", borderRadius: "12px", fontSize: "0.75rem", fontWeight: "700" }}>
                ALL PHASES OPERATIONAL
              </span>
            </div>
            <p style={{ color: "#94a3b8", margin: 0, fontSize: "0.95rem" }}>
              Live Real-Time AI Pipeline: YOLOv8 Person Detection + MediaPipe Iris Mesh + solvePnP 3D Head Pose + 7-Class Emotion FER + BiLSTM Temporal Fusion
            </p>
          </div>
          <div style={{ display: "flex", gap: "0.8rem" }}>
            <a
              href={`${examApi.getApiBaseUrl()}/docs`}
              target="_blank"
              rel="noreferrer"
              style={{ padding: "0.6rem 1.2rem", backgroundColor: "#0284c7", color: "white", borderRadius: "8px", textDecoration: "none", fontWeight: "600", fontSize: "0.9rem" }}
            >
              Interactive API Docs (Swagger) ↗
            </a>
          </div>
        </div>

        {/* Phase Badges Bar */}
        <div style={{ display: "flex", gap: "0.6rem", marginTop: "1.2rem", flexWrap: "wrap" }}>
          {[
            { phase: "Phase 0", title: "API & Base Env", status: "Complete", color: "#10b981" },
            { phase: "Phase 1", title: "Live Visual & Tab Pipelines", status: "Active Real-Time", color: "#10b981" },
            { phase: "Phase 2", title: "Facial Emotion Recognition (FER)", status: "Active Real-Time", color: "#10b981" },
            { phase: "Phase 3", title: "Learned Fusion & BiLSTM Temporal", status: "Active Real-Time", color: "#10b981" },
            { phase: "Phase 4", title: "Evaluation & Ablation (97.35% Acc)", status: "Benchmarked", color: "#38bdf8" },
          ].map((item, idx) => (
            <div key={idx} style={{ backgroundColor: "#1e293b", border: "1px solid #334155", padding: "4px 10px", borderRadius: "6px", fontSize: "0.8rem", display: "flex", gap: "6px", alignItems: "center" }}>
              <span style={{ fontWeight: "700", color: "#cbd5e1" }}>{item.phase}:</span>
              <span style={{ color: "#94a3b8" }}>{item.title}</span>
              <span style={{ backgroundColor: item.color + "22", color: item.color, padding: "1px 6px", borderRadius: "4px", fontSize: "0.7rem", fontWeight: "700" }}>
                ✓ {item.status}
              </span>
            </div>
          ))}
        </div>
      </header>

      {/* Main Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "1.45fr 1fr", gap: "2rem" }}>
        {/* Left Column: Live Webcam + Scenario Simulation */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          {/* Candidate Video Feed Card */}
          <section style={{ backgroundColor: "#1e293b", padding: "1.5rem", borderRadius: "12px", border: "1px solid #334155" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
              <div>
                <h2 style={{ fontSize: "1.2rem", margin: 0 }}>Candidate Video Feed (Real-Time AI)</h2>
                <span style={{ fontSize: "0.8rem", color: "#94a3b8" }}>
                  {cameraActive ? (
                    <span style={{ color: "#34d399", fontWeight: "600" }}>
                      ● Streaming live webcam frames to PyTorch / YOLOv8 / MediaPipe / EmotionCNN ({lastLatency ? `${lastLatency}ms latency` : "Streaming..."})
                    </span>
                  ) : (
                    "Click Start Camera Feed to begin live computer vision inference"
                  )}
                </span>
              </div>
              <div style={{ display: "flex", gap: "0.6rem", flexWrap: "wrap" }}>
                {!cameraActive ? (
                  <>
                    <button
                      onClick={startCamera}
                      style={{ padding: "0.5rem 1.2rem", backgroundColor: "#10b981", color: "white", border: "none", borderRadius: "6px", cursor: "pointer", fontWeight: "700" }}
                    >
                      ▶ Start Camera Feed
                    </button>
                    <button
                      onClick={fetchExamSummary}
                      disabled={loadingReport}
                      style={{ padding: "0.5rem 1.2rem", backgroundColor: "#334155", color: "#38bdf8", border: "1px solid #475569", borderRadius: "6px", cursor: "pointer", fontWeight: "700" }}
                    >
                      {loadingReport ? "Loading Report..." : "📊 View Integrity Score"}
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      onClick={stopCamera}
                      style={{ padding: "0.5rem 1rem", backgroundColor: "#64748b", color: "white", border: "none", borderRadius: "6px", cursor: "pointer", fontWeight: "600" }}
                    >
                      Pause Feed
                    </button>
                    <button
                      onClick={handleEndExam}
                      disabled={loadingReport}
                      style={{ padding: "0.5rem 1.2rem", backgroundColor: "#6366f1", color: "white", border: "none", borderRadius: "6px", cursor: "pointer", fontWeight: "700", boxShadow: "0 0 12px rgba(99,102,241,0.4)" }}
                    >
                      {loadingReport ? "Calculating Report..." : "🏁 End Exam & View Integrity Report"}
                    </button>
                  </>
                )}
              </div>
            </div>

            <div style={{ width: "100%", height: "380px", backgroundColor: "#020617", borderRadius: "8px", overflow: "hidden", display: "flex", alignItems: "center", justifyContent: "center", position: "relative" }}>
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                style={{ width: "100%", height: "100%", objectFit: "cover", display: cameraActive ? "block" : "none" }}
              />
              {!cameraActive && (
                <div style={{ textAlign: "center", color: "#64748b" }}>
                  <p style={{ fontSize: "1.2rem", margin: "0 0 0.5rem 0", fontWeight: "600" }}>Camera is currently idle</p>
                  <p style={{ fontSize: "0.85rem" }}>Click "Start Real-Time Camera Feed" above to enable live AI proctoring</p>
                </div>
              )}

              {/* Real-Time Live HUD Overlay on Video */}
              {cameraActive && (
                <div style={{ position: "absolute", top: "12px", left: "12px", display: "flex", flexDirection: "column", gap: "6px" }}>
                  <div style={{ backgroundColor: "rgba(16, 185, 129, 0.9)", color: "white", padding: "4px 10px", borderRadius: "4px", fontSize: "0.78rem", fontWeight: "700", display: "inline-block" }}>
                    ● LIVE CV INFERENCE ACTIVE
                  </div>
                  {signals && (
                    <div style={{ backgroundColor: "rgba(15, 23, 42, 0.85)", backdropFilter: "blur(4px)", padding: "8px 12px", borderRadius: "6px", fontSize: "0.78rem", border: "1px solid #334155", color: "#f8fafc", lineHeight: "1.6" }}>
                      <div><strong>Persons:</strong> <span style={{ color: signals.multi_person_flag ? "#ef4444" : signals.person_count === 1 ? "#34d399" : "#fbbf24" }}>{signals.person_count ?? 1} {signals.multi_person_flag ? "(ALERT: Multi-person)" : ""}</span></div>
                      <div><strong>Gaze:</strong> <span style={{ color: signals.looking_away ? "#ef4444" : "#34d399" }}>{signals.looking_away ? "LOOKING AWAY ⚠️" : "ON SCREEN ✓"}</span></div>
                      <div><strong>Head Pose:</strong> <span style={{ color: signals.turned_away ? "#ef4444" : "#34d399" }}>{signals.turned_away ? "TURNED AWAY ⚠️" : "FORWARD ✓"}</span> (Y:{Math.round(signals.yaw || 0)}° P:{Math.round(signals.pitch || 0)}°)</div>
                      <div><strong>Voice:</strong> <span style={{ color: signals.sustained_talking ? "#ef4444" : "#34d399" }}>{signals.sustained_talking ? "SPEECH DETECTED ⚠️" : micActive ? "QUIET (Normal) ✓" : "MIC OFF"}</span></div>
                      <div><strong>Emotion:</strong> <span style={{ color: "#38bdf8", textTransform: "capitalize" }}>{signals.dominant_emotion || "Analyzing..."}</span> ({Math.round((signals.emotion_confidence || 0) * 100)}%)</div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </section>

          {/* AI Inference Engine & Scenario Controls */}
          <section style={{ backgroundColor: "#1e293b", padding: "1.5rem", borderRadius: "12px", border: "1px solid #334155" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
              <div>
                <h3 style={{ fontSize: "1.1rem", margin: 0, color: "#f8fafc" }}>Multimodal AI Engine Settings</h3>
                <span style={{ fontSize: "0.8rem", color: "#94a3b8" }}>Select the active deep learning fusion algorithm</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                <span style={{ fontSize: "0.85rem", color: "#cbd5e1" }}>Engine:</span>
                <select
                  value={inferenceMode}
                  onChange={(e) => handleModeChange(e.target.value)}
                  style={{ backgroundColor: "#0f172a", color: "#38bdf8", border: "1px solid #334155", borderRadius: "6px", padding: "6px 10px", fontSize: "0.85rem", fontWeight: "600" }}
                >
                  <option value="temporal">Temporal BiLSTM (Phase 3D - Recommended)</option>
                  <option value="learned">Learned MLP Fusion (Phase 3B)</option>
                  <option value="baseline">Rule-Based Baseline (Phase 1)</option>
                </select>
              </div>
            </div>

            {!cameraActive && (
              <div>
                <div style={{ fontSize: "0.85rem", color: "#94a3b8", marginBottom: "0.5rem" }}>Or Test With Simulated Scenarios (Camera Idle):</div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: "0.6rem" }}>
                  {[
                    { id: "normal", label: "Normal Student", desc: "Single person, focused" },
                    { id: "multi_person", label: "Multi-Person (2)", desc: "Collusion detection" },
                    { id: "looking_away", label: "Looking Away", desc: "Iris / head turn" },
                    { id: "talking", label: "Voice / Speech", desc: "Silero VAD active" },
                    { id: "tab_cheat", label: "Multi-Violation", desc: "Tab away + voice" },
                  ].map((sc) => (
                    <button
                      key={sc.id}
                      onClick={() => {
                        setSelectedScenario(sc.id);
                        runWindowAnalysis(sc.id, inferenceMode);
                      }}
                      style={{
                        padding: "8px 10px",
                        backgroundColor: selectedScenario === sc.id ? "#0284c7" : "#0f172a",
                        border: `1px solid ${selectedScenario === sc.id ? "#38bdf8" : "#334155"}`,
                        borderRadius: "6px",
                        color: "white",
                        cursor: "pointer",
                        textAlign: "left",
                      }}
                    >
                      <div style={{ fontWeight: "600", fontSize: "0.82rem" }}>{sc.label}</div>
                      <div style={{ fontSize: "0.72rem", color: "#94a3b8" }}>{sc.desc}</div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {cameraActive && (
              <div style={{ backgroundColor: "#0f172a", padding: "0.8rem", borderRadius: "8px", border: "1px solid #334155", color: "#34d399", fontSize: "0.85rem", display: "flex", alignItems: "center", gap: "0.6rem" }}>
                <span style={{ width: "10px", height: "10px", borderRadius: "50%", backgroundColor: "#34d399", display: "inline-block" }}></span>
                <span>Real-Time Inference is continuously streaming every ~380ms. Look away or turn your head to watch the score react instantly!</span>
              </div>
            )}
          </section>
        </div>

        {/* Right Column: AI Verdict, Telemetry & Modality Breakdown */}
        <section style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          {/* Real-Time AI Suspicion Score & Verdict Card */}
          <div style={{ backgroundColor: "#1e293b", padding: "1.2rem", borderRadius: "12px", border: "1px solid #334155" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.8rem" }}>
              <h3 style={{ fontSize: "1rem", margin: 0, color: "#94a3b8" }}>Live AI Suspicion Verdict (Phase 3)</h3>
              <span style={{ fontSize: "0.75rem", backgroundColor: "#334155", color: "#cbd5e1", padding: "2px 8px", borderRadius: "4px" }}>
                Mode: {inferenceMode.toUpperCase()}
              </span>
            </div>

            {inferenceResult ? (
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                  <div style={{ fontSize: "0.85rem", color: "#94a3b8" }}>Calibrated Suspicion Probability:</div>
                  <div style={{ fontSize: "1.5rem", fontWeight: "800", color: inferenceResult.flag ? "#f87171" : "#34d399" }}>
                    {(inferenceResult.suspicion_score * 100).toFixed(1)}%
                  </div>
                </div>

                {/* Score Bar */}
                <div style={{ width: "100%", height: "10px", backgroundColor: "#0f172a", borderRadius: "5px", overflow: "hidden", marginBottom: "0.8rem" }}>
                  <div
                    style={{
                      height: "100%",
                      width: `${Math.min(100, Math.max(0, inferenceResult.suspicion_score * 100))}%`,
                      backgroundColor: inferenceResult.flag ? "#ef4444" : "#10b981",
                      transition: "width 0.3s ease",
                    }}
                  />
                </div>

                {/* Verdict Badge */}
                <div
                  style={{
                    padding: "8px 12px",
                    borderRadius: "6px",
                    backgroundColor: inferenceResult.flag ? "#7f1d1d44" : "#065f4644",
                    border: `1px solid ${inferenceResult.flag ? "#ef4444" : "#10b981"}`,
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: "0.8rem",
                  }}
                >
                  <span style={{ fontWeight: "700", color: inferenceResult.flag ? "#fca5a5" : "#6ee7b7", fontSize: "0.9rem" }}>
                    {inferenceResult.flag ? "⚠️ SUSPICIOUS ACTIVITY FLAGGED" : "✓ NORMAL EXAM CONDUCT"}
                  </span>
                  <span style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
                    Threshold: 50%
                  </span>
                </div>

                {/* Contributors */}
                {inferenceResult.contributors && inferenceResult.contributors.length > 0 && (
                  <div style={{ marginBottom: "0.8rem" }}>
                    <div style={{ fontSize: "0.8rem", color: "#94a3b8", marginBottom: "0.3rem" }}>Flagged Contributing Factors:</div>
                    <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
                      {inferenceResult.contributors.map((c, i) => (
                        <span key={i} style={{ backgroundColor: "#ef444422", color: "#f87171", border: "1px solid #ef444455", padding: "2px 8px", borderRadius: "4px", fontSize: "0.75rem", fontWeight: "600" }}>
                          {c.replace(/_/g, " ")}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Modality Telemetry Grid */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.6rem", marginBottom: "0.8rem" }}>
                  <div style={{ backgroundColor: "#0f172a", padding: "0.6rem 0.8rem", borderRadius: "6px", border: "1px solid #334155" }}>
                    <div style={{ fontSize: "0.72rem", color: "#64748b" }}>PERSONS (YOLO)</div>
                    <div style={{ fontSize: "0.95rem", fontWeight: "700", color: signals.multi_person_flag ? "#f87171" : "#34d399" }}>
                      {signals.person_count ?? 1} {signals.multi_person_flag ? "(Multi!)" : ""}
                    </div>
                  </div>

                  <div style={{ backgroundColor: "#0f172a", padding: "0.6rem 0.8rem", borderRadius: "6px", border: "1px solid #334155" }}>
                    <div style={{ fontSize: "0.72rem", color: "#64748b" }}>GAZE (IRIS MESH)</div>
                    <div style={{ fontSize: "0.95rem", fontWeight: "700", color: signals.looking_away ? "#f87171" : "#34d399" }}>
                      {signals.looking_away ? "Looking Away" : "Focused"}
                    </div>
                  </div>

                  <div style={{ backgroundColor: "#0f172a", padding: "0.6rem 0.8rem", borderRadius: "6px", border: "1px solid #334155" }}>
                    <div style={{ fontSize: "0.72rem", color: "#64748b" }}>HEAD POSE (3D YAW)</div>
                    <div style={{ fontSize: "0.95rem", fontWeight: "700", color: signals.turned_away ? "#f87171" : "#34d399" }}>
                      {Math.round(signals.yaw || 0)}° {signals.turned_away ? "(Turned)" : ""}
                    </div>
                  </div>

                  <div style={{ backgroundColor: "#0f172a", padding: "0.6rem 0.8rem", borderRadius: "6px", border: "1px solid #334155" }}>
                    <div style={{ fontSize: "0.72rem", color: "#64748b" }}>VOICE VAD (MIC / SILERO)</div>
                    <div style={{ fontSize: "0.95rem", fontWeight: "700", color: signals.sustained_talking ? "#f87171" : "#34d399" }}>
                      {signals.sustained_talking ? "Speech Detected ⚠️" : micActive ? "Quiet (Voice Inactive) ✓" : "Quiet"}
                    </div>
                    {micActive && (
                      <div style={{ marginTop: "6px", width: "100%", height: "4px", backgroundColor: "#1e293b", borderRadius: "2px", overflow: "hidden" }}>
                        <div style={{ width: `${Math.min(100, Math.max(4, (micLevel / 50) * 100))}%`, height: "100%", backgroundColor: signals.sustained_talking ? "#ef4444" : "#10b981", transition: "width 0.2s ease" }} />
                      </div>
                    )}
                  </div>
                </div>

                {/* Phase 2: Affective Emotion Signal */}
                {signals.dominant_emotion && (
                  <div style={{ backgroundColor: "#0f172a", padding: "0.8rem", borderRadius: "8px", border: "1px solid #334155" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div>
                        <div style={{ fontSize: "0.72rem", color: "#94a3b8" }}>PHASE 2 AFFECTIVE STATE (FER CNN)</div>
                        <div style={{ fontSize: "1rem", fontWeight: "700", color: "#38bdf8", textTransform: "capitalize" }}>
                          {signals.dominant_emotion} ({(signals.emotion_confidence * 100).toFixed(0)}% confidence)
                        </div>
                      </div>
                      <span style={{ fontSize: "0.7rem", color: "#64748b", maxWidth: "150px", textAlign: "right" }}>
                        Affective context only — never independently penalizes
                      </span>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div style={{ color: "#64748b", fontSize: "0.9rem" }}>Initializing real-time inference pipeline...</div>
            )}
          </div>

          {/* Browser Tab & Focus Monitoring Card */}
          <div style={{ backgroundColor: "#1e293b", padding: "1.2rem", borderRadius: "12px", border: "1px solid #334155" }}>
            <h3 style={{ fontSize: "1rem", margin: "0 0 0.8rem 0", color: "#94a3b8" }}>Browser Tab & Focus Monitor (Phase 1)</h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1rem" }}>
              <div style={{ backgroundColor: "#0f172a", padding: "0.8rem", borderRadius: "8px" }}>
                <div style={{ fontSize: "0.8rem", color: "#64748b" }}>CURRENT STATE</div>
                <div style={{ fontSize: "1.1rem", fontWeight: "700", color: tabStatus === "Active" ? "#34d399" : "#f87171" }}>
                  {tabStatus}
                </div>
              </div>
              <div style={{ backgroundColor: "#0f172a", padding: "0.8rem", borderRadius: "8px" }}>
                <div style={{ fontSize: "0.8rem", color: "#64748b" }}>TAB SWITCHES</div>
                <div style={{ fontSize: "1.1rem", fontWeight: "700", color: switchCount > 0 ? "#f87171" : "#38bdf8" }}>
                  {switchCount}
                </div>
              </div>
            </div>

            <div style={{ fontSize: "0.85rem", color: "#94a3b8" }}>Recent Focus Events:</div>
            <div style={{ marginTop: "0.5rem", maxHeight: "90px", overflowY: "auto", fontSize: "0.8rem" }}>
              {eventsLog.length === 0 ? (
                <div style={{ color: "#64748b" }}>Switch tabs or minimize window to test event capture</div>
              ) : (
                eventsLog.map((ev, i) => (
                  <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "4px 0", borderBottom: "1px solid #334155" }}>
                    <span style={{ color: ev.type.includes("hidden") || ev.type.includes("blur") ? "#f87171" : "#34d399" }}>
                      {ev.type}
                    </span>
                    <span style={{ color: "#64748b" }}>{ev.time}</span>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Backend Service Status */}
          <div style={{ backgroundColor: "#1e293b", padding: "1.2rem", borderRadius: "12px", border: "1px solid #334155" }}>
            <h3 style={{ fontSize: "1rem", margin: "0 0 0.8rem 0", color: "#94a3b8" }}>Backend Service Status (Phase 0)</h3>
            {health ? (
              <div style={{ display: "flex", alignItems: "center", gap: "0.8rem" }}>
                <span style={{ width: "12px", height: "12px", borderRadius: "50%", backgroundColor: "#10b981", display: "inline-block" }}></span>
                <div>
                  <strong style={{ color: "#34d399" }}>FastAPI Connected:</strong> {health.service} (v{health.version})
                </div>
              </div>
            ) : error ? (
              <div style={{ color: "#f87171" }}>Backend Offline: {error}</div>
            ) : (
              <div style={{ color: "#fbbf24" }}>Connecting to backend...</div>
            )}
          </div>
        </section>
      </div>

      {/* Post-Exam Integrity Report Modal */}
      {showReportModal && examSummary && (
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
            }}
          >
            {/* Header */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1.5rem", borderBottom: "1px solid #334155", paddingBottom: "1rem" }}>
              <div>
                <span style={{ fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "1px", color: "#94a3b8", fontWeight: "700" }}>
                  Official Session Audit Record
                </span>
                <h2 style={{ fontSize: "1.5rem", margin: "0.2rem 0 0 0", color: "#f8fafc" }}>
                  Exam Proctoring & Integrity Report
                </h2>
                <div style={{ fontSize: "0.85rem", color: "#64748b", marginTop: "4px" }}>
                  Session ID: <code style={{ color: "#38bdf8" }}>{examSummary.session_id}</code>
                </div>
              </div>
              <button
                onClick={() => setShowReportModal(false)}
                style={{ backgroundColor: "transparent", border: "none", color: "#94a3b8", fontSize: "1.5rem", cursor: "pointer", padding: "0 6px" }}
              >
                ✕
              </button>
            </div>

            {/* Score & Verdict Banner */}
            <div
              style={{
                backgroundColor: "#0f172a",
                borderRadius: "12px",
                border: `2px solid ${examSummary.verdict_color}`,
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
                <div style={{ fontSize: "0.85rem", color: "#94a3b8", textTransform: "uppercase", fontWeight: "600" }}>
                  Final Calculated Integrity Score:
                </div>
                <div style={{ fontSize: "2.8rem", fontWeight: "900", color: examSummary.verdict_color, lineHeight: "1.1" }}>
                  {examSummary.integrity_score}%
                </div>
                <div style={{ marginTop: "0.4rem", fontSize: "0.85rem", color: "#cbd5e1" }}>
                  Flagged Ratio: <strong>{examSummary.flagged_percentage}%</strong> ({examSummary.flagged_frames_count} of {examSummary.total_frames_analyzed} frames)
                </div>
              </div>

              <div style={{ textAlign: "right" }}>
                <span
                  style={{
                    backgroundColor: examSummary.verdict_color + "22",
                    color: examSummary.verdict_color,
                    border: `1px solid ${examSummary.verdict_color}`,
                    padding: "6px 14px",
                    borderRadius: "8px",
                    fontWeight: "800",
                    fontSize: "0.95rem",
                    display: "inline-block",
                  }}
                >
                  {examSummary.verdict_label}
                </span>
                <div style={{ fontSize: "0.8rem", color: "#64748b", marginTop: "0.5rem" }}>
                  Exam Duration: <strong>{examSummary.exam_duration_seconds}s</strong>
                </div>
              </div>
            </div>

            {/* Forensic Violations Breakdown */}
            <div style={{ marginBottom: "1.5rem" }}>
              <h4 style={{ fontSize: "0.95rem", color: "#cbd5e1", margin: "0 0 0.8rem 0" }}>
                Forensic Modality Violations Breakdown:
              </h4>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: "0.8rem" }}>
                {[
                  { label: "Multi-Person Presence", val: examSummary.violations_summary.multi_person, alert: examSummary.violations_summary.multi_person > 0 },
                  { label: "Looking Away", val: examSummary.violations_summary.looking_away, alert: examSummary.violations_summary.looking_away > 5 },
                  { label: "Head Turned Away", val: examSummary.violations_summary.head_turned, alert: examSummary.violations_summary.head_turned > 5 },
                  { label: "Speech / Talking", val: examSummary.violations_summary.speech_detected, alert: examSummary.violations_summary.speech_detected > 3 },
                  { label: "Browser Tab Hidden / Away", val: examSummary.violations_summary.tab_unfocused, alert: examSummary.violations_summary.tab_unfocused > 0 },
                  { label: "Candidate Absence", val: examSummary.violations_summary.absence, alert: examSummary.violations_summary.absence > 0 },
                ].map((item, idx) => (
                  <div key={idx} style={{ backgroundColor: "#0f172a", border: `1px solid ${item.alert ? "#ef444466" : "#334155"}`, borderRadius: "8px", padding: "0.8rem" }}>
                    <div style={{ fontSize: "0.72rem", color: "#94a3b8" }}>{item.label}</div>
                    <div style={{ fontSize: "1.1rem", fontWeight: "800", color: item.alert ? "#f87171" : "#34d399", marginTop: "4px" }}>
                      {item.val} frames {item.alert ? "⚠️" : "✓"}
                    </div>
                    <div style={{ fontSize: "0.7rem", color: "#64748b", marginTop: "2px" }}>
                      ≈ {(item.val * 0.38).toFixed(1)}s duration
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Emotional State & Top Contributors */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1.5rem" }}>
              <div style={{ backgroundColor: "#0f172a", padding: "1rem", borderRadius: "8px", border: "1px solid #334155" }}>
                <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>DOMINANT EMOTION (FER)</div>
                <div style={{ fontSize: "1.1rem", fontWeight: "700", color: "#38bdf8", textTransform: "capitalize", marginTop: "4px" }}>
                  {examSummary.dominant_emotion}
                </div>
                <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: "2px" }}>Affective context only</div>
              </div>

              <div style={{ backgroundColor: "#0f172a", padding: "1rem", borderRadius: "8px", border: "1px solid #334155" }}>
                <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>PRIMARY CONTRIBUTORS</div>
                <div style={{ display: "flex", gap: "4px", flexWrap: "wrap", marginTop: "6px" }}>
                  {examSummary.top_contributors.length === 0 ? (
                    <span style={{ color: "#34d399", fontSize: "0.85rem", fontWeight: "600" }}>None (Clean conduct)</span>
                  ) : (
                    examSummary.top_contributors.map((c, i) => (
                      <span key={i} style={{ backgroundColor: "#ef444422", color: "#f87171", border: "1px solid #ef444455", padding: "2px 6px", borderRadius: "4px", fontSize: "0.7rem", fontWeight: "600" }}>
                        {c.replace(/_/g, " ")}
                      </span>
                    ))
                  )}
                </div>
              </div>
            </div>

            {/* Modal Actions */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: "1rem", borderTop: "1px solid #334155" }}>
              <button
                onClick={handleResetSession}
                style={{ padding: "0.6rem 1.2rem", backgroundColor: "#334155", color: "#f87171", border: "1px solid #ef444455", borderRadius: "6px", cursor: "pointer", fontWeight: "600", fontSize: "0.85rem" }}
              >
                🗑 Reset & Start New Session
              </button>

              <div style={{ display: "flex", gap: "0.8rem" }}>
                <button
                  onClick={() => window.print()}
                  style={{ padding: "0.6rem 1.2rem", backgroundColor: "#0284c7", color: "white", border: "none", borderRadius: "6px", cursor: "pointer", fontWeight: "700", fontSize: "0.85rem" }}
                >
                  🖨 Print / Save Report
                </button>
                <button
                  onClick={() => setShowReportModal(false)}
                  style={{ padding: "0.6rem 1.2rem", backgroundColor: "#10b981", color: "white", border: "none", borderRadius: "6px", cursor: "pointer", fontWeight: "700", fontSize: "0.85rem" }}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}



