// ta/Review.jsx — one answer sheet in the TA view.
// Left: the student's full answer sheet. Right: the student's remark (re-evaluation tab), the teacher's
// question paper / answer key / solutions / rubric, and every question with the AI's mark and reason.
// The TA enters the final marks (only changed ones are sent) and an optional remark to the student.

import { useMemo, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import PageWrapper from "../../components/layout/PageWrapper";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Skeleton from "../../components/ui/Skeleton";
import AnswerSheetViewer from "../../components/AnswerSheetViewer";
import { useTaItem, useSubmitTaMarks } from "../../hooks/useTa";

// Teacher-uploaded documents shown as links (only those that exist)
const DOCS = [
  ["questionPaperUrl", "Question paper"], ["answerKeyRefUrl", "Answer key"], ["answerKeyPdfUrl", "Answer key (PDF)"],
  ["answerSheetRefUrl", "Reference solution"], ["detailedAnswerPdfUrl", "Detailed answers"],
  ["gradeRubricPdfUrl", "Grading rubric (PDF)"],
];

// Answer key, numerical keys and subjective rubrics from the paper
function PaperMaterials({ paper }) {
  if (!paper) return null;
  const docs = DOCS.filter(([k]) => paper[k]);
  const num = Object.entries(paper.numericalAnswers || {});
  return (
    <Card>
      <Card.Header><h2 className="font-semibold text-gray-700">Paper: {paper.name}</h2></Card.Header>
      <Card.Body className="space-y-4 text-sm">
        {docs.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {docs.map(([k, label]) => (
              <a key={k} href={paper[k]} target="_blank" rel="noreferrer"
                 className="px-3 py-1.5 rounded-lg border border-green-200 bg-green-50 text-green-700 hover:bg-green-100">
                {label}
              </a>
            ))}
          </div>
        )}
        {/* MCQ key */}
        {Object.keys(paper.mcqAnswers || {}).length > 0 && (
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase mb-1">MCQ answer key</p>
            <div className="flex flex-wrap gap-2">
              {Object.entries(paper.mcqAnswers).map(([q, a]) => (
                <span key={q} className="px-2 py-0.5 rounded bg-gray-100 text-gray-700">{q}: <b>{a}</b></span>
              ))}
            </div>
          </div>
        )}
        {/* Numerical key: value ± tolerance (unit shown, not graded) */}
        {num.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Numerical answer key</p>
            {num.map(([q, k]) => (
              <p key={q}>{q}: <b>{typeof k === "object" && !Array.isArray(k) ? `${k.answer} ${k.unit || ""}`.trim() : String(k)}</b>
                {k?.tolerance ? <span className="text-gray-400"> (±{k.tolerance})</span> : null}</p>
            ))}
          </div>
        )}
        {/* Subjective: question, rubric points, model answer */}
        {(paper.subjectiveRubrics || []).map((r, i) => (
          <div key={i} className="border-t border-gray-100 pt-3">
            <p className="font-medium text-gray-800">S{i + 1}. {paper.subjectiveQuestions?.[i]}</p>
            <ul className="list-disc ml-5 text-gray-600">
              {(r.key_concepts || []).map((c) => <li key={c}>{c}</li>)}
            </ul>
            {r.model_answer && <p className="text-gray-500 mt-1"><span className="text-xs uppercase">Reference:</span> {r.model_answer}</p>}
          </div>
        ))}
      </Card.Body>
    </Card>
  );
}

const fmt = (n) => (n === null || n === undefined ? "—" : Number(n).toString());

