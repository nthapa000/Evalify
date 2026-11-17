// pages.test.jsx — existing teacher pages: dashboard, paper view, create-paper wizard.
import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import { renderAt, loginAs } from "../../../test/utils";

vi.mock("../../../services/api", async () => ({ default: (await import("../../../test/mockApi")).makeApi() }));
import api from "../../../services/api";
import TeacherDashboard from "../Dashboard";
import PaperView from "../PaperView";
import CreatePaper from "../CreatePaper";

const PAPER = { id: "p1", name: "Unit Test 1", subject: "Computer Science", type: "mcq_numerical_subjective",
                totalMarks: 8, mcqCount: 2, mcqMarks: 1, mcqAnswers: { Q1: "B", Q2: "A" }, numericalCount: 1,
                numericalMarks: 2, numericalAnswers: { N1: { answer: "2500", unit: "m", tolerance: 0.001 } },
                subjectiveCount: 1, subjectiveMarks: 2, subjectiveQuestions: ["What is solar energy?"],
                subjectiveRubrics: [{ key_concepts: ["energy derived from the sun"], marks_per_concept: 2 }],
                resultCount: 3, createdAt: "2026-11-15T10:00:00Z", resultsReleased: false };

beforeEach(() => {
  loginAs("teacher", { name: "Prof. Ramesh Kumar", subject: "Computer Science" });
  api.routes["GET /papers"] = [PAPER];
  api.routes["GET /papers/p1"] = PAPER;
});

