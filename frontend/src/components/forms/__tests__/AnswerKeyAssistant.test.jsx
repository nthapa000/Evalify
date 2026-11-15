// AnswerKeyAssistant.test.jsx — optional drafting of reference answers + rubric points from the teacher's material.
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

vi.mock("../../../services/api", async () => ({ default: (await import("../../../test/mockApi")).makeApi() }));
import api from "../../../services/api";
import AnswerKeyAssistant from "../AnswerKeyAssistant";

const DRAFT = { question: "What is solar energy?", covered: true, model_answer: "Energy from the sun, e.g. solar panels.",
  key_concepts: ["energy obtained from the sun", "a valid example"], marks_per_concept: 1,
  citations: [{ n: 1, source: "notes.pdf", page: 3, text: "Solar energy is energy that we get from the sun." }], note: "" };

function setup(extra = {}) {
  const props = { count: 2, questions: ["What is solar energy?", ""], marks: [2, 2], rubrics: [],
                  uploadFn: vi.fn(async (f) => `/api/papers/files/${f.name}`), onUse: vi.fn(), onRubricChange: vi.fn(), ...extra };
  render(<AnswerKeyAssistant {...props} />);
  return props;
}

const upload = (name = "notes.pdf") =>
  fireEvent.change(screen.getByLabelText(/Reference files/), { target: { files: [new File(["x"], name)] } });

beforeEach(() => {
  api.routes["POST /papers/answer-key/draft"] = { drafts: [DRAFT, { question: "Define power.", covered: false,
    model_answer: "", key_concepts: [], marks_per_concept: 2, citations: [], note: "Not in the material." }], skipped_pages: [] };
});

describe("AnswerKeyAssistant", () => {
  // Why: drafting needs the teacher's reference files and the question texts; the button waits for both
  it("needs reference files and a question before drafting", async () => {
    setup();
    const btn = screen.getByRole("button", { name: /Draft answer key/ });
    expect(btn).toBeDisabled();
    upload();
    expect(await screen.findByText("notes.pdf")).toBeInTheDocument();
    expect(btn).not.toBeDisabled();
  });

  // Why: the request carries the uploaded files, every question and its marks
  it("sends files, questions and marks", async () => {
    setup();
    upload();
    await screen.findByText("notes.pdf");
    fireEvent.change(screen.getByLabelText("Question S2"), { target: { value: "Define power." } });
    fireEvent.click(screen.getByRole("button", { name: /Draft answer key/ }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith("/papers/answer-key/draft", {
      reference_urls: ["/api/papers/files/notes.pdf"], questions: ["What is solar energy?", "Define power."], marks: [2, 2] }));
  });

  // Why: every drafted point must show where it came from, so the teacher can check it
  it("shows the draft with citations", async () => {
    setup();
    upload();
    await screen.findByText("notes.pdf");
    fireEvent.click(screen.getByRole("button", { name: /Draft answer key/ }));
    expect(await screen.findByText("energy obtained from the sun")).toBeInTheDocument();
    expect(screen.getByText(/notes.pdf, page 3/)).toBeInTheDocument();
    expect(screen.getByText(/Not in the material/)).toBeInTheDocument();
  });

  // Why: "Use this draft" copies it into the paper's rubric for that question (the teacher then edits it)
  it("uses a draft as the rubric", async () => {
    const props = setup();
    upload();
    await screen.findByText("notes.pdf");
    fireEvent.click(screen.getByRole("button", { name: /Draft answer key/ }));
    fireEvent.click(await screen.findByRole("button", { name: "Use this draft for S1" }));
    expect(props.onUse).toHaveBeenCalledWith(0, { question: "What is solar energy?", rubric: {
      key_concepts: ["energy obtained from the sun", "a valid example"], mandatory_concepts: [], marks_per_concept: 1,
      model_answer: "Energy from the sun, e.g. solar panels.", rubric_source: "drafted from reference files, edited by teacher" } });
  });

  // Why: an uncovered question cannot be used as a draft (nothing to copy)
  it("does not offer an uncovered draft", async () => {
    setup();
    upload();
    await screen.findByText("notes.pdf");
    fireEvent.click(screen.getByRole("button", { name: /Draft answer key/ }));
    await screen.findByText(/Not in the material/);
    expect(screen.queryByRole("button", { name: "Use this draft for S2" })).toBeNull();
  });

  // Why: once a rubric exists for a question the teacher edits it right here
  it("shows the editable rubric of a question that has one", () => {
    setup({ rubrics: [{ key_concepts: ["energy obtained from the sun"], mandatory_concepts: [], marks_per_concept: 2, model_answer: "" }] });
    expect(screen.getByText("Subjective Q1 — Rubric")).toBeInTheDocument();
  });
});
