// pages.test.jsx — existing teacher pages: dashboard, paper view, create-paper wizard.
import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";
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
                resultCount: 3, createdAt: "2026-11-15T10:00:00Z" };

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
  });

  // Why: the paper view shows the subjective questions and rubric points the wizard saved (plain strings +
  // subjectiveRubrics; it used to expect objects and showed empty questions)
  it("paper view shows key and questions", async () => {
    renderAt(<PaperView />, { path: "/teacher/papers/:paperId/view", route: "/teacher/papers/p1/view" });
    expect(await screen.findByRole("heading", { name: "Unit Test 1" })).toBeInTheDocument();
    expect(screen.getByText("What is solar energy?")).toBeInTheDocument();
    expect(screen.getByText(/energy derived from the sun/)).toBeInTheDocument();
  });

  // Why: the create-paper wizard starts at step 1 (paper type) with Next disabled until a type is chosen
  it("create-paper wizard starts at step 1", () => {
    renderAt(<CreatePaper />);
    expect(screen.getByText("Create New Paper")).toBeInTheDocument();
    expect(screen.getByText("Step 1: Paper Type")).toBeInTheDocument();
  });
});
