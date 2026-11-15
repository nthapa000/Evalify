// marks.test.jsx — the ruled number row (StatLedger) and the red-pen score box (ScoreMark).
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import StatLedger from "../StatLedger";
import ScoreMark from "../ScoreMark";

describe("marks components", () => {
  // Why: summary numbers (submissions, average, highest…) are shown as one ruled row with labels
  it("StatLedger shows each label with its value", () => {
    render(<StatLedger items={[{ label: "Submissions", value: 12 }, { label: "Average", value: "31.5" }]} />);
    expect(screen.getByText("Submissions")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("31.5")).toBeInTheDocument();
  });

  // Why: the student's total is shown like a teacher's score box: marks, maximum and grade
  it("ScoreMark shows score, maximum and grade", () => {
    render(<ScoreMark score={17} max={50} />);
    expect(screen.getByText("17")).toBeInTheDocument();
    expect(screen.getByText("of 50")).toBeInTheDocument();
    expect(screen.getByText("Grade F")).toBeInTheDocument();
  });
});
