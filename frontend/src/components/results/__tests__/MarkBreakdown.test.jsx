// MarkBreakdown.test.jsx — how a written answer was marked, point by point, for the student.
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import MarkBreakdown from "../MarkBreakdown";

const rubric = { key_concepts: ["energy derived from the sun", "an example of solar energy"], marks_per_concept: 1 };
const concepts = [
  { concept: "energy derived from the sun", present: true, partial: false, evidence: "energy we get from sun light" },
  { concept: "an example of solar energy", present: false, partial: true, evidence: "sun is used" },
];
const row = (extra = {}) => ({ question: "S4", marks_available: 2, marks_earned: 1.5, rubric_marks: 1.5,
                               calibrated_marks: null, mandatory_met: true, concepts, ...extra });

describe("MarkBreakdown", () => {
  // Why: the student must see, for every rubric point, whether it was met and how many marks it gave
  it("lists each rubric point with its verdict and marks", () => {
    render(<MarkBreakdown row={row()} rubric={rubric} />);
    expect(screen.getByTestId("point-0")).toHaveTextContent("Met");
    expect(screen.getByTestId("point-0")).toHaveTextContent("energy derived from the sun");
    expect(screen.getByTestId("point-0")).toHaveTextContent("+1");
    expect(screen.getByTestId("point-1")).toHaveTextContent("Partly met");
    expect(screen.getByTestId("point-1")).toHaveTextContent("+0.5");
  });

  // Why: showing the student's own words makes the decision checkable (and a re-evaluation request precise)
  it("quotes what the student wrote", () => {
    render(<MarkBreakdown row={row()} rubric={rubric} />);
    expect(screen.getByText(/energy we get from sun light/)).toBeInTheDocument();
  });

  // Why: points not found in the answer are shown as missed with 0 marks
  it("shows missed points", () => {
    const c = [{ ...concepts[0] }, { concept: "an example of solar energy", present: false, partial: false, evidence: "" }];
    render(<MarkBreakdown row={row({ concepts: c, marks_earned: 1, rubric_marks: 1 })} rubric={rubric} />);
    expect(screen.getByTestId("point-1")).toHaveTextContent("Missed");
    expect(screen.getByTestId("point-1")).toHaveTextContent("0");
    expect(screen.getByTestId("point-1")).toHaveTextContent("Not found in your answer");
  });

  // Why: calibration changes the whole answer's mark, not one point, so it is shown as its own line
  it("shows the teacher's marking adjustment", () => {
    render(<MarkBreakdown row={row({ marks_earned: 2, calibrated_marks: 2 })} rubric={rubric} />);
    expect(screen.getByTestId("adjustment")).toHaveTextContent("Teacher's marking adjustment");
    expect(screen.getByTestId("adjustment")).toHaveTextContent("+0.5");
  });

  // Why: a TA's re-evaluation is final; the student sees it replaced the rubric mark
  it("shows a TA change", () => {
    render(<MarkBreakdown row={row({ marks_earned: 2, final_by: "ta" })} rubric={rubric} />);
    expect(screen.getByTestId("override")).toHaveTextContent("Re-evaluated by a TA: 1.5 → 2");
  });

  // Why: when a required point is missing the answer gets 0 even if other points were met; say why
  it("explains a missing required point", () => {
    render(<MarkBreakdown row={row({ mandatory_met: false, marks_earned: 0, rubric_marks: 0 })} rubric={rubric} />);
    expect(screen.getByText(/required point is missing/)).toBeInTheDocument();
  });

  // Why: answers graded before per-point decisions existed have nothing to break down
  it("renders nothing without per-point decisions", () => {
    const { container } = render(<MarkBreakdown row={row({ concepts: [] })} rubric={rubric} />);
    expect(container).toBeEmptyDOMElement();
  });
});
