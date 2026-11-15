// teacher/PaperResults.jsx — all student submissions for one paper.
// Stat bar (avg/highest/lowest), a results table with AI-flag / TA / re-evaluation status per student and,
// for papers with subjective questions, optional calibration: the teacher hand-marks a few sheets and
// "Apply calibration" shifts the other students' subjective marks to the teacher's standard.

import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { usePaperResults, usePaperView, useCalibration } from "../../hooks/usePapers";
import PageWrapper from "../../components/layout/PageWrapper";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Modal from "../../components/ui/Modal";
import StatLedger from "../../components/ui/StatLedger";
import { SkeletonRow } from "../../components/ui/Skeleton";
import { formatDateTime, formatPercent, gradeFromPercent } from "../../utils/formatters";

// Map percentage to a badge color
const gradeBadgeVariant = (pct) => {
  if (pct >= 80) return "success";
  if (pct >= 50) return "info";
  return "error";
};

// AI flag / TA review / re-evaluation / hand-marked badges for one submission
function StatusBadges({ sub }) {
  const flagged = sub.review?.length ?? 0;
  const out = [];
  if (flagged) out.push(<Badge key="f" variant="warning">{flagged} flagged</Badge>);
  if (sub.ta_review?.status === "done") out.push(<Badge key="t" variant="success">TA reviewed</Badge>);
  else if (flagged) out.push(<Badge key="t" variant="neutral">TA pending</Badge>);
  if (sub.reevaluation?.status === "pending") out.push(<Badge key="r" variant="warning">Re-evaluation pending</Badge>);
  if (sub.reevaluation?.status === "resolved") out.push(<Badge key="r" variant="info">Re-evaluated</Badge>);
  if (sub.teacher_marks) out.push(<Badge key="h" variant="indigo">Hand-marked</Badge>);
  return <div className="flex flex-wrap gap-1">{out.length ? out : <span className="text-xs text-gray-400">—</span>}</div>;
}

// Dialog where the teacher enters their own marks for a sheet's subjective answers
function HandMarkDialog({ sub, onClose, onSave, busy }) {
  const rows = sub?.subjectiveDetail ?? [];
  const [marks, setMarks] = useState(() => Object.fromEntries(rows.map((r) => [r.question, sub.teacher_marks?.[r.question] ?? r.marks_earned])));
  const bad = rows.some((r) => marks[r.question] === "" || Number(marks[r.question]) < 0 || Number(marks[r.question]) > r.marks_available);
  return (
    <Modal isOpen={!!sub} onClose={onClose} title={`Hand-mark ${sub?.student_name ?? ""}`}
      footer={<>
        <Button variant="secondary" onClick={onClose}>Cancel</Button>
        <Button loading={busy} disabled={bad}
          onClick={() => onSave(Object.fromEntries(rows.map((r) => [r.question, Number(marks[r.question])])))}>
          Save my marks
        </Button>
      </>}>
      <p className="text-xs text-gray-500 mb-3">Your marks are final for this sheet and are used to learn your marking standard.</p>
      <div className="space-y-2 max-h-80 overflow-y-auto">
        {rows.map((r) => (
          <div key={r.question} className="flex items-center gap-3">
            <span className="flex-1 text-sm text-gray-700">{r.question}. {r.question_text}
              <span className="text-xs text-gray-400"> (AI {r.rubric_marks ?? r.marks_earned})</span></span>
            <input type="number" step="0.5" min="0" max={r.marks_available} aria-label={`Teacher marks for ${r.question}`}
              value={marks[r.question]} onChange={(e) => setMarks({ ...marks, [r.question]: e.target.value })}
              className="w-20 border border-gray-300 rounded-lg px-2 py-1 text-sm text-right" />
            <span className="text-xs text-gray-400">/ {r.marks_available}</span>
          </div>
        ))}
      </div>
    </Modal>
  );
}

