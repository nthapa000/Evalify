// AnswerKeyAssistant.jsx — optional: draft each subjective question's reference answer and rubric points from the
// teacher's own reference files (RAG). Every point cites the passage it came from; "Use this draft" copies it into
// the paper's rubric, where the teacher edits it. Drafts are never used to grade students.

import { useState } from "react";
import api from "../../services/api";
import Button from "../ui/Button";
import RubricBuilder from "./RubricBuilder";
import useToastStore from "../../store/toastStore";

export default function AnswerKeyAssistant({ count, questions = [], marks = [], rubrics = [], uploadFn, onUse, onRubricChange }) {
  const [files, setFiles] = useState([]);               // [{ name, url }]
  const [texts, setTexts] = useState(() => Array.from({ length: count }, (_, i) => questions[i] ?? ""));
  const [drafts, setDrafts] = useState(null);
  const [busy, setBusy] = useState(false);
  const { addToast } = useToastStore();

  // Upload each chosen file through the wizard's uploader and keep its server URL
  const addFiles = async (list) => {
    for (const f of Array.from(list)) {
      const url = await uploadFn(f);
      if (url) setFiles((prev) => [...prev, { name: f.name, url }]);
    }
  };

  // Ask the server for one cited draft per question
  const draft = async () => {
    setBusy(true);
    try {
      const { data } = await api.post("/papers/answer-key/draft", {
        reference_urls: files.map((f) => f.url), questions: texts, marks: texts.map((_, i) => Number(marks[i] ?? 1)) });
      setDrafts(data.drafts);
      if (data.skipped_pages?.length) addToast(`No text on: ${data.skipped_pages.join(", ")} (scanned pages are skipped).`, "info");
    } catch (e) {
      addToast(e.response?.data?.detail || "Could not draft the answer key.", "error");
    } finally {
      setBusy(false);
    }
  };

  const ready = files.length > 0 && texts.some((t) => t.trim());

  return (
    <section className="border border-paper-300 rounded-sm p-4 space-y-4 bg-paper-50">
      <div>
        <p className="kicker">Optional</p>
        <h3 className="font-serif text-lg text-paper-900">Draft the answer key from your notes</h3>
        <p className="text-xs text-paper-500">
          Upload your reference material; for each question a reference answer and rubric points are drafted from it,
          with the passage each point came from. You check and edit everything before saving. Drafts are never used to mark students.
        </p>
      </div>

      {/* Question texts (pre-filled when already extracted) */}
      <div className="space-y-2">
        {texts.map((t, i) => (
          <div key={i} className="flex items-baseline gap-3">
            <label htmlFor={`akq-${i}`} className="font-mono text-xs text-paper-500 w-8">S{i + 1}</label>
            <input id={`akq-${i}`} aria-label={`Question S${i + 1}`} value={t} placeholder="Question text"
              onChange={(e) => setTexts(texts.map((x, j) => (j === i ? e.target.value : x)))}
              className="flex-1 border-0 border-b border-paper-300 bg-transparent px-0 py-1 text-sm focus:outline-none focus:border-paper-900 focus:ring-0" />
            <span className="font-mono text-xs text-paper-400">{marks[i] ?? 1} marks</span>
          </div>
        ))}
      </div>

      {/* Reference files */}
      <div>
        <label htmlFor="ak-files" className="kicker block mb-1">Reference files (PDF with text, or .txt)</label>
        <input id="ak-files" type="file" multiple accept=".pdf,.txt" onChange={(e) => addFiles(e.target.files)} className="text-sm" />
        {files.length > 0 && (
          <ul className="mt-2 text-sm text-paper-700">{files.map((f) => <li key={f.url} className="font-mono text-xs">{f.name}</li>)}</ul>
        )}
      </div>

      <Button variant="secondary" onClick={draft} loading={busy} disabled={!ready}>Draft answer key</Button>

      {/* Drafts with citations */}
      {drafts && drafts.map((d, i) => (
        <article key={i} className="border-t border-paper-300 pt-3 space-y-2">
          <p className="text-sm text-paper-900"><span className="font-mono text-xs text-paper-500 mr-2">S{i + 1}</span>{d.question}</p>
          {!d.covered ? (
            <p className="text-sm text-ochre-700">Not covered by your material. {d.note}</p>
          ) : (
            <>
              <p className="text-sm text-paper-700"><span className="kicker mr-2">Reference</span>{d.model_answer}</p>
              <ol className="text-sm list-decimal ml-5 text-paper-900">{d.key_concepts.map((c) => <li key={c}>{c}</li>)}</ol>
              <p className="text-xs text-paper-500">{d.marks_per_concept} mark(s) per point</p>
              <div className="space-y-1">
                {d.citations.map((c) => (
                  <p key={c.n} className="text-xs text-paper-500 border-l-2 border-paper-300 pl-2">
                    [{c.n}] {c.source}, page {c.page}: “{c.text.slice(0, 160)}{c.text.length > 160 ? "…" : ""}”
                  </p>
                ))}
              </div>
              {d.note && <p className="text-xs text-ochre-700">Check: {d.note}</p>}
              <Button size="sm" aria-label={`Use this draft for S${i + 1}`}
                onClick={() => onUse(i, { question: d.question, rubric: {
                  key_concepts: d.key_concepts, mandatory_concepts: [], marks_per_concept: d.marks_per_concept,
                  model_answer: d.model_answer, rubric_source: "drafted from reference files, edited by teacher" } })}>
                Use this draft
              </Button>
            </>
          )}
        </article>
      ))}

      {/* Rubrics already set for the paper: edit them here */}
      {rubrics.map((r, i) => r && (r.key_concepts?.length > 0) && (
        <RubricBuilder key={`rb-${i}`} questionIndex={i} value={r} onChange={(v) => onRubricChange(i, v)} />
      ))}
    </section>
  );
}
