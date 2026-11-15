// pages.test.jsx — existing student pages: dashboard, subject page, answer-sheet upload.
import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";
import { renderAt, loginAs } from "../../../test/utils";

vi.mock("../../../services/api", async () => ({ default: (await import("../../../test/mockApi")).makeApi() }));
import api from "../../../services/api";
import StudentDashboard from "../Dashboard";
import SubjectPage from "../SubjectPage";
import Submission from "../Submission";

const PAPERS = [
  { id: "p1", name: "Unit Test 1", subject: "Computer Science", type: "mcq", totalMarks: 10, createdAt: "2026-11-15T10:00:00Z",
    submissionStatus: "not_submitted", submissionId: null },
  { id: "p2", name: "Unit Test 2", subject: "Computer Science", type: "mcq_numerical_subjective", totalMarks: 20,
    createdAt: "2026-11-15T10:00:00Z", submissionStatus: "evaluated", submissionId: "s2" },
];

beforeEach(() => {
  loginAs("student", { name: "Aarav Sharma" });
  api.routes["GET /papers/available"] = PAPERS;
  api.routes["GET /papers/p1"] = { ...PAPERS[0], mcqCount: 10 };
});

describe("Student pages", () => {
  // Why: the dashboard groups the student's papers by enrolled subject and counts pending ones
  it("dashboard shows subjects and pending count", async () => {
    renderAt(<StudentDashboard />);
    expect(await screen.findByText("Computer Science")).toBeInTheDocument();
    expect(screen.getByText(/1 exam pending submission/)).toBeInTheDocument();
  });

  // Why: the subject page offers "upload" for new papers and "view result" for evaluated ones
  it("subject page shows the right action per paper", async () => {
    renderAt(<SubjectPage />, { path: "/student/subjects/:subject", route: "/student/subjects/Computer%20Science" });
    expect(await screen.findByText("Unit Test 1")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Upload Answer Sheet" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /View Result/ })).toHaveAttribute("href", "/student/results/s2");
  });

  // Why: the upload page opens for the chosen paper
  it("upload page renders for a paper", async () => {
    renderAt(<Submission />, { path: "/student/submit/:paperId", route: "/student/submit/p1" });
    expect((await screen.findAllByText("Upload Answer Sheet")).length).toBeGreaterThan(0);
  });
});
