import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api/attempts.js", () => ({ getAttempt: vi.fn() }));
import ResultsPage from "./ResultsPage.jsx";
import { getAttempt } from "../api/attempts.js";

const ATTEMPT = {
  id: 1,
  status: "graded",
  score: 1,
  max_score: 2,
  questions: [
    {
      id: 10,
      type: "single",
      prompt: "Capital of France?",
      is_correct: true,
      user_answer: ["Paris"],
      correct_answer: ["Paris"],
      choices: [
        { id: 1, text: "Paris", is_correct: true, selected: true },
        { id: 2, text: "Lyon", is_correct: false, selected: false },
      ],
    },
    {
      id: 11,
      type: "text",
      prompt: "Largest ocean?",
      is_correct: false,
      user_answer: "Atlantic",
      correct_answer: "Pacific",
      choices: [],
    },
  ],
};

function renderResults() {
  return render(
    <MemoryRouter initialEntries={["/results/1"]}>
      <Routes>
        <Route path="/results/:id" element={<ResultsPage />} />
      </Routes>
    </MemoryRouter>
  );
}

beforeEach(() => getAttempt.mockResolvedValue(ATTEMPT));

describe("ResultsPage", () => {
  it("shows the overall score and both prompts", async () => {
    renderResults();
    expect(await screen.findByText("1 / 2")).toBeInTheDocument();
    expect(screen.getByText("Capital of France?")).toBeInTheDocument();
    expect(screen.getByText("Largest ocean?")).toBeInTheDocument();
  });

  it("marks correctness per question (accessible labels)", async () => {
    renderResults();
    await screen.findByText("1 / 2");
    expect(screen.getByLabelText("Correct")).toBeInTheDocument();
    expect(screen.getByLabelText("Incorrect")).toBeInTheDocument();
  });

  it("reveals the user's answer and the correct answer for text questions", async () => {
    renderResults();
    await screen.findByText("1 / 2");
    expect(screen.getByText("Atlantic")).toBeInTheDocument(); // user's answer
    expect(screen.getByText("Pacific")).toBeInTheDocument(); // correct answer
  });
});
