import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext.jsx";
import { startAttempt } from "../api/attempts.js";

export default function Dashboard() {
  const { user, isAdmin } = useAuth();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function onStart() {
    setBusy(true);
    setError(null);
    try {
      const attempt = await startAttempt();
      navigate(`/quiz/${attempt.id}`, { state: { attempt } });
    } catch (err) {
      setError(
        err.response?.data?.detail || "Could not start a quiz. Please try again."
      );
      setBusy(false);
    }
  }

  return (
    <main className="container">
      <h1>Welcome, {user.username}</h1>
      <p>
        You are signed in as <strong>{user.role}</strong>.
      </p>

      <section aria-labelledby="start-heading" className="card">
        <h2 id="start-heading">Take a quiz</h2>
        <p>
          Each attempt serves a fresh, randomized set of questions from the bank.
        </p>
        {error && <p role="alert" className="status-error">{error}</p>}
        <button type="button" onClick={onStart} disabled={busy}>
          {busy ? "Starting…" : "Start new quiz"}
        </button>
      </section>

      <section aria-labelledby="links-heading">
        <h2 id="links-heading">More</h2>
        <ul>
          <li>
            <Link to="/history">Your past attempts</Link>
          </li>
          {isAdmin && (
            <li>
              <Link to="/admin/questions">Manage the question bank</Link>
            </li>
          )}
        </ul>
      </section>
    </main>
  );
}
