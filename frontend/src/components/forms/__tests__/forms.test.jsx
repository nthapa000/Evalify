// forms.test.jsx — paper-creation building blocks (step indicator, rubric editor).
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import StepWizard from "../StepWizard";
import RubricBuilder from "../RubricBuilder";

describe("forms", () => {
  // Why: the teacher must see which step of paper creation they are on and which are done
  it("StepWizard marks finished steps with a check", () => {
    render(<StepWizard steps={["Details", "Answers", "Review"]} current={2} />);
    expect(screen.getByText("✓")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  // Why: rubric points drive subjective grading; adding, starring (mandatory) and removing must update the rubric
  it("RubricBuilder adds, stars and removes concepts", () => {
    const onChange = vi.fn();
    const value = { key_concepts: ["energy from the sun"], mandatory_concepts: [], marks_per_concept: 1, model_answer: "" };
    render(<RubricBuilder questionIndex={0} value={value} onChange={onChange} />);
    fireEvent.change(screen.getByPlaceholderText(/Type concept/), { target: { value: "an example" } });
    fireEvent.click(screen.getByRole("button", { name: "Add" }));
    expect(onChange).toHaveBeenLastCalledWith(expect.objectContaining({ key_concepts: ["energy from the sun", "an example"] }));
    fireEvent.click(screen.getByTitle("Toggle mandatory"));
    expect(onChange).toHaveBeenLastCalledWith(expect.objectContaining({ mandatory_concepts: ["energy from the sun"] }));
    fireEvent.click(screen.getByText("×"));
    expect(onChange).toHaveBeenLastCalledWith(expect.objectContaining({ key_concepts: [] }));
  });
});
