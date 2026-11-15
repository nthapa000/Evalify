// Dashboard.test.jsx — the TA's home: subjects and the two tabs (Flagged by AI, Re-evaluation requests).
import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, fireEvent, waitFor } from "@testing-library/react";
import { renderAt, loginAs } from "../../../test/utils";
// The fake API is built inside the (hoisted) mock factory; tests set its routes
vi.mock("../../../services/api", async () => ({ default: (await import("../../../test/mockApi")).makeApi() }));
import api from "../../../services/api";
import TaDashboard from "../Dashboard";

const FLAGGED = [{ submission_id: "s1", paper_name: "Unit Test 1", student_name: "Aarav Sharma", roll_no: "CS2025001",
                   totalScore: 4.5, maxScore: 8, questions: [{ question: "Q2", reason: "readers disagree (A: A, B: C)" }] }];
const REEVAL = [{ submission_id: "s2", paper_name: "Unit Test 1", student_name: "Priya Patel", roll_no: "CS2025002",
                  totalScore: 6, maxScore: 8, questions: [], remark: "S1: I gave solar panels as an example." }];

beforeEach(() => {
  loginAs("ta");
  api.routes["GET /ta/subjects"] = [{ subject: "Computer Science", flagged: 1, reevaluation: 1 }];
  api.routes["GET /ta/queue"] = (config) => (config.params.tab === "flagged" ? FLAGGED : REEVAL);
});

describe("TA dashboard", () => {
  // Why: the TA must see the subjects they are TA of and how much work waits in each tab
  it("shows subjects and tab counts", async () => {
    renderAt(<TaDashboard />);
    expect(await screen.findByText("Computer Science")).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Flagged by AI \(1\)/ })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Re-evaluation requests \(1\)/ })).toBeInTheDocument();
  });

  // Why: the Flagged tab lists each answer sheet with the AI's one-line reason per flagged question
  it("lists flagged sheets with reasons and a review link", async () => {
    renderAt(<TaDashboard />);
    expect(await screen.findByText("Aarav Sharma")).toBeInTheDocument();
    expect(screen.getByText(/Q2: readers disagree/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Review" })).toHaveAttribute("href", "/ta/review/s1?tab=flagged");
  });

  // Why: the Re-evaluation tab shows the student's remark so the TA knows what to re-check
  it("switches to re-evaluation requests", async () => {
    renderAt(<TaDashboard />);
    await screen.findByText("Aarav Sharma");
    fireEvent.click(screen.getByRole("tab", { name: /Re-evaluation requests/ }));
    expect(await screen.findByText(/I gave solar panels/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Review" })).toHaveAttribute("href", "/ta/review/s2?tab=reevaluation");
    await waitFor(() => expect(api.get).toHaveBeenCalledWith("/ta/queue",
      { params: { subject: "Computer Science", tab: "reevaluation" } }));
  });

  // Why: an empty tab must say so instead of showing a blank page
  it("shows an empty state", async () => {
    api.routes["GET /ta/queue"] = [];
    renderAt(<TaDashboard />);
    await screen.findByText("Computer Science");
    expect(await screen.findByText(/Nothing to review/, {}, { timeout: 5000 })).toBeInTheDocument();
  });
});
