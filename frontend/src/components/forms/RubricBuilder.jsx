// RubricBuilder.jsx — per-subjective-question rubric editor (Step 4 of CreatePaper).
// Teacher fills in key concepts, marks per concept, and a model answer.

import { useState } from "react";
import Button from "../ui/Button";

export default function RubricBuilder({ questionIndex, value, onChange }) {
  const [conceptInput, setConceptInput] = useState("");

  const rubric = value ?? {
    key_concepts: [],
    mandatory_concepts: [],
    marks_per_concept: 2,
    model_answer: "",
  };

  const update = (patch) => onChange({ ...rubric, ...patch });

  const addConcept = () => {
    const trimmed = conceptInput.trim();
    if (!trimmed || rubric.key_concepts.includes(trimmed)) return;
    update({ key_concepts: [...rubric.key_concepts, trimmed] });
    setConceptInput("");
  };

  const removeConcept = (c) =>
    update({
      key_concepts: rubric.key_concepts.filter((x) => x !== c),
      mandatory_concepts: rubric.mandatory_concepts.filter((x) => x !== c),
    });

  const toggleMandatory = (c) => {
    const already = rubric.mandatory_concepts.includes(c);
    update({
      mandatory_concepts: already
        ? rubric.mandatory_concepts.filter((x) => x !== c)
        : [...rubric.mandatory_concepts, c],
    });
  };

  return (
    <div className="space-y-4 p-4 bg-gray-50 rounded-xl border border-gray-200">
      <h4 className="text-sm font-semibold text-gray-700">
        Subjective Q{questionIndex + 1} — Rubric
      </h4>

      {/* Key Concepts */}
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">Key Concepts</label>
        <div className="flex gap-2">
          <input
            value={conceptInput}
            onChange={(e) => setConceptInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addConcept())}
            placeholder="Type concept and press Enter"
            className="flex-1 text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-400"
          />
          <Button size="sm" variant="secondary" type="button" onClick={addConcept}>Add</Button>
        </div>
        {/* Tag list — click M to toggle mandatory */}
        <div className="flex flex-wrap gap-2 mt-2">
          {rubric.key_concepts.map((c) => (
            <span
              key={c}
              className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium
                ${rubric.mandatory_concepts.includes(c) ? "bg-indigo-100 text-indigo-700" : "bg-gray-200 text-gray-600"}`}
            >
              {c}
              {/* M = toggle mandatory; * = remove */}
              <button type="button" onClick={() => toggleMandatory(c)} title="Toggle mandatory" className="hover:text-indigo-900">
                {rubric.mandatory_concepts.includes(c) ? "★" : "☆"}
              </button>
              <button type="button" onClick={() => removeConcept(c)} className="hover:text-red-500">×</button>
            </span>
          ))}
        </div>
        <p className="text-xs text-gray-400 mt-1">★ = mandatory (student must mention to get any marks)</p>
      </div>

      {/* Marks per Concept */}
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">Marks per Concept</label>
        <input
          type="number"
          min="0.5"
          step="0.5"
          value={rubric.marks_per_concept}
          onChange={(e) => update({ marks_per_concept: parseFloat(e.target.value) || 1 })}
          className="w-24 text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-400"
        />
      </div>

      {/* Model Answer */}
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">Model Answer (for LLM reference)</label>
        <textarea
          rows={3}
          value={rubric.model_answer}
          onChange={(e) => update({ model_answer: e.target.value })}
          placeholder="Write the ideal answer here..."
          className="w-full text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-none"
        />
      </div>
    </div>
  );
}
