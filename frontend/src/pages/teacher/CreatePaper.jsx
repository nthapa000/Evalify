// teacher/CreatePaper.jsx — 5-step wizard to create an exam paper.
// Step 1: type  | Step 2: details + per-Q marks + question paper PDF
// Step 3: answer key (manual or PDF extract) + answer key reference PDF
// Step 4: config | Step 5: review

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import PageWrapper from "../../components/layout/PageWrapper";
import StepWizard from "../../components/forms/StepWizard";
import RubricBuilder from "../../components/forms/RubricBuilder";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import Modal from "../../components/ui/Modal";
import { useCreatePaper } from "../../hooks/usePapers";
import { paperTypeLabel } from "../../utils/formatters";

const STEPS = ["Paper Type", "Details", "Answer Key", "Configuration", "Review"];

const PAPER_TYPES = [
  { value: "mcq", icon: "☑️", label: "MCQ Only", desc: "OMR bubbles or written MCQ answers" },
  { value: "mcq_numerical", icon: "🔢", label: "MCQ + Numerical", desc: "MCQ section + numerical answers with tolerance" },
  { value: "mcq_numerical_subjective", icon: "✍️", label: "MCQ + Numerical + Subjective", desc: "Full paper graded with LLM on subjective section" },
];

// ── Helpers ───────────────────────────────────────────────────────────────────

// Returns the sum of all per-question marks for the MCQ section
function mcqTotal(form) {
  return Array.from({ length: form.mcqCount }, (_, i) =>
    form.mcqQuestionMarks[`Q${i + 1}`] ?? form.mcqMarks
  ).reduce((a, b) => a + b, 0);
}

// Returns the sum of all per-question marks for the Numerical section
function numericalTotal(form) {
  return Array.from({ length: form.numericalCount }, (_, i) =>
    form.numericalQuestionMarks[`N${i + 1}`] ?? form.numericalMarks
  ).reduce((a, b) => a + b, 0);
}

// Returns the sum of all per-question marks for the Subjective section
function subjectiveTotal(form) {
  return Array.from({ length: form.subjectiveCount }, (_, i) =>
    form.subjectiveQuestionMarks[`S${i + 1}`] ?? form.subjectiveMarks
  ).reduce((a, b) => a + b, 0);
}

// Mock: simulate reading answers from an uploaded PDF (2 s delay)
async function mockExtractAnswersFromPdf(mcqCount) {
  await new Promise((r) => setTimeout(r, 2000));
  const opts = ["A", "B", "C", "D"];
  const answers = {};
  for (let i = 1; i <= mcqCount; i++) {
    answers[`Q${i}`] = opts[Math.floor(Math.random() * 4)];
  }
  return answers;
}

// ── PDF upload zone — inline to keep it small and avoid focus issues ──────────
// Accepts a PDF file and calls onFile(file, objectUrl).
// Must be at module scope to avoid remounting on parent re-render.
function PdfUploadZone({ label, hint, currentUrl, onFile }) {
  const handleChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    onFile(file, URL.createObjectURL(file));
    e.target.value = "";              // allow re-selecting the same file
  };

  return (
    <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl border border-dashed border-gray-300">
      <span className="text-2xl">📄</span>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-700">{label}</p>
        <p className="text-xs text-gray-400">{hint}</p>
      </div>
      {currentUrl && (
        // Opens the uploaded PDF in a new browser tab
        <button
          type="button"
          onClick={() => window.open(currentUrl, "_blank")}
          className="text-xs text-indigo-600 hover:underline whitespace-nowrap"
        >
          View PDF
        </button>
      )}
      <label className="cursor-pointer text-xs bg-white border border-gray-300 rounded-lg px-3 py-1.5 text-gray-600 hover:border-indigo-400 hover:text-indigo-600 whitespace-nowrap">
        {currentUrl ? "Replace" : "Upload"}
        <input type="file" accept="application/pdf" className="hidden" onChange={handleChange} />
      </label>
    </div>
  );
}

