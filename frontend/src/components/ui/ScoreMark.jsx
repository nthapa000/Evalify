// ScoreMark.jsx — the total as a teacher writes it on an answer sheet: a red-pen box with marks and grade.

import { gradeFromPercent } from "../../utils/formatters";

export default function ScoreMark({ score, max }) {
  const pct = max > 0 ? (score / max) * 100 : 0;
  return (
    <div className="inline-flex flex-col items-center border-2 border-pen-500 px-6 py-3 -rotate-1">
      <span className="font-serif text-5xl leading-none text-pen-600">{score}</span>
      <span className="font-mono text-xs text-pen-600 mt-1">of {max}</span>
      <span className="font-mono text-[11px] uppercase tracking-label text-pen-500 border-t border-pen-300 mt-2 pt-1">
        Grade {gradeFromPercent(pct)}
      </span>
    </div>
  );
}
