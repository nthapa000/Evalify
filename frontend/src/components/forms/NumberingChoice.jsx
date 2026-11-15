// NumberingChoice.jsx — how students number their written answers on the sheet.
// "separate": S1, S2, ... ; "continuous": the numbers carry on after the MCQ / numerical questions (Q21, Q22, ...).
// The pipeline matches transcribed answers to questions by these labels, so it must match the printed paper.

export default function NumberingChoice({ value, mcqCount = 0, numericalCount = 0, onChange }) {
  const first = Number(mcqCount || 0) + Number(numericalCount || 0) + 1;
  const current = value === "continuous" ? "continuous" : "separate";
  const options = [
    { key: "separate", text: "S1, S2, ... (separate numbering)" },
    { key: "continuous", text: `Q${first}, Q${first + 1}, ... (numbers continue after the other questions)` },
  ];
  return (
    <fieldset className="space-y-1">
      <legend className="block text-sm font-medium text-gray-700 mb-1">How are written answers numbered on the sheet?</legend>
      {options.map((o) => (
        <label key={o.key} className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
          <input type="radio" name="subjective-numbering" value={o.key} checked={current === o.key}
            onChange={() => onChange(o.key)} />
          {o.text}
        </label>
      ))}
    </fieldset>
  );
}
