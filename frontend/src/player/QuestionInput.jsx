// Renders the appropriate accessible input for a single served question.
// `value` shape depends on type; `onChange` reports the new value.
// `labelledById` points to the element holding the question prompt so the
// radio/checkbox group is announced with the actual question text.
export default function QuestionInput({ question, value, onChange, onImage, labelledById }) {
  const { id, type, choices } = question;
  const groupId = `q-${id}`;

  if (type === "single") {
    return (
      <fieldset className="q-fieldset" aria-labelledby={labelledById}>
        <legend className="sr-only">Choose one answer</legend>
        {choices.map((c) => (
          <label key={c.id} className="option">
            <input
              type="radio"
              name={groupId}
              checked={value?.[0] === c.id}
              onChange={() => onChange([c.id])}
            />
            <span>{c.text}</span>
          </label>
        ))}
      </fieldset>
    );
  }

  if (type === "multiple") {
    const selected = value || [];
    const toggle = (cid) =>
      onChange(
        selected.includes(cid)
          ? selected.filter((x) => x !== cid)
          : [...selected, cid]
      );
    return (
      <fieldset className="q-fieldset" aria-labelledby={labelledById}>
        <legend className="sr-only">Choose all that apply</legend>
        {choices.map((c) => (
          <label key={c.id} className="option">
            <input
              type="checkbox"
              checked={selected.includes(c.id)}
              onChange={() => toggle(c.id)}
            />
            <span>{c.text}</span>
          </label>
        ))}
      </fieldset>
    );
  }

  // For single-input types, include the question prompt in the accessible name
  // by referencing both the prompt and the visible field label.
  const labelId = `${groupId}-lbl`;
  const ariaLabelledBy = [labelledById, labelId].filter(Boolean).join(" ");

  if (type === "numerical") {
    return (
      <div className="field">
        <label id={labelId} htmlFor={groupId}>Your answer (number)</label>
        <input
          id={groupId}
          type="number"
          step="any"
          aria-labelledby={ariaLabelledBy}
          value={value ?? ""}
          onChange={(e) => onChange(e.target.value)}
        />
      </div>
    );
  }

  if (type === "text") {
    return (
      <div className="field">
        <label id={labelId} htmlFor={groupId}>Your answer</label>
        <input
          id={groupId}
          type="text"
          aria-labelledby={ariaLabelledBy}
          value={value ?? ""}
          onChange={(e) => onChange(e.target.value)}
        />
      </div>
    );
  }

  if (type === "image") {
    const reqId = `${groupId}-req`;
    return (
      <div className="field">
        {question.image_requirement && (
          <p className="hint" id={reqId}>Requirement: {question.image_requirement}</p>
        )}
        <label id={labelId} htmlFor={groupId}>Upload an image</label>
        <input
          id={groupId}
          type="file"
          accept="image/png,image/jpeg,image/webp"
          aria-labelledby={ariaLabelledBy}
          aria-describedby={question.image_requirement ? reqId : undefined}
          onChange={(e) => onImage(e.target.files?.[0] || null)}
        />
        {value && <p className="hint">Selected: {value.name}</p>}
        <p className="hint">This answer is graded by an admin after you submit.</p>
      </div>
    );
  }

  return null;
}
