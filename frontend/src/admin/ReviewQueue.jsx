import { useEffect, useState } from "react";
import { listReviewQueue, submitVerdict } from "../api/review.js";

export default function ReviewQueue() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [busyId, setBusyId] = useState(null);
  const [message, setMessage] = useState(null);

  function load() {
    setLoading(true);
    listReviewQueue()
      .then(setItems)
      .catch(() => setError("Failed to load the review queue."))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function review(item, isCorrect) {
    setBusyId(item.id);
    setError(null);
    try {
      const res = await submitVerdict(item.id, isCorrect);
      // Drop the reviewed item from the list.
      setItems((cur) => cur.filter((i) => i.id !== item.id));
      setMessage(
        `Marked ${isCorrect ? "correct" : "incorrect"}. ` +
          `Attempt #${res.attempt_id} is now ${res.attempt_status.replace("_", " ")} ` +
          `(${res.attempt_score}/${res.attempt_max_score}).`
      );
    } catch {
      setError("Could not save the verdict. Please try again.");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <main className="container">
      <h1>Image review queue</h1>
      <p className="hint">
        Image answers from submitted attempts await your verdict. Grading one
        finalizes that attempt's score.
      </p>

      {message && <p role="status" className="status-ok">{message}</p>}
      {error && <p role="alert" className="status-error">{error}</p>}

      {loading ? (
        <p role="status">Loading…</p>
      ) : items.length === 0 ? (
        <p>🎉 Nothing to review right now.</p>
      ) : (
        <ul className="review-queue">
          {items.map((item) => (
            <li key={item.id} className="question-card review-item">
              <div className="review-img">
                {item.image ? (
                  <a href={item.image} target="_blank" rel="noreferrer">
                    <img src={item.image} alt={`Submission for: ${item.prompt}`} />
                  </a>
                ) : (
                  <p className="muted">No image uploaded</p>
                )}
              </div>
              <div className="review-meta">
                <p className="q-prompt">{item.prompt}</p>
                <p>
                  <strong>Requirement:</strong> {item.image_requirement || "—"}
                </p>
                <p className="hint">
                  By {item.user} · attempt #{item.attempt_id}
                </p>
                <div className="form-actions">
                  <button
                    type="button"
                    disabled={busyId === item.id}
                    onClick={() => review(item, true)}
                  >
                    ✅ Correct
                  </button>
                  <button
                    type="button"
                    className="btn-danger"
                    disabled={busyId === item.id}
                    onClick={() => review(item, false)}
                  >
                    ❌ Incorrect
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
