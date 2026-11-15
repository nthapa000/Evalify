// EvaluationNotice.test.jsx — what the student sees until the teacher releases results.
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import EvaluationNotice from "../EvaluationNotice";

describe("EvaluationNotice", () => {
  // Why: while the sheet is being read and marked the student is told so (no marks yet)
  it("explains that the sheet is being marked", () => {
    render(<EvaluationNotice status="processing" />);
    expect(screen.getByRole("heading", { name: "Your answer sheet is being evaluated" })).toBeInTheDocument();
    expect(screen.getByText(/being read and marked/)).toBeInTheDocument();
  });

  // Why: after marking, results stay hidden until the teacher releases them — the student sees the same window
  it("explains that results wait for the teacher's release", () => {
    render(<EvaluationNotice status="awaiting_release" />);
    expect(screen.getByRole("heading", { name: "Your answer sheet is being evaluated" })).toBeInTheDocument();
    expect(screen.getByText(/teacher releases the results/)).toBeInTheDocument();
  });
});
