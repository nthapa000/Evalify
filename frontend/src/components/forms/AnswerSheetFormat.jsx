// AnswerSheetFormat.jsx — MCQ-only papers: will the students fill an OMR bubble sheet or write their answers by hand?
// The answer is stored on the paper; the student's upload page then offers only that kind of sheet.

const OPTIONS = [
  { key: "omr", label: "OMR bubble sheet", note: "Students fill circles on a printed bubble sheet. You can add a blank copy of it next, so any layout is read correctly." },
  { key: "handwritten", label: "Handwritten", note: "Students write the answers (for example Q1. A, Q2. C) on plain paper. They are read by the AI readers." },
];

export default function AnswerSheetFormat({ value, onChange }) {
  return (
    <fieldset>
      <legend className="block text-sm font-medium text-gray-700 mb-1">Answer sheet students will use</legend>
      <div className="space-y-2">
        {OPTIONS.map((o) => (
          <label key={o.key} className={`flex items-start gap-3 border rounded-lg px-3 py-2 cursor-pointer ${value === o.key ? "border-paper-900 bg-white" : "border-gray-200 bg-gray-50"}`}>
            <input type="radio" name="answerSheetFormat" className="mt-1" checked={value === o.key} onChange={() => onChange(o.key)} />
            <span>
              <span className="block text-sm text-gray-800">{o.label}</span>
              <span className="block text-xs text-gray-500">{o.note}</span>
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
