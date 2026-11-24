import React, { useState, useEffect, useRef, useMemo } from "react";
import examApi from "../services/examApi";
import ProctoringReportModal from "./ProctoringReportModal";

export default function StudentExamPortal() {
  // Phase: 'lobby' | 'readiness' | 'exam' | 'result'
  const [phase, setPhase] = useState("lobby");

  // Student credentials
  const [studentName, setStudentName] = useState(() => localStorage.getItem("sentinel_student_name") || "");
  const [studentId, setStudentId] = useState(() => localStorage.getItem("sentinel_student_id") || "");

  // Lobby state
  const [exams, setExams] = useState([]);
  const [selectedExamId, setSelectedExamId] = useState("");
  const [loadingExams, setLoadingExams] = useState(false);
  const [lobbyError, setLobbyError] = useState(null);

  // Readiness state
  const [backendHealthy, setBackendHealthy] = useState(false);
  const [rulesAccepted, setRulesAccepted] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const [micActive, setMicActive] = useState(false);
  const [micLevel, setMicLevel] = useState(0);

  // Active Exam state
  const [examData, setExamData] = useState(null);
  const [currentQIndex, setCurrentQIndex] = useState(0);
  const [answers, setAnswers] = useState({}); // { [question_id]: option_index }
  const [timeLeftSeconds, setTimeLeftSeconds] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [sessionId, setSessionId] = useState("");
  const [confirmSubmitOpen, setConfirmSubmitOpen] = useState(false);

  // AI Proctoring & HUD state
  const [realtimeInference, setRealtimeInference] = useState(null);
  const [analyzedFramesCount, setAnalyzedFramesCount] = useState(0);
  const [tabSwitches, setTabSwitches] = useState(0);
  const [recentWarning, setRecentWarning] = useState(null);

  // Post-submission Result state
  const [submissionResult, setSubmissionResult] = useState(null);
  const [showAuditModal, setShowAuditModal] = useState(false);

  // Media & Processing refs
  const videoRef = useRef(null);
  const readinessVideoRef = useRef(null);
  const streamRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const audioDataRef = useRef(null);
  const speechStreakRef = useRef(0);
  const isInferringFrameRef = useRef(false);
  const warningTimeoutRef = useRef(null);
  const sessionIdRef = useRef("");

  // Persist student credentials
  useEffect(() => {
    if (studentName) localStorage.setItem("sentinel_student_name", studentName);
  }, [studentName]);

  useEffect(() => {
    if (studentId) localStorage.setItem("sentinel_student_id", studentId);
  }, [studentId]);

  // 1. Fetch available published exams
  const fetchPublishedExams = async () => {
    try {
      setLoadingExams(true);
      setLobbyError(null);
      // Fetch only published exams for student view
      const list = await examApi.getExams(true);
      setExams(list);
      if (list.length > 0 && !selectedExamId) {
        setSelectedExamId(list[0].id);
      }
    } catch (err) {
      console.error("Failed to load exams:", err);
      setLobbyError("Unable to connect to exam server. Please ensure backend is running.");
    } finally {
      setLoadingExams(false);
    }
  };

  useEffect(() => {
    fetchPublishedExams();
  }, []);

  // Display a brief warning on HUD
  const triggerHUDWarning = (msg) => {
    setRecentWarning(msg);
    if (warningTimeoutRef.current) clearTimeout(warningTimeoutRef.current);
    warningTimeoutRef.current = setTimeout(() => {
      setRecentWarning(null);
    }, 3500);
  };

  // 2. Start Camera & Audio
  const initMediaStream = async () => {
    if (streamRef.current && streamRef.current.active) {
      setCameraActive(true);
      return true;
    }

    try {
      let stream = null;
      let hasAudio = false;

      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480 },
          audio: true,
        });
        hasAudio = true;
      } catch (audioErr) {
        console.warn("Audio mic access denied, falling back to video only:", audioErr);
        stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480 },
          audio: false,
        });
      }

      streamRef.current = stream;

      // Bind Web Audio API Analyser for speech detection & visual meter
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
      return true;
    } catch (err) {
      alert("Camera access is mandatory for proctored examination: " + err.message);
      return false;
    }
  };

  // Bind video element whenever phase changes or stream is acquired
  useEffect(() => {
    if (!streamRef.current) return;

    if (phase === "readiness" && readinessVideoRef.current) {
      readinessVideoRef.current.srcObject = streamRef.current;
      readinessVideoRef.current.play().catch(() => {});
    } else if (phase === "exam" && videoRef.current) {
      videoRef.current.srcObject = streamRef.current;
      videoRef.current.play().catch(() => {});
    }
  }, [phase, cameraActive]);

  // Stop Media Stream on finish/exit
  const stopMediaStream = () => {
    if (audioContextRef.current) {
      try {
        audioContextRef.current.close();
      } catch (_) {}
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
    if (readinessVideoRef.current) {
      readinessVideoRef.current.srcObject = null;
    }
    setCameraActive(false);
  };

  // 3. Move from Lobby to Pre-Exam Readiness
  const handleProceedToReadiness = async (targetExamId) => {
    if (!studentName.trim()) {
      alert("Please enter your Full Name.");
      return;
    }
    if (!studentId.trim()) {
      alert("Please enter your Student ID.");
      return;
    }

    const examIdToLoad = targetExamId || selectedExamId;
    if (!examIdToLoad) {
      alert("Please select an examination.");
      return;
    }

    try {
      // Secure student view of questions
      const data = await examApi.getExamForStudent(examIdToLoad);
      setExamData(data);
      setSelectedExamId(examIdToLoad);

      // Check backend health
      try {
        const h = await examApi.checkHealth();
        setBackendHealthy(h.status === "ok");
      } catch {
        setBackendHealthy(false);
      }

      // Initialize camera/mic for readiness check
      await initMediaStream();

      setPhase("readiness");
    } catch (err) {
      alert("Could not load examination: " + err.message);
    }
  };

  // 4. Launch Proctored Exam from Readiness
  const handleStartExam = async () => {
    if (!rulesAccepted) {
      alert("Please confirm the examination rules checkbox to proceed.");
      return;
    }
    if (!cameraActive) {
      const ok = await initMediaStream();
      if (!ok) return;
    }

    // 1. Initialize server-authoritative attempt and timer
    let initialSeconds = examData.duration_minutes * 60;
    try {
      const startData = await examApi.startExamAttempt(selectedExamId, {
        student_name: studentName.trim(),
        student_id: studentId.trim(),
        access_code: null,
      });
      if (startData && startData.session_id) {
        setSessionId(startData.session_id);
        sessionIdRef.current = startData.session_id;
        if (startData.remaining_seconds) {
          initialSeconds = startData.remaining_seconds;
        }
      }
    } catch (err) {
      console.warn("Attempt start API fallback:", err.message);
      const cleanId = studentId.trim().toLowerCase().replace(/[^a-z0-9]/g, "");
      const newSessionId = `sess-${cleanId || "stu"}-${Date.now().toString(36)}`;
      setSessionId(newSessionId);
      sessionIdRef.current = newSessionId;
    }

    // Check for saved draft answers in sessionStorage
    const cleanId = studentId.trim().toLowerCase().replace(/[^a-z0-9]/g, "");
    const storageKey = `sentinel_answers_${selectedExamId}_${cleanId}`;
    let savedAnswers = {};
    try {
      const cached = sessionStorage.getItem(storageKey);
      if (cached) savedAnswers = JSON.parse(cached);
    } catch (_) {}

    setAnswers(savedAnswers);
    setTimeLeftSeconds(initialSeconds);
    setCurrentQIndex(0);
    setTabSwitches(0);
    setAnalyzedFramesCount(0);
    setRealtimeInference(null);

    setPhase("exam");
  };

  // 5. Timer Countdown & Auto-Submit
  useEffect(() => {
    if (phase !== "exam") return;
    if (timeLeftSeconds <= 0) {
      handleSubmitExam(true); // Auto-submit when time expires
      return;
    }

    const timer = setInterval(() => {
      setTimeLeftSeconds((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          handleSubmitExam(true);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [phase, timeLeftSeconds]);

  // Format time MM:SS
  const formattedTime = useMemo(() => {
    const mins = Math.floor(timeLeftSeconds / 60);
    const secs = timeLeftSeconds % 60;
    return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  }, [timeLeftSeconds]);

  // 6. Continuous Multimodal AI Proctoring Loop during active exam
  useEffect(() => {
    if (phase !== "exam" || !cameraActive) return;

    const canvas = document.createElement("canvas");
    canvas.width = 320;
    canvas.height = 240;
    const ctx = canvas.getContext("2d");

    const interval = setInterval(async () => {
      const v = videoRef.current;
      if (!v || isInferringFrameRef.current) return;

      // Ensure video is playing and has frames ready
      if (v.readyState < 2 || v.paused) {
        if (streamRef.current && v.srcObject !== streamRef.current) {
          v.srcObject = streamRef.current;
        }
        v.play().catch(() => {});
        return;
      }

      try {
        isInferringFrameRef.current = true;
        ctx.drawImage(v, 0, 0, canvas.width, canvas.height);
        const imageBase64 = canvas.toDataURL("image/jpeg", 0.6);

        // Compute RMS for Speech
        let speechProbability = 0.0;
        let sustainedTalking = false;
        let avgLevel = 0;

        if (analyserRef.current && audioDataRef.current) {
          analyserRef.current.getFloatTimeDomainData(audioDataRef.current);
          let sumSquares = 0;
          const pcm = audioDataRef.current;
          for (let i = 0; i < pcm.length; i++) {
            sumSquares += pcm[i] * pcm[i];
          }
          const rms = Math.sqrt(sumSquares / pcm.length);
          avgLevel = Math.round(Math.min(100, rms * 550));
          setMicLevel(avgLevel);

          if (rms >= 0.034) {
            speechStreakRef.current = Math.min(10, speechStreakRef.current + 1);
          } else {
            speechStreakRef.current = Math.max(0, speechStreakRef.current - 1);
          }

          if (speechStreakRef.current >= 2 || (speechStreakRef.current >= 1 && rms >= 0.052)) {
            sustainedTalking = true;
            speechProbability = Math.min(1.0, Math.max(0.60, (rms - 0.020) / 0.075));
          }
        }

        const isCurrentlyHidden = document.hidden;
        const isCurrentlyFocused = typeof document.hasFocus === "function" ? document.hasFocus() : true;
        const isCurrentlyAway = isCurrentlyHidden || !isCurrentlyFocused;
        const currentSession = sessionIdRef.current || sessionId || "exam-live-session";

        const infData = await examApi.sendProctoringFrame({
          session_id: currentSession,
          image_base64: imageBase64,
          mode: "temporal",
          audio_signals: {
            speech_probability: speechProbability,
            sustained_talking: sustainedTalking,
            audio_level: avgLevel,
          },
          browser_signals: {
            tab_hidden: isCurrentlyHidden,
            window_blur: !isCurrentlyFocused,
            is_away: isCurrentlyAway,
          },
        });

        if (infData) {
          setRealtimeInference(infData);
          setAnalyzedFramesCount((c) => c + 1);

          // Check signals and trigger non-intrusive warning toasts
          const sig = infData.signals || {};
          if (infData.flag) {
            if (sig.person_count > 1 || sig.multi_person_flag) {
              triggerHUDWarning("⚠️ Multiple people detected in camera view!");
            } else if (sig.person_count === 0) {
              triggerHUDWarning("⚠️ Candidate absent — please stay in camera frame!");
            } else if (sig.turned_away) {
              triggerHUDWarning("⚠️ Head turned away from screen — please face forward!");
            } else if (sig.looking_away) {
              triggerHUDWarning("⚠️ Gaze detected looking away — please focus on screen!");
            } else if (sig.sustained_talking || sig.speech_probability > 0.5) {
              triggerHUDWarning("⚠️ Speech / talking detected!");
            } else if (infData.contributors && infData.contributors.length > 0) {
              triggerHUDWarning(`⚠️ Flagged event: ${infData.contributors[0].toUpperCase()}`);
            }
          }
        }
      } catch (err) {
        console.error("Proctoring inference error:", err);
      } finally {
        isInferringFrameRef.current = false;
      }
    }, 380);

    return () => clearInterval(interval);
  }, [phase, cameraActive, sessionId]);

  // 7. Browser Tab & Blur Focus Tracking
  useEffect(() => {
    if (phase !== "exam") return;

    const handleVisibilityChange = () => {
      if (document.hidden) {
        setTabSwitches((c) => c + 1);
        triggerHUDWarning("⚠️ VIOLATION: Browser tab switched or minimized!");
        const currentSession = sessionIdRef.current || sessionId;
        examApi
          .logBrowserEvent({
            session_id: currentSession,
            type: "tab_hidden",
            timestamp: new Date().toISOString(),
          })
          .catch(() => {});
      }
    };

    const handleWindowBlur = () => {
      triggerHUDWarning("⚠️ Focus lost: Please keep the examination window in focus!");
      const currentSession = sessionIdRef.current || sessionId;
      examApi
        .logBrowserEvent({
          session_id: currentSession,
          type: "window_blur",
          timestamp: new Date().toISOString(),
        })
        .catch(() => {});
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    window.addEventListener("blur", handleWindowBlur);

    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      window.removeEventListener("blur", handleWindowBlur);
    };
  }, [phase, sessionId]);

  // 8. Handle Question Option Selection & Persistence
  const handleSelectOption = (questionId, optionIndex) => {
    setAnswers((prev) => {
      const updated = {
        ...prev,
        [questionId]: optionIndex,
      };
      // Persist in sessionStorage
      const cleanId = studentId.trim().toLowerCase().replace(/[^a-z0-9]/g, "");
      const storageKey = `sentinel_answers_${selectedExamId}_${cleanId}`;
      try {
        sessionStorage.setItem(storageKey, JSON.stringify(updated));
      } catch (_) {}
      return updated;
    });

    // Asynchronously autosave to PostgreSQL database
    examApi.autosaveAnswer(selectedExamId, questionId, optionIndex).catch((e) => {
      console.warn("Background autosave sync note:", e.message);
    });
  };

  const handleClearOption = (questionId) => {
    setAnswers((prev) => {
      const copy = { ...prev };
      delete copy[questionId];
      const cleanId = studentId.trim().toLowerCase().replace(/[^a-z0-9]/g, "");
      const storageKey = `sentinel_answers_${selectedExamId}_${cleanId}`;
      try {
        sessionStorage.setItem(storageKey, JSON.stringify(copy));
      } catch (_) {}
      return copy;
    });
  };

  // 9. Submit Exam
  const handleSubmitExam = async (isAutoSubmit = false) => {
    if (submitting) return; // Prevent duplicate submissions

    if (!isAutoSubmit && !confirmSubmitOpen) {
      setConfirmSubmitOpen(true);
      return;
    }

    try {
      setSubmitting(true);
      setConfirmSubmitOpen(false);
      const currentSession = sessionIdRef.current || sessionId;

      const payload = {
        student_name: studentName.trim(),
        student_id: studentId.trim(),
        session_id: currentSession,
        answers: answers,
      };

      const report = await examApi.submitExam(selectedExamId, payload);
      setSubmissionResult(report);

      // Clean up draft storage
      const cleanId = studentId.trim().toLowerCase().replace(/[^a-z0-9]/g, "");
      try {
        sessionStorage.removeItem(`sentinel_answers_${selectedExamId}_${cleanId}`);
      } catch (_) {}

      // Stop camera and microphone
      stopMediaStream();

      // Transition to results phase
      setPhase("result");
    } catch (err) {
      console.error("Submission error:", err);
      alert("Failed to submit exam: " + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  // Current question data
  const currentQuestion = examData?.questions ? examData.questions[currentQIndex] : null;
  const totalQuestions = examData?.questions?.length || 0;
  const answeredCount = Object.keys(answers).length;

  return (
    <div style={{ color: "#f8fafc", width: "100%", maxWidth: "1280px", margin: "0 auto", paddingBottom: "3rem" }}>
      {/* ---------------------------------------------------- */}
      {/* PHASE 1: STUDENT LANDING & LOBBY */}
      {/* ---------------------------------------------------- */}
      {phase === "lobby" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
          {/* Welcome Header */}
          <div
            style={{
              backgroundColor: "#0f172a",
              border: "1px solid #1e293b",
              borderRadius: "14px",
              padding: "2rem",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "1.5rem",
              background: "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
            }}
          >
            <div>
              <span
                style={{
                  backgroundColor: "rgba(2, 132, 199, 0.2)",
                  color: "#38bdf8",
                  fontSize: "0.75rem",
                  fontWeight: "800",
                  padding: "4px 10px",
                  borderRadius: "20px",
                  letterSpacing: "0.5px",
                }}
              >
                SENTINELPROCTOR AI EXAMINATION SUITE
              </span>
              <h1 style={{ fontSize: "1.75rem", fontWeight: "800", margin: "0.6rem 0 0.3rem 0" }}>
                Student Examination Portal
              </h1>
              <p style={{ margin: 0, fontSize: "0.9rem", color: "#94a3b8", maxWidth: "600px" }}>
                Enter your student credentials, review system compatibility requirements, and select your scheduled
                examination to begin under multimodal AI monitoring.
              </p>
            </div>

            {/* Candidate Identity Input Card */}
            <div
              style={{
                backgroundColor: "#090d16",
                border: "1px solid #334155",
                borderRadius: "12px",
                padding: "1.2rem 1.5rem",
                display: "flex",
                flexDirection: "column",
                gap: "0.8rem",
                minWidth: "280px",
              }}
            >
              <div style={{ fontSize: "0.78rem", fontWeight: "700", color: "#94a3b8", textTransform: "uppercase" }}>
                Candidate Credentials
              </div>
              <div>
                <input
                  type="text"
                  placeholder="Full Legal Name"
                  value={studentName}
                  onChange={(e) => setStudentName(e.target.value)}
                  style={{
                    width: "100%",
                    backgroundColor: "#0f172a",
                    border: "1px solid #334155",
                    borderRadius: "6px",
                    padding: "8px 12px",
                    color: "#f8fafc",
                    fontSize: "0.88rem",
                    boxSizing: "border-box",
                  }}
                />
              </div>
              <div>
                <input
                  type="text"
                  placeholder="Student ID (e.g. STU-2024-001)"
                  value={studentId}
                  onChange={(e) => setStudentId(e.target.value)}
                  style={{
                    width: "100%",
                    backgroundColor: "#0f172a",
                    border: "1px solid #334155",
                    borderRadius: "6px",
                    padding: "8px 12px",
                    color: "#f8fafc",
                    fontSize: "0.88rem",
                    boxSizing: "border-box",
                  }}
                />
              </div>
            </div>
          </div>

          {/* Available Examinations Section */}
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
                <h2 style={{ margin: 0, fontSize: "1.25rem", fontWeight: "800" }}>Available Examinations</h2>
                <p style={{ margin: 0, fontSize: "0.82rem", color: "#94a3b8" }}>
                  Official examinations currently published and accepting student attempts.
                </p>
              </div>
              <button
                onClick={fetchPublishedExams}
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
                🔄 Refresh Exam List
              </button>
            </div>

            {loadingExams && (
              <div style={{ padding: "3rem", textAlign: "center", color: "#94a3b8" }}>
                Loading published examinations...
              </div>
            )}

            {lobbyError && (
              <div
                style={{
                  backgroundColor: "rgba(239, 68, 68, 0.15)",
                  border: "1px solid #ef4444",
                  borderRadius: "8px",
                  padding: "1rem",
                  color: "#f87171",
                  fontSize: "0.9rem",
                }}
              >
                {lobbyError}
              </div>
            )}

            {!loadingExams && !lobbyError && (
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fill, minmax(360px, 1fr))",
                  gap: "1.4rem",
                }}
              >
                {exams.map((ex) => (
                  <div
                    key={ex.id}
                    style={{
                      backgroundColor: "#0f172a",
                      border: selectedExamId === ex.id ? "2px solid #0284c7" : "1px solid #1e293b",
                      borderRadius: "12px",
                      padding: "1.6rem",
                      display: "flex",
                      flexDirection: "column",
                      justifyContent: "space-between",
                      transition: "all 0.15s ease",
                      boxShadow: selectedExamId === ex.id ? "0 0 20px rgba(2, 132, 199, 0.25)" : "none",
                    }}
                  >
                    <div>
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          marginBottom: "0.8rem",
                        }}
                      >
                        <span
                          style={{
                            backgroundColor: "rgba(16, 185, 129, 0.15)",
                            color: "#34d399",
                            fontSize: "0.72rem",
                            fontWeight: "800",
                            padding: "3px 8px",
                            borderRadius: "12px",
                          }}
                        >
                          ● READY TO TAKE
                        </span>
                        <span style={{ fontSize: "0.75rem", color: "#64748b", fontFamily: "monospace" }}>
                          {ex.id}
                        </span>
                      </div>

                      <h3 style={{ margin: "0 0 0.5rem 0", fontSize: "1.2rem", fontWeight: "800", color: "#f8fafc" }}>
                        {ex.title}
                      </h3>
                      <p
                        style={{
                          margin: 0,
                          fontSize: "0.85rem",
                          color: "#94a3b8",
                          lineHeight: "1.5",
                          minHeight: "2.8rem",
                        }}
                      >
                        {ex.description || "Standard MCQ assessment."}
                      </p>

                      <div
                        style={{
                          display: "flex",
                          gap: "1.2rem",
                          marginTop: "1.4rem",
                          paddingTop: "1rem",
                          borderTop: "1px solid #1e293b",
                          fontSize: "0.85rem",
                          color: "#94a3b8",
                        }}
                      >
                        <div>
                          ⏱️ <strong style={{ color: "#f8fafc" }}>{ex.duration_minutes}</strong> mins
                        </div>
                        <div>
                          ❓ <strong style={{ color: "#f8fafc" }}>{ex.questions_count}</strong> Questions
                        </div>
                        <div>
                          🏆 <strong style={{ color: "#10b981" }}>{ex.total_points}</strong> Points
                        </div>
                      </div>
                    </div>

                    <div style={{ marginTop: "1.5rem" }}>
                      <button
                        onClick={() => handleProceedToReadiness(ex.id)}
                        style={{
                          width: "100%",
                          backgroundColor: "#0284c7",
                          color: "#ffffff",
                          border: "none",
                          borderRadius: "8px",
                          padding: "10px",
                          fontSize: "0.9rem",
                          fontWeight: "700",
                          cursor: "pointer",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          gap: "8px",
                          boxShadow: "0 2px 10px rgba(2, 132, 199, 0.4)",
                        }}
                      >
                        <span>🛡️</span> Verify System & Start Examination
                      </button>
                    </div>
                  </div>
                ))}

                {exams.length === 0 && (
                  <div
                    style={{
                      gridColumn: "1 / -1",
                      backgroundColor: "#0f172a",
                      border: "1px solid #1e293b",
                      borderRadius: "12px",
                      padding: "3rem",
                      textAlign: "center",
                      color: "#94a3b8",
                    }}
                  >
                    No published examinations are currently open. Please ask your instructor to publish an examination in
                    the <strong>Teacher Workspace</strong>.
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ---------------------------------------------------- */}
      {/* PHASE 2: PRE-EXAM READINESS VERIFICATION */}
      {/* ---------------------------------------------------- */}
      {phase === "readiness" && examData && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          {/* Header */}
          <div
            style={{
              backgroundColor: "#0f172a",
              border: "1px solid #1e293b",
              borderRadius: "14px",
              padding: "1.5rem 2rem",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "1rem",
            }}
          >
            <div>
              <button
                onClick={() => {
                  stopMediaStream();
                  setPhase("lobby");
                }}
                style={{
                  background: "none",
                  border: "none",
                  color: "#38bdf8",
                  fontSize: "0.85rem",
                  cursor: "pointer",
                  padding: 0,
                  marginBottom: "0.3rem",
                  fontWeight: "600",
                }}
              >
                ← Return to Examination Lobby
              </button>
              <h2 style={{ margin: 0, fontSize: "1.4rem", fontWeight: "800" }}>System Readiness & Hardware Check</h2>
              <p style={{ margin: 0, fontSize: "0.85rem", color: "#94a3b8" }}>
                Examination: <strong style={{ color: "#f8fafc" }}>{examData.title}</strong> ({examData.duration_minutes}{" "}
                mins, {examData.questions?.length} MCQs)
              </p>
            </div>
            <div
              style={{
                backgroundColor: "#090d16",
                padding: "8px 16px",
                borderRadius: "8px",
                border: "1px solid #334155",
                fontSize: "0.85rem",
              }}
            >
              Candidate: <strong style={{ color: "#38bdf8" }}>{studentName}</strong> ({studentId})
            </div>
          </div>

          {/* Verification Columns */}
          <div style={{ display: "grid", gridTemplateColumns: "1.1fr 1fr", gap: "1.5rem" }}>
            {/* Left Column: Live Camera & Microphone Preview */}
            <div
              style={{
                backgroundColor: "#0f172a",
                border: "1px solid #1e293b",
                borderRadius: "14px",
                padding: "1.5rem",
                display: "flex",
                flexDirection: "column",
                gap: "1.2rem",
              }}
            >
              <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: "700" }}>Sensor Feeds & Calibration</h3>

              {/* Video Preview Box */}
              <div
                style={{
                  position: "relative",
                  width: "100%",
                  aspectRatio: "4/3",
                  backgroundColor: "#000000",
                  borderRadius: "10px",
                  overflow: "hidden",
                  border: cameraActive ? "2px solid #10b981" : "2px dashed #475569",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <video
                  ref={readinessVideoRef}
                  autoPlay
                  playsInline
                  muted
                  style={{
                    width: "100%",
                    height: "100%",
                    objectFit: "cover",
                    transform: "scaleX(-1)", // Mirror view for natural feel
                  }}
                />
                {!cameraActive && (
                  <div style={{ textAlign: "center", padding: "1rem" }}>
                    <div style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>📷</div>
                    <div style={{ fontSize: "0.9rem", color: "#94a3b8" }}>Camera permission is required</div>
                    <button
                      onClick={initMediaStream}
                      style={{
                        marginTop: "0.8rem",
                        backgroundColor: "#0284c7",
                        color: "white",
                        border: "none",
                        padding: "6px 14px",
                        borderRadius: "6px",
                        cursor: "pointer",
                        fontWeight: "600",
                        fontSize: "0.8rem",
                      }}
                    >
                      Grant Camera Access
                    </button>
                  </div>
                )}
                {cameraActive && (
                  <div
                    style={{
                      position: "absolute",
                      top: "12px",
                      left: "12px",
                      backgroundColor: "rgba(0, 0, 0, 0.65)",
                      color: "#34d399",
                      padding: "4px 10px",
                      borderRadius: "20px",
                      fontSize: "0.75rem",
                      fontWeight: "700",
                      backdropFilter: "blur(4px)",
                    }}
                  >
                    ● Camera Live & Centered
                  </div>
                )}
              </div>

              {/* Microphone Level Meter */}
              <div
                style={{
                  backgroundColor: "#090d16",
                  border: "1px solid #1e293b",
                  borderRadius: "8px",
                  padding: "1rem",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: "0.5rem",
                  }}
                >
                  <span style={{ fontSize: "0.85rem", fontWeight: "600", color: "#e2e8f0" }}>
                    🎤 Microphone Input Level
                  </span>
                  <span
                    style={{
                      fontSize: "0.75rem",
                      fontWeight: "700",
                      color: micActive ? "#34d399" : "#f87171",
                    }}
                  >
                    {micActive ? "Functional" : "Not Detected"}
                  </span>
                </div>
                <div
                  style={{
                    width: "100%",
                    height: "10px",
                    backgroundColor: "#1e293b",
                    borderRadius: "5px",
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      width: `${micLevel}%`,
                      height: "100%",
                      backgroundColor: micLevel > 40 ? "#f59e0b" : "#10b981",
                      transition: "width 0.1s ease",
                    }}
                  />
                </div>
                <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: "0.4rem" }}>
                  Speak a few words to confirm microphone pickup level.
                </div>
              </div>
            </div>

            {/* Right Column: Pre-Flight Checklist & Rules */}
            <div
              style={{
                backgroundColor: "#0f172a",
                border: "1px solid #1e293b",
                borderRadius: "14px",
                padding: "1.5rem",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                gap: "1.2rem",
              }}
            >
              <div>
                <h3 style={{ margin: "0 0 1rem 0", fontSize: "1.05rem", fontWeight: "700" }}>
                  Pre-Flight Checklist & Integrity Rules
                </h3>

                {/* Status checks */}
                <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem", marginBottom: "1.2rem" }}>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "8px 12px",
                      backgroundColor: "#090d16",
                      borderRadius: "6px",
                      fontSize: "0.85rem",
                    }}
                  >
                    <span>Webcam Permission</span>
                    <strong style={{ color: cameraActive ? "#34d399" : "#f87171" }}>
                      {cameraActive ? "✓ Passed" : "✕ Pending"}
                    </strong>
                  </div>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "8px 12px",
                      backgroundColor: "#090d16",
                      borderRadius: "6px",
                      fontSize: "0.85rem",
                    }}
                  >
                    <span>Microphone Permission</span>
                    <strong style={{ color: micActive ? "#34d399" : "#f59e0b" }}>
                      {micActive ? "✓ Passed" : "⚠ Audio Fallback"}
                    </strong>
                  </div>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "8px 12px",
                      backgroundColor: "#090d16",
                      borderRadius: "6px",
                      fontSize: "0.85rem",
                    }}
                  >
                    <span>Backend AI Engine Connectivity</span>
                    <strong style={{ color: backendHealthy ? "#34d399" : "#f87171" }}>
                      {backendHealthy ? "✓ Connected" : "✕ Unreachable"}
                    </strong>
                  </div>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "8px 12px",
                      backgroundColor: "#090d16",
                      borderRadius: "6px",
                      fontSize: "0.85rem",
                    }}
                  >
                    <span>Browser Compatibility</span>
                    <strong style={{ color: "#34d399" }}>✓ Compatible</strong>
                  </div>
                </div>

                {/* Official Instructions */}
                <div
                  style={{
                    backgroundColor: "#090d16",
                    border: "1px solid #1e293b",
                    borderRadius: "8px",
                    padding: "1rem",
                    marginBottom: "1rem",
                  }}
                >
                  <div
                    style={{
                      fontSize: "0.78rem",
                      fontWeight: "700",
                      color: "#94a3b8",
                      textTransform: "uppercase",
                      marginBottom: "0.5rem",
                    }}
                  >
                    Examination Instructions
                  </div>
                  <div
                    style={{
                      fontSize: "0.82rem",
                      color: "#cbd5e1",
                      lineHeight: "1.6",
                      whiteSpace: "pre-line",
                    }}
                  >
                    {examData.instructions ||
                      "1. Remain seated facing the camera.\n2. Do not switch tabs or open other browser windows.\n3. Keep your microphone unmuted.\n4. Questions will auto-submit when the timer elapses."}
                  </div>
                </div>

                {/* Rules Checkbox */}
                <label
                  style={{
                    display: "flex",
                    alignItems: "flex-start",
                    gap: "10px",
                    cursor: "pointer",
                    fontSize: "0.82rem",
                    color: "#e2e8f0",
                    lineHeight: "1.4",
                  }}
                >
                  <input
                    type="checkbox"
                    checked={rulesAccepted}
                    onChange={(e) => setRulesAccepted(e.target.checked)}
                    style={{ marginTop: "3px", cursor: "pointer", width: "16px", height: "16px" }}
                  />
                  <span>
                    I confirm that I am seated in a quiet room, my camera and microphone are operational, and I agree to
                    continuous multimodal AI proctoring for the duration of this examination.
                  </span>
                </label>
              </div>

              {/* Start Button */}
              <button
                onClick={handleStartExam}
                disabled={!rulesAccepted || !cameraActive}
                style={{
                  width: "100%",
                  backgroundColor: rulesAccepted && cameraActive ? "#10b981" : "#334155",
                  color: "#ffffff",
                  border: "none",
                  borderRadius: "10px",
                  padding: "14px",
                  fontSize: "1rem",
                  fontWeight: "800",
                  cursor: rulesAccepted && cameraActive ? "pointer" : "not-allowed",
                  boxShadow: rulesAccepted && cameraActive ? "0 4px 16px rgba(16, 185, 129, 0.4)" : "none",
                  transition: "all 0.15s ease",
                }}
              >
                🚀 Begin Proctored Examination
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ---------------------------------------------------- */}
      {/* PHASE 3: ACTIVE EXAMINATION INTERFACE */}
      {/* ---------------------------------------------------- */}
      {phase === "exam" && examData && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.2rem" }}>
          {/* Top Examination Navigation Header */}
          <div
            style={{
              backgroundColor: "#0f172a",
              border: "1px solid #1e293b",
              borderRadius: "12px",
              padding: "1rem 1.6rem",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "1rem",
            }}
          >
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span
                  style={{
                    backgroundColor: "#ef4444",
                    color: "#ffffff",
                    fontSize: "0.7rem",
                    fontWeight: "800",
                    padding: "2px 6px",
                    borderRadius: "4px",
                  }}
                >
                  LIVE PROCTORED
                </span>
                <span style={{ fontSize: "0.8rem", color: "#94a3b8" }}>Candidate: {studentName}</span>
              </div>
              <h2 style={{ margin: "0.2rem 0 0 0", fontSize: "1.2rem", fontWeight: "800" }}>{examData.title}</h2>
            </div>

            {/* Timer & Submit Action */}
            <div style={{ display: "flex", alignItems: "center", gap: "1.2rem" }}>
              <div
                style={{
                  backgroundColor: timeLeftSeconds <= 120 ? "rgba(239, 68, 68, 0.2)" : "#090d16",
                  border: timeLeftSeconds <= 120 ? "1px solid #ef4444" : "1px solid #334155",
                  borderRadius: "8px",
                  padding: "8px 16px",
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                }}
              >
                <span style={{ fontSize: "1.1rem" }}>⏱️</span>
                <div>
                  <div style={{ fontSize: "0.68rem", color: "#94a3b8", textTransform: "uppercase" }}>TIME REMAINING</div>
                  <div
                    style={{
                      fontFamily: "monospace",
                      fontSize: "1.25rem",
                      fontWeight: "800",
                      color: timeLeftSeconds <= 120 ? "#f87171" : "#38bdf8",
                    }}
                  >
                    {formattedTime}
                  </div>
                </div>
              </div>

              <button
                onClick={() => setConfirmSubmitOpen(true)}
                disabled={submitting}
                style={{
                  backgroundColor: "#0284c7",
                  color: "#ffffff",
                  border: "none",
                  borderRadius: "8px",
                  padding: "10px 20px",
                  fontSize: "0.9rem",
                  fontWeight: "700",
                  cursor: submitting ? "wait" : "pointer",
                  boxShadow: "0 2px 10px rgba(2, 132, 199, 0.3)",
                }}
              >
                {submitting ? "Submitting..." : "Finish & Submit Exam"}
              </button>
            </div>
          </div>

          {/* Active Warning Banner on HUD */}
          {recentWarning && (
            <div
              style={{
                backgroundColor: "rgba(239, 68, 68, 0.95)",
                color: "#ffffff",
                padding: "10px 16px",
                borderRadius: "8px",
                fontSize: "0.88rem",
                fontWeight: "700",
                display: "flex",
                alignItems: "center",
                gap: "10px",
                boxShadow: "0 4px 14px rgba(239, 68, 68, 0.4)",
              }}
            >
              <span>⚠️</span>
              <span>{recentWarning}</span>
            </div>
          )}

          {/* Main 2-Column Examination Workspace */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: "1.2rem", alignItems: "start" }}>
            {/* Left: Question Card & Answering Area */}
            <div
              style={{
                backgroundColor: "#0f172a",
                border: "1px solid #1e293b",
                borderRadius: "14px",
                padding: "2rem",
                display: "flex",
                flexDirection: "column",
                gap: "1.8rem",
                minHeight: "480px",
                justifyContent: "space-between",
              }}
            >
              {currentQuestion && (
                <div>
                  {/* Question Header & Points */}
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      borderBottom: "1px solid #1e293b",
                      paddingBottom: "1rem",
                      marginBottom: "1.2rem",
                    }}
                  >
                    <div>
                      <span style={{ fontSize: "0.8rem", color: "#38bdf8", fontWeight: "700" }}>
                        QUESTION {currentQIndex + 1} OF {totalQuestions}
                      </span>
                    </div>
                    <span
                      style={{
                        backgroundColor: "rgba(16, 185, 129, 0.15)",
                        color: "#34d399",
                        padding: "3px 10px",
                        borderRadius: "12px",
                        fontSize: "0.78rem",
                        fontWeight: "700",
                      }}
                    >
                      {currentQuestion.points} Point{currentQuestion.points > 1 ? "s" : ""}
                    </span>
                  </div>

                  {/* Question Text */}
                  <div
                    style={{
                      fontSize: "1.15rem",
                      fontWeight: "600",
                      lineHeight: "1.6",
                      color: "#f8fafc",
                      marginBottom: "1.8rem",
                    }}
                  >
                    {currentQuestion.question_text}
                  </div>

                  {/* 4 MCQ Radio Options */}
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.8rem" }}>
                    {currentQuestion.options.map((opt, optIdx) => {
                      const isSelected = answers[currentQuestion.id] === optIdx;
                      return (
                        <div
                          key={optIdx}
                          onClick={() => handleSelectOption(currentQuestion.id, optIdx)}
                          style={{
                            padding: "14px 18px",
                            borderRadius: "10px",
                            border: isSelected ? "2px solid #0284c7" : "1px solid #334155",
                            backgroundColor: isSelected ? "rgba(2, 132, 199, 0.15)" : "#090d16",
                            color: isSelected ? "#f8fafc" : "#cbd5e1",
                            cursor: "pointer",
                            display: "flex",
                            alignItems: "center",
                            gap: "14px",
                            transition: "all 0.15s ease",
                          }}
                        >
                          <div
                            style={{
                              width: "22px",
                              height: "22px",
                              borderRadius: "50%",
                              border: isSelected ? "6px solid #0284c7" : "2px solid #64748b",
                              backgroundColor: isSelected ? "#ffffff" : "transparent",
                              boxSizing: "border-box",
                              flexShrink: 0,
                            }}
                          />
                          <span style={{ fontWeight: "700", color: isSelected ? "#38bdf8" : "#94a3b8" }}>
                            {String.fromCharCode(65 + optIdx)}.
                          </span>
                          <span style={{ fontSize: "0.95rem", lineHeight: "1.4" }}>{opt}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Bottom Navigation Buttons */}
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  borderTop: "1px solid #1e293b",
                  paddingTop: "1.2rem",
                  marginTop: "1.5rem",
                }}
              >
                <div style={{ display: "flex", gap: "8px" }}>
                  <button
                    onClick={() => setCurrentQIndex((i) => Math.max(0, i - 1))}
                    disabled={currentQIndex === 0}
                    style={{
                      backgroundColor: "#1e293b",
                      color: currentQIndex === 0 ? "#64748b" : "#e2e8f0",
                      border: "1px solid #334155",
                      borderRadius: "7px",
                      padding: "8px 16px",
                      fontSize: "0.85rem",
                      fontWeight: "600",
                      cursor: currentQIndex === 0 ? "not-allowed" : "pointer",
                    }}
                  >
                    ← Previous
                  </button>
                  <button
                    onClick={() => setCurrentQIndex((i) => Math.min(totalQuestions - 1, i + 1))}
                    disabled={currentQIndex === totalQuestions - 1}
                    style={{
                      backgroundColor: "#1e293b",
                      color: currentQIndex === totalQuestions - 1 ? "#64748b" : "#e2e8f0",
                      border: "1px solid #334155",
                      borderRadius: "7px",
                      padding: "8px 16px",
                      fontSize: "0.85rem",
                      fontWeight: "600",
                      cursor: currentQIndex === totalQuestions - 1 ? "not-allowed" : "pointer",
                    }}
                  >
                    Next →
                  </button>
                </div>

                {answers[currentQuestion?.id] !== undefined && (
                  <button
                    onClick={() => handleClearOption(currentQuestion.id)}
                    style={{
                      background: "none",
                      border: "none",
                      color: "#94a3b8",
                      fontSize: "0.8rem",
                      cursor: "pointer",
                      textDecoration: "underline",
                    }}
                  >
                    Clear answer
                  </button>
                )}
              </div>
            </div>

            {/* Right: AI Proctor HUD & Interactive Question Palette */}
            <div style={{ display: "flex", flexDirection: "column", gap: "1.2rem" }}>
              {/* Compact AI Proctoring HUD */}
              <div
                style={{
                  backgroundColor: "#0f172a",
                  border: "1px solid #1e293b",
                  borderRadius: "14px",
                  padding: "1rem",
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.8rem",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontSize: "0.75rem", fontWeight: "700", color: "#94a3b8", textTransform: "uppercase" }}>
                    AI Proctor HUD
                  </span>
                  <span
                    style={{
                      fontSize: "0.72rem",
                      fontWeight: "700",
                      color: realtimeInference?.flag ? "#f87171" : "#34d399",
                    }}
                  >
                    {realtimeInference?.flag ? "● Warning State" : "● Nominal Active"}
                  </span>
                </div>

                {/* Live Webcam Stream Frame */}
                <div
                  style={{
                    position: "relative",
                    width: "100%",
                    aspectRatio: "4/3",
                    backgroundColor: "#000000",
                    borderRadius: "8px",
                    overflow: "hidden",
                    border: "1px solid #334155",
                  }}
                >
                  <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    style={{
                      width: "100%",
                      height: "100%",
                      objectFit: "cover",
                      transform: "scaleX(-1)",
                    }}
                  />
                  <div
                    style={{
                      position: "absolute",
                      bottom: "6px",
                      left: "6px",
                      backgroundColor: "rgba(0, 0, 0, 0.7)",
                      color: "#ffffff",
                      fontSize: "0.68rem",
                      padding: "2px 6px",
                      borderRadius: "4px",
                      fontFamily: "monospace",
                    }}
                  >
                    Frames: {analyzedFramesCount}
                  </div>
                </div>

                {/* HUD Telemetry Stats */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px", fontSize: "0.75rem" }}>
                  <div
                    style={{
                      backgroundColor: "#090d16",
                      padding: "6px 8px",
                      borderRadius: "6px",
                      border: "1px solid #1e293b",
                    }}
                  >
                    <span style={{ color: "#64748b" }}>Camera: </span>
                    <strong style={{ color: cameraActive ? "#34d399" : "#f87171" }}>
                      {cameraActive ? "Tracking" : "Off"}
                    </strong>
                  </div>
                  <div
                    style={{
                      backgroundColor: "#090d16",
                      padding: "6px 8px",
                      borderRadius: "6px",
                      border: "1px solid #1e293b",
                    }}
                  >
                    <span style={{ color: "#64748b" }}>Mic RMS: </span>
                    <strong style={{ color: micLevel > 40 ? "#f59e0b" : "#34d399" }}>{micLevel}%</strong>
                  </div>
                  <div
                    style={{
                      backgroundColor: "#090d16",
                      padding: "6px 8px",
                      borderRadius: "6px",
                      border: "1px solid #1e293b",
                    }}
                  >
                    <span style={{ color: "#64748b" }}>Tab Switches: </span>
                    <strong style={{ color: tabSwitches > 0 ? "#f87171" : "#e2e8f0" }}>{tabSwitches}</strong>
                  </div>
                  <div
                    style={{
                      backgroundColor: "#090d16",
                      padding: "6px 8px",
                      borderRadius: "6px",
                      border: "1px solid #1e293b",
                    }}
                  >
                    <span style={{ color: "#64748b" }}>Session: </span>
                    <strong style={{ color: "#38bdf8", fontFamily: "monospace" }}>
                      {sessionId.substring(0, 8)}...
                    </strong>
                  </div>
                </div>
              </div>

              {/* Interactive Question Palette */}
              <div
                style={{
                  backgroundColor: "#0f172a",
                  border: "1px solid #1e293b",
                  borderRadius: "14px",
                  padding: "1.2rem",
                  display: "flex",
                  flexDirection: "column",
                  gap: "1rem",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontSize: "0.8rem", fontWeight: "700", color: "#94a3b8" }}>QUESTION PALETTE</span>
                  <span style={{ fontSize: "0.75rem", color: "#34d399", fontWeight: "700" }}>
                    {answeredCount} / {totalQuestions} Answered
                  </span>
                </div>

                {/* Progress bar */}
                <div
                  style={{
                    width: "100%",
                    height: "6px",
                    backgroundColor: "#1e293b",
                    borderRadius: "3px",
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      width: `${(answeredCount / Math.max(1, totalQuestions)) * 100}%`,
                      height: "100%",
                      backgroundColor: "#10b981",
                      transition: "width 0.2s ease",
                    }}
                  />
                </div>

                {/* Question Number Badges Grid */}
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(5, 1fr)",
                    gap: "8px",
                  }}
                >
                  {examData.questions.map((q, idx) => {
                    const isAnswered = answers[q.id] !== undefined;
                    const isCurrent = idx === currentQIndex;
                    return (
                      <button
                        key={q.id || idx}
                        onClick={() => setCurrentQIndex(idx)}
                        style={{
                          aspectRatio: "1/1",
                          borderRadius: "8px",
                          border: isCurrent ? "2px solid #38bdf8" : "1px solid #334155",
                          backgroundColor: isAnswered ? "#10b981" : isCurrent ? "#0284c7" : "#090d16",
                          color: isAnswered || isCurrent ? "#ffffff" : "#94a3b8",
                          fontWeight: "800",
                          fontSize: "0.85rem",
                          cursor: "pointer",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          boxShadow: isCurrent ? "0 0 10px rgba(56, 189, 248, 0.4)" : "none",
                        }}
                      >
                        {idx + 1}
                      </button>
                    );
                  })}
                </div>

                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    fontSize: "0.72rem",
                    color: "#64748b",
                    marginTop: "0.4rem",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                    <div style={{ width: "8px", height: "8px", backgroundColor: "#10b981", borderRadius: "2px" }} />
                    <span>Answered</span>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                    <div style={{ width: "8px", height: "8px", backgroundColor: "#090d16", borderRadius: "2px", border: "1px solid #334155" }} />
                    <span>Unanswered</span>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                    <div style={{ width: "8px", height: "8px", backgroundColor: "#0284c7", borderRadius: "2px" }} />
                    <span>Current</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Submission Confirmation Modal */}
          {confirmSubmitOpen && (
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
                  backgroundColor: "#0f172a",
                  border: "1px solid #334155",
                  borderRadius: "14px",
                  width: "100%",
                  maxWidth: "480px",
                  padding: "1.8rem",
                  boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.8)",
                }}
              >
                <h3 style={{ margin: "0 0 0.8rem 0", fontSize: "1.25rem", fontWeight: "800", color: "#f8fafc" }}>
                  Submit Examination?
                </h3>
                <p style={{ margin: "0 0 1.2rem 0", fontSize: "0.9rem", color: "#94a3b8", lineHeight: "1.5" }}>
                  You have completed <strong style={{ color: "#38bdf8" }}>{answeredCount}</strong> of{" "}
                  <strong style={{ color: "#f8fafc" }}>{totalQuestions}</strong> questions.
                  {answeredCount < totalQuestions && (
                    <span style={{ display: "block", color: "#f59e0b", marginTop: "0.5rem" }}>
                      ⚠️ You have {totalQuestions - answeredCount} unanswered questions remaining.
                    </span>
                  )}
                </p>

                <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
                  <button
                    onClick={() => setConfirmSubmitOpen(false)}
                    style={{
                      backgroundColor: "transparent",
                      color: "#94a3b8",
                      border: "1px solid #334155",
                      borderRadius: "7px",
                      padding: "8px 16px",
                      fontSize: "0.85rem",
                      cursor: "pointer",
                    }}
                  >
                    Continue Answering
                  </button>
                  <button
                    onClick={() => handleSubmitExam(true)}
                    disabled={submitting}
                    style={{
                      backgroundColor: "#10b981",
                      color: "#ffffff",
                      border: "none",
                      borderRadius: "7px",
                      padding: "8px 20px",
                      fontSize: "0.85rem",
                      fontWeight: "700",
                      cursor: submitting ? "wait" : "pointer",
                    }}
                  >
                    {submitting ? "Submitting..." : "Yes, Submit Final Answers"}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ---------------------------------------------------- */}
      {/* PHASE 4: POST-SUBMISSION RESULTS & PROCTORING VERDICT */}
      {/* ---------------------------------------------------- */}
      {phase === "result" && submissionResult && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.8rem" }}>
          {/* Header Banner */}
          <div
            style={{
              backgroundColor: "#0f172a",
              border: "1px solid #1e293b",
              borderRadius: "14px",
              padding: "2rem",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "1.5rem",
              background: "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
            }}
          >
            <div>
              <span
                style={{
                  backgroundColor: "rgba(16, 185, 129, 0.2)",
                  color: "#34d399",
                  fontSize: "0.75rem",
                  fontWeight: "800",
                  padding: "4px 10px",
                  borderRadius: "20px",
                }}
              >
                ✓ EXAMINATION SUBMITTED SUCCESSFULLY
              </span>
              <h1 style={{ fontSize: "1.75rem", fontWeight: "800", margin: "0.6rem 0 0.3rem 0" }}>
                Assessment Performance Record
              </h1>
              <p style={{ margin: 0, fontSize: "0.88rem", color: "#94a3b8" }}>
                Candidate: <strong style={{ color: "#f8fafc" }}>{submissionResult.student_name}</strong> (
                {submissionResult.student_id}) — Submission ID:{" "}
                <code style={{ color: "#38bdf8" }}>{submissionResult.submission_id}</code>
              </p>
            </div>

            <button
              onClick={() => {
                setSubmissionResult(null);
                setAnswers({});
                setExamData(null);
                fetchPublishedExams();
                setPhase("lobby");
              }}
              style={{
                backgroundColor: "#1e293b",
                color: "#e2e8f0",
                border: "1px solid #334155",
                borderRadius: "8px",
                padding: "10px 18px",
                fontSize: "0.85rem",
                fontWeight: "600",
                cursor: "pointer",
              }}
            >
              Return to Examination Lobby
            </button>
          </div>

          {/* Academic Grade vs AI Integrity Comparison */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
            {/* Academic Grade Card */}
            <div
              style={{
                backgroundColor: "#0f172a",
                border: "1px solid #1e293b",
                borderRadius: "14px",
                padding: "1.8rem",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                gap: "1rem",
              }}
            >
              <div>
                <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: "700", textTransform: "uppercase" }}>
                  Academic Assessment Result
                </span>
                <div style={{ display: "flex", alignItems: "baseline", gap: "12px", marginTop: "0.5rem" }}>
                  <div style={{ fontSize: "2.8rem", fontWeight: "900", color: "#10b981" }}>
                    {submissionResult.percentage}%
                  </div>
                  <div style={{ fontSize: "1.1rem", color: "#94a3b8" }}>
                    ({submissionResult.score} / {submissionResult.total_points} marks)
                  </div>
                </div>
              </div>

              <div
                style={{
                  backgroundColor: "#090d16",
                  border: "1px solid #1e293b",
                  borderRadius: "8px",
                  padding: "10px 14px",
                  fontSize: "0.82rem",
                  color: "#94a3b8",
                }}
              >
                Grade evaluated on multiple-choice question marking criteria.
              </div>
            </div>

            {/* AI Integrity Verdict Card */}
            <div
              style={{
                backgroundColor: "#0f172a",
                border: "1px solid #1e293b",
                borderRadius: "14px",
                padding: "1.8rem",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                gap: "1rem",
              }}
            >
              <div>
                <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: "700", textTransform: "uppercase" }}>
                  AI Multimodal Proctoring Verdict
                </span>
                <div style={{ display: "flex", alignItems: "baseline", gap: "12px", marginTop: "0.5rem" }}>
                  <div
                    style={{
                      fontSize: "2.8rem",
                      fontWeight: "900",
                      color: submissionResult.integrity_score >= 80 ? "#10b981" : "#f87171",
                    }}
                  >
                    {submissionResult.integrity_score}%
                  </div>
                  <div
                    style={{
                      fontSize: "1rem",
                      fontWeight: "800",
                      color: submissionResult.verdict_color,
                    }}
                  >
                    {submissionResult.verdict_label}
                  </div>
                </div>
              </div>

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: "0.78rem", color: "#64748b" }}>
                  Non-punitive AI integrity indicator for instructor review.
                </span>
                {submissionResult.proctoring_summary && (
                  <button
                    onClick={() => setShowAuditModal(true)}
                    style={{
                      backgroundColor: "#0284c7",
                      color: "#ffffff",
                      border: "none",
                      borderRadius: "6px",
                      padding: "8px 14px",
                      fontSize: "0.8rem",
                      fontWeight: "700",
                      cursor: "pointer",
                    }}
                  >
                    🔍 Inspect Audit Report
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Detailed Question Review Sheet */}
          <div
            style={{
              backgroundColor: "#0f172a",
              border: "1px solid #1e293b",
              borderRadius: "14px",
              padding: "1.8rem",
            }}
          >
            <h3 style={{ margin: "0 0 1.2rem 0", fontSize: "1.2rem", fontWeight: "800" }}>Question Marking Sheet</h3>

            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              {(submissionResult.question_results || []).map((qr, idx) => (
                <div
                  key={idx}
                  style={{
                    backgroundColor: "#090d16",
                    border: qr.is_correct ? "1px solid rgba(16, 185, 129, 0.35)" : "1px solid rgba(239, 68, 68, 0.35)",
                    borderRadius: "10px",
                    padding: "1.2rem",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      marginBottom: "0.6rem",
                    }}
                  >
                    <span style={{ fontWeight: "700", color: "#38bdf8", fontSize: "0.95rem" }}>
                      Question #{idx + 1}: {qr.question_text}
                    </span>
                    <span
                      style={{
                        fontSize: "0.82rem",
                        fontWeight: "800",
                        color: qr.is_correct ? "#10b981" : "#f87171",
                      }}
                    >
                      {qr.is_correct ? `+${qr.points_earned} Points` : `0 / ${qr.max_points} Points`}
                    </span>
                  </div>

                  <div style={{ display: "flex", gap: "2rem", fontSize: "0.88rem", marginTop: "0.6rem" }}>
                    <div>
                      <span style={{ color: "#64748b" }}>Your Selection: </span>
                      <strong style={{ color: qr.is_correct ? "#34d399" : "#f87171" }}>
                        {qr.selected_option_index !== null && qr.selected_option_index !== undefined
                          ? `Option ${String.fromCharCode(65 + qr.selected_option_index)}`
                          : "Unanswered"}
                      </strong>
                    </div>
                    <div>
                      <span style={{ color: "#64748b" }}>Correct Answer: </span>
                      <strong style={{ color: "#34d399" }}>
                        Option {String.fromCharCode(65 + qr.correct_option_index)}
                      </strong>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Official AI Forensic Audit Modal */}
          {showAuditModal && submissionResult.proctoring_summary && (
            <ProctoringReportModal
              summary={submissionResult.proctoring_summary}
              onClose={() => setShowAuditModal(false)}
            />
          )}
        </div>
      )}
    </div>
  );
}
