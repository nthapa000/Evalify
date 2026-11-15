// forms.test.jsx — paper-creation building blocks (step indicator, rubric editor).
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import StepWizard from "../StepWizard";
import RubricBuilder from "../RubricBuilder";

describe("forms", () => {
  // Why: the teacher must see which step of paper creation they are on and which are done
  it("StepWizard marks finished steps with a check", () => {
    render(<StepWizard steps={["Details", "Answers", "Review"]} current={2} />);
    expect(screen.getByText("01 done")).toBeInTheDocument();
    expect(screen.getByText("02")).toBeInTheDocument();
    expect(screen.getByText("Answers").closest("li")).toHaveAttribute("aria-current", "step");
  });

  // Why: rubric points drive subjective grading; adding, starring (mandatory) and removing must update the rubric
  it("RubricBuilder adds, stars and removes concepts", () => {
    const onChange = vi.fn();
    const value = { key_concepts: ["energy from the sun"], mandatory_concepts: [], marks_per_concept: 1, model_answer: "" };
    render(<RubricBuilder questionIndex={0} value={value} onChange={onChange} />);
    fireEvent.change(screen.getByPlaceholderText(/Type concept/), { target: { value: "an example" } });
    fireEvent.click(screen.getByRole("button", { name: "Add" }));
    expect(onChange).toHaveBeenLastCalledWith(expect.objectContaining({ key_concepts: ["energy from the sun", "an example"] }));
    fireEvent.click(screen.getByRole("button", { name: 'Mark "energy from the sun" as required' }));
    expect(onChange).toHaveBeenLastCalledWith(expect.objectContaining({ mandatory_concepts: ["energy from the sun"] }));
    fireEvent.click(screen.getByRole("button", { name: 'Remove "energy from the sun"' }));
    expect(onChange).toHaveBeenLastCalledWith(expect.objectContaining({ key_concepts: [] }));
  });
});