// ── Step 1: Paper Type ────────────────────────────────────────────────────────
function Step1({ value, onChange }) {
  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-500 mb-4">Select the type of exam paper to create.</p>
      {PAPER_TYPES.map((t) => (
        <button
          key={t.value}
          type="button"
          onClick={() => onChange(t.value)}
          className={`w-full text-left p-4 rounded-xl border-2 transition-all flex items-start gap-4
            ${value === t.value ? "border-indigo-500 bg-indigo-50" : "border-gray-200 hover:border-indigo-200"}`}
        >
          <span className="text-2xl mt-0.5">{t.icon}</span>
          <div>
            <p className="font-semibold text-gray-800">{t.label}</p>
            <p className="text-xs text-gray-500 mt-0.5">{t.desc}</p>
          </div>
          {value === t.value && <span className="ml-auto text-indigo-600 text-lg">✓</span>}
        </button>
      ))}
    </div>
  );
}

// ── Shared text/number field — at module scope to prevent remount ─────────────
function Field({ label, name, type = "text", min, placeholder, form, setForm }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input
        type={type}
        min={min}
        value={form[name]}
        onChange={(e) =>
          setForm({ ...form, [name]: type === "number" ? parseInt(e.target.value) || 0 : e.target.value })
        }
        placeholder={placeholder}
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
      />
    </div>
  );
}

