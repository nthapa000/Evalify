// PaperResults.test.jsx — teacher's results table with TA / re-evaluation status and optional calibration.
import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, fireEvent, waitFor, within } from "@testing-library/react";
import { renderAt, loginAs } from "../../../test/utils";

vi.mock("../../../services/api", async () => ({ default: (await import("../../../test/mockApi")).makeApi() }));
import api from "../../../services/api";
import PaperResults from "../PaperResults";

const sub = (id, name, extra = {}) => ({
  id, student_name: name, roll_no: id.toUpperCase(), paper_name: "Unit Test 1", submittedAt: "2026-11-15T10:00:00Z",
  result: { totalScore: 4.5, maxScore: 8, percentage: 56.2 },
  subjectiveDetail: [{ question: "S1", question_text: "What is solar energy?", marks_available: 2, marks_earned: 1, rubric_marks: 1 },
                     { question: "S2", question_text: "Define power.", marks_available: 2, marks_earned: 0.5, rubric_marks: 0.5 }],
  review: [], ...extra });

beforeEach(() => {
  loginAs("teacher");
  api.routes["GET /papers/p1"] = { id: "p1", name: "Unit Test 1", type: "mcq_numerical_subjective" };
  api.routes["GET /results/paper/p1"] = { calibration: null, stats: { count: 2, average: 4.5, highest: 4.5, lowest: 4.5 },
    submissions: [sub("s1", "Aarav Sharma", { review: [{ question: "Q2", reason: "readers disagree" }] }),
                  sub("s2", "Priya Patel", { ta_review: { status: "done" }, reevaluation: { status: "pending" },
                                             teacher_marks: { S1: 2, S2: 1.5 } })] };
  api.routes["PUT /papers/p1/calibration/marks/s1"] = { teacher_marks: { S1: 2, S2: 1.5 } };
  api.routes["POST /papers/p1/calibration/apply"] = { answers: 2, sheets: 1, updated_submissions: 1, global: 1, per_question: {} };
});

const page = () => renderAt(<PaperResults />, { path: "/teacher/papers/:paperId/results", route: "/teacher/papers/p1/results" });

describe("Teacher paper results", () => {
  // Why: the teacher sees which sheets the AI flagged, which a TA has reviewed, and pending re-evaluations
  it("shows AI flag, TA and re-evaluation status per student", async () => {
    page();
    const r1 = within(await screen.findByTestId("row-s1"));
    expect(r1.getByText("1 flagged")).toBeInTheDocument();
    expect(r1.getByText("TA pending")).toBeInTheDocument();
    const r2 = within(screen.getByTestId("row-s2"));
    expect(r2.getByText("TA reviewed")).toBeInTheDocument();
    expect(r2.getByText("Re-evaluation pending")).toBeInTheDocument();
  });

  // Why: calibration is optional — the teacher hand-marks a sheet's subjective answers in a dialog
  it("hand-marks a sheet for calibration", async () => {
    page();
    fireEvent.click(within(await screen.findByTestId("row-s1")).getByRole("button", { name: /Hand-mark/ }));
    fireEvent.change(screen.getByLabelText("Teacher marks for S1"), { target: { value: "2" } });
    fireEvent.change(screen.getByLabelText("Teacher marks for S2"), { target: { value: "1.5" } });
    fireEvent.click(screen.getByRole("button", { name: /Save my marks/ }));
    await waitFor(() => expect(api.put).toHaveBeenCalledWith("/papers/p1/calibration/marks/s1",
      { marks: { S1: 2, S2: 1.5 } }));
  });

  // Why: applying calibration shifts the other students' subjective marks to this teacher's standard
  it("applies calibration", async () => {
    page();
    fireEvent.click(await screen.findByRole("button", { name: /Apply calibration/ }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith("/papers/p1/calibration/apply"));
    expect(await screen.findByText(/learned from 1 hand-marked sheet/)).toBeInTheDocument();
  });

  // Why: calibration needs at least one hand-marked sheet, so the button stays disabled until then
  it("disables calibration until a sheet is hand-marked", async () => {
    const d = api.routes["GET /results/paper/p1"];
    api.routes["GET /results/paper/p1"] = { ...d, submissions: d.submissions.map(({ teacher_marks, ...s }) => s) };
    page();
    expect(await screen.findByRole("button", { name: /Apply calibration/ })).toBeDisabled();
  });

  // Why: calibration only makes sense for papers with subjective questions
  it("hides calibration for papers without subjective questions", async () => {
    api.routes["GET /papers/p1"] = { id: "p1", name: "MCQ test", type: "mcq" };
    page();
    await screen.findByTestId("row-s1");
    expect(screen.queryByRole("button", { name: /Apply calibration/ })).toBeNull();
  });
});