describe("Teacher pages", () => {
  // Why: the teacher's dashboard lists their papers with links to results and the paper
  it("dashboard lists papers with result links", async () => {
    renderAt(<TeacherDashboard />);
    expect(await screen.findByText("Unit Test 1")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /View Results/ })).toHaveAttribute("href", "/teacher/papers/p1/results");
    expect(screen.getByText("Not released")).toBeInTheDocument();     // results hidden from students until released
  });

  // Why: user report (17 Nov) — the teacher must see their own subject on the home page, even with no papers yet
  it("dashboard shows the teacher's subject", async () => {
    api.routes["GET /papers"] = [];
    renderAt(<TeacherDashboard />);
    expect(await screen.findByTestId("teacher-subject")).toHaveTextContent("Computer Science");
  });

  // Why: user request (17 Nov) — a teacher with two subjects sees both on the home page
  it("dashboard shows both subjects of a two-subject teacher", async () => {
    loginAs("teacher", { name: "Dr. Anita Desai", subject: "Physics", subjects: ["Physics", "Mathematics"] });
    api.routes["GET /papers"] = [];
    renderAt(<TeacherDashboard />);
    expect(await screen.findByTestId("teacher-subject")).toHaveTextContent("Physics, Mathematics");
  });

  // Why: the paper view shows the subjective questions and rubric points the wizard saved (plain strings +
  // subjectiveRubrics; it used to expect objects and showed empty questions)
  it("paper view shows key and questions", async () => {
    renderAt(<PaperView />, { path: "/teacher/papers/:paperId/view", route: "/teacher/papers/p1/view" });
    expect(await screen.findByRole("heading", { name: "Unit Test 1" })).toBeInTheDocument();
    expect(screen.getByText("What is solar energy?")).toBeInTheDocument();
    expect(screen.getByText(/energy derived from the sun/)).toBeInTheDocument();
  });

  // Why: user report (17 Nov) — the answer key PDF uploaded in the wizard was not listed under "Uploaded documents"
  it("paper view lists the answer key PDF uploaded for extraction", async () => {
    api.routes["GET /papers/p1"] = { ...PAPER, questionPaperUrl: "/api/papers/files/q.pdf",
                                     answerKeyPdfUrl: "/api/papers/files/k.pdf" };
    renderAt(<PaperView />, { path: "/teacher/papers/:paperId/view", route: "/teacher/papers/p1/view" });
    expect(await screen.findByText("Answer Key (Reference)")).toBeInTheDocument();
    expect(screen.getByText("Question Paper (Reference)")).toBeInTheDocument();
  });

  // Why: user request (17 Nov) — the blank OMR sheet (layout) of an OMR paper is listed under "Uploaded documents"
  it("paper view lists the OMR layout of an OMR paper", async () => {
    api.routes["GET /papers/p1"] = { ...PAPER, type: "mcq", omrTemplate: { blank_url: "/api/papers/files/b.png", confirmed: true } };
    renderAt(<PaperView />, { path: "/teacher/papers/:paperId/view", route: "/teacher/papers/p1/view" });
    expect(await screen.findByText("OMR Layout (Blank Sheet)")).toBeInTheDocument();
  });

  // Why: a type C paper also keeps its detailed answers and grading rubric PDFs, which the teacher wants to find again
  it("paper view lists the rubric source PDFs of a type C paper", async () => {
    api.routes["GET /papers/p1"] = { ...PAPER, detailedAnswerPdfUrl: "/api/papers/files/d.pdf",
                                     gradeRubricPdfUrl: "/api/papers/files/g.pdf" };
    renderAt(<PaperView />, { path: "/teacher/papers/:paperId/view", route: "/teacher/papers/p1/view" });
    expect(await screen.findByText("Detailed Answers")).toBeInTheDocument();
    expect(screen.getByText("Grading Rubric")).toBeInTheDocument();
  });

  // Why: user report (17 Nov) — keys with two correct options ("A,C") showed no highlighted option at all
  it("paper view highlights every correct option of a multi-answer key", async () => {
    api.routes["GET /papers/p1"] = { ...PAPER, mcqCount: 2, mcqAnswers: { Q1: "A,C", Q2: "B" } };
    renderAt(<PaperView />, { path: "/teacher/papers/:paperId/view", route: "/teacher/papers/p1/view" });
    await screen.findByText("MCQ answer key");
    const lit = (q) => [...screen.getByText(q).parentElement.querySelectorAll("span.bg-green-600")].map((e) => e.textContent);
    expect(lit("Q1")).toEqual(["A", "C"]);
    expect(lit("Q2")).toEqual(["B"]);
  });

  // Why: user request (17 Nov) — the teacher's worked solution is called "Detailed Solution", not "Answer Sheet"
  it("paper view calls the worked solution PDF a detailed solution", async () => {
    api.routes["GET /papers/p1"] = { ...PAPER, answerSheetRefUrl: "/api/papers/files/s.pdf" };
    renderAt(<PaperView />, { path: "/teacher/papers/:paperId/view", route: "/teacher/papers/p1/view" });
    expect(await screen.findByText("Detailed Solution (Reference)")).toBeInTheDocument();
    expect(screen.queryByText("Answer Sheet (Reference)")).toBeNull();
  });

  // Why: the create-paper wizard starts at step 1 (paper type) with Next disabled until a type is chosen
  it("create-paper wizard starts at step 1", () => {
    renderAt(<CreatePaper />);
    expect(screen.getByText("Create New Paper")).toBeInTheDocument();
    expect(screen.getByText("Step 1: Paper Type")).toBeInTheDocument();
  });

  // Why: user report (17 Nov) — an MCQ-only paper must ask whether students use an OMR sheet or write by hand,
  // and the OMR sheet upload is offered only for OMR (other paper types are always handwritten)
  it("wizard asks OMR or handwritten for MCQ-only papers", async () => {
    renderAt(<CreatePaper />);
    fireEvent.click(screen.getByText("MCQ Only"));
    fireEvent.click(screen.getByRole("button", { name: /next/i }));
    expect(await screen.findByLabelText(/OMR bubble sheet/)).toBeChecked();
    expect(screen.getByLabelText(/Handwritten/)).not.toBeChecked();
  });

  it("wizard does not ask it for papers with numerical or written answers", async () => {
    renderAt(<CreatePaper />);
    fireEvent.click(screen.getByText("MCQ + Numerical"));
    fireEvent.click(screen.getByRole("button", { name: /next/i }));
    expect(await screen.findByText("Step 2: Details")).toBeInTheDocument();
    expect(screen.queryByText("Answer sheet students will use")).toBeNull();
  });
});

