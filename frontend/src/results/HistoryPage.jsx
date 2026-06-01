import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listAttempts } from "../api/attempts.js";

const STATUS_LABEL = {
  in_progress: "In progress",
  awaiting_review: "Awaiting review",
  graded: "Graded",
};

function formatDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString();
}

export default function HistoryPage() {
  const [attempts, setAttempts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    listAttempts()
      .then(setAttempts)
      .catch(() => setError("Could not load your attempts."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="container">
      <h1>My attempts</h1>
      {error && <p role="alert" className="status-error">{error}</p>}
      {loading ? (
        <p role="status">Loading…</p>
      ) : attempts.length === 0 ? (
        <p>
          You haven't taken any quizzes yet. <Link to="/">Start one →</Link>
        </p>
      ) : (
        <table className="data-table">
          <caption className="sr-only">Your quiz attempts</caption>
          <thead>
            <tr>
              <th scope="col">Date</th>
              <th scope="col">Score</th>
              <th scope="col">Status</th>
              <th scope="col">Actions</th>
            </tr>
          </thead>
          <tbody>
            {attempts.map((a) => (
              <tr key={a.id}>
                <td>{formatDate(a.created_at)}</td>
                <td>
                  {a.score === null ? "—" : `${a.score} / ${a.max_score}`}
                </td>
                <td>{STATUS_LABEL[a.status] || a.status}</td>
                <td className="row-actions">
                  {a.submitted_at ? (
                    <Link to={`/results/${a.id}`}>Review</Link>
                  ) : (
                    <Link to={`/quiz/${a.id}`}>Resume</Link>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
