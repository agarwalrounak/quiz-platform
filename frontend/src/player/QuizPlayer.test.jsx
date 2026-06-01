import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

vi.mock("../api/attempts.js", () => ({
  getAttempt: vi.fn(),
  submitAttempt: vi.fn(),
}));
import QuizPlayer from "./QuizPlayer.jsx";

const ATTEMPT = {
  id: 5,
  status: "in_progress",
  max_score: 2,
  questions: [
    {
      id: 1,
      type: "single",
      prompt: "Capital of France?",
      choices: [
        { id: 1, text: "Paris" },
        { id: 2, text: "Lyon" },
      ],
    },
    { id: 2, type: "text", prompt: "Largest ocean?", choices: [] },
  ],
};

function renderPlayer() {
  // Pass the attempt via location state so no fetch is needed.
  return render(
    <MemoryRouter initialEntries={[{ pathname: "/quiz/5", state: { attempt: ATTEMPT } }]}>
      <Routes>
        <Route path="/quiz/:id" element={<QuizPlayer />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("QuizPlayer", () => {
  it("renders each served question and an answered-progress indicator", () => {
    renderPlayer();
    expect(screen.getByText("Capital of France?")).toBeInTheDocument();
    expect(screen.getByText("Largest ocean?")).toBeInTheDocument();
    expect(screen.getByText("0 / 2 answered")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /submit quiz/i })).toBeInTheDocument();
  });

  it("renders single-choice options as radios tied to the prompt", () => {
    renderPlayer();
    // The radio group is labelled by the question prompt.
    expect(
      screen.getByRole("group", { name: /capital of france/i })
    ).toBeInTheDocument();
    expect(screen.getAllByRole("radio")).toHaveLength(2);
  });
});
