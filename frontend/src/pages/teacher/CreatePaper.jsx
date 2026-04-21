// teacher/CreatePaper.jsx — 5-step wizard to create an exam paper.
// Step 1: type
// Step 2: details + marks (uniform default, per-Q optional) + question paper PDF upload
// Step 3: answer key (manual or PDF extract) + answer sheet reference PDF upload
// Step 4: configuration — negative marking with whole-paper or per-question scope
// Step 5: review

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import useAuthStore from "../../store/authStore";
import PageWrapper from "../../components/layout/PageWrapper";
import StepWizard from "../../components/forms/StepWizard";
import RubricBuilder from "../../components/forms/RubricBuilder";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";
import Modal from "../../components/ui/Modal";
import { useCreatePaper, useUploadPaperFile, useExtractAnswers, useExtractRubric } from "../../hooks/usePapers";
import { paperTypeLabel } from "../../utils/formatters";

const STEPS = ["Paper Type", "Details", "Answer Key", "Configuration", "Review"];

const PAPER_TYPES = [
  { value: "mcq", icon: "☑️", label: "MCQ Only", desc: "OMR bubbles or written MCQ answers" },
  { value: "mcq_numerical", icon: "🔢", label: "MCQ + Numerical", desc: "MCQ section + numerical answers with tolerance" },
  { value: "mcq_numerical_subjective", icon: "✍️", label: "MCQ + Numerical + Subjective", desc: "Full paper graded with LLM on subjective section" },
];

// ── Helpers ───────────────────────────────────────────────────────────────────

function mcqTotal(form) {
  return Array.from({ length: form.mcqCount }, (_, i) =>
    form.uniformMcqMarks ? form.mcqMarks : (form.mcqQuestionMarks[`Q${i + 1}`] ?? form.mcqMarks)
  ).reduce((a, b) => a + b, 0);
}

function numericalTotal(form) {
  return Array.from({ length: form.numericalCount }, (_, i) =>
    form.uniformNumericalMarks ? form.numericalMarks : (form.numericalQuestionMarks[`N${i + 1}`] ?? form.numericalMarks)
  ).reduce((a, b) => a + b, 0);
}

function subjectiveTotal(form) {
  return Array.from({ length: form.subjectiveCount }, (_, i) =>
    form.uniformSubjectiveMarks ? form.subjectiveMarks : (form.subjectiveQuestionMarks[`S${i + 1}`] ?? form.subjectiveMarks)
  ).reduce((a, b) => a + b, 0);
}

// ── PDF upload zone ───────────────────────────────────────────────────────────
// At module scope to avoid remounting on parent re-render.
// If uploadFn is provided, the file is uploaded to the server; otherwise a
// browser object URL is used (fallback for cases where upload is not needed).

