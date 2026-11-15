// Result.test.jsx — the student's result: question-wise marks, marks history, the one re-evaluation request.
import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, fireEvent, waitFor } from "@testing-library/react";
import { renderAt, loginAs } from "../../../test/utils";

vi.mock("../../../services/api", async () => ({ default: (await import("../../../test/mockApi")).makeApi() }));
import api from "../../../services/api";
import Result from "../Result";

const base = () => ({
  id: "s1", student_name: "Aarav Sharma", roll_no: "CS2025001", paper_name: "Unit Test 1", paper_id: "p1",
  paper: { type: "mcq_numerical_subjective", mcqCount: 2, mcqMarks: 1, numericalCount: 1, numericalMarks: 2,
           subjectiveCount: 2, subjectiveMarks: 2 },
  result: { totalScore: 5.5, maxScore: 8, percentage: 68.8, mcqScore: 2, numericalScore: 2, subjectiveScore: 1.5 },
  stats: { average: 5, highest: 6 },
  mcqDetail: [{ question: "Q1", student_answer: "B", marks_available: 1, marks_earned: 1, status: "correct" },
              { question: "Q2", student_answer: "A", marks_available: 1, marks_earned: 1, status: "wrong" }],
  numericalDetail: [{ question: "N1", student_answer: "2500 m", marks_available: 2, marks_earned: 2, status: "correct" }],
  subjectiveDetail: [{ question: "S1", question_text: "What is solar energy?", student_answer: "energy from the sun",
                       marks_available: 2, marks_earned: 1, status: "graded_by_llm" },
                     { question: "S2", question_text: "Define power.", student_answer: null, marks_available: 2,
                       marks_earned: 0.5, status: "graded_by_llm" }],
  marks_history: [], reevaluation: null,
});

beforeEach(() => {
  loginAs("student", { roll_no: "CS2025001" });
  api.routes["GET /results/s1"] = base();
  api.routes["POST /submissions/s1/reevaluation"] = { reevaluation: { status: "pending", remark: "x" } };
});

const page = () => renderAt(<Result />, { path: "/student/results/:submissionId", route: "/student/results/s1" });

describe("Student result", () => {
  // Why: students must see the marks of every question, not only section totals
  it("shows question-wise marks", async () => {
    page();
    expect(await screen.findByText("What is solar energy?")).toBeInTheDocument();
    const row = screen.getByTestId("q-row-S1");
    expect(row).toHaveTextContent("1 / 2");
  });

  // Why: the student may ask once for re-evaluation, writing which parts to re-check and why
  it("sends the one re-evaluation request", async () => {
    page();
    const box = await screen.findByLabelText(/Your remark/);
    const send = screen.getByRole("button", { name: /Request re-evaluation/ });
    expect(send).toBeDisabled();
    fireEvent.change(box, { target: { value: "S1: I gave solar panels as an example." } });
    fireEvent.click(send);
    await waitFor(() => expect(api.post).toHaveBeenCalledWith("/submissions/s1/reevaluation",
      { remark: "S1: I gave solar panels as an example." }));
    expect(await screen.findByText(/Re-evaluation requested/)).toBeInTheDocument();
  });

  // Why: after asking, the form is gone (only one request) and the status is shown
  it("shows a pending request instead of the form", async () => {
    api.routes["GET /results/s1"] = { ...base(), reevaluation: { remark: "S1 please", status: "pending" } };
    page();
    expect(await screen.findByText(/waiting for a TA/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Request re-evaluation/ })).toBeNull();
  });

  // Why: after re-evaluation the student sees the new marks and the history of earlier marks (TA remark optional)
  it("shows marks history and the TA's response", async () => {
    api.routes["GET /results/s1"] = { ...base(),
      marks_history: [{ question: "Q2", old: 0, new: 1, by_role: "ta", remark: "Yes, A.", at: "2026-11-15T10:00:00Z" }],
      reevaluation: { remark: "Q2 was A", status: "resolved", response: "Yes, A." } };
    page();
    expect(await screen.findByText(/Marks history/)).toBeInTheDocument();
    expect(screen.getByTestId("history-0")).toHaveTextContent("Q2");
    expect(screen.getByTestId("history-0")).toHaveTextContent("0 → 1");
    expect(screen.getByTestId("history-0")).toHaveTextContent("TA");
    expect(screen.getByText(/Re-evaluated/)).toBeInTheDocument();
    expect(screen.getAllByText(/Yes, A\./).length).toBeGreaterThan(0);
  });
});
