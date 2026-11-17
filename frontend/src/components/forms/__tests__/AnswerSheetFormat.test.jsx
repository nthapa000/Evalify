// AnswerSheetFormat.test.jsx — the wizard's question "will students use an OMR sheet or write by hand?" for MCQ papers.
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import AnswerSheetFormat from "../AnswerSheetFormat";

describe("AnswerSheetFormat", () => {
  // Why: the teacher must be asked and the current choice must show as selected
  it("asks for OMR or handwritten and shows the current choice", () => {
    render(<AnswerSheetFormat value="omr" onChange={() => {}} />);
    expect(screen.getByLabelText(/OMR bubble sheet/)).toBeChecked();
    expect(screen.getByLabelText(/Handwritten/)).not.toBeChecked();
  });

  // Why: picking the other format must be reported so the wizard can show or hide the OMR template upload
  it("reports a change", () => {
    const onChange = vi.fn();
    render(<AnswerSheetFormat value="omr" onChange={onChange} />);
    fireEvent.click(screen.getByLabelText(/Handwritten/));
    expect(onChange).toHaveBeenCalledWith("handwritten");
  });
});
