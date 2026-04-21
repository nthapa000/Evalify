// StepWizard.jsx — horizontal step progress indicator used in CreatePaper.
// Renders numbered circles with labels; completed steps show a check mark.

export default function StepWizard({ steps, current }) {
  return (
    <div className="flex items-center w-full">
      {steps.map((label, i) => {
        const stepNum = i + 1;
        const done    = stepNum < current;
        const active  = stepNum === current;

        return (
          <div key={i} className="flex items-center flex-1 last:flex-none">
            {/* Circle */}
            <div className="flex flex-col items-center">
              <div
                className={`
                  w-9 h-9 rounded-full flex items-center justify-center text-sm font-semibold
                  ${done   ? "bg-green-600 text-white" : ""}
                  ${active ? "bg-green-600 text-white ring-4 ring-green-100" : ""}
                  ${!done && !active ? "bg-gray-200 text-gray-500" : ""}
                `}
              >
                {done ? "✓" : stepNum}
              </div>
              {/* Label below circle */}
              <span className={`mt-1 text-xs font-medium whitespace-nowrap ${active ? "text-green-600" : "text-gray-400"}`}>
                {label}
              </span>
            </div>

            {/* Connector line between steps (not after last) */}
            {i < steps.length - 1 && (
              <div className={`flex-1 h-0.5 mx-2 mb-5 ${done ? "bg-green-600" : "bg-gray-200"}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}
