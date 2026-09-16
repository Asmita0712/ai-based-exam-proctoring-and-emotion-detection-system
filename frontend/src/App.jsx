import { useEffect, useState, useRef } from "react";

function App() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);
  const [cameraActive, setCameraActive] = useState(false);
  const [tabStatus, setTabStatus] = useState("Active");
  const [switchCount, setSwitchCount] = useState(0);
  const [eventsLog, setEventsLog] = useState([]);
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  // 1. Health check poll
  useEffect(() => {
    fetch("http://localhost:8000/health")
      .then((res) => res.json())
      .then((data) => {
        setHealth(data);
        setError(null);
      })
      .catch((err) => setError(err.message));
  }, []);

  // 2. Camera feed handler
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

  // 3. Browser tab/window event tracking
  const sendBrowserEvent = (eventType) => {
    const payload = {
      session_id: "demo-session-001",
      type: eventType,
      timestamp: new Date().toISOString(),
    };

    fetch("http://localhost:8000/proctoring/events", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).catch(() => {});

    setEventsLog((prev) => [
      { type: eventType, time: new Date().toLocaleTimeString() },
      ...prev.slice(0, 8),
    ]);
  };

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
  }, []);

  return (
    <div style={{ fontFamily: "system-ui, -apple-system, sans-serif", backgroundColor: "#0f172a", color: "#f8fafc", minHeight: "100vh", padding: "2rem" }}>
      <header style={{ borderBottom: "1px solid #334155", paddingBottom: "1.5rem", marginBottom: "2rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h1 style={{ fontSize: "1.8rem", margin: 0, fontWeight: "700", color: "#38bdf8" }}>
              AI Proctoring & Suspicious Activity Detection
            </h1>
            <p style={{ color: "#94a3b8", margin: "0.4rem 0 0 0" }}>
              Multimodal Examination Monitoring System (Phase 1 Ready)
            </p>
          </div>
          <div style={{ display: "flex", gap: "1rem" }}>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              style={{ padding: "0.6rem 1.2rem", backgroundColor: "#0284c7", color: "white", borderRadius: "8px", textDecoration: "none", fontWeight: "600", fontSize: "0.9rem" }}
            >
              Interactive API Docs (Swagger) ↗
            </a>
          </div>
        </div>
      </header>

      <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: "2rem" }}>
        {/* Left Column: Live Webcam */}
        <section style={{ backgroundColor: "#1e293b", padding: "1.5rem", borderRadius: "12px", border: "1px solid #334155" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
            <h2 style={{ fontSize: "1.2rem", margin: 0 }}>Candidate Video Feed</h2>
            <div>
              {!cameraActive ? (
                <button
                  onClick={startCamera}
                  style={{ padding: "0.5rem 1rem", backgroundColor: "#10b981", color: "white", border: "none", borderRadius: "6px", cursor: "pointer", fontWeight: "600" }}
                >
                  Start Camera Feed
                </button>
              ) : (
                <button
                  onClick={stopCamera}
                  style={{ padding: "0.5rem 1rem", backgroundColor: "#ef4444", color: "white", border: "none", borderRadius: "6px", cursor: "pointer", fontWeight: "600" }}
                >
                  Stop Camera
                </button>
              )}
            </div>
          </div>

          <div style={{ width: "100%", height: "400px", backgroundColor: "#020617", borderRadius: "8px", overflow: "hidden", display: "flex", alignItems: "center", justifyContent: "center", position: "relative" }}>
            <video
              ref={videoRef}
              autoPlay
              playsInline
              style={{ width: "100%", height: "100%", objectFit: "cover", display: cameraActive ? "block" : "none" }}
            />
            {!cameraActive && (
              <div style={{ textAlign: "center", color: "#64748b" }}>
                <p style={{ fontSize: "1.1rem", margin: "0 0 0.5rem 0" }}>Camera is currently idle</p>
                <p style={{ fontSize: "0.85rem" }}>Click "Start Camera Feed" to preview local candidate video</p>
              </div>
            )}
            {cameraActive && (
              <div style={{ position: "absolute", top: "12px", left: "12px", backgroundColor: "rgba(16, 185, 129, 0.9)", padding: "4px 10px", borderRadius: "4px", fontSize: "0.8rem", fontWeight: "700" }}>
                LIVE FEED ACTIVE
              </div>
            )}
          </div>
        </section>

        {/* Right Column: Live Telemetry & Modality Signals */}
        <section style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          {/* Backend Health Card */}
          <div style={{ backgroundColor: "#1e293b", padding: "1.2rem", borderRadius: "12px", border: "1px solid #334155" }}>
            <h3 style={{ fontSize: "1rem", margin: "0 0 0.8rem 0", color: "#94a3b8" }}>Backend Service Status</h3>
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

          {/* Browser Tab & Focus Monitoring Card */}
          <div style={{ backgroundColor: "#1e293b", padding: "1.2rem", borderRadius: "12px", border: "1px solid #334155" }}>
            <h3 style={{ fontSize: "1rem", margin: "0 0 0.8rem 0", color: "#94a3b8" }}>Browser Tab & Focus Monitor</h3>
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
            <div style={{ marginTop: "0.5rem", maxHeight: "120px", overflowY: "auto", fontSize: "0.8rem" }}>
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

          {/* Multimodal Modalities Overview */}
          <div style={{ backgroundColor: "#1e293b", padding: "1.2rem", borderRadius: "12px", border: "1px solid #334155" }}>
            <h3 style={{ fontSize: "1rem", margin: "0 0 0.8rem 0", color: "#94a3b8" }}>Active Modality Engines</h3>
            <ul style={{ margin: 0, paddingLeft: "1.2rem", fontSize: "0.85rem", color: "#cbd5e1", lineHeight: "1.8" }}>
              <li><strong>Person Detection:</strong> YOLOv8 (CPU-first)</li>
              <li><strong>Multi-Person:</strong> Temporal Debounce Filter</li>
              <li><strong>Gaze Tracking:</strong> MediaPipe Iris Mesh</li>
              <li><strong>Head Pose:</strong> solvePnP 3D Euler Angles</li>
              <li><strong>Audio VAD:</strong> Silero VAD (16kHz Speech Activity)</li>
              <li><strong>Multimodal Fusion:</strong> Rule-Based Baseline (Score: 0.0 - 1.0)</li>
            </ul>
          </div>
        </section>
      </div>
    </div>
  );
}

export default App;
