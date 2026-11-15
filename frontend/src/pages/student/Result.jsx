// student/Result.jsx — shows the evaluation result for a completed submission.

import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useResult, useRequestReevaluation } from "../../hooks/useSubmission";
import useAuthStore from "../../store/authStore";
import PageWrapper from "../../components/layout/PageWrapper";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Skeleton from "../../components/ui/Skeleton";
import Button from "../../components/ui/Button";
import ScoreMark from "../../components/ui/ScoreMark";
import StatLedger from "../../components/ui/StatLedger";
import { formatDateTime, formatPercent } from "../../utils/formatters";

// One "label …… value" line in the section breakdown
function Row({ label, value }) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-gray-100">
      <span className="text-sm text-gray-600">{label}</span>
      <span className="font-semibold text-gray-800">{value}</span>
    </div>
  );
}

// Marks without trailing zeros: 1, 0.5, 2.5
const fmt = (n) => (n === null || n === undefined ? "—" : Number(n).toString());
const ROLE = { ta: "TA", teacher: "Teacher" };

// Every question with the student's answer and marks (shows updated marks after re-evaluation)
function QuestionMarks({ data }) {
  const rows = [...(data.mcqDetail || []), ...(data.numericalDetail || []), ...(data.subjectiveDetail || [])];
  if (!rows.length) return null;
  return (
    <Card className="mt-6">
      <Card.Header><h2 className="text-base font-semibold text-gray-700">Question-wise marks</h2></Card.Header>
      <Card.Body className="divide-y divide-gray-100">
        {rows.map((r) => (
          <div key={r.question} data-testid={`q-row-${r.question}`} className="py-2 flex items-start gap-4">
            <span className="w-10 font-medium text-gray-700">{r.question}</span>
            <div className="flex-1 min-w-0">
              {r.question_text && <p className="text-sm text-gray-800">{r.question_text}</p>}
              <p className="text-xs text-gray-500 truncate">Your answer: {r.student_answer ?? "—"}</p>
            </div>
            <span className="font-semibold text-gray-800 whitespace-nowrap">{fmt(r.marks_earned)} / {fmt(r.marks_available)}</span>
          </div>
        ))}
      </Card.Body>
    </Card>
  );
}

// Earlier marks that a TA or the teacher changed (newest last)
function MarksHistory({ history }) {
  if (!history?.length) return null;
  return (
    <Card className="mt-6">
      <Card.Header><h2 className="text-base font-semibold text-gray-700">Marks history</h2></Card.Header>
      <Card.Body className="space-y-2">
        {history.map((h, i) => (
          <div key={i} data-testid={`history-${i}`} className="text-sm text-gray-700">
            <b>{h.question}</b>: {fmt(h.old)} → {fmt(h.new)} ({ROLE[h.by_role] ?? h.by_role})
            {h.at && <span className="text-xs text-gray-400"> · {formatDateTime(h.at)}</span>}
            {h.remark && <p className="text-xs text-gray-500">“{h.remark}”</p>}
          </div>
        ))}
      </Card.Body>
    </Card>
  );
}

