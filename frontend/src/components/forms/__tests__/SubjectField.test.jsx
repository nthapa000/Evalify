// SubjectField.test.jsx — the subject line of the paper wizard (fixed for one subject, a choice for two).
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import SubjectField from "../SubjectField";

describe("SubjectField", () => {
  // Why: a teacher with one subject keeps the old behaviour, the subject is shown and cannot be changed
  it("shows a single subject as fixed", () => {
    render(<SubjectField value="Physics" subjects={["Physics"]} onChange={() => {}} />);
    expect(screen.getByText("Physics")).toBeInTheDocument();
    expect(screen.queryByRole("combobox")).toBeNull();
  });

  // Why: a teacher with two subjects must be able to pick which one the new paper is for
  it("lets a two-subject teacher pick the subject", () => {
    const onChange = vi.fn();
    render(<SubjectField value="Physics" subjects={["Physics", "Mathematics"]} onChange={onChange} />);
    const select = screen.getByRole("combobox", { name: /subject/i });
    expect(select).toHaveValue("Physics");
    fireEvent.change(select, { target: { value: "Mathematics" } });
    expect(onChange).toHaveBeenCalledWith("Mathematics");
  });
});
