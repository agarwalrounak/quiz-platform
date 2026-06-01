import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { getAttempt, submitAttempt } from "../api/attempts.js";
import QuestionInput from "./QuestionInput.jsx";

export default function QuizPlayer() {
  const { id } = useParams();
  const location = useLocation();

  const [attempt, setAttempt] = useState(location.state?.attempt || null);
  const [loading, setLoading] = useState(!location.state?.attempt);
  const [answers, setAnswers] = useState({}); // aqId -> value
  const [images, setImages] = useState({}); // aqId -> File
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (attempt) return;
    getAttempt(id)
      .then(setAttempt)
      .catch(() => setError("Could not load this quiz."))
      .finally(() => setLoading(false));
  }, [id]);

  const questions = attempt?.questions || [];

  const answeredCount = useMemo(() => {
    return questions.filter((q) => {
      const v = answers[q.id];
      if (q.type === "image") return !!images[q.id];
      if (q.type === "single" || q.type === "multiple") return v && v.length > 0;
      return v !== undefined && v !== "";
    }).length;
  }, [questions, answers, images]);

  function setAnswer(aqId, value) {
    setAnswers((a) => ({ ...a, [aqId]: value }));
  }
  function setImage(aqId, file) {
    setImages((m) => ({ ...m, [aqId]: file }));
  }

  function buildAnswers() {
    return questions.map((q) => {
      const base = { attempt_question: q.id };
      const v = answers[q.id];
      if (q.type === "single" || q.type === "multiple") base.selected_choice_ids = v || [];
      else if (q.type === "numerical") base.numeric_value = v ?? "";
      else if (q.type === "text") base.text_value = v ?? "";
      return base;
    });
  }

  async function onSubmit(e) {
    e.preventDefault();
    if (!window.confirm("Submit this quiz? You can't change answers afterwards.")) return;
    setBusy(true);
    setError(null);
    try {
      const data = await submitAttempt(id, buildAnswers(), images);
      setResult(data);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch {
      setError("Submission failed. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <p className="container" role="status">Loading quiz…</p>;
  if (error && !attempt)
    return <p className="container status-error" role="alert">{error}</p>;

  // --- Result summary (shown after submit) ---
  if (result) {
    const pending = result.status === "awaiting_review";
    return (
      <main className="container narrow">
        <h1>Quiz submitted</h1>
        <p className="score-big" role="status">
          {result.score} / {result.max_score}
        </p>
        {pending && (
          <p className="hint">
            Some answers (image uploads) are awaiting admin review — your score
            may change once reviewed.
          </p>
        )}
        <div className="form-actions">
          <Link className="btn-link" to={`/results/${result.id}`}>
            Review answers
          </Link>
          <Link className="link-btn" to="/history">
            My attempts
          </Link>
          <Link className="link-btn" to="/">
            Home
          </Link>
        </div>
      </main>
    );
  }

  // --- Active quiz ---
  return (
    <main className="container">
      <div className="page-head">
        <h1>Quiz</h1>
        <p className="progress" aria-live="polite">
          {answeredCount} / {questions.length} answered
        </p>
      </div>

      {error && <p role="alert" className="status-error">{error}</p>}

      <form onSubmit={onSubmit}>
        <ol className="question-list">
          {questions.map((q, i) => (
            <li key={q.id} className="question-card">
              <div className="q-prompt" id={`prompt-${q.id}`}>
                <span className="q-num">Q{i + 1}</span>
                <span>{q.prompt}</span>
              </div>
              <QuestionInputWrapper
                question={q}
                value={answers[q.id] ?? (images[q.id] || undefined)}
                onChange={(v) => setAnswer(q.id, v)}
                onImage={(f) => setImage(q.id, f)}
                imageValue={images[q.id]}
                labelledById={`prompt-${q.id}`}
              />
            </li>
          ))}
        </ol>

        <button type="submit" disabled={busy}>
          {busy ? "Submitting…" : "Submit quiz"}
        </button>
      </form>
    </main>
  );
}

// Thin wrapper so image File value is passed correctly.
function QuestionInputWrapper({ question, value, onChange, onImage, imageValue, labelledById }) {
  return (
    <QuestionInput
      question={question}
      value={question.type === "image" ? imageValue : value}
      onChange={onChange}
      onImage={onImage}
      labelledById={labelledById}
    />
  );
}
