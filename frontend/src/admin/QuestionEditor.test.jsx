import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

// Partial-mock: keep real constants (QUESTION_TYPES, DIFFICULTIES), stub the API calls.
vi.mock("../api/questions.js", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    createQuestion: vi.fn(() => Promise.resolve({ id: 1 })),
    getQuestion: vi.fn(),
    updateQuestion: vi.fn(),
  };
});

import QuestionEditor from "./QuestionEditor.jsx";
import { createQuestion } from "../api/questions.js";

function renderNew() {
  return render(
    <MemoryRouter initialEntries={["/admin/questions/new"]}>
      <Routes>
        <Route path="/admin/questions/new" element={<QuestionEditor />} />
        <Route path="/admin/questions" element={<div>list</div>} />
      </Routes>
    </MemoryRouter>
  );
}

beforeEach(() => createQuestion.mockClear());

describe("QuestionEditor", () => {
  it("blocks submit and shows validation errors when invalid", () => {
    renderNew(); // defaults to single choice, empty prompt + empty choices
    fireEvent.click(screen.getByRole("button", { name: /create question/i }));
    expect(screen.getByText(/prompt is required/i)).toBeInTheDocument();
    expect(screen.getByText(/at least two choices/i)).toBeInTheDocument();
    expect(createQuestion).not.toHaveBeenCalled();
  });

  it("submits a valid single-choice question", async () => {
    renderNew();
    fireEvent.change(screen.getByLabelText("Prompt"), {
      target: { value: "Capital of France?" },
    });
    fireEvent.change(screen.getByLabelText("Choice 1 text"), {
      target: { value: "Paris" },
    });
    fireEvent.change(screen.getByLabelText("Choice 2 text"), {
      target: { value: "Lyon" },
    });
    fireEvent.click(screen.getByLabelText("Choice 1 is correct"));
    fireEvent.click(screen.getByRole("button", { name: /create question/i }));

    await waitFor(() => expect(createQuestion).toHaveBeenCalledTimes(1));
    const payload = createQuestion.mock.calls[0][0];
    expect(payload.type).toBe("single");
    expect(payload.choices.filter((c) => c.is_correct)).toHaveLength(1);
  });

  it("uses an accessible fieldset/legend for choices", () => {
    renderNew();
    expect(
      screen.getByRole("group", { name: /mark exactly one correct/i })
    ).toBeInTheDocument();
  });
});
