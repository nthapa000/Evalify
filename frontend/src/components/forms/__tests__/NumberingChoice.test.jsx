// NumberingChoice.test.jsx — how written answers are numbered on the students' sheets.
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import NumberingChoice from "../NumberingChoice";

describe("NumberingChoice", () => {
  // Why: the default (S1, S2, ...) must be shown as selected, with the first written label as an example
  it("shows separate numbering by default", () => {
    render(<NumberingChoice value={undefined} mcqCount={20} numericalCount={0} onChange={() => {}} />);
    expect(screen.getByLabelText(/S1, S2/)).toBeChecked();
    expect(screen.getByLabelText(/Q21, Q22/)).not.toBeChecked();
  });

  // Why: sheets that number written answers after the MCQs (Q21–Q35) are only read correctly with "continuous"
  it("selecting continuous numbering reports it", () => {
    const onChange = vi.fn();
    render(<NumberingChoice value="separate" mcqCount={20} numericalCount={0} onChange={onChange} />);
    fireEvent.click(screen.getByLabelText(/Q21, Q22/));
    expect(onChange).toHaveBeenCalledWith("continuous");
  });

  // Why: the example label must follow the MCQ + numerical count, so the teacher recognises their sheet
  it("example label follows the question counts", () => {
    render(<NumberingChoice value="continuous" mcqCount={2} numericalCount={3} onChange={() => {}} />);
    expect(screen.getByLabelText(/Q6, Q7/)).toBeChecked();
  });
});
