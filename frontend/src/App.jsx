import { useState } from "react";

const API_URL = "http://localhost:5001"; // your Flask backend

function App() {
  const [applicantId, setApplicantId] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleExplain() {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await fetch(`${API_URL}/explain/${applicantId}`);
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Something went wrong"); // e.g. applicant not found
      } else {
        setResult(data);
      }
    } catch (e) {
      // fires if the backend isn't running / unreachable
      setError("Could not reach the backend. Is app.py running on port 5001?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{ maxWidth: 700, margin: "40px auto", fontFamily: "sans-serif" }}
    >
      <h1>Credit Decision Explainer</h1>
      <p>
        Enter an applicant ID to see the model's decision and the reasons behind
        it.
      </p>

      <div style={{ display: "flex", marginTop: "10px", gap: 8 }}>
        <input
          value={applicantId}
          onChange={(e) => setApplicantId(e.target.value)}
          placeholder="e.g. 295946"
          style={{ flex: 1, padding: 8 }}
        />
        <button onClick={handleExplain} disabled={loading || !applicantId}>
          {loading ? "Thinking..." : "Explain"}
        </button>
      </div>

      {error && <p style={{ color: "crimson" }}>{error}</p>}

      {result && (
        <div
          style={{
            marginTop: 24,
            padding: 16,
            border: "1px solid #ddd",
            borderRadius: 8,
          }}
        >
          <h2
            style={{
              color: result.decision === "DECLINE" ? "crimson" : "green",
            }}
          >
            {result.decision}
          </h2>
          <p>
            <strong>Default probability:</strong>{" "}
            {(result.default_probability * 100).toFixed(1)}%
          </p>
          <p>{result.explanation}</p>
        </div>
      )}
    </div>
  );
}

export default App;
