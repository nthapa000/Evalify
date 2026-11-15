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
    <div className="space-y-4 p-4 bg-paper-50 rounded-sm border border-paper-300">
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
            className="flex-1 text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-green-400"
          />
          <Button size="sm" variant="secondary" type="button" onClick={addConcept}>Add</Button>
        </div>
        {/* Concept list: "Required" toggles a mandatory point, "Remove" drops it */}
        <ul className="mt-2 divide-y divide-paper-200 border-y border-paper-200">
          {rubric.key_concepts.map((c) => {
            const required = rubric.mandatory_concepts.includes(c);
            return (
              <li key={c} className="flex items-center gap-3 py-1.5 text-sm">
                <span className="flex-1 text-paper-800">{c}</span>
                <button type="button" onClick={() => toggleMandatory(c)} aria-pressed={required}
                  aria-label={`Mark "${c}" as required`}
                  className={`font-mono text-[11px] uppercase px-1.5 border rounded-sm ${required
                    ? "border-pen-400 text-pen-600" : "border-paper-300 text-paper-500 hover:text-paper-900"}`}>
                  {required ? "Required" : "Optional"}
                </button>
                <button type="button" onClick={() => removeConcept(c)} aria-label={`Remove "${c}"`}
                  className="font-mono text-[11px] uppercase text-paper-500 hover:text-pen-600">Remove</button>
              </li>
            );
          })}
        </ul>
        <p className="text-xs text-paper-500 mt-1">Required = the student must state this point to get any marks.</p>
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
          className="w-24 text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-green-400"
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
          className="w-full text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-green-400 resize-none"
        />
      </div>
    </div>
  );
}
