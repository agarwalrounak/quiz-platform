import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import QuestionInput from "./QuestionInput.jsx";

const noop = () => {};

describe("QuestionInput", () => {
  it("renders radio buttons for single choice", () => {
    const q = {
      id: 1,
      type: "single",
      choices: [
        { id: 10, text: "Paris" },
        { id: 11, text: "Lyon" },
      ],
    };
    render(<QuestionInput question={q} value={[]} onChange={noop} onImage={noop} />);
    const radios = screen.getAllByRole("radio");
    expect(radios).toHaveLength(2);
  });

  it("renders checkboxes for multiple choice", () => {
    const q = {
      id: 2,
      type: "multiple",
      choices: [
        { id: 20, text: "A" },
        { id: 21, text: "B" },
        { id: 22, text: "C" },
      ],
    };
    render(<QuestionInput question={q} value={[]} onChange={noop} onImage={noop} />);
    expect(screen.getAllByRole("checkbox")).toHaveLength(3);
  });

  it("renders a number input for numerical", () => {
    const q = { id: 3, type: "numerical", choices: [] };
    render(<QuestionInput question={q} value="" onChange={noop} onImage={noop} />);
    expect(screen.getByLabelText(/number/i)).toHaveAttribute("type", "number");
  });

  it("renders a file input for image and shows the requirement", () => {
    const q = {
      id: 4,
      type: "image",
      choices: [],
      image_requirement: "A red object",
    };
    render(<QuestionInput question={q} value={null} onChange={noop} onImage={noop} />);
    expect(screen.getByText(/A red object/)).toBeInTheDocument();
    expect(screen.getByLabelText(/upload an image/i)).toHaveAttribute("type", "file");
  });
});
