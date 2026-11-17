// EvaluationPanel.test.jsx — the teacher's "Start evaluation" for the whole class and its progress.
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

vi.mock("../../../services/api", async () => ({ default: (await import("../../../test/mockApi")).makeApi() }));
import api from "../../../services/api";
import EvaluationPanel from "../EvaluationPanel";

const counts = (c = {}) => ({ queued: 0, reading: 0, read: 0, grading: 0, evaluated: 0, error: 0, ...c });
const batch = (extra = {}) => ({ id: "b1", status: "running", stage: "reading", total: 4, counts: counts(), ...extra });

beforeEach(() => {
  for (const k of Object.keys(api.routes)) delete api.routes[k];
  vi.clearAllMocks();
});

describe("EvaluationPanel", () => {
  // Why: the teacher sees how many submitted sheets wait and starts them all with one button
  it("starts evaluation of all waiting sheets", async () => {
    api.routes["GET /papers/p1/evaluation"] = { waiting: 3, batch: null };
    api.routes["POST /papers/p1/evaluate"] = batch({ total: 3, counts: counts({ queued: 3 }) });
    render(<EvaluationPanel paperId="p1" />);
    expect(await screen.findByText(/3 answer sheets waiting/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Start evaluation" }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith("/papers/p1/evaluate"));
    expect(await screen.findByText("Stage 1 of 2: Reading answer sheets")).toBeInTheDocument();
  });

  // Why: with nothing submitted there is nothing to start — the button is disabled and says why
  it("disables the button when no sheet is waiting", async () => {
    api.routes["GET /papers/p1/evaluation"] = { waiting: 0, batch: null };
    render(<EvaluationPanel paperId="p1" />);
    expect(await screen.findByText(/No answer sheets are waiting/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Start evaluation" })).toBeDisabled();
  });

  // Why: during a batch the teacher sees the stage (reading, then grading) and how far each has got
  it("shows the two stages with counts", async () => {
    api.routes["GET /papers/p1/evaluation"] = { waiting: 0, batch: batch({ stage: "grading",
      counts: counts({ grading: 1, evaluated: 2, error: 1 }) }) };
    render(<EvaluationPanel paperId="p1" />);
    expect(await screen.findByText("Stage 2 of 2: Grading answers")).toBeInTheDocument();
    expect(screen.getByTestId("read-progress")).toHaveTextContent("4 / 4");
    expect(screen.getByTestId("grade-progress")).toHaveTextContent("2 / 4");
    expect(screen.getByText(/1 sheet could not be evaluated/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Start evaluation" })).toBeDisabled();
  });

  // Why: when the batch finishes the results table must reload with the new marks
  it("tells the page when the batch has finished", async () => {
    const onFinished = vi.fn();
    api.routes["GET /papers/p1/evaluation"] = { waiting: 0, batch: batch({ status: "done", stage: "done",
      counts: counts({ evaluated: 4 }), finished_at: "2026-11-17T02:00:00Z" }) };
    render(<EvaluationPanel paperId="p1" onFinished={onFinished} />);
    expect(await screen.findByText(/Evaluation finished/)).toBeInTheDocument();
    expect(onFinished).toHaveBeenCalled();
  });

  // Why: a refused start (e.g. already running) is reported to the teacher, not swallowed
  it("shows the server's reason when the start is refused", async () => {
    api.routes["GET /papers/p1/evaluation"] = { waiting: 2, batch: null };
    api.post.mockRejectedValueOnce({ response: { status: 409, data: { detail: "An evaluation of this paper is already running." } } });
    render(<EvaluationPanel paperId="p1" />);
    fireEvent.click(await screen.findByRole("button", { name: "Start evaluation" }));
    expect(await screen.findByText(/already running/)).toBeInTheDocument();
  });

  // Why: user feedback (17 Nov) — a running evaluation must look alive: say it is running, for how long, and that
  // the teacher can leave the page, instead of a static "0 / 1"
  it("shows a waiting message with elapsed time while running", async () => {
    const started = new Date(Date.now() - 75_000).toISOString();
    api.routes["GET /papers/p1/evaluation"] = { waiting: 0, batch: batch({ total: 1, created_at: started }) };
    render(<EvaluationPanel paperId="p1" />);
    expect(await screen.findByText(/Evaluation is running/)).toBeInTheDocument();
    expect(screen.getByText(/1 min 1\d s|1 min 2\d s/)).toBeInTheDocument();
    expect(screen.getByText(/You can leave this page/)).toBeInTheDocument();
    expect(screen.queryByText(/longer than usual/)).toBeNull();
  });

  // Why: after 10 minutes without a finished sheet the teacher is told something may be wrong (servers busy or offline)
  it("warns when a batch runs unusually long", async () => {
    const started = new Date(Date.now() - 11 * 60_000).toISOString();
    api.routes["GET /papers/p1/evaluation"] = { waiting: 0, batch: batch({ total: 2, created_at: started }) };
    render(<EvaluationPanel paperId="p1" />);
    expect(await screen.findByText(/taking longer than usual/)).toBeInTheDocument();
  });

  // Why: a batch that stopped unexpectedly must say so with the reason, not look like "nothing is waiting"
  it("shows why a batch stopped", async () => {
    api.routes["GET /papers/p1/evaluation"] = { waiting: 2, batch: batch({ status: "failed", stage: "reading",
      error: "database connection lost", finished_at: "2026-11-17T01:00:00Z" }) };
    render(<EvaluationPanel paperId="p1" />);
    expect(await screen.findByText(/The last evaluation stopped/)).toBeInTheDocument();
    expect(screen.getByText(/database connection lost/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Start evaluation" })).toBeEnabled();      // its sheets can be sent again
  });
});