// The one re-evaluation request: form → pending → resolved (with the TA's optional response)
function Reevaluation({ submissionId, state, onRequested }) {
  const { request, sending } = useRequestReevaluation();
  const [remark, setRemark] = useState("");
  return (
    <Card className="mt-6">
      <Card.Header><h2 className="text-base font-semibold text-gray-700">Re-evaluation</h2></Card.Header>
      <Card.Body className="space-y-3">
        {!state && (
          <>
            <label htmlFor="reeval-remark" className="block text-sm text-gray-700">
              Your remark (which questions should be re-checked, and why)
            </label>
            <textarea id="reeval-remark" rows={3} value={remark} onChange={(e) => setRemark(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
              placeholder="e.g. Q24: I gave solar panels as the example." />
            <p className="text-xs text-gray-400">You can ask only once for this paper.</p>
            <Button disabled={!remark.trim()} loading={sending}
              onClick={async () => { const r = await request(submissionId, remark.trim()); if (r) onRequested(r); }}>
              Request re-evaluation
            </Button>
          </>
        )}
        {state?.status === "pending" && (
          <>
            <Badge variant="warning">Re-evaluation requested — waiting for a TA</Badge>
            <p className="text-sm text-gray-600">Your remark: “{state.remark}”</p>
          </>
        )}
        {state?.status === "resolved" && (
          <>
            <Badge variant="success">Re-evaluated by a TA</Badge>
            <p className="text-sm text-gray-600">Your remark: “{state.remark}”</p>
            {state.response && <p className="text-sm text-gray-800">TA response: {state.response}</p>}
          </>
        )}
      </Card.Body>
    </Card>
  );
}

export default function Result() {
  const { submissionId } = useParams();
  const { data, loading, setData } = useResult(submissionId);
  const token = useAuthStore((s) => s.token);
  const [fileLoading, setFileLoading] = useState(false);

  // Fetch the uploaded sheet with the auth header and open it in a new tab
  const viewAnswerSheet = async () => {
    setFileLoading(true);
    try {
      const res = await fetch(`/api/submissions/${submissionId}/file`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to load file");
      const blob = await res.blob();
      const url  = URL.createObjectURL(blob);
      window.open(url, "_blank");
    } catch {
      alert("Could not load answer sheet.");
    } finally {
      setFileLoading(false);
    }
  };

  // Loading skeleton
  if (loading) {
    return (
      <PageWrapper>
        <div className="max-w-2xl mx-auto space-y-4">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-48 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
      </PageWrapper>
    );
  }

  // Not evaluated yet
  if (!data) {
    return (
      <PageWrapper>
        <div className="text-center py-20 text-gray-400">
          <p className="text-lg font-medium">Result not available yet.</p>
          <Link to="/student/dashboard" className="text-sm text-green-600 hover:underline mt-2 inline-block">
            &larr; Back to Dashboard
          </Link>
        </div>
      </PageWrapper>
    );
  }

  const { result, student_name, roll_no, paper_name, stats, paper } = data;
  const isType2 = paper?.type === "mcq_numerical" || paper?.type === "mcq_numerical_subjective";
  const isType3 = paper?.type === "mcq_numerical_subjective";
  // Section max = count × marks per question ("—" if unknown)
  const sectionMax = (k) => (paper?.[`${k}Count`] ?? 0) * (paper?.[`${k}Marks`] ?? 0) || "—";

  return (
    <PageWrapper>
      <Link to="/student/dashboard" className="text-sm text-green-600 hover:underline mb-4 inline-block">
        &larr; Back to Dashboard
      </Link>

      <p className="kicker">Result</p>
      <h1 className="text-3xl text-gray-900 mb-6">{paper_name}</h1>

      {/* Score summary: the red-pen score box, then the class comparison as a ruled row */}
      <div className="flex flex-col md:flex-row md:items-center gap-8 mb-6">
        <ScoreMark score={result.totalScore} max={result.maxScore} />
        <div className="flex-1 space-y-3">
          <div>
            <p className="kicker">Student</p>
            <p className="text-lg text-gray-900">{student_name} <span className="font-mono text-sm text-gray-500">{roll_no}</span></p>
          </div>
          <StatLedger items={[
            { label: "Your score", value: `${result.totalScore}/${result.maxScore}` },
            { label: "Class average", value: stats.average },
            { label: "Highest", value: stats.highest },
            { label: "Percentage", value: formatPercent(result.percentage) },
          ]} />
        </div>
      </div>

      <div className="mb-4">
        <Button variant="secondary" size="sm" onClick={viewAnswerSheet} loading={fileLoading}>
          View my answer sheet
        </Button>
      </div>

      <Card>
        <Card.Header>
          <h2 className="text-base font-semibold text-gray-700">Section Breakdown</h2>
        </Card.Header>
        <Card.Body className="space-y-3">
          {/* Per-section score / section max (only sections this paper type has) */}
          <Row label="MCQ Section" value={`${result.mcqScore} / ${sectionMax("mcq")}`} />
          {isType2 && <Row label="Numerical Section" value={`${result.numericalScore} / ${sectionMax("numerical")}`} />}
          {isType3 && <Row label="Subjective Section" value={`${result.subjectiveScore} / ${sectionMax("subjective")}`} />}
          <div className="flex justify-between items-center py-2 font-bold">
            <span className="text-gray-800">Total</span>
            <span className="text-green-600">{result.totalScore} / {result.maxScore}</span>
          </div>
        </Card.Body>
      </Card>

      {/* Per-question marks, changes by TA / teacher, and the re-evaluation request */}
      <QuestionMarks data={data} />
      <MarksHistory history={data.marks_history} />
      <Reevaluation submissionId={submissionId} state={data.reevaluation}
        onRequested={(r) => setData({ ...data, reevaluation: r })} />
    </PageWrapper>
  );
}
