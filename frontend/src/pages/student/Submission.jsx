// student/Submission.jsx — student uploads their answer sheet for evaluation.
//
// Flow:
//   Step 1 — student picks sheet type (OMR only shown for MCQ-only papers)
//   Step 2 — student uploads the image file.
//   After submit — polls status every 2s, auto-redirects to Result page.

import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useSubmitAnswerSheet, useSubmissionStatus } from "../../hooks/useSubmission";
import { usePaperView } from "../../hooks/usePapers";
import PageWrapper from "../../components/layout/PageWrapper";
import Button from "../../components/ui/Button";
import Card from "../../components/ui/Card";

// ── Multi-image upload zone ───────────────────────────────────────────────────

function MultiImageUpload({ files, onAdd, onRemove }) {
  const inputRef = useRef();
  const [dragging, setDragging] = useState(false);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    onAdd(e.dataTransfer.files);
  };

  return (
    <div className="space-y-3">
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`cursor-pointer rounded-xl border-2 border-dashed p-6 text-center transition-colors
          ${dragging ? "border-green-400 bg-green-50" : "border-gray-300 hover:border-green-300 hover:bg-gray-50"}`}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/png,image/jpeg"
          multiple
          className="hidden"
          onChange={(e) => { onAdd(e.target.files); e.target.value = ""; }}
        />
        <div className="flex flex-col items-center gap-2">
          <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
            <svg className="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
          <p className="text-sm font-medium text-gray-700">
            {files.length === 0 ? "Add answer sheet image(s)" : "Add another page"}
          </p>
          <p className="text-xs text-gray-400">PNG or JPG only · Drag & drop or click · Max 10 MB each</p>
        </div>
      </div>

      {files.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {files.map((f, i) => (
            <div key={i} className="relative group rounded-lg overflow-hidden border border-gray-200 bg-gray-50">
              <img
                src={URL.createObjectURL(f)}
                alt={`Page ${i + 1}`}
                className="w-full h-28 object-cover"
              />
              <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors" />
              <div className="absolute top-1 left-1 bg-green-600 text-white text-xs font-bold px-1.5 py-0.5 rounded">
                P{i + 1}
              </div>
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); onRemove(i); }}
                className="absolute top-1 right-1 w-5 h-5 rounded-full bg-red-500 text-white text-xs flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
              >
                ×
              </button>
              <p className="text-xs text-gray-500 truncate px-2 py-1">{f.name}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Sheet type option card ────────────────────────────────────────────────────

function SheetTypeCard({ type, selected, onSelect }) {
  const info = SHEET_TYPES[type];
  const isSelected = selected === type;

  return (
    <button
      type="button"
      onClick={() => onSelect(type)}
      className={`
        w-full text-left rounded-xl border-2 p-5 transition-all
        ${isSelected
          ? "border-green-500 bg-green-50 shadow-sm"
          : "border-gray-200 bg-white hover:border-green-300 hover:bg-gray-50"
        }
      `}
    >
      <div className="flex items-center gap-3 mb-2">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center
          ${isSelected ? "bg-green-100" : "bg-gray-100"}`}>
          {info.icon}
        </div>
        <div>
          <p className={`font-semibold text-sm ${isSelected ? "text-green-700" : "text-gray-800"}`}>
            {info.title}
          </p>
          <p className="text-xs text-gray-500">{info.subtitle}</p>
        </div>
        <div className={`ml-auto w-5 h-5 rounded-full border-2 flex items-center justify-center
          ${isSelected ? "border-green-500 bg-green-500" : "border-gray-300"}`}>
          {isSelected && <span className="text-white text-xs">✓</span>}
        </div>
      </div>

      <ul className="space-y-1 mt-3 pl-1">
        {info.bullets.map((b) => (
          <li key={b} className="text-xs text-gray-500 flex gap-1.5">
            <span className={isSelected ? "text-green-400" : "text-gray-400"}>•</span>
            {b}
          </li>
        ))}
      </ul>

      <div className={`mt-3 inline-block text-xs px-2 py-0.5 rounded-full font-mono
        ${isSelected ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
        Engine: {info.engine}
      </div>
    </button>
  );
}

// Static metadata for each sheet type
const SHEET_TYPES = {
  omr: {
    icon: (
      <svg className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
      </svg>
    ),
    title: "OMR Bubble Sheet",
    subtitle: "Standard multiple-choice bubble form",
    engine: "OpenCV OMR",
    bullets: [
      "Fill the circles with pencil or dark pen",
      "Each row = one question (A B C D left-to-right)",
      "System uses computer vision to detect filled bubbles",
    ],
  },
  handwritten: {
    icon: (
      <svg className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
      </svg>
    ),
    title: "Handwritten Answer Sheet",
    subtitle: "Written text responses (e.g. Q1. A  Q2. C)",
    engine: "Ollama Vision",
    bullets: [
      "Write answers as: Q1. A   Q2. C   3. B …",
      "One answer per line for best recognition",
      "System uses AI vision model to read handwriting",
    ],
  },
};

// ── Main page ─────────────────────────────────────────────────────────────────

export default function Submission() {
  const { paperId } = useParams();
  const navigate    = useNavigate();
  const { submit, loading }       = useSubmitAnswerSheet();
  const { paper, loading: paperLoading } = usePaperView(paperId);

  // OMR is only available for MCQ-only (Type 1) papers
  const isOmrAllowed = paper?.type === "mcq";

  const [step, setStep]           = useState(1);
  const [sheetType, setSheetType] = useState("omr");
  const [files, setFiles]         = useState([]);
  const [submissionId, setSubmissionId] = useState(null);

  // Force handwritten when paper is not MCQ-only
  useEffect(() => {
    if (paper && paper.type !== "mcq") {
      setSheetType("handwritten");
    }
  }, [paper]);

  const { status } = useSubmissionStatus(submissionId);

  useEffect(() => {
    if (status === "evaluated" && submissionId) {
      navigate(`/student/results/${submissionId}`);
    }
  }, [status, submissionId, navigate]);

  const handleSubmit = async () => {
    if (files.length === 0) return;
    const sub = await submit(paperId, files, sheetType);
    if (sub) setSubmissionId(sub.id);
  };

  const addFiles = (newFiles) => {
    const imgs = Array.from(newFiles).filter(
      (f) => f.type === "image/png" || f.type === "image/jpeg"
    );
    setFiles((prev) => [...prev, ...imgs]);
  };

  const removeFile = (idx) =>
    setFiles((prev) => prev.filter((_, i) => i !== idx));

  // ── Evaluating state ──────────────────────────────────────────────────────
  if (submissionId) {
    return (
      <PageWrapper>
        <div className="max-w-md mx-auto mt-20 text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-green-100 flex items-center justify-center">
            <svg className="w-8 h-8 text-green-600 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-gray-800">Evaluating Your Answer Sheet</h2>
          <p className="text-gray-500 text-sm mt-2">
            {sheetType === "omr"
              ? "Detecting filled bubbles with computer vision…"
              : "Reading your handwriting with Ollama Vision…"
            }
          </p>
          <p className="text-xs text-green-500 mt-1 font-mono">
            Engine: {SHEET_TYPES[sheetType].engine}
          </p>
          <div className="flex justify-center gap-1.5 mt-6">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="w-2.5 h-2.5 bg-green-400 rounded-full animate-pulse"
                style={{ animationDelay: `${i * 0.2}s` }}
              />
            ))}
          </div>
          <p className="text-xs text-gray-400 mt-4">Status: {status}</p>
        </div>
      </PageWrapper>
    );
  }

  // ── Step 1: sheet type selection ─────────────────────────────────────────
  if (step === 1) {
    return (
      <PageWrapper>
        <Link to="/student/dashboard" className="text-sm text-green-600 hover:underline mb-4 inline-block">
          &larr; Back to Dashboard
        </Link>

        <div className="max-w-xl mx-auto">
          <h1 className="text-2xl font-bold text-gray-800 mb-1">Upload Answer Sheet</h1>
          <p className="text-sm text-gray-500 mb-6">
            {isOmrAllowed
              ? "Choose the type of answer sheet you used."
              : "This paper requires a handwritten answer sheet."}
          </p>

          {/* Step indicator */}
          <div className="flex items-center gap-2 mb-6">
            <div className="w-6 h-6 rounded-full bg-green-600 text-white text-xs flex items-center justify-center font-bold">1</div>
            <span className="text-sm font-medium text-green-700">Choose Sheet Type</span>
            <div className="flex-1 h-px bg-gray-200 mx-2" />
            <div className="w-6 h-6 rounded-full bg-gray-200 text-gray-400 text-xs flex items-center justify-center font-bold">2</div>
            <span className="text-sm text-gray-400">Upload Image</span>
          </div>

          {paperLoading ? (
            <div className="text-sm text-gray-400 text-center py-8">Loading paper details…</div>
          ) : (
            <div className="grid grid-cols-1 gap-4 mb-6">
              {isOmrAllowed && (
                <SheetTypeCard type="omr" selected={sheetType} onSelect={setSheetType} />
              )}
              <SheetTypeCard type="handwritten" selected={sheetType} onSelect={setSheetType} />
            </div>
          )}

          <Button className="w-full" onClick={() => setStep(2)} disabled={paperLoading}>
            Continue with {SHEET_TYPES[sheetType].title} &rarr;
          </Button>
        </div>
      </PageWrapper>
    );
  }

  // ── Step 2: file upload ───────────────────────────────────────────────────
  return (
    <PageWrapper>
      <Link to="/student/dashboard" className="text-sm text-green-600 hover:underline mb-4 inline-block">
        &larr; Back to Dashboard
      </Link>

      <div className="max-w-xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-800 mb-1">Upload Answer Sheet</h1>
        <p className="text-sm text-gray-500 mb-6">
          Upload a clear scan or photo of your answer sheet.
        </p>

        {/* Step indicator */}
        <div className="flex items-center gap-2 mb-6">
          <div className="w-6 h-6 rounded-full bg-green-100 text-green-600 text-xs flex items-center justify-center font-bold">✓</div>
          <span className="text-sm text-gray-400">Choose Sheet Type</span>
          <div className="flex-1 h-px bg-green-300 mx-2" />
          <div className="w-6 h-6 rounded-full bg-green-600 text-white text-xs flex items-center justify-center font-bold">2</div>
          <span className="text-sm font-medium text-green-700">Upload Image</span>
        </div>

        {/* Selected type reminder badge */}
        <div className="flex items-center gap-2 mb-4 bg-green-50 border border-green-200 rounded-lg px-4 py-2">
          <div className="w-8 h-8 rounded-lg bg-green-100 flex items-center justify-center">
            {SHEET_TYPES[sheetType].icon}
          </div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-green-800">{SHEET_TYPES[sheetType].title}</p>
            <p className="text-xs text-green-500">Engine: {SHEET_TYPES[sheetType].engine}</p>
          </div>
          {isOmrAllowed && (
            <button
              type="button"
              onClick={() => { setStep(1); setFiles([]); }}
              className="text-xs text-green-600 hover:underline"
            >
              Change
            </button>
          )}
        </div>

        <Card>
          <Card.Body className="space-y-5">
            <MultiImageUpload files={files} onAdd={addFiles} onRemove={removeFile} />

            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-700 space-y-1">
              <p className="font-semibold">
                {sheetType === "omr" ? "Tips for OMR sheets:" : "Tips for Handwritten sheets:"}
              </p>
              {sheetType === "omr" ? (
                <>
                  <p>• Take photo flat on a desk, directly overhead — no angle</p>
                  <p>• Use good even lighting, no shadows on the sheet</p>
                  <p>• If your sheet has multiple pages, add all pages in order</p>
                </>
              ) : (
                <>
                  <p>• Write each answer on its own line: "1. A"</p>
                  <p>• Write clearly and large enough to photograph</p>
                  <p>• Add additional pages if your answers span multiple sheets</p>
                </>
              )}
            </div>
          </Card.Body>

          <Card.Footer className="flex gap-3">
            {isOmrAllowed && (
              <Button variant="secondary" onClick={() => setStep(1)}>&larr; Back</Button>
            )}
            <Button
              onClick={handleSubmit}
              loading={loading}
              disabled={files.length === 0}
              className="flex-1"
            >
              Submit {files.length > 1 ? `${files.length} Pages` : ""} for Evaluation
            </Button>
          </Card.Footer>
        </Card>
      </div>
    </PageWrapper>
  );
}
