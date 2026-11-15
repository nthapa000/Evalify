// formatters.test.js — display helpers used on every results page.
import { describe, it, expect } from "vitest";
import { formatPercent, gradeFromPercent, paperTypeLabel, statusLabel, formatDate } from "../formatters";

describe("formatters", () => {
  // Why: percentages are shown with one decimal everywhere (results, teacher table)
  it("formats percentages with one decimal", () => {
    expect(formatPercent(56.25)).toBe("56.3%");
    expect(formatPercent("80")).toBe("80.0%");
  });

  // Why: the grade letter shown to students must follow the fixed bands
  it("maps percentages to grade letters", () => {
    expect([95, 85, 75, 65, 55, 10].map(gradeFromPercent)).toEqual(["A+", "A", "B", "C", "D", "F"]);
  });

  // Why: paper types and submission statuses are stored as codes but shown as words
  it("labels paper types and statuses", () => {
    expect(paperTypeLabel("mcq_numerical_subjective")).toBe("MCQ + Numerical + Subjective");
    expect(paperTypeLabel("other")).toBe("other");
    expect(statusLabel("not_submitted")).toBe("Not Submitted");
  });

  // Why: dates are shown in the Indian day-month-year format
  it("formats dates", () => {
    expect(formatDate("2026-11-15T10:00:00Z")).toMatch(/15 Nov 2026/);
  });
});
