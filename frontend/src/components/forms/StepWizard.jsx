// StepWizard.jsx — step indicator for CreatePaper: numbered steps on one rule, current step in ink,
// finished steps marked "done" in mono capitals.

export default function StepWizard({ steps, current }) {
  return (
    <ol className="grid border-t border-paper-900" style={{ gridTemplateColumns: `repeat(${steps.length}, minmax(0, 1fr))` }}>
      {steps.map((label, i) => {
        const n = i + 1;
        const done = n < current;
        const active = n === current;
        return (
          <li key={label} aria-current={active ? "step" : undefined}
              className={`pt-2 pr-2 border-t-4 -mt-px ${active ? "border-ink-600" : done ? "border-paper-900" : "border-transparent"}`}>
            <span className="font-mono text-[11px] text-paper-500">{String(n).padStart(2, "0")}{done ? " done" : ""}</span>
            <p className={`text-sm ${active ? "text-paper-900 font-medium" : "text-paper-500"}`}>{label}</p>
          </li>
        );
      })}
    </ol>
  );
}
