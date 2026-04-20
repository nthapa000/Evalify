// student/Submission.jsx — student uploads their answer sheet for evaluation.
//
// Flow:
//   Step 1 — student picks sheet type:
//               "omr"         → standard bubble/OMR sheet (OpenCV engine)
//               "handwritten" → written text answers (TrOCR engine)
//   Step 2 — student uploads the image file.
//   After submit — polls status every 2s, auto-redirects to Result page.

import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useSubmitAnswerSheet, useSubmissionStatus } from "../../hooks/useSubmission";
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
      {/* Drop target */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`cursor-pointer rounded-xl border-2 border-dashed p-6 text-center transition-colors
          ${dragging ? "border-indigo-400 bg-indigo-50" : "border-gray-300 hover:border-indigo-300 hover:bg-gray-50"}`}
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
          <div className="w-12 h-12 rounded-full bg-indigo-100 flex items-center justify-center text-2xl">🖼️</div>
          <p className="text-sm font-medium text-gray-700">
            {files.length === 0 ? "Add answer sheet image(s)" : "Add another page"}
          </p>
          <p className="text-xs text-gray-400">PNG or JPG only · Drag & drop or click · Max 10 MB each</p>
        </div>
      </div>

      {/* Thumbnails */}
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
              <div className="absolute top-1 left-1 bg-indigo-600 text-white text-xs font-bold px-1.5 py-0.5 rounded">
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
          ? "border-indigo-500 bg-indigo-50 shadow-sm"
          : "border-gray-200 bg-white hover:border-indigo-300 hover:bg-gray-50"
        }
      `}
    >
      {/* Icon + title row */}
      <div className="flex items-center gap-3 mb-2">
        <span className="text-3xl">{info.icon}</span>
        <div>
          <p className={`font-semibold text-sm ${isSelected ? "text-indigo-700" : "text-gray-800"}`}>
            {info.title}
          </p>
          <p className="text-xs text-gray-500">{info.subtitle}</p>
        </div>
        {/* Selection indicator */}
        <div className={`ml-auto w-5 h-5 rounded-full border-2 flex items-center justify-center
          ${isSelected ? "border-indigo-500 bg-indigo-500" : "border-gray-300"}`}>
          {isSelected && <span className="text-white text-xs">✓</span>}
        </div>
      </div>

      {/* Description bullets */}
      <ul className="space-y-1 mt-3 pl-1">
        {info.bullets.map((b) => (
          <li key={b} className="text-xs text-gray-500 flex gap-1.5">
            <span className={isSelected ? "text-indigo-400" : "text-gray-400"}>•</span>
            {b}
          </li>
        ))}
      </ul>

      {/* Engine badge */}
      <div className={`mt-3 inline-block text-xs px-2 py-0.5 rounded-full font-mono
        ${isSelected ? "bg-indigo-100 text-indigo-700" : "bg-gray-100 text-gray-500"}`}>
        Engine: {info.engine}
      </div>
    </button>
  );
}

// Static metadata for each sheet type
const SHEET_TYPES = {
  omr: {
    icon: "⭕",
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
    icon: "✍️",
    title: "Handwritten Answer Sheet",
    subtitle: "Written text responses (e.g. '1. A  2. C')",
    engine: "TrOCR (Handwriting OCR)",
    bullets: [
      "Write answers as: Q1. A   Q2. C   3. B …",
      "One answer per line for best recognition",
      "System uses AI handwriting recognition (TrOCR)",
    ],
  },
};

// ── Main page ─────────────────────────────────────────────────────────────────

export default function Submission() {
  const { paperId } = useParams();
  const navigate    = useNavigate();
  const { submit, loading } = useSubmitAnswerSheet();

  // Step 1: choose sheet type  |  Step 2: upload files
  const [step, setStep]           = useState(1);
  const [sheetType, setSheetType] = useState("omr");
  const [files, setFiles]         = useState([]);   // array of File objects
  const [submissionId, setSubmissionId] = useState(null);

  // Poll for evaluation status after submission
  const { status } = useSubmissionStatus(submissionId);

  // Auto-navigate to result page when evaluation completes
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
          <div className="text-6xl mb-4 animate-bounce">⏳</div>
          <h2 className="text-xl font-bold text-gray-800">Evaluating Your Answer Sheet</h2>
          <p className="text-gray-500 text-sm mt-2">
            {sheetType === "omr"
              ? "Detecting filled bubbles with computer vision…"
              : "Reading your handwriting with TrOCR…"
            }
          </p>
          <p className="text-xs text-indigo-500 mt-1 font-mono">
            Engine: {SHEET_TYPES[sheetType].engine}
          </p>
          {/* Animated dots */}
          <div className="flex justify-center gap-1.5 mt-6">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="w-2.5 h-2.5 bg-indigo-400 rounded-full animate-pulse"
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
        <Link to="/student/dashboard" className="text-sm text-indigo-600 hover:underline mb-4 inline-block">
          ← Back to Dashboard
        </Link>

        <div className="max-w-xl mx-auto">
          <h1 className="text-2xl font-bold text-gray-800 mb-1">Upload Answer Sheet</h1>
          <p className="text-sm text-gray-500 mb-6">
            First, tell us what kind of answer sheet you wrote on so we can use the right AI model.
          </p>

          {/* Step indicator */}
          <div className="flex items-center gap-2 mb-6">
            <div className="w-6 h-6 rounded-full bg-indigo-600 text-white text-xs flex items-center justify-center font-bold">1</div>
            <span className="text-sm font-medium text-indigo-700">Choose Sheet Type</span>
            <div className="flex-1 h-px bg-gray-200 mx-2" />
            <div className="w-6 h-6 rounded-full bg-gray-200 text-gray-400 text-xs flex items-center justify-center font-bold">2</div>
            <span className="text-sm text-gray-400">Upload Image</span>
          </div>

          {/* Sheet type cards */}
          <div className="grid grid-cols-1 gap-4 mb-6">
            <SheetTypeCard type="omr"         selected={sheetType} onSelect={setSheetType} />
            <SheetTypeCard type="handwritten" selected={sheetType} onSelect={setSheetType} />
          </div>

          <Button className="w-full" onClick={() => setStep(2)}>
            Continue with {SHEET_TYPES[sheetType].title} →
          </Button>
        </div>
      </PageWrapper>
    );
  }

  // ── Step 2: file upload ───────────────────────────────────────────────────
  return (
    <PageWrapper>
      <Link to="/student/dashboard" className="text-sm text-indigo-600 hover:underline mb-4 inline-block">
        ← Back to Dashboard
      </Link>

      <div className="max-w-xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-800 mb-1">Upload Answer Sheet</h1>
        <p className="text-sm text-gray-500 mb-6">
          Upload a clear scan or photo of your answer sheet.
        </p>

        {/* Step indicator */}
        <div className="flex items-center gap-2 mb-6">
          <div className="w-6 h-6 rounded-full bg-indigo-100 text-indigo-600 text-xs flex items-center justify-center font-bold">✓</div>
          <span className="text-sm text-gray-400">Choose Sheet Type</span>
          <div className="flex-1 h-px bg-indigo-300 mx-2" />
          <div className="w-6 h-6 rounded-full bg-indigo-600 text-white text-xs flex items-center justify-center font-bold">2</div>
          <span className="text-sm font-medium text-indigo-700">Upload Image</span>
        </div>

        {/* Selected type reminder badge */}
        <div className="flex items-center gap-2 mb-4 bg-indigo-50 border border-indigo-200 rounded-lg px-4 py-2">
          <span className="text-xl">{SHEET_TYPES[sheetType].icon}</span>
          <div className="flex-1">
            <p className="text-sm font-semibold text-indigo-800">{SHEET_TYPES[sheetType].title}</p>
            <p className="text-xs text-indigo-500">Engine: {SHEET_TYPES[sheetType].engine}</p>
          </div>
          {/* Allow going back to change type */}
          <button
            type="button"
            onClick={() => { setStep(1); setFiles([]); }}
            className="text-xs text-indigo-600 hover:underline"
          >
            Change
          </button>
        </div>

        <Card>
          <Card.Body className="space-y-5">
            {/* Multi-image drop zone */}
            <MultiImageUpload files={files} onAdd={addFiles} onRemove={removeFile} />

            {/* Contextual tips per sheet type */}
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-700 space-y-1">
              <p className="font-semibold">
                {sheetType === "omr" ? "⭕ Tips for OMR sheets:" : "✍️ Tips for Handwritten sheets:"}
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
            <Button variant="secondary" onClick={() => setStep(1)}>← Back</Button>
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
