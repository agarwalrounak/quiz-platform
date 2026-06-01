import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  DIFFICULTIES,
  QUESTION_TYPES,
  deleteQuestion,
  listQuestions,
  typeLabel,
} from "../api/questions.js";

export default function QuestionList() {
  const [questions, setQuestions] = useState([]);
  const [filters, setFilters] = useState({ type: "", difficulty: "", category: "" });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  function load() {
    setLoading(true);
    listQuestions(filters)
      .then(setQuestions)
      .catch(() => setError("Failed to load questions."))
      .finally(() => setLoading(false));
  }

  // Reload whenever filters change.
  useEffect(load, [filters.type, filters.difficulty, filters.category]);

  async function onDelete(q) {
    if (!window.confirm(`Delete this ${typeLabel(q.type)} question?`)) return;
    await deleteQuestion(q.id);
    load();
  }

  return (
    <main className="container">
      <div className="page-head">
        <h1>Question bank</h1>
        <Link className="btn-link" to="/admin/questions/new">
          + New question
        </Link>
      </div>

      <form className="filters" aria-label="Filter questions" onSubmit={(e) => e.preventDefault()}>
        <div className="field">
          <label htmlFor="f-type">Type</label>
          <select
            id="f-type"
            value={filters.type}
            onChange={(e) => setFilters({ ...filters, type: e.target.value })}
          >
            <option value="">All</option>
            {QUESTION_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor="f-diff">Difficulty</label>
          <select
            id="f-diff"
            value={filters.difficulty}
            onChange={(e) => setFilters({ ...filters, difficulty: e.target.value })}
          >
            <option value="">All</option>
            {DIFFICULTIES.map((d) => (
              <option key={d.value} value={d.value}>
                {d.label}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor="f-cat">Category</label>
          <input
            id="f-cat"
            value={filters.category}
            placeholder="e.g. geography"
            onChange={(e) => setFilters({ ...filters, category: e.target.value })}
          />
        </div>
      </form>

      {error && <p role="alert" className="status-error">{error}</p>}
      {loading ? (
        <p role="status">Loading…</p>
      ) : questions.length === 0 ? (
        <p>No questions match. Try creating one.</p>
      ) : (
        <table className="data-table">
          <caption className="sr-only">Questions</caption>
          <thead>
            <tr>
              <th scope="col">Prompt</th>
              <th scope="col">Type</th>
              <th scope="col">Category</th>
              <th scope="col">Difficulty</th>
              <th scope="col">Active</th>
              <th scope="col">Actions</th>
            </tr>
          </thead>
          <tbody>
            {questions.map((q) => (
              <tr key={q.id}>
                <td>{q.prompt}</td>
                <td>{typeLabel(q.type)}</td>
                <td>{q.category || "—"}</td>
                <td>{q.difficulty}</td>
                <td>{q.is_active ? "Yes" : "No"}</td>
                <td className="row-actions">
                  <Link to={`/admin/questions/${q.id}/edit`}>Edit</Link>
                  <button type="button" className="link-btn danger" onClick={() => onDelete(q)}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
