import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getAttempt } from "../api/attempts.js";

// ✅ / ❌ / ⏳ marker for a question's correctness.
function Mark({ value }) {
  if (value === true) return <span className="mark ok" aria-label="Correct">✅</span>;
  if (value === false) return <span className="mark no" aria-label="Incorrect">❌</span>;
  return <span className="mark pending" aria-label="Awaiting review">⏳</span>;
}

function renderAnswer(q, value) {
  if (value === null || value === undefined || value === "")
    return <em className="muted">No answer</em>;
  if (q.type === "image") {
    return (
      <a href={value} target="_blank" rel="noreferrer">
        View uploaded image
      </a>
    );
  }
  if (Array.isArray(value)) return value.length ? value.join(", ") : <em className="muted">No answer</em>;
  return String(value);
}

export default function ResultsPage() {
  const { id } = useParams();
  const [attempt, setAttempt] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getAttempt(id)
      .then(setAttempt)
      .catch(() => setError("Could not load these results."))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <p className="container" role="status">Loading results…</p>;
  if (error) return <p className="container status-error" role="alert">{error}</p>;

  const pending = attempt.status === "awaiting_review";

  return (
    <main className="container">
      <div className="page-head">
        <h1>Results</h1>
        <Link className="link-btn" to="/history">All attempts</Link>
      </div>

      <section className="card" aria-labelledby="score-heading">
        <h2 id="score-heading" className="sr-only">Score</h2>
        <p className="score-big" role="status">
          {attempt.score} / {attempt.max_score}
        </p>
        {pending && (
          <p className="hint">
            ⏳ Some answers (image uploads) are awaiting admin review. Your score
            may rise once they're graded.
          </p>
        )}
      </section>

      <h2>Review</h2>
      <ol className="question-list">
        {attempt.questions.map((q, i) => (
          <li key={q.id} className="question-card">
            <div className="q-prompt">
              <span className="q-num">Q{i + 1}</span>
              <span>{q.prompt}</span>
              <Mark value={q.is_correct} />
            </div>

            {/* Choice questions: show each option with correct/selected status. */}
            {q.choices.length > 0 ? (
              <ul className="review-choices">
                {q.choices.map((c) => (
                  <li
                    key={c.id}
                    className={[
                      c.is_correct ? "correct" : "",
                      c.selected ? "selected" : "",
                    ].join(" ").trim()}
                  >
                    <span className="choice-tag">
                      {c.is_correct ? "✓" : c.selected ? "✗" : "•"}
                    </span>
                    {c.text}
                    {c.selected && <span className="badge subtle">your pick</span>}
                  </li>
                ))}
              </ul>
            ) : (
              <dl className="review-dl">
                <dt>Your answer</dt>
                <dd>{renderAnswer(q, q.user_answer)}</dd>
                {q.type !== "image" && (
                  <>
                    <dt>Correct answer</dt>
                    <dd>{renderAnswer(q, q.correct_answer)}</dd>
                  </>
                )}
                {q.type === "image" && (
                  <>
                    <dt>Requirement</dt>
                    <dd>{q.correct_answer || "—"}</dd>
                  </>
                )}
              </dl>
            )}
          </li>
        ))}
      </ol>

      <Link className="btn-link" to="/">Back to home</Link>
    </main>
  );
}
