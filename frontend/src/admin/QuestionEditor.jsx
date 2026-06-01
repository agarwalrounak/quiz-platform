import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  DIFFICULTIES,
  QUESTION_TYPES,
  createQuestion,
  getQuestion,
  updateQuestion,
} from "../api/questions.js";

const EMPTY = {
  type: "single",
  prompt: "",
  category: "",
  difficulty: "med",
  is_active: true,
  accepted_text: "",
  numeric_answer: "",
  image_requirement: "",
  choices: [
    { text: "", is_correct: false },
    { text: "", is_correct: false },
  ],
};

const isChoiceType = (t) => t === "single" || t === "multiple";

export default function QuestionEditor() {
  const { id } = useParams();
  const editing = Boolean(id);
  const navigate = useNavigate();

  const [form, setForm] = useState(EMPTY);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(editing);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!editing) return;
    getQuestion(id)
      .then((q) =>
        setForm({
          ...EMPTY,
          ...q,
          numeric_answer: q.numeric_answer ?? "",
          choices: q.choices?.length ? q.choices : EMPTY.choices,
        })
      )
      .finally(() => setLoading(false));
  }, [id]);

  const set = (field, value) => setForm((f) => ({ ...f, [field]: value }));

  // --- Choice helpers ---
  function setChoice(i, patch) {
    setForm((f) => {
      const choices = f.choices.map((c, idx) => (idx === i ? { ...c, ...patch } : c));
      return { ...f, choices };
    });
  }
  function pickSingle(i) {
    // Single choice: selecting one clears the others.
    setForm((f) => ({
      ...f,
      choices: f.choices.map((c, idx) => ({ ...c, is_correct: idx === i })),
    }));
  }
  const addChoice = () =>
    setForm((f) => ({ ...f, choices: [...f.choices, { text: "", is_correct: false }] }));
  const removeChoice = (i) =>
    setForm((f) => ({ ...f, choices: f.choices.filter((_, idx) => idx !== i) }));

  // --- Client-side validation mirroring the server rules ---
  function validate() {
    const e = {};
    if (!form.prompt.trim()) e.prompt = "Prompt is required.";
    if (isChoiceType(form.type)) {
      const filled = form.choices.filter((c) => c.text.trim());
      if (filled.length < 2) e.choices = "Provide at least two choices.";
      else {
        const correct = filled.filter((c) => c.is_correct).length;
        if (form.type === "single" && correct !== 1)
          e.choices = "Exactly one choice must be correct.";
        if (form.type === "multiple" && correct < 1)
          e.choices = "At least one choice must be correct.";
      }
    } else if (form.type === "text") {
      if (!form.accepted_text.trim()) e.accepted_text = "Accepted answer is required.";
    } else if (form.type === "numerical") {
      if (form.numeric_answer === "" || isNaN(Number(form.numeric_answer)))
        e.numeric_answer = "A numeric answer is required.";
    } else if (form.type === "image") {
      if (!form.image_requirement.trim())
        e.image_requirement = "Describe what the image must show.";
    }
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  function buildPayload() {
    const base = {
      type: form.type,
      prompt: form.prompt.trim(),
      category: form.category.trim(),
      difficulty: form.difficulty,
      is_active: form.is_active,
    };
    if (isChoiceType(form.type)) {
      base.choices = form.choices
        .filter((c) => c.text.trim())
        .map((c, i) => ({ text: c.text.trim(), is_correct: !!c.is_correct, order: i }));
    } else if (form.type === "text") {
      base.accepted_text = form.accepted_text.trim();
    } else if (form.type === "numerical") {
      base.numeric_answer = form.numeric_answer;
    } else if (form.type === "image") {
      base.image_requirement = form.image_requirement.trim();
    }
    return base;
  }

  async function onSubmit(e) {
    e.preventDefault();
    if (!validate()) return;
    setBusy(true);
    try {
      const payload = buildPayload();
      if (editing) await updateQuestion(id, payload);
      else await createQuestion(payload);
      navigate("/admin/questions");
    } catch (err) {
      const data = err.response?.data || {};
      setErrors((prev) => ({
        ...prev,
        ...Object.fromEntries(
          Object.entries(data).map(([k, v]) => [k, [].concat(v).join(" ")])
        ),
      }));
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <p className="container" role="status">Loading…</p>;

  return (
    <main className="container narrow">
      <h1>{editing ? "Edit question" : "New question"}</h1>
      <form onSubmit={onSubmit} noValidate>
        <div className="field">
          <label htmlFor="type">Type</label>
          <select id="type" value={form.type} onChange={(e) => set("type", e.target.value)}>
            {QUESTION_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label htmlFor="prompt">Prompt</label>
          <textarea
            id="prompt"
            rows={3}
            value={form.prompt}
            onChange={(e) => set("prompt", e.target.value)}
            aria-invalid={!!errors.prompt}
          />
          {errors.prompt && <p className="field-error" role="alert">{errors.prompt}</p>}
        </div>

        <div className="grid-2">
          <div className="field">
            <label htmlFor="category">Category</label>
            <input
              id="category"
              value={form.category}
              onChange={(e) => set("category", e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="difficulty">Difficulty</label>
            <select
              id="difficulty"
              value={form.difficulty}
              onChange={(e) => set("difficulty", e.target.value)}
            >
              {DIFFICULTIES.map((d) => (
                <option key={d.value} value={d.value}>
                  {d.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* --- Type-specific answer section --- */}
        {isChoiceType(form.type) && (
          <fieldset className="choices-fieldset">
            <legend>
              Choices —{" "}
              {form.type === "single"
                ? "mark exactly one correct"
                : "mark at least one correct"}
            </legend>
            {errors.choices && <p className="field-error" role="alert">{errors.choices}</p>}
            {form.choices.map((c, i) => (
              <div className="choice-row" key={i}>
                <input
                  type={form.type === "single" ? "radio" : "checkbox"}
                  name="correct"
                  checked={!!c.is_correct}
                  aria-label={`Choice ${i + 1} is correct`}
                  onChange={() =>
                    form.type === "single"
                      ? pickSingle(i)
                      : setChoice(i, { is_correct: !c.is_correct })
                  }
                />
                <input
                  type="text"
                  value={c.text}
                  placeholder={`Choice ${i + 1}`}
                  aria-label={`Choice ${i + 1} text`}
                  onChange={(e) => setChoice(i, { text: e.target.value })}
                />
                {form.choices.length > 2 && (
                  <button
                    type="button"
                    className="link-btn danger"
                    onClick={() => removeChoice(i)}
                    aria-label={`Remove choice ${i + 1}`}
                  >
                    Remove
                  </button>
                )}
              </div>
            ))}
            <button type="button" className="link-btn" onClick={addChoice}>
              + Add choice
            </button>
          </fieldset>
        )}

        {form.type === "text" && (
          <div className="field">
            <label htmlFor="accepted_text">Accepted answer</label>
            <input
              id="accepted_text"
              value={form.accepted_text}
              onChange={(e) => set("accepted_text", e.target.value)}
              aria-invalid={!!errors.accepted_text}
            />
            <p className="hint">Matching is case-insensitive and trims whitespace.</p>
            {errors.accepted_text && (
              <p className="field-error" role="alert">{errors.accepted_text}</p>
            )}
          </div>
        )}

        {form.type === "numerical" && (
          <div className="field">
            <label htmlFor="numeric_answer">Correct value</label>
            <input
              id="numeric_answer"
              type="number"
              step="any"
              value={form.numeric_answer}
              onChange={(e) => set("numeric_answer", e.target.value)}
              aria-invalid={!!errors.numeric_answer}
            />
            <p className="hint">Graded by exact match.</p>
            {errors.numeric_answer && (
              <p className="field-error" role="alert">{errors.numeric_answer}</p>
            )}
          </div>
        )}

        {form.type === "image" && (
          <div className="field">
            <label htmlFor="image_requirement">Image requirement</label>
            <textarea
              id="image_requirement"
              rows={2}
              value={form.image_requirement}
              onChange={(e) => set("image_requirement", e.target.value)}
              aria-invalid={!!errors.image_requirement}
            />
            <p className="hint">Reviewers grade uploads against this requirement.</p>
            {errors.image_requirement && (
              <p className="field-error" role="alert">{errors.image_requirement}</p>
            )}
          </div>
        )}

        <div className="field checkbox-field">
          <input
            id="is_active"
            type="checkbox"
            checked={form.is_active}
            onChange={(e) => set("is_active", e.target.checked)}
          />
          <label htmlFor="is_active">Active (included in the quiz pool)</label>
        </div>

        <div className="form-actions">
          <button type="submit" disabled={busy}>
            {busy ? "Saving…" : editing ? "Save changes" : "Create question"}
          </button>
          <button
            type="button"
            className="link-btn"
            onClick={() => navigate("/admin/questions")}
          >
            Cancel
          </button>
        </div>
      </form>
    </main>
  );
}
