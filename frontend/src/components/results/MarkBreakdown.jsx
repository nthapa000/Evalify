// MarkBreakdown.jsx — how a written (subjective) answer was marked, for the student:
// every rubric point with Met / Partly met / Missed, its marks and the student's own words as evidence; then the
// teacher's calibration adjustment and a TA's re-evaluation as separate lines, so the parts add up to the mark.

const fmt = (n) => Number(n).toString();
const signed = (n) => (n > 0 ? `+${fmt(n)}` : fmt(n));

// Verdict word and marks for one rubric point (partial = half the point's marks)
function verdict(c, per) {
  if (c.present) return { word: "Met", marks: per, tone: "text-moss-700 border-moss-400" };
  if (c.partial) return { word: "Partly met", marks: per / 2, tone: "text-ochre-700 border-ochre-400" };
  return { word: "Missed", marks: 0, tone: "text-pen-600 border-pen-300" };
}

export default function MarkBreakdown({ row, rubric }) {
  const concepts = row?.concepts ?? [];
  if (!concepts.length) return null;
  const per = Number(rubric?.marks_per_concept ?? 1);
  const rubricMarks = Number(row.rubric_marks ?? row.marks_earned);
  const earned = Number(row.marks_earned);
  const byTa = row.final_by === "ta" || row.final_by === "teacher";
  const adjustment = !byTa && row.calibrated_marks != null ? earned - rubricMarks : 0;

  return (
    <div className="mt-2 border-l-2 border-paper-300 pl-4 space-y-2">
      <p className="kicker">How this answer was marked</p>
      {concepts.map((c, i) => {
        const v = verdict(c, per);
        return (
          <div key={i} data-testid={`point-${i}`} className="grid grid-cols-[6.5rem_minmax(0,1fr)_3rem] gap-3 items-baseline text-sm">
            <span className={`font-mono text-[11px] uppercase border rounded-sm px-1.5 text-center ${v.tone}`}>{v.word}</span>
            <div className="min-w-0">
              <p className="text-paper-900">{c.concept}</p>
              <p className="text-xs text-paper-500">{c.evidence ? <>You wrote: “{c.evidence}”</> : "Not found in your answer"}</p>
            </div>
            <span className="font-mono text-right text-paper-900">{v.marks ? signed(v.marks) : "0"}</span>
          </div>
        );
      })}
      {/* A missing required point makes the whole answer 0 */}
      {row.mandatory_met === false && (
        <p className="text-sm text-pen-600">A required point is missing, so this answer gets 0.</p>
      )}
      {/* Calibration: the teacher's general leniency, applied to the whole answer */}
      {adjustment !== 0 && (
        <p data-testid="adjustment" className="text-sm text-paper-700 flex justify-between">
          <span>Teacher's marking adjustment</span><span className="font-mono">{signed(adjustment)}</span>
        </p>
      )}
      {/* A TA (or the teacher) re-evaluated this answer: their mark is final */}
      {byTa && earned !== rubricMarks && (
        <p data-testid="override" className="text-sm text-ink-700">
          Re-evaluated by a {row.final_by === "ta" ? "TA" : "teacher"}: {fmt(rubricMarks)} → {fmt(earned)}
        </p>
      )}
    </div>
  );
}