function PdfUploadZone({ label, hint, currentUrl, onFile, uploadFn }) {
  const [uploading, setUploading] = useState(false);

  const handleChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    e.target.value = "";

    if (uploadFn) {
      setUploading(true);
      const url = await uploadFn(file);
      setUploading(false);
      if (url) onFile(url);
    } else {
      onFile(URL.createObjectURL(file));
    }
  };

  const openUrl = (url) => {
    // Server URLs like /api/papers/files/xxx.pdf open via the Vite proxy
    window.open(url, "_blank");
  };

  return (
    <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl border border-dashed border-gray-300">
      <span className="text-2xl">📄</span>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-700">{label}</p>
        <p className="text-xs text-gray-400 truncate">
          {uploading ? "Uploading to server…" : currentUrl ? "Uploaded" : hint}
        </p>
      </div>
      {currentUrl && !uploading && (
        <button
          type="button"
          onClick={() => openUrl(currentUrl)}
          className="text-xs text-green-600 hover:underline whitespace-nowrap"
        >
          View PDF
        </button>
      )}
      {uploading && (
        <span className="text-xs text-green-400 animate-pulse whitespace-nowrap">Saving…</span>
      )}
      <label className={`cursor-pointer text-xs bg-white border border-gray-300 rounded-lg px-3 py-1.5 whitespace-nowrap
        ${uploading ? "opacity-50 cursor-not-allowed text-gray-400" : "text-gray-600 hover:border-green-400 hover:text-green-600"}`}>
        {currentUrl ? "Replace" : "Upload"}
        <input
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={handleChange}
          disabled={uploading}
        />
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
            ${value === t.value ? "border-green-500 bg-green-50" : "border-gray-200 hover:border-green-200"}`}
        >
          <span className="text-2xl mt-0.5">{t.icon}</span>
          <div>
            <p className="font-semibold text-gray-800">{t.label}</p>
            <p className="text-xs text-gray-500 mt-0.5">{t.desc}</p>
          </div>
          {value === t.value && <span className="ml-auto text-green-600 text-lg">✓</span>}
        </button>
      ))}
    </div>
  );
}

// ── Shared text/number input ──────────────────────────────────────────────────

function Field({ label, name, type = "text", min, step, placeholder, form, setForm }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input
        type={type}
        min={min}
        step={step}
        value={form[name]}
        onChange={(e) =>
          setForm({ ...form, [name]: type === "number" ? (parseFloat(e.target.value) || 0) : e.target.value })
        }
        placeholder={placeholder}
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-400"
      />
    </div>
  );
}

// ── Marks section — uniform toggle + optional per-question grid ───────────────
// uniformKey: form field name for the toggle (e.g. "uniformMcqMarks")
// defaultMarksKey: form field name for default marks (e.g. "mcqMarks")
// countKey: form field name for question count (e.g. "mcqCount")
// questionMarksKey: form field name for the per-Q map (e.g. "mcqQuestionMarks")
// prefix: question ID prefix ("Q" | "N" | "S")
// label: section label

function MarksSection({ form, setForm, uniformKey, defaultMarksKey, countKey, questionMarksKey, prefix, label }) {
  const count = form[countKey];
  const defaultMark = form[defaultMarksKey];
  const isUniform = form[uniformKey];

  const applyDefaultToAll = () => {
    const updated = {};
    for (let i = 1; i <= count; i++) updated[`${prefix}${i}`] = defaultMark;
    setForm({ ...form, [questionMarksKey]: updated });
  };

  const setQMark = (qid, val) =>
    setForm({ ...form, [questionMarksKey]: { ...form[questionMarksKey], [qid]: Math.max(0, val) } });

  return (
    <div className="bg-gray-50 rounded-xl p-3 space-y-3">
      {/* Header row: label + uniform toggle */}
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold text-gray-600">{label}</p>
        <label className="flex items-center gap-2 cursor-pointer select-none">
          <span className="text-xs text-gray-500">Custom per question</span>
          <input
            type="checkbox"
            checked={!isUniform}
            onChange={(e) => {
              const customise = e.target.checked;
              if (customise) applyDefaultToAll();  // seed grid from default
              setForm({ ...form, [uniformKey]: !customise });
            }}
            className="rounded border-gray-300 text-green-600 focus:ring-green-400"
          />
        </label>
      </div>

      {/* Default marks input — always visible */}
      <div>
        <label className="block text-xs text-gray-500 mb-1">
          {isUniform ? `Marks per ${label} question (all same)` : `Default marks (used when customising)`}
        </label>
        <input
          type="number"
          min="0"
          step="0.5"
          value={defaultMark}
          onChange={(e) => {
            const val = parseFloat(e.target.value) || 0;
            const patch = { [defaultMarksKey]: val };
            // If uniform, also reset the per-Q map so total stays consistent
            if (isUniform) {
              const updated = {};
              for (let i = 1; i <= count; i++) updated[`${prefix}${i}`] = val;
              patch[questionMarksKey] = updated;
            }
            setForm({ ...form, ...patch });
          }}
          className="w-24 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-400"
        />
      </div>

      {/* Per-question grid — shown only when customising */}
      {!isUniform && count > 0 && (
        <>
          <div className="flex justify-end">
            <button type="button" onClick={applyDefaultToAll} className="text-xs text-green-600 hover:underline">
              Reset all to default
            </button>
          </div>
          <div className="grid grid-cols-4 sm:grid-cols-6 gap-2">
            {Array.from({ length: count }, (_, i) => {
              const qid = `${prefix}${i + 1}`;
              return (
                <div key={qid} className="flex flex-col items-center gap-1">
                  <span className="text-xs text-gray-400">{qid}</span>
                  <input
                    type="number"
                    min="0"
                    step="0.5"
                    value={form[questionMarksKey][qid] ?? defaultMark}
                    onChange={(e) => setQMark(qid, parseFloat(e.target.value) || 0)}
                    className="w-full text-center text-sm border border-gray-300 rounded-lg px-1 py-1.5 focus:outline-none focus:ring-2 focus:ring-green-400"
                  />
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

// ── Step 2: Paper Details ─────────────────────────────────────────────────────

function Step2({ form, setForm, uploadFn }) {
  const isType2 = form.type === "mcq_numerical" || form.type === "mcq_numerical_subjective";
  const isType3 = form.type === "mcq_numerical_subjective";

  // For Type 3, MCQ and Numerical can be 0. Subjective must be ≥ 1.
  const minCount = (prefix) => {
    if (!isType3) return 1;
    return prefix === "S" ? 1 : 0;
  };

  const setCount = (countKey, marksKey, qMarksKey, prefix, n) => {
    const count = Math.max(minCount(prefix), n);
    const updated = { ...form[qMarksKey] };
    for (let i = 1; i <= count; i++) {
      if (updated[`${prefix}${i}`] === undefined) updated[`${prefix}${i}`] = form[marksKey];
    }
    Object.keys(updated).forEach((k) => {
      if (parseInt(k.slice(prefix.length)) > count) delete updated[k];
    });
    setForm({ ...form, [countKey]: count, [qMarksKey]: updated });
  };

  const total =
    mcqTotal(form) +
    (isType2 ? numericalTotal(form) : 0) +
    (isType3 ? subjectiveTotal(form) : 0);

  return (
    <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-1">
      <Field label="Paper Name" name="name" placeholder="e.g. CS101 Midterm 2026" form={form} setForm={setForm} />
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Subject</label>
        <div className="flex items-center gap-2 border border-gray-200 bg-gray-50 rounded-lg px-3 py-2 text-sm text-gray-600">
          <span className="font-medium text-gray-800">{form.subject || "—"}</span>
          <span className="text-xs text-gray-400">(fixed to your assigned subject)</span>
        </div>
      </div>

      {/* Question Paper PDF — uploaded to server for persistent reference */}
      <PdfUploadZone
        label="Question Paper PDF (Reference)"
        hint="Optional — stored on server, viewable from paper page"
        currentUrl={form.questionPaperUrl}
        uploadFn={uploadFn}
        onFile={(url) => setForm({ ...form, questionPaperUrl: url })}
      />

      {/* MCQ count + marks */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          MCQ Questions {isType3 && <span className="text-xs text-gray-400 font-normal">(0 = no MCQ section)</span>}
        </label>
        <input
          type="number" min={isType3 ? "0" : "1"}
          value={form.mcqCount}
          onChange={(e) => setCount("mcqCount", "mcqMarks", "mcqQuestionMarks", "Q", parseInt(e.target.value) || 0)}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-400"
        />
      </div>
      {form.mcqCount > 0 && (
        <MarksSection
          form={form} setForm={setForm}
          uniformKey="uniformMcqMarks" defaultMarksKey="mcqMarks"
          countKey="mcqCount" questionMarksKey="mcqQuestionMarks"
          prefix="Q" label="MCQ"
        />
      )}

      {isType2 && (
        <>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Numerical Questions {isType3 && <span className="text-xs text-gray-400 font-normal">(0 = no Numerical section)</span>}
            </label>
            <input
              type="number" min={isType3 ? "0" : "1"}
              value={form.numericalCount}
              onChange={(e) => setCount("numericalCount", "numericalMarks", "numericalQuestionMarks", "N", parseInt(e.target.value) || 0)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-400"
            />
          </div>
          {form.numericalCount > 0 && (
            <MarksSection
              form={form} setForm={setForm}
              uniformKey="uniformNumericalMarks" defaultMarksKey="numericalMarks"
              countKey="numericalCount" questionMarksKey="numericalQuestionMarks"
              prefix="N" label="Numerical"
            />
          )}
        </>
      )}

      {isType3 && (
        <>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Subjective Questions</label>
            <input
              type="number" min="1"
              value={form.subjectiveCount}
              onChange={(e) => setCount("subjectiveCount", "subjectiveMarks", "subjectiveQuestionMarks", "S", parseInt(e.target.value) || 1)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-400"
            />
          </div>
          <MarksSection
            form={form} setForm={setForm}
            uniformKey="uniformSubjectiveMarks" defaultMarksKey="subjectiveMarks"
            countKey="subjectiveCount" questionMarksKey="subjectiveQuestionMarks"
            prefix="S" label="Subjective"
          />
        </>
      )}

      <div className="bg-green-50 rounded-lg p-3 text-sm">
        <span className="text-gray-600">Total Marks: </span>
        <span className="font-bold text-green-700">{total}</span>
      </div>
    </div>
  );
}

// ── Step 3: Answer Key ────────────────────────────────────────────────────────

function Step3({ form, setForm, uploadFn, extractFn, extracting }) {
  const MCQ_OPTIONS = ["A", "B", "C", "D"];
  const isType2 = form.type === "mcq_numerical" || form.type === "mcq_numerical_subjective";

  // Toggle one option in/out of a question's answer set.
  // Single answer:  click A         → stores "A"
  // Multi answer:   click A then C  → stores "A,C"
  // Deselect:       click A when "A,C" → stores "C"
  const toggleMcqOption = (qid, opt) => {
    const current = form.mcqAnswers[qid] || "";
    const selected = current ? current.split(",") : [];
    const next = selected.includes(opt)
      ? selected.filter((o) => o !== opt)
      : [...selected, opt].sort();
    const newVal = next.join(",");
    setForm({ ...form, mcqAnswers: { ...form.mcqAnswers, [qid]: newVal || undefined } });
  };

  const setNumericalAnswer = (qid, patch) =>
    setForm({
      ...form,
      numericalAnswers: { ...form.numericalAnswers, [qid]: { ...(form.numericalAnswers[qid] ?? {}), ...patch } },
    });

  const handleExtract = async () => {
    if (!form.answerKeyPdfUrl) return;
    const result = await extractFn(form.answerKeyPdfUrl, form.mcqCount);
    if (result) {
      setForm({ ...form, mcqAnswers: result.answers });
    }
  };

  return (
    <div className="space-y-5 max-h-[60vh] overflow-y-auto pr-1">

      {/* ── Answer key source ─────────────────────────────────────────────── */}
      <div className="space-y-3">
        <h4 className="text-sm font-semibold text-gray-700">Answer Key Source</h4>

        <div className="flex gap-2">
          {["manual", "pdf"].map((mode) => (
            <button
              key={mode}
              type="button"
              onClick={() => setForm({ ...form, answerKeyMode: mode })}
              className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium border-2 transition-all
                ${form.answerKeyMode === mode
                  ? "border-green-500 bg-green-50 text-green-700"
                  : "border-gray-200 text-gray-500 hover:border-gray-300"}`}
            >
              {mode === "manual" ? "✏️ Enter Manually" : "📄 Upload PDF & Extract"}
            </button>
          ))}
        </div>

        {/* PDF upload + extract (PDF mode only) */}
        {form.answerKeyMode === "pdf" && (
          <div className="space-y-2">
            <PdfUploadZone
              label="Answer Key PDF"
              hint="Upload your answer key — answers will be extracted automatically"
              currentUrl={form.answerKeyPdfUrl}
              uploadFn={uploadFn}
              onFile={(url) => setForm({ ...form, answerKeyPdfUrl: url })}
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
                ✓ {Object.keys(form.mcqAnswers).length} answers extracted — review and edit below
              </p>
            )}
          </div>
        )}

        {/* Answer Key Reference PDF — stored for archival viewing, not extraction */}
        <PdfUploadZone
          label="Answer Key Reference PDF (optional)"
          hint="Stored on server for teacher reference — not used for extraction"
          currentUrl={form.answerKeyRefUrl}
          uploadFn={uploadFn}
          onFile={(url) => setForm({ ...form, answerKeyRefUrl: url })}
        />

        {/* Physical Answer Sheet Reference — the teacher's filled sheet */}
        <PdfUploadZone
          label="Answer Sheet Reference PDF (optional)"
          hint="Upload your completed answer sheet for future reference"
          currentUrl={form.answerSheetRefUrl}
          uploadFn={uploadFn}
          onFile={(url) => setForm({ ...form, answerSheetRefUrl: url })}
        />

      </div>

      {/* ── MCQ answer grid ───────────────────────────────────────────────── */}
      {form.mcqCount > 0 && <div>
        <h4 className="text-sm font-semibold text-gray-700 mb-1">
          MCQ Answers {form.answerKeyMode === "pdf" ? "(extracted — confirm or edit)" : "(enter manually)"}
        </h4>
        <p className="text-xs text-gray-400 mb-3">
          Click one option for a single answer. Click multiple to set multi-answer (e.g. A + C).
          Over-filling earns zero marks.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {Array.from({ length: form.mcqCount }, (_, i) => {
            const qid = `Q${i + 1}`;
            const marks = form.uniformMcqMarks
              ? form.mcqMarks
              : (form.mcqQuestionMarks[qid] ?? form.mcqMarks);
            const selected = form.mcqAnswers[qid] ? form.mcqAnswers[qid].split(",") : [];
            const isMulti = selected.length > 1;
            return (
              <div key={qid} className={`flex items-center gap-2 rounded-lg px-3 py-2 border
                ${isMulti ? "bg-amber-50 border-amber-200" : "bg-gray-50 border-transparent"}`}>
                <span className="text-xs font-medium text-gray-500 w-8">{qid}</span>
                <span className="text-xs text-gray-400 w-8">[{marks}m]</span>
                <div className="flex gap-1">
                  {MCQ_OPTIONS.map((opt) => {
                    const active = selected.includes(opt);
                    return (
                      <button
                        key={opt}
                        type="button"
                        onClick={() => toggleMcqOption(qid, opt)}
                        className={`w-8 h-8 rounded-lg text-sm font-semibold transition-colors
                          ${active
                            ? isMulti
                              ? "bg-amber-500 text-white"
                              : "bg-green-600 text-white"
                            : "bg-white border border-gray-300 text-gray-600 hover:border-green-300"}`}
                      >
                        {opt}
                      </button>
                    );
                  })}
                </div>
                {isMulti && (
                  <span className="text-xs text-amber-600 font-medium ml-auto">multi</span>
                )}
              </div>
            );
          })}
        </div>
      </div>}

      {/* ── Numerical answer grid ─────────────────────────────────────────── */}
      {isType2 && form.numericalCount > 0 && (
        <div className="space-y-3">

          {/* Convention guidance banner */}
          <div className="rounded-xl bg-blue-50 border border-blue-200 px-4 py-3 text-xs text-blue-800 space-y-1">
            <p className="font-semibold">📋 Answer Sheet Convention for Students</p>
            <p>Students write answers in the following order on their sheet:</p>
            <ol className="list-decimal list-inside space-y-0.5 pl-1">
              {form.mcqCount > 0 && <li><strong>MCQ section first</strong> — circles / letters for Q1, Q2, Q3 …</li>}
              <li><strong>Numerical section</strong> — numbers for N1, N2, N3 …</li>
            </ol>
            <p className="text-blue-600">
              The system extracts them section by section — students do not need to write labels.
            </p>
          </div>

          <h4 className="text-sm font-semibold text-gray-700">Numerical Answers</h4>
          <p className="text-xs text-gray-400">
            List every accepted form of each answer. Exact match against any one value earns full marks.
            You are responsible for adding all valid variants (e.g. both <code>3</code> and <code>3.0</code>).
          </p>

          <div className="space-y-3">
            {Array.from({ length: form.numericalCount }, (_, i) => {
              const qid   = `N${i + 1}`;
              const marks = form.uniformNumericalMarks
                ? form.numericalMarks
                : (form.numericalQuestionMarks[qid] ?? form.numericalMarks);
              const ans     = form.numericalAnswers[qid] ?? { mode: "single", values: [""] };
              const isMulti = ans.mode === "multiple";

              const setMode = (mode) => {
                const values = mode === "single"
                  ? [ans.values[0] ?? ""]
                  : (ans.values.length >= 2 ? ans.values : [...ans.values, ""]);
                setNumericalAnswer(qid, { mode, values });
              };
              const setValue = (idx, val) => {
                const next = [...ans.values];
                next[idx] = val;
                setNumericalAnswer(qid, { values: next });
              };
              const addValue    = () => setNumericalAnswer(qid, { values: [...ans.values, ""] });
              const removeValue = (idx) => {
                if (ans.values.length <= 1) return;
                setNumericalAnswer(qid, { values: ans.values.filter((_, j) => j !== idx) });
              };

              return (
                <div key={qid} className="bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 space-y-2">
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-semibold text-green-600 w-8">{qid}</span>
                    <span className="text-xs text-gray-400">[{marks}m]</span>
                    <select
                      value={ans.mode}
                      onChange={(e) => setMode(e.target.value)}
                      className="ml-auto text-xs border border-gray-300 rounded-lg px-2 py-1 focus:outline-none focus:ring-1 focus:ring-green-400"
                    >
                      <option value="single">Single answer</option>
                      <option value="multiple">Multiple accepted answers</option>
                    </select>
                  </div>

                  <div className="space-y-1.5">
                    {ans.values.map((val, idx) => (
                      <div key={idx} className="flex items-center gap-2">
                        {isMulti && (
                          <span className="text-xs text-gray-400 w-4">{idx + 1}.</span>
                        )}
                        <input
                          type="text"
                          value={val}
                          onChange={(e) => setValue(idx, e.target.value)}
                          placeholder={isMulti ? `Accepted answer ${idx + 1}` : "Answer (e.g. 3.5)"}
                          className="flex-1 text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-green-400"
                        />
                        {isMulti && ans.values.length > 1 && (
                          <button
                            type="button"
                            onClick={() => removeValue(idx)}
                            className="text-xs text-red-400 hover:text-red-600 px-1"
                          >✕</button>
                        )}
                      </div>
                    ))}
                  </div>

                  {isMulti && (
                    <button
                      type="button"
                      onClick={addValue}
                      className="text-xs text-green-500 hover:text-green-700 font-medium"
                    >
                      + Add accepted answer
                    </button>
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

// ── Rubric preview card (per question, read-only) ─────────────────────────────

function RubricPreviewCard({ rubric, questionText, index }) {
  const concepts   = rubric?.key_concepts        ?? [];
  const mandatory  = rubric?.mandatory_concepts  ?? [];
  const mpc        = rubric?.marks_per_concept   ?? 1;
  const modelSnip  = (rubric?.model_answer ?? "").slice(0, 120);

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-green-700">S{index + 1}</span>
        <span className="text-xs text-gray-400">{mpc} mark{mpc !== 1 ? "s" : ""} per concept</span>
      </div>
      {questionText && (
        <p className="text-xs text-gray-700 font-medium">{questionText.slice(0, 100)}{questionText.length > 100 ? "…" : ""}</p>
      )}
      {concepts.length > 0 ? (
        <div className="flex flex-wrap gap-1.5">
          {concepts.map((c) => (
            <span
              key={c}
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium
                ${mandatory.includes(c) ? "bg-green-100 text-green-700" : "bg-gray-200 text-gray-600"}`}
            >
              {mandatory.includes(c) && <span title="mandatory">★</span>}
              {c}
            </span>
          ))}
        </div>
      ) : (
        <p className="text-xs text-gray-400 italic">No concepts extracted for this question.</p>
      )}
      {modelSnip && (
        <p className="text-xs text-gray-500 border-t border-gray-200 pt-2">
          <span className="font-medium text-gray-600">Model answer: </span>
          {modelSnip}{(rubric?.model_answer ?? "").length > 120 ? "…" : ""}
        </p>
      )}
    </div>
  );
}


// ── Step 4: Configuration ─────────────────────────────────────────────────────

function Step4({ form, setForm, uploadFn, extractRubricFn, extractingRubric }) {
  const isType3  = form.type === "mcq_numerical_subjective";
  const hasMcq   = form.mcqCount > 0;
  const cfg      = form.config;

  const setConfig = (patch) => setForm({ ...form, config: { ...cfg, ...patch } });

  const toggleNegativeQuestion = (qid) => {
    const qs = cfg.negativeMarkingQuestions ?? [];
    const next = qs.includes(qid) ? qs.filter((q) => q !== qid) : [...qs, qid];
    setConfig({ negativeMarkingQuestions: next });
  };

  const handleExtractRubric = async () => {
    const result = await extractRubricFn({
      detailedAnswerUrl: form.detailedAnswerPdfUrl,
      gradeRubricUrl:    form.gradeRubricPdfUrl,
      subjectiveCount:   form.subjectiveCount,
    });
    if (result) {
      setForm({
        ...form,
        subjectiveQuestions:        result.subjective_questions,
        subjectiveRubrics:          result.subjective_rubrics,
        subjectivePromptTemplates:  result.subjective_prompt_templates ?? [],
      });
    }
  };

  const rubricReady = form.subjectiveRubrics?.length > 0 &&
    form.subjectiveRubrics.some(r => (r?.key_concepts ?? []).length > 0);

  return (
    <div className="space-y-5 max-h-[60vh] overflow-y-auto pr-1">

      {/* ── Type 3: PDF-based rubric setup ───────────────────────────────── */}
      {isType3 && (
        <div className="space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-1">Rubric Setup</h3>
            <p className="text-xs text-gray-500">
              Upload your model answer and marking scheme. The system will automatically
              extract the rubric for each of your {form.subjectiveCount} subjective question(s).
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <p className="text-xs font-medium text-gray-600">Detailed Answer PDF</p>
              <p className="text-xs text-gray-400">Full model answer for each subjective question</p>
              <PdfUploadZone
                label="Detailed Answer"
                hint="Upload model answer document"
                currentUrl={form.detailedAnswerPdfUrl}
                uploadFn={uploadFn}
                onFile={(url) => setForm({ ...form, detailedAnswerPdfUrl: url })}
              />
            </div>
            <div className="space-y-1">
              <p className="text-xs font-medium text-gray-600">Grade Rubric PDF</p>
              <p className="text-xs text-gray-400">Marking scheme with key concepts and marks</p>
              <PdfUploadZone
                label="Grade Rubric"
                hint="Upload marking scheme document"
                currentUrl={form.gradeRubricPdfUrl}
                uploadFn={uploadFn}
                onFile={(url) => setForm({ ...form, gradeRubricPdfUrl: url })}
              />
            </div>
          </div>

          <Button
            onClick={handleExtractRubric}
            loading={extractingRubric}
            disabled={!form.detailedAnswerPdfUrl || !form.gradeRubricPdfUrl || extractingRubric}
            variant="secondary"
            className="w-full"
          >
            {extractingRubric ? "Extracting rubric from PDFs…" : "Extract Rubric from PDFs"}
          </Button>

          {/* Extracted rubric preview */}
          {rubricReady && (
            <div className="space-y-2">
              <p className="text-xs font-semibold text-green-700">
                Rubric extracted — {form.subjectiveRubrics.filter(r => (r?.key_concepts ?? []).length > 0).length}/{form.subjectiveCount} question(s) processed
              </p>
              {Array.from({ length: form.subjectiveCount }, (_, i) => (
                <RubricPreviewCard
                  key={i}
                  index={i}
                  rubric={form.subjectiveRubrics?.[i]}
                  questionText={form.subjectiveQuestions?.[i]}
                />
              ))}
            </div>
          )}

          {!rubricReady && form.subjectiveRubrics?.length > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 text-xs text-amber-700">
              Extraction completed but no concepts were found. Check that your PDFs contain readable text (not scanned images).
              You can still create the paper — evaluation will use keyword fallback.
            </div>
          )}

          <div className="border-t border-gray-100 pt-3" />
        </div>
      )}

      {/* ── Negative marking (MCQ only, shown when paper has MCQ questions) ─ */}
      {hasMcq && (
        <>
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
            <div>
              <p className="text-sm font-medium text-gray-700">Negative Marking</p>
              <p className="text-xs text-gray-400">Deduct marks for wrong MCQ answers</p>
            </div>
            <button
              type="button"
              onClick={() => setConfig({ negativeMaking: !cfg.negativeMaking })}
              className={`w-12 h-6 rounded-full transition-colors relative ${cfg.negativeMaking ? "bg-green-600" : "bg-gray-300"}`}
            >
              <span className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform
                ${cfg.negativeMaking ? "translate-x-6" : "translate-x-0"}`} />
            </button>
          </div>

          {cfg.negativeMaking && (
            <div className="space-y-4 pl-1">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Marks deducted per wrong answer</label>
                <input
                  type="number" min="0.25" step="0.25"
                  value={cfg.marksDeducted ?? 0.5}
                  onChange={(e) => setConfig({ marksDeducted: parseFloat(e.target.value) || 0.25 })}
                  className="w-24 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-400"
                />
              </div>

              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-700">Apply negative marking to:</p>
                <div className="flex gap-2">
                  {[
                    { value: "all", label: "All MCQ Questions" },
                    { value: "per_question", label: "Specific Questions" },
                  ].map((opt) => (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => setConfig({ negativeMarkingScope: opt.value, negativeMarkingQuestions: [] })}
                      className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium border-2 transition-all
                        ${cfg.negativeMarkingScope === opt.value
                          ? "border-green-500 bg-green-50 text-green-700"
                          : "border-gray-200 text-gray-500 hover:border-gray-300"}`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>

                {cfg.negativeMarkingScope === "per_question" && (
                  <div className="space-y-2">
                    <div className="flex gap-3">
                      <button
                        type="button"
                        onClick={() => setConfig({ negativeMarkingQuestions: Array.from({ length: form.mcqCount }, (_, i) => `Q${i + 1}`) })}
                        className="text-xs text-green-600 hover:underline"
                      >
                        Select all
                      </button>
                      <button
                        type="button"
                        onClick={() => setConfig({ negativeMarkingQuestions: [] })}
                        className="text-xs text-gray-500 hover:underline"
                      >
                        Clear all
                      </button>
                    </div>
                    <div className="grid grid-cols-4 sm:grid-cols-6 gap-2">
                      {Array.from({ length: form.mcqCount }, (_, i) => {
                        const qid = `Q${i + 1}`;
                        const checked = (cfg.negativeMarkingQuestions ?? []).includes(qid);
                        return (
                          <label
                            key={qid}
                            className={`flex flex-col items-center gap-1 p-2 rounded-lg border cursor-pointer transition-colors
                              ${checked ? "border-red-300 bg-red-50" : "border-gray-200 bg-white hover:border-red-200"}`}
                          >
                            <span className="text-xs text-gray-500">{qid}</span>
                            <input
                              type="checkbox"
                              checked={checked}
                              onChange={() => toggleNegativeQuestion(qid)}
                              className="rounded border-gray-300 text-red-500 focus:ring-red-400"
                            />
                          </label>
                        );
                      })}
                    </div>
                    {(cfg.negativeMarkingQuestions ?? []).length > 0 && (
                      <p className="text-xs text-red-500">
                        Negative marking applies to: {cfg.negativeMarkingQuestions.join(", ")}
                      </p>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      )}

      {/* Message when Type 3 has no MCQ (nothing to configure beyond rubric) */}
      {isType3 && !hasMcq && (
        <p className="text-xs text-gray-400 text-center py-2">
          No MCQ questions — negative marking not applicable.
        </p>
      )}
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

  const cfg = form.config;

  const Row = ({ label, value }) => (
    <div className="flex justify-between py-2 border-b border-gray-100 last:border-0">
      <span className="text-sm text-gray-500">{label}</span>
      <span className="text-sm font-medium text-gray-800">{value}</span>
    </div>
  );

  const negMarkingSummary = () => {
    if (!cfg.negativeMaking) return "No";
    const base = `Yes (−${cfg.marksDeducted ?? 0.5}/wrong)`;
    if (cfg.negativeMarkingScope === "per_question") {
      const qs = cfg.negativeMarkingQuestions ?? [];
      return qs.length > 0 ? `${base} — ${qs.join(", ")}` : `${base} — no questions selected`;
    }
    return `${base} — all questions`;
  };

  return (
    <div className="space-y-4">
      <div className="bg-gray-50 rounded-xl p-4">
        <Row label="Paper Name" value={form.name || "—"} />
        <Row label="Subject" value={form.subject || "—"} />
        <Row label="Type" value={paperTypeLabel(form.type)} />
        {form.mcqCount > 0 && <Row label="MCQ Questions" value={`${form.mcqCount} questions = ${mcqTotal(form)} marks`} />}
        {isType2 && form.numericalCount > 0 && <Row label="Numerical Questions" value={`${form.numericalCount} questions = ${numericalTotal(form)} marks`} />}
        {isType3 && <Row label="Subjective Questions" value={`${form.subjectiveCount} questions = ${subjectiveTotal(form)} marks`} />}
        <Row label="Total Marks" value={<span className="text-green-600 font-bold">{total}</span>} />
        <Row label="Negative Marking" value={negMarkingSummary()} />
        {form.mcqCount > 0 && <Row label="MCQ Answers set" value={`${Object.keys(form.mcqAnswers).length} / ${form.mcqCount}`} />}
        {isType2 && form.numericalCount > 0 && (
          <Row
            label="Numerical Answers set"
            value={`${Object.values(form.numericalAnswers).filter(a => (a.values ?? []).some(v => v.trim())).length} / ${form.numericalCount}`}
          />
        )}
        <Row label="Question Paper PDF" value={form.questionPaperUrl ? "✓ Uploaded" : "Not uploaded"} />
        <Row label="Answer Key PDF" value={(form.answerKeyPdfUrl || form.answerKeyRefUrl) ? "✓ Uploaded" : "Not uploaded"} />
        <Row label="Answer Sheet PDF" value={form.answerSheetRefUrl ? "✓ Uploaded" : "Not uploaded"} />
      </div>

      {/* Quick links to review uploaded PDFs before saving */}
      <div className="flex flex-wrap gap-2">
        {form.questionPaperUrl && (
          <button type="button" onClick={() => window.open(form.questionPaperUrl, "_blank")}
            className="flex-1 text-xs text-green-600 border border-green-200 rounded-lg py-2 hover:bg-green-50">
            📄 View Question Paper
          </button>
        )}
        {(form.answerKeyPdfUrl || form.answerKeyRefUrl) && (
          <button type="button" onClick={() => window.open(form.answerKeyRefUrl || form.answerKeyPdfUrl, "_blank")}
            className="flex-1 text-xs text-green-600 border border-green-200 rounded-lg py-2 hover:bg-green-50">
            📝 View Answer Key
          </button>
        )}
        {form.answerSheetRefUrl && (
          <button type="button" onClick={() => window.open(form.answerSheetRefUrl, "_blank")}
            className="flex-1 text-xs text-green-600 border border-green-200 rounded-lg py-2 hover:bg-green-50">
            📋 View Answer Sheet
          </button>
        )}
      </div>

      <p className="text-xs text-gray-400 text-center">Review above, then click "Create Paper" to save.</p>
    </div>
  );
}

// ── Initial form state ────────────────────────────────────────────────────────

const INITIAL = {
  type: null,
  name: "",
  subject: "",
  // MCQ
  mcqCount: 5,
  mcqMarks: 2,
  mcqQuestionMarks: {},
  uniformMcqMarks: true,         // true = all questions get same marks (default)
  // Numerical
  numericalCount: 3,
  numericalMarks: 5,
  numericalQuestionMarks: {},
  uniformNumericalMarks: true,
  // Subjective
  subjectiveCount: 2,
  subjectiveMarks: 10,
  subjectiveQuestionMarks: {},
  uniformSubjectiveMarks: true,
  // Answers
  mcqAnswers: {},
  numericalAnswers: {},
  subjectiveQuestions: [],
  subjectiveRubrics: [],
  subjectivePromptTemplates: [],
  // Configuration
  config: {
    negativeMaking: false,
    marksDeducted: 0.5,
    negativeMarkingScope: "all",       // "all" | "per_question"
    negativeMarkingQuestions: [],      // used when scope === "per_question"
  },
  // Answer key
  answerKeyMode: "manual",
  // Uploaded PDF server URLs (set by PdfUploadZone after upload)
  questionPaperUrl: null,
  answerKeyPdfUrl: null,
  answerKeyRefUrl: null,
  answerSheetRefUrl: null,
  // Type 3 rubric source PDFs
  detailedAnswerPdfUrl: null,
  gradeRubricPdfUrl: null,
};

// ── Main Wizard ───────────────────────────────────────────────────────────────

export default function CreatePaper() {
  const { user } = useAuthStore();
  const teacherSubject = user?.subject ?? "";

  const [step, setStep] = useState(1);
  const [form, setForm] = useState({ ...INITIAL, subject: teacherSubject });
  const [success, setSuccess] = useState(false);
  const { createPaper, loading } = useCreatePaper();
  const { upload: uploadFn } = useUploadPaperFile();
  const { extract: extractFn, extracting } = useExtractAnswers();
  const { extractRubric, extracting: extractingRubric } = useExtractRubric();
  const navigate = useNavigate();

  const canNext = () => {
    if (step === 1) return !!form.type;
    if (step === 2) {
      if (!form.name.trim()) return false;
      if (form.type === "mcq_numerical_subjective") return form.subjectiveCount > 0;
      return form.mcqCount > 0;
    }
    return true;
  };

  const handleSubmit = async () => {
    const isType2 = form.type === "mcq_numerical" || form.type === "mcq_numerical_subjective";
    const isType3 = form.type === "mcq_numerical_subjective";

    // Materialise per-question marks when using uniform mode
    let mcqQuestionMarks = form.mcqQuestionMarks;
    if (form.uniformMcqMarks) {
      mcqQuestionMarks = {};
      for (let i = 1; i <= form.mcqCount; i++) mcqQuestionMarks[`Q${i}`] = form.mcqMarks;
    }
    let numericalQuestionMarks = form.numericalQuestionMarks;
    if (form.uniformNumericalMarks) {
      numericalQuestionMarks = {};
      for (let i = 1; i <= form.numericalCount; i++) numericalQuestionMarks[`N${i}`] = form.numericalMarks;
    }
    let subjectiveQuestionMarks = form.subjectiveQuestionMarks;
    if (form.uniformSubjectiveMarks) {
      subjectiveQuestionMarks = {};
      for (let i = 1; i <= form.subjectiveCount; i++) subjectiveQuestionMarks[`S${i}`] = form.subjectiveMarks;
    }

    const totalMarks =
      mcqTotal(form) +
      (isType2 ? numericalTotal(form) : 0) +
      (isType3 ? subjectiveTotal(form) : 0);

    // Convert numerical answers from UI format { mode, values } to backend list format ["3","3.0"]
    const numericalAnswers = {};
    for (const [qid, ans] of Object.entries(form.numericalAnswers)) {
      const values = (ans.values ?? [ans.answer ?? ""])
        .map((v) => String(v).trim())
        .filter(Boolean);
      if (values.length > 0) numericalAnswers[qid] = values;
    }

    // Strip UI-only toggle fields before sending to backend
    const {
      uniformMcqMarks, uniformNumericalMarks, uniformSubjectiveMarks,
      ...paperData
    } = form;

    const paper = await createPaper({
      ...paperData,
      mcqQuestionMarks,
      numericalQuestionMarks,
      numericalAnswers,
      subjectiveQuestionMarks,
      totalMarks,
      typeLabel: paperTypeLabel(form.type),
    });

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
            {step === 2 && <Step2 form={form} setForm={setForm} uploadFn={uploadFn} />}
            {step === 3 && <Step3 form={form} setForm={setForm} uploadFn={uploadFn} extractFn={extractFn} extracting={extracting} />}
            {step === 4 && <Step4 form={form} setForm={setForm} uploadFn={uploadFn} extractRubricFn={extractRubric} extractingRubric={extractingRubric} />}
            {step === 5 && <Step5 form={form} />}
          </Card.Body>
          <Card.Footer className="flex justify-between">
            <Button variant="secondary" onClick={() => setStep((s) => s - 1)} disabled={step === 1}>
              ← Back
            </Button>
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
            Successfully created <strong>{form.name}</strong>.
          </p>
          <p className="text-sm text-gray-500 mt-2">Students can now upload their answer sheets for evaluation.</p>
        </div>
      </Modal>
    </PageWrapper>
  );
}