// ── Step 2: Paper Details + per-question marks + question paper PDF ───────────
function Step2({ form, setForm }) {
  const isType2 = form.type === "mcq_numerical" || form.type === "mcq_numerical_subjective";
  const isType3 = form.type === "mcq_numerical_subjective";

  // When MCQ count changes, grow/shrink the per-question marks map
  const setMcqCount = (n) => {
    const count = Math.max(1, n);
    const updated = { ...form.mcqQuestionMarks };
    for (let i = 1; i <= count; i++) {
      if (!updated[`Q${i}`]) updated[`Q${i}`] = form.mcqMarks;
    }
    // Remove entries beyond new count
    Object.keys(updated).forEach((k) => {
      if (parseInt(k.slice(1)) > count) delete updated[k];
    });
    setForm({ ...form, mcqCount: count, mcqQuestionMarks: updated });
  };

  // Update marks for one specific question
  const setQMark = (qid, val) =>
    setForm({ ...form, mcqQuestionMarks: { ...form.mcqQuestionMarks, [qid]: Math.max(0, val) } });

  // Pressing "Apply to all" resets every Q to the current default marks value
  const applyDefaultToAll = () => {
    const updated = {};
    for (let i = 1; i <= form.mcqCount; i++) updated[`Q${i}`] = form.mcqMarks;
    setForm({ ...form, mcqQuestionMarks: updated });
  };

  // When Numerical count changes, grow/shrink the per-question marks map
  const setNumericalCount = (n) => {
    const count = Math.max(1, n);
    const updated = { ...form.numericalQuestionMarks };
    for (let i = 1; i <= count; i++) {
      if (!updated[`N${i}`]) updated[`N${i}`] = form.numericalMarks;
    }
    Object.keys(updated).forEach((k) => {
      if (parseInt(k.slice(1)) > count) delete updated[k];
    });
    setForm({ ...form, numericalCount: count, numericalQuestionMarks: updated });
  };

  const setNumericalQMark = (qid, val) =>
    setForm({ ...form, numericalQuestionMarks: { ...form.numericalQuestionMarks, [qid]: Math.max(0, val) } });

  const applyNumericalDefaultToAll = () => {
    const updated = {};
    for (let i = 1; i <= form.numericalCount; i++) updated[`N${i}`] = form.numericalMarks;
    setForm({ ...form, numericalQuestionMarks: updated });
  };

  // When Subjective count changes, grow/shrink the per-question marks map
  const setSubjectiveCount = (n) => {
    const count = Math.max(1, n);
    const updated = { ...form.subjectiveQuestionMarks };
    for (let i = 1; i <= count; i++) {
      if (!updated[`S${i}`]) updated[`S${i}`] = form.subjectiveMarks;
    }
    Object.keys(updated).forEach((k) => {
      if (parseInt(k.slice(1)) > count) delete updated[k];
    });
    setForm({ ...form, subjectiveCount: count, subjectiveQuestionMarks: updated });
  };

  const setSubjectiveQMark = (qid, val) =>
    setForm({ ...form, subjectiveQuestionMarks: { ...form.subjectiveQuestionMarks, [qid]: Math.max(0, val) } });

  const applySubjectiveDefaultToAll = () => {
    const updated = {};
    for (let i = 1; i <= form.subjectiveCount; i++) updated[`S${i}`] = form.subjectiveMarks;
    setForm({ ...form, subjectiveQuestionMarks: updated });
  };

  const total =
    mcqTotal(form) +
    (isType2 ? numericalTotal(form) : 0) +
    (isType3 ? subjectiveTotal(form) : 0);

  return (
    <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-1">
      <Field label="Paper Name" name="name" placeholder="e.g. CS101 Midterm 2026" form={form} setForm={setForm} />
      <Field label="Subject" name="subject" placeholder="e.g. Computer Science" form={form} setForm={setForm} />

      {/* Question paper PDF — uploaded for reference; not parsed */}
      <PdfUploadZone
        label="Question Paper (Reference PDF)"
        hint="Optional — students and teacher can view this on the paper page"
        currentUrl={form.questionPaperUrl}
        onFile={(_, url) => setForm({ ...form, questionPaperUrl: url })}
      />

      {/* MCQ section */}
      <div className="grid grid-cols-2 gap-3">
        {/* Controlled separately so we can sync mcqQuestionMarks on change */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">MCQ Questions</label>
          <input
            type="number" min="1"
            value={form.mcqCount}
            onChange={(e) => setMcqCount(parseInt(e.target.value) || 1)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Default Marks / MCQ</label>
          <input
            type="number" min="1"
            value={form.mcqMarks}
            onChange={(e) => setForm({ ...form, mcqMarks: parseInt(e.target.value) || 1 })}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          />
        </div>
      </div>

      {/* Per-question marks grid */}
      {form.mcqCount > 0 && (
        <div className="bg-gray-50 rounded-xl p-3 space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold text-gray-600">Per-Question Marks (edit individually)</p>
            <button
              type="button"
              onClick={applyDefaultToAll}
              className="text-xs text-indigo-600 hover:underline"
            >
              Apply default to all
            </button>
          </div>
          <div className="grid grid-cols-4 sm:grid-cols-6 gap-2">
            {Array.from({ length: form.mcqCount }, (_, i) => {
              const qid = `Q${i + 1}`;
              return (
                <div key={qid} className="flex flex-col items-center gap-1">
                  <span className="text-xs text-gray-400">{qid}</span>
                  <input
                    type="number"
                    min="0"
                    step="0.5"
                    value={form.mcqQuestionMarks[qid] ?? form.mcqMarks}
                    onChange={(e) => setQMark(qid, parseFloat(e.target.value) || 0)}
                    className="w-full text-center text-sm border border-gray-300 rounded-lg px-1 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-400"
                  />
                </div>
              );
            })}
          </div>
        </div>
      )}

      {isType2 && (
        <>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Numerical Questions</label>
              <input
                type="number" min="1"
                value={form.numericalCount}
                onChange={(e) => setNumericalCount(parseInt(e.target.value) || 1)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Default Marks / Numerical</label>
              <input
                type="number" min="1"
                value={form.numericalMarks}
                onChange={(e) => setForm({ ...form, numericalMarks: parseInt(e.target.value) || 1 })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
            </div>
          </div>
          {form.numericalCount > 0 && (
            <div className="bg-gray-50 rounded-xl p-3 space-y-2">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold text-gray-600">Per-Question Marks — Numerical (edit individually)</p>
                <button type="button" onClick={applyNumericalDefaultToAll} className="text-xs text-indigo-600 hover:underline">Apply default to all</button>
              </div>
              <div className="grid grid-cols-4 sm:grid-cols-6 gap-2">
                {Array.from({ length: form.numericalCount }, (_, i) => {
                  const qid = `N${i + 1}`;
                  return (
                    <div key={qid} className="flex flex-col items-center gap-1">
                      <span className="text-xs text-gray-400">{qid}</span>
                      <input
                        type="number" min="0" step="0.5"
                        value={form.numericalQuestionMarks[qid] ?? form.numericalMarks}
                        onChange={(e) => setNumericalQMark(qid, parseFloat(e.target.value) || 0)}
                        className="w-full text-center text-sm border border-gray-300 rounded-lg px-1 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-400"
                      />
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </>
      )}
      {isType3 && (
        <>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Subjective Questions</label>
              <input
                type="number" min="1"
                value={form.subjectiveCount}
                onChange={(e) => setSubjectiveCount(parseInt(e.target.value) || 1)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Default Marks / Subjective</label>
              <input
                type="number" min="1"
                value={form.subjectiveMarks}
                onChange={(e) => setForm({ ...form, subjectiveMarks: parseInt(e.target.value) || 1 })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
            </div>
          </div>
          {form.subjectiveCount > 0 && (
            <div className="bg-gray-50 rounded-xl p-3 space-y-2">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold text-gray-600">Per-Question Marks — Subjective (edit individually)</p>
                <button type="button" onClick={applySubjectiveDefaultToAll} className="text-xs text-indigo-600 hover:underline">Apply default to all</button>
              </div>
              <div className="grid grid-cols-4 sm:grid-cols-6 gap-2">
                {Array.from({ length: form.subjectiveCount }, (_, i) => {
                  const qid = `S${i + 1}`;
                  return (
                    <div key={qid} className="flex flex-col items-center gap-1">
                      <span className="text-xs text-gray-400">{qid}</span>
                      <input
                        type="number" min="0" step="0.5"
                        value={form.subjectiveQuestionMarks[qid] ?? form.subjectiveMarks}
                        onChange={(e) => setSubjectiveQMark(qid, parseFloat(e.target.value) || 0)}
                        className="w-full text-center text-sm border border-gray-300 rounded-lg px-1 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-400"
                      />
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </>
      )}

      <div className="bg-indigo-50 rounded-lg p-3 text-sm">
        <span className="text-gray-600">Total Marks: </span>
        <span className="font-bold text-indigo-700">{total}</span>
      </div>
    </div>
  );
}

// ── Step 3: Answer Key — manual entry OR extract from PDF ─────────────────────
function Step3({ form, setForm }) {
  const [extracting, setExtracting] = useState(false);
  const MCQ_OPTIONS = ["A", "B", "C", "D"];
  const isType2 = form.type === "mcq_numerical" || form.type === "mcq_numerical_subjective";

  const setMcqAnswer = (qid, val) =>
    setForm({ ...form, mcqAnswers: { ...form.mcqAnswers, [qid]: val } });
  const setNumericalAnswer = (qid, patch) =>
    setForm({ ...form, numericalAnswers: { ...form.numericalAnswers, [qid]: { ...(form.numericalAnswers[qid] ?? {}), ...patch } } });

  // Simulates reading MCQ answers from the uploaded answer key PDF
  const handleExtract = async () => {
    if (!form.answerKeyPdfUrl) return;
    setExtracting(true);
    const answers = await mockExtractAnswersFromPdf(form.mcqCount);
    setForm({ ...form, mcqAnswers: answers });
    setExtracting(false);
  };

  return (
    <div className="space-y-5 max-h-[60vh] overflow-y-auto pr-1">

      {/* ── Answer Key PDF section ─────────────────────────────────────────── */}
      <div className="space-y-3">
        <h4 className="text-sm font-semibold text-gray-700">Answer Key Source</h4>

        {/* Mode toggle: manual vs PDF extract */}
        <div className="flex gap-2">
          {["manual", "pdf"].map((mode) => (
            <button
              key={mode}
              type="button"
              onClick={() => setForm({ ...form, answerKeyMode: mode })}
              className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium border-2 transition-all
                ${form.answerKeyMode === mode
                  ? "border-indigo-500 bg-indigo-50 text-indigo-700"
                  : "border-gray-200 text-gray-500 hover:border-gray-300"}`}
            >
              {mode === "manual" ? "✏️ Enter Manually" : "📄 Upload PDF & Extract"}
            </button>
          ))}
        </div>

        {/* PDF upload + extract button */}
        {form.answerKeyMode === "pdf" && (
          <div className="space-y-2">
            <PdfUploadZone
              label="Answer Key PDF"
              hint="Upload your answer key — we'll extract MCQ answers automatically"
              currentUrl={form.answerKeyPdfUrl}
              onFile={(_, url) => setForm({ ...form, answerKeyPdfUrl: url })}
            />
            <Button
              size="sm"
              variant="secondary"
              disabled={!form.answerKeyPdfUrl}
              loading={extracting}
              onClick={handleExtract}
              className="w-full"
            >
              {extracting ? "Extracting answers…" : "Extract Answers from PDF"}
            </Button>
            {Object.keys(form.mcqAnswers).length > 0 && !extracting && (
              <p className="text-xs text-green-600 font-medium text-center">
                ✓ {Object.keys(form.mcqAnswers).length} answers extracted — review below
              </p>
            )}
          </div>
        )}

        {/* Reference copy of answer key PDF (separate from the extraction one) */}
        <PdfUploadZone
          label="Answer Key Reference PDF (optional)"
          hint="Stored alongside the paper for viewing later"
          currentUrl={form.answerKeyRefUrl}
          onFile={(_, url) => setForm({ ...form, answerKeyRefUrl: url })}
        />
      </div>

      {/* ── MCQ answer grid ────────────────────────────────────────────────── */}
      <div>
        <h4 className="text-sm font-semibold text-gray-700 mb-3">
          MCQ Answers {form.answerKeyMode === "pdf" ? "(extracted — confirm or edit)" : "(enter manually)"}
        </h4>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {Array.from({ length: form.mcqCount }, (_, i) => {
            const qid = `Q${i + 1}`;
            const marks = form.mcqQuestionMarks[qid] ?? form.mcqMarks;
            return (
              <div key={qid} className="flex items-center gap-2 bg-gray-50 rounded-lg px-3 py-2">
                <span className="text-xs font-medium text-gray-500 w-8">{qid}</span>
                {/* Per-Q marks shown as a reminder */}
                <span className="text-xs text-gray-400 w-8">[{marks}m]</span>
                <div className="flex gap-1">
                  {MCQ_OPTIONS.map((opt) => (
                    <button
                      key={opt}
                      type="button"
                      onClick={() => setMcqAnswer(qid, opt)}
                      className={`w-8 h-8 rounded-lg text-sm font-semibold transition-colors
                        ${form.mcqAnswers[qid] === opt
                          ? "bg-indigo-600 text-white"
                          : "bg-white border border-gray-300 text-gray-600 hover:border-indigo-300"}`}
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Numerical answer grid ──────────────────────────────────────────── */}
      {isType2 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Numerical Answers</h4>
          <div className="space-y-2">
            {Array.from({ length: form.numericalCount }, (_, i) => {
              const qid = `N${i + 1}`;
              const ans = form.numericalAnswers[qid] ?? { answer: "", tolerance_type: "range", tolerance_value: 0.1 };
              return (
                <div key={qid} className="flex flex-wrap items-center gap-2 bg-gray-50 rounded-lg px-3 py-2">
                  <span className="text-xs font-medium text-gray-500 w-6">{qid}</span>
                  <input
                    type="number" step="any" value={ans.answer}
                    onChange={(e) => setNumericalAnswer(qid, { answer: e.target.value })}
                    placeholder="Answer"
                    className="w-24 text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-indigo-400"
                  />
                  <select
                    value={ans.tolerance_type}
                    onChange={(e) => setNumericalAnswer(qid, { tolerance_type: e.target.value })}
                    className="text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none"
                  >
                    <option value="exact">Exact</option>
                    <option value="range">±Range</option>
                    <option value="decimal_variants">Variants</option>
                  </select>
                  {ans.tolerance_type === "range" && (
                    <input
                      type="number" step="any" value={ans.tolerance_value}
                      onChange={(e) => setNumericalAnswer(qid, { tolerance_value: parseFloat(e.target.value) })}
                      placeholder="±"
                      className="w-16 text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-indigo-400"
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Step 4: Configuration ─────────────────────────────────────────────────────
function Step4({ form, setForm }) {
  const isType3 = form.type === "mcq_numerical_subjective";

  const toggleNegative = () =>
    setForm({ ...form, config: { ...form.config, negativeMaking: !form.config.negativeMaking } });

  const updateRubric = (i, rubric) => {
    const rubrics = [...(form.subjectiveRubrics ?? [])];
    rubrics[i] = rubric;
    setForm({ ...form, subjectiveRubrics: rubrics });
  };

  return (
    <div className="space-y-5 max-h-[50vh] overflow-y-auto pr-1">
      <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
        <div>
          <p className="text-sm font-medium text-gray-700">Negative Marking</p>
          <p className="text-xs text-gray-400">Deduct marks for wrong MCQ answers</p>
        </div>
        <button
          type="button"
          onClick={toggleNegative}
          className={`w-12 h-6 rounded-full transition-colors relative ${form.config.negativeMaking ? "bg-indigo-600" : "bg-gray-300"}`}
        >
          <span className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform
            ${form.config.negativeMaking ? "translate-x-6 left-0.5" : "translate-x-0 left-0.5"}`} />
        </button>
      </div>

      {form.config.negativeMaking && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Marks deducted per wrong answer</label>
          <input
            type="number" min="0.25" step="0.25"
            value={form.config.marksDeducted ?? 0.5}
            onChange={(e) => setForm({ ...form, config: { ...form.config, marksDeducted: parseFloat(e.target.value) } })}
            className="w-24 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          />
        </div>
      )}

      {isType3 && Array.from({ length: form.subjectiveCount }, (_, i) => (
        <div key={i}>
          <p className="text-xs text-gray-500 font-medium mb-1">Question Text for S{i + 1}</p>
          <input
            value={(form.subjectiveQuestions?.[i]?.question_text) ?? ""}
            onChange={(e) => {
              const qs = [...(form.subjectiveQuestions ?? [])];
              qs[i] = { ...(qs[i] ?? {}), question_text: e.target.value };
              setForm({ ...form, subjectiveQuestions: qs });
            }}
            placeholder="Enter the subjective question text..."
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 mb-2"
          />
          <RubricBuilder questionIndex={i} value={form.subjectiveRubrics?.[i]} onChange={(r) => updateRubric(i, r)} />
        </div>
      ))}
    </div>
  );
}

// ── Step 5: Review ────────────────────────────────────────────────────────────
function Step5({ form }) {
  const isType2 = form.type === "mcq_numerical" || form.type === "mcq_numerical_subjective";
  const isType3 = form.type === "mcq_numerical_subjective";
  const total =
    mcqTotal(form) +
    (isType2 ? numericalTotal(form) : 0) +
    (isType3 ? subjectiveTotal(form) : 0);

  const Row = ({ label, value }) => (
    <div className="flex justify-between py-2 border-b border-gray-100 last:border-0">
      <span className="text-sm text-gray-500">{label}</span>
      <span className="text-sm font-medium text-gray-800">{value}</span>
    </div>
  );

  return (
    <div className="space-y-4">
      <div className="bg-gray-50 rounded-xl p-4">
        <Row label="Paper Name" value={form.name || "—"} />
        <Row label="Subject" value={form.subject || "—"} />
        <Row label="Type" value={paperTypeLabel(form.type)} />
        <Row label="MCQ Questions" value={`${form.mcqCount} questions (varying marks) = ${mcqTotal(form)} marks`} />
        {isType2 && <Row label="Numerical Questions" value={`${form.numericalCount} questions (varying marks) = ${numericalTotal(form)} marks`} />}
        {isType3 && <Row label="Subjective Questions" value={`${form.subjectiveCount} questions (varying marks) = ${subjectiveTotal(form)} marks`} />}
        <Row label="Total Marks" value={<span className="text-indigo-600 font-bold">{total}</span>} />
        <Row label="Negative Marking" value={form.config.negativeMaking ? `Yes (−${form.config.marksDeducted ?? 0.5}/wrong)` : "No"} />
        <Row label="MCQ Answers set" value={`${Object.keys(form.mcqAnswers).length} / ${form.mcqCount}`} />
        <Row label="Question Paper PDF" value={form.questionPaperUrl ? "✓ Uploaded" : "Not uploaded"} />
        <Row label="Answer Key PDF" value={(form.answerKeyPdfUrl || form.answerKeyRefUrl) ? "✓ Uploaded" : "Not uploaded"} />
      </div>

      {/* Quick links to review uploaded PDFs before saving */}
      <div className="flex gap-3">
        {form.questionPaperUrl && (
          <button type="button" onClick={() => window.open(form.questionPaperUrl, "_blank")}
            className="flex-1 text-xs text-indigo-600 border border-indigo-200 rounded-lg py-2 hover:bg-indigo-50">
            📄 View Question Paper
          </button>
        )}
        {(form.answerKeyPdfUrl || form.answerKeyRefUrl) && (
          <button type="button" onClick={() => window.open(form.answerKeyRefUrl || form.answerKeyPdfUrl, "_blank")}
            className="flex-1 text-xs text-indigo-600 border border-indigo-200 rounded-lg py-2 hover:bg-indigo-50">
            📝 View Answer Key
          </button>
        )}
      </div>

      <p className="text-xs text-gray-400 text-center">Review above, then click "Create Paper" to save.</p>
    </div>
  );
}

// ── Main Wizard ───────────────────────────────────────────────────────────────
const INITIAL = {
  type: null,
  name: "",
  subject: "",
  mcqCount: 5,
  mcqMarks: 2,                  // default marks; individual Q marks can differ
  mcqQuestionMarks: {},         // { Q1: 2, Q2: 3, ... } — populated in Step 2
  numericalCount: 3,
  numericalMarks: 5,
  numericalQuestionMarks: {},   // { N1: 5, N2: 3, ... } — populated in Step 2
  subjectiveCount: 2,
  subjectiveMarks: 10,
  subjectiveQuestionMarks: {},  // { S1: 10, S2: 8, ... } — populated in Step 2
  mcqAnswers: {},
  numericalAnswers: {},
  subjectiveQuestions: [],
  subjectiveRubrics: [],
  config: { negativeMaking: false },
  answerKeyMode: "manual",      // "manual" | "pdf"
  questionPaperUrl: null,       // object URL for question paper PDF (reference)
  answerKeyPdfUrl: null,        // object URL for the PDF used for extraction
  answerKeyRefUrl: null,        // object URL for the answer key reference PDF
};

export default function CreatePaper() {
  const [step, setStep] = useState(1);
  const [form, setForm] = useState(INITIAL);
  const [success, setSuccess] = useState(false);
  const { createPaper, loading } = useCreatePaper();
  const navigate = useNavigate();

  const canNext = () => {
    if (step === 1) return !!form.type;
    if (step === 2) return form.name.trim() && form.subject.trim() && form.mcqCount > 0;
    return true;
  };

  const handleSubmit = async () => {
    const isType2 = form.type === "mcq_numerical" || form.type === "mcq_numerical_subjective";
    const isType3 = form.type === "mcq_numerical_subjective";
    const totalMarks =
      mcqTotal(form) +
      (isType2 ? numericalTotal(form) : 0) +
      (isType3 ? subjectiveTotal(form) : 0);

    const paper = await createPaper({ ...form, totalMarks, typeLabel: paperTypeLabel(form.type) });
    if (paper) setSuccess(true);
  };

  return (
    <PageWrapper>
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-800 mb-6">Create New Paper</h1>
        <StepWizard steps={STEPS} current={step} />

        <Card className="mt-8">
          <Card.Header>
            <h2 className="text-base font-semibold text-gray-700">Step {step}: {STEPS[step - 1]}</h2>
          </Card.Header>
          <Card.Body>
            {step === 1 && <Step1 value={form.type} onChange={(t) => setForm({ ...form, type: t })} />}
            {step === 2 && <Step2 form={form} setForm={setForm} />}
            {step === 3 && <Step3 form={form} setForm={setForm} />}
            {step === 4 && <Step4 form={form} setForm={setForm} />}
            {step === 5 && <Step5 form={form} />}
          </Card.Body>
          <Card.Footer className="flex justify-between">
            <Button variant="secondary" onClick={() => setStep((s) => s - 1)} disabled={step === 1}>← Back</Button>
            {step < 5
              ? <Button onClick={() => setStep((s) => s + 1)} disabled={!canNext()}>Next →</Button>
              : <Button onClick={handleSubmit} loading={loading}>Create Paper ✓</Button>
            }
          </Card.Footer>
        </Card>
      </div>

      <Modal
        isOpen={success}
        onClose={() => { setSuccess(false); navigate("/teacher/dashboard"); }}
        title="Paper Created!"
        footer={<Button onClick={() => { setSuccess(false); navigate("/teacher/dashboard"); }}>Go to Dashboard</Button>}
      >
        <div className="text-center py-4">
          <div className="text-5xl mb-3">🎉</div>
          <p className="text-gray-700 font-medium">
            You have successfully created an exam evaluation for <strong>{form.name}</strong>.
          </p>
          <p className="text-sm text-gray-500 mt-2">Students can now upload their answer sheets for evaluation.</p>
        </div>
      </Modal>
    </PageWrapper>
  );
}