export default function TaReview() {
  const { submissionId } = useParams();
  const [params] = useSearchParams();
  const tab = params.get("tab") === "reevaluation" ? "reevaluation" : "flagged";
  const navigate = useNavigate();
  const { data, loading } = useTaItem(submissionId);
  const { submit, saving } = useSubmitTaMarks();
  const [edits, setEdits] = useState({});
  const [remark, setRemark] = useState("");

  // Validation: every edited mark must be a number between 0 and the question's maximum
  const errors = useMemo(() => {
    const out = {};
    for (const q of data?.questions || []) {
      if (!(q.question in edits)) continue;
      const v = edits[q.question];
      if (v === "" || isNaN(Number(v)) || Number(v) < 0 || Number(v) > q.marks_available) {
        out[q.question] = `Marks must be between 0 and ${q.marks_available}`;
      }
    }
    return out;
  }, [edits, data]);

  // Only send marks that differ from the current ones
  const onSubmit = async () => {
    const marks = {};
    for (const q of data.questions) {
      if (q.question in edits && Number(edits[q.question]) !== Number(q.marks_earned)) marks[q.question] = Number(edits[q.question]);
    }
    if (await submit(submissionId, { tab, marks, remark: remark.trim() })) navigate("/ta/dashboard");
  };

  if (loading || !data) {
    return <PageWrapper><Skeleton className="h-8 w-64 mb-4" /><Skeleton className="h-96 w-full" /></PageWrapper>;
  }
  const { submission, paper, questions, reevaluation } = data;

  return (
    <PageWrapper>
      <Link to="/ta/dashboard" className="text-sm text-green-600 hover:underline mb-3 inline-block">&larr; Back to review queue</Link>
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <h1 className="text-2xl font-bold text-gray-800">{submission.student_name}</h1>
        <span className="text-sm text-gray-500">{submission.roll_no}</span>
        <Badge variant={tab === "flagged" ? "warning" : "info"}>{tab === "flagged" ? "Flagged by AI" : "Re-evaluation request"}</Badge>
        <span className="text-sm text-gray-500">AI score {fmt(submission.result?.totalScore)} / {fmt(submission.result?.maxScore)}</span>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Left: the full answer sheet */}
        <div className="xl:sticky xl:top-0 xl:max-h-[calc(100vh-8rem)] xl:overflow-y-auto">
          <AnswerSheetViewer submissionId={submissionId} />
        </div>

        {/* Right: remark, materials, questions, submit */}
        <div className="space-y-4">
          {tab === "reevaluation" && reevaluation && (
            <Card>
              <Card.Body>
                <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Student's remark</p>
                <p className="text-gray-800 whitespace-pre-wrap">{reevaluation.remark}</p>
              </Card.Body>
            </Card>
          )}

          <PaperMaterials paper={paper} />

          <Card>
            <Card.Header><h2 className="font-semibold text-gray-700">Questions — AI marks and your final marks</h2></Card.Header>
            <Card.Body className="space-y-3">
              {questions.map((q) => (
                <div key={q.question}
                     className={`rounded-lg border p-3 ${q.needs_review ? "border-amber-300 bg-amber-50" : "border-gray-100"}`}>
                  <div className="flex flex-wrap items-start gap-3">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-800">{q.question}{q.question_text ? ` — ${q.question_text}` : ""}</p>
                      <p className="text-sm text-gray-600">Student: <span className="font-mono">{q.student_answer ?? "—"}</span>
                        {q.correct_answer ? <span className="text-gray-400"> · key {q.correct_answer}</span> : null}</p>
                      {/* The AI's one-line reason for flagging */}
                      {q.review_reason && <p className="text-sm text-amber-700">{q.review_reason}</p>}
                      {/* Subjective: rubric point verdicts with the student's words as evidence */}
                      {(q.concepts || []).map((c) => (
                        <p key={c.concept} className="text-xs text-gray-500">
                          {c.present ? "✔" : c.partial ? "½" : "✘"} {c.concept}{c.evidence ? ` — “${c.evidence}”` : ""}
                        </p>
                      ))}
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-gray-400">AI: {fmt(q.marks_earned)} / {fmt(q.marks_available)}</p>
                      <label className="sr-only" htmlFor={`m-${q.question}`}>Marks for {q.question}</label>
                      <input id={`m-${q.question}`} aria-label={`Marks for ${q.question}`} type="number" step="0.5" min="0"
                        max={q.marks_available} value={q.question in edits ? edits[q.question] : q.marks_earned}
                        onChange={(e) => setEdits({ ...edits, [q.question]: e.target.value })}
                        className="w-20 border border-gray-300 rounded-lg px-2 py-1 text-sm text-right" />
                    </div>
                  </div>
                  {errors[q.question] && <p className="text-xs text-red-600 mt-1">{q.question}: {errors[q.question]}</p>}
                </div>
              ))}
            </Card.Body>
          </Card>

          <Card>
            <Card.Body className="space-y-3">
              <label htmlFor="ta-remark" className="block text-sm font-medium text-gray-700">Remark to the student (optional)</label>
              <textarea id="ta-remark" rows={3} value={remark} onChange={(e) => setRemark(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" placeholder="e.g. Your example was accepted." />
              <Button onClick={onSubmit} loading={saving} disabled={Object.keys(errors).length > 0} className="w-full">
                Submit re-evaluated marks
              </Button>
              <p className="text-xs text-gray-400">Marks you submit are final. Leave a mark unchanged to keep the AI's mark.</p>
            </Card.Body>
          </Card>
        </div>
      </div>
    </PageWrapper>
  );
}