export default function PaperResults() {
  const { paperId } = useParams();
  const { data, loading, refetch } = usePaperResults(paperId);
  const { paper } = usePaperView(paperId);
  const cal = useCalibration(paperId);
  const [marking, setMarking] = useState(null);
  const [summary, setSummary] = useState(null);
  const subjective = paper?.type === "mcq_numerical_subjective";
  const handMarked = data?.submissions?.filter((s) => s.teacher_marks).length ?? 0;

  // Save the teacher's marks for one sheet, then reload the table
  const saveHandMarks = async (marks) => {
    if (await cal.handMark(marking.id, marks)) { setMarking(null); refetch(); }
  };
  // Learn the shift from the hand-marked sheets and apply it to the others
  const applyCalibration = async () => {
    const res = await cal.apply();
    if (res) { setSummary(res); refetch(); }
  };
  const removeCalibration = async () => {
    if (await cal.remove()) { setSummary(null); refetch(); }
  };

  return (
    <PageWrapper>
      {/* Back link */}
      <Link to="/teacher/dashboard" className="text-sm text-green-600 hover:underline mb-4 inline-block">
        ← Back to Dashboard
      </Link>

      <p className="kicker">Results</p>
      <h1 className="text-3xl text-gray-900 mb-6">
        {loading ? "Loading…" : paper?.name ?? data?.submissions?.[0]?.paper_name ?? "Paper"}
      </h1>

      {/* Stats as one ruled row */}
      {!loading && data && (
        <div className="mb-6">
          <StatLedger items={[
            { label: "Submissions", value: data.stats.count },
            { label: "Average", value: data.stats.average },
            { label: "Highest", value: data.stats.highest },
            { label: "Lowest", value: data.stats.lowest },
          ]} />
        </div>
      )}

      {/* Optional calibration (subjective papers only) */}
      {subjective && data && (
        <Card className="mb-6">
          <Card.Body className="space-y-2">
            <h2 className="font-semibold text-gray-700">Match your marking style (optional)</h2>
            <p className="text-sm text-gray-500">
              Hand-mark 5–10 answer sheets with “Hand-mark”, then apply calibration: the other students' subjective marks
              are shifted to your standard (the rubric marks are kept). Without it, marks follow the rubric strictly.
              TA decisions are never changed.
            </p>
            <p className="text-sm text-gray-700">Hand-marked sheets: <b>{handMarked}</b>
              {data.calibration && <span className="text-green-700"> · calibration active</span>}</p>
            <div className="flex gap-2">
              <Button size="sm" onClick={applyCalibration} loading={cal.busy} disabled={handMarked === 0}>Apply calibration</Button>
              {data.calibration && <Button size="sm" variant="secondary" onClick={removeCalibration}>Remove calibration</Button>}
            </div>
            {summary && (
              <p className="text-sm text-green-700">
                Calibration learned from {summary.sheets} hand-marked sheet(s) ({summary.answers} answers);
                {" "}{summary.updated_submissions} other sheet(s) updated.
              </p>
            )}
          </Card.Body>
        </Card>
      )}

      {/* Results table */}
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 text-left">
                {["Student Name", "Roll No", "Score", "Percentage", "Grade", "Status", "Submitted", ""].map((h) => (
                  <th key={h} className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading
                ? Array.from({ length: 3 }).map((_, i) => <SkeletonRow key={i} />)
                : data?.submissions?.length === 0
                ? (
                  <tr>
                    <td colSpan={8} className="px-6 py-10 text-center text-gray-400">
                      No submissions yet.
                    </td>
                  </tr>
                )
                : data?.submissions?.map((sub) => (
                  <tr key={sub.id} data-testid={`row-${sub.id}`} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 font-medium text-gray-800">{sub.student_name}</td>
                    <td className="px-6 py-4 text-gray-600">{sub.roll_no}</td>
                    <td className="px-6 py-4 text-gray-800">
                      {sub.result.totalScore} / {sub.result.maxScore}
                    </td>
                    <td className="px-6 py-4">{formatPercent(sub.result.percentage)}</td>
                    <td className="px-6 py-4">
                      <Badge variant={gradeBadgeVariant(sub.result.percentage)}>
                        {gradeFromPercent(sub.result.percentage)}
                      </Badge>
                    </td>
                    <td className="px-6 py-4"><StatusBadges sub={sub} /></td>
                    <td className="px-6 py-4 text-gray-400 text-xs">{formatDateTime(sub.submittedAt)}</td>
                    <td className="px-6 py-4">
                      {subjective && <Button size="sm" variant="secondary" onClick={() => setMarking(sub)}>Hand-mark</Button>}
                    </td>
                  </tr>
                ))
              }
            </tbody>
          </table>
        </div>
      </Card>

      {marking && <HandMarkDialog sub={marking} busy={cal.busy} onClose={() => setMarking(null)} onSave={saveHandMarks} />}
    </PageWrapper>
  );
}
