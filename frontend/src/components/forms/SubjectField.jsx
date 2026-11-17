// SubjectField.jsx — the subject line of the paper wizard: fixed for a teacher with one subject,
// a drop-down for a teacher with two (the paper is created for the chosen one).

export default function SubjectField({ value, subjects = [], onChange }) {
  return (
    <div>
      <label htmlFor="paper-subject" className="block text-sm font-medium text-gray-700 mb-1">Subject</label>
      {subjects.length > 1 ? (
        <select id="paper-subject" value={value} onChange={(e) => onChange(e.target.value)}
                className="w-full border border-gray-200 bg-white rounded-lg px-3 py-2 text-sm text-gray-800">
          {subjects.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      ) : (
        <div className="flex items-center gap-2 border border-gray-200 bg-gray-50 rounded-lg px-3 py-2 text-sm text-gray-600">
          <span className="font-medium text-gray-800">{value || "—"}</span>
          <span className="text-xs text-gray-400">(fixed to your assigned subject)</span>
        </div>
      )}
    </div>
  );
}
