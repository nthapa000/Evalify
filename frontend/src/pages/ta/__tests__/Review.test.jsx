// Review.test.jsx — one answer sheet in the TA view: sheet, paper materials, AI marks + reason, final marks.
import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, fireEvent, waitFor } from "@testing-library/react";
import { renderAt, loginAs } from "../../../test/utils";
// The fake API is built inside the (hoisted) mock factory; tests set its routes
vi.mock("../../../services/api", async () => ({ default: (await import("../../../test/mockApi")).makeApi() }));
import api from "../../../services/api";
import TaReview from "../Review";

const ITEM = {
  submission: { id: "s1", student_name: "Aarav Sharma", roll_no: "CS2025001", page_count: 2,
                result: { totalScore: 4.5, maxScore: 8 } },
  paper: { name: "Unit Test 1", type: "mcq_numerical_subjective", questionPaperUrl: "/api/papers/files/qp.pdf",
           answerKeyRefUrl: "/api/papers/files/key.pdf", mcqAnswers: { Q1: "B", Q2: "A" },
           numericalAnswers: { N1: { answer: "2500", unit: "m", tolerance: 0.001 } },
           subjectiveQuestions: ["What is solar energy?"],
           subjectiveRubrics: [{ key_concepts: ["energy derived from the sun", "an example"], marks_per_concept: 1,
                                 model_answer: "Energy from the sun, e.g. solar panels." }] },
  questions: [
    { question: "Q1", kind: "mcq", student_answer: "B", marks_available: 1, marks_earned: 1, needs_review: false, review_reason: "" },
    { question: "Q2", kind: "mcq", student_answer: "C", marks_available: 1, marks_earned: 0, needs_review: true,
      review_reason: "readers disagree (A: A, B: C, C: D)" },
    { question: "S1", kind: "subjective", question_text: "What is solar energy?", student_answer: "energy from the sun",
      marks_available: 2, marks_earned: 1, needs_review: false, review_reason: "",
      concepts: [{ concept: "energy derived from the sun", present: true, partial: false, evidence: "energy from the sun" }] },
  ],
  reevaluation: { remark: "S1: I gave solar panels as an example.", status: "pending" },
  marks_history: [],
};

beforeEach(() => {
  loginAs("ta");
  global.URL.createObjectURL = vi.fn(() => "blob:page");
  api.routes["GET /ta/items/s1"] = ITEM;
  api.routes["GET /submissions/s1/pages"] = { count: 2 };
  api.routes["GET /submissions/s1/pages/0"] = new Blob(["x"]);
  api.routes["GET /submissions/s1/pages/1"] = new Blob(["y"]);
  api.routes["POST /ta/items/s1/marks"] = { result: { totalScore: 5.5 } };
});

const page = (tab = "reevaluation") =>
  renderAt(<TaReview />, { path: "/ta/review/:submissionId", route: `/ta/review/s1?tab=${tab}`,
                           extra: { "/ta/dashboard": <p>TA home</p> } });

describe("TA review", () => {
  // Why: the TA must see the whole answer sheet (every page), not just one question
  it("shows every page of the answer sheet", async () => {
    page();
    expect(await screen.findAllByRole("img", { name: /Answer sheet page/ })).toHaveLength(2);
  });

  // Why: the TA checks against the teacher's question paper, answer key and rubric
  it("shows the paper materials", async () => {
    page();
    expect(await screen.findByRole("link", { name: /Question paper/ })).toHaveAttribute("href", "/api/papers/files/qp.pdf");
    expect(screen.getByRole("link", { name: /Answer key/ })).toHaveAttribute("href", "/api/papers/files/key.pdf");
    expect(screen.getAllByText("energy derived from the sun").length).toBeGreaterThan(0);
    expect(screen.getByText(/2500 m/)).toBeInTheDocument();
  });

  // Why: the AI's mark and its one-line reason tell the TA why the question was flagged
  it("shows AI marks and the flag reason", async () => {
    page("flagged");
    expect(await screen.findByText("readers disagree (A: A, B: C, C: D)")).toBeInTheDocument();
    expect(screen.getByLabelText("Marks for Q2")).toHaveValue(0);
  });

  // Why: in the re-evaluation tab the TA reads the student's remark first
  it("shows the student's remark", async () => {
    page();
    expect(await screen.findByText("S1: I gave solar panels as an example.")).toBeInTheDocument();
  });

  // Why: only the marks the TA changed are sent, with the optional remark, and the TA returns to the dashboard
  it("submits re-evaluated marks", async () => {
    page();
    fireEvent.change(await screen.findByLabelText("Marks for S1"), { target: { value: "2" } });
    fireEvent.change(screen.getByLabelText(/Remark to the student/), { target: { value: "Example accepted." } });
    fireEvent.click(screen.getByRole("button", { name: /Submit re-evaluated marks/ }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith("/ta/items/s1/marks",
      { tab: "reevaluation", marks: { S1: 2 }, remark: "Example accepted." }));
    expect(await screen.findByText("TA home")).toBeInTheDocument();
  });

  // Why: marks above a question's maximum are blocked before sending
  it("blocks marks above the maximum", async () => {
    page();
    fireEvent.change(await screen.findByLabelText("Marks for S1"), { target: { value: "3" } });
    expect(screen.getByRole("button", { name: /Submit re-evaluated marks/ })).toBeDisabled();
    expect(screen.getByText(/between 0 and 2/)).toBeInTheDocument();
  });
});
