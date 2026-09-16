import { useEffect, useState } from "react";

// Phase 0: confirms the frontend can start and reach the backend
// health endpoint. No exam UI, webcam preview, or dashboard yet --
// those arrive with the Final Dashboard Requirements in later phases.
function App() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch("http://localhost:8000/health")
      .then((res) => res.json())
      .then(setHealth)
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div style={{ fontFamily: "sans-serif", padding: "2rem" }}>
      <h1>Proctoring System — Phase 0</h1>
      <p>Frontend skeleton is running.</p>
      {health && <p>Backend health check: {JSON.stringify(health)}</p>}
      {error && <p style={{ color: "red" }}>Backend not reachable: {error}</p>}
    </div>
  );
}

export default App;
