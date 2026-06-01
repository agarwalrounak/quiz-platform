import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api/attempts.js", () => ({ listAttempts: vi.fn() }));
import HistoryPage from "./HistoryPage.jsx";
import { listAttempts } from "../api/attempts.js";

describe("HistoryPage", () => {
  it("lists attempts with score and a review link", async () => {
    listAttempts.mockResolvedValue([
      {
        id: 7,
        status: "graded",
        score: 3,
        max_score: 10,
        created_at: "2026-01-01T00:00:00Z",
        submitted_at: "2026-01-01T00:05:00Z",
      },
    ]);
    render(
      <MemoryRouter>
        <HistoryPage />
      </MemoryRouter>
    );
    expect(await screen.findByText("3 / 10")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /review/i })).toHaveAttribute(
      "href",
      "/results/7"
    );
  });

  it("shows an empty state when there are no attempts", async () => {
    listAttempts.mockResolvedValue([]);
    render(
      <MemoryRouter>
        <HistoryPage />
      </MemoryRouter>
    );
    expect(await screen.findByText(/haven't taken any quizzes/i)).toBeInTheDocument();
  });
});
