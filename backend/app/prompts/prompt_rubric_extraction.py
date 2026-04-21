# prompt_rubric_extraction.py — LLM prompt that parses two teacher-uploaded PDFs
# (detailed answer + grade rubric) into per-question structured rubric data.
#
# Used by rubric_extractor.py at paper-creation time (text-only call, no image).
# Returns one entry per subjective question with fields that match RubricBuilder's schema.


def build_rubric_extraction_prompt(
    detailed_answer_text: str,
    grade_rubric_text:    str,
    subjective_count:     int,
) -> str:
    """
    Build the prompt to extract per-question rubric data from two PDF documents.

    Output JSON schema per question:
      question_id       — "S1", "S2", …
      question_text     — the question itself (extracted from documents if visible)
      model_answer      — the ideal full answer from the detailed answer document
      key_concepts      — list of scoreable concepts/points
      mandatory_concepts — subset that must be mentioned to earn any marks
      marks_per_concept — marks awarded per concept found
    """
    return f"""You are an expert exam grader assistant. You have been given two teacher-prepared documents.

DOCUMENT 1 — DETAILED ANSWER (model answer / solution key):
─────────────────────────────────────────────────────────────
{detailed_answer_text.strip() or "(document is blank or unreadable)"}
─────────────────────────────────────────────────────────────

DOCUMENT 2 — GRADE RUBRIC (marking scheme / scoring criteria):
─────────────────────────────────────────────────────────────
{grade_rubric_text.strip() or "(document is blank or unreadable)"}
─────────────────────────────────────────────────────────────

TASK:
Extract the model answer and grading rubric for each of the {subjective_count} subjective question(s) (S1 to S{subjective_count}).

RULES:
1. Match questions across both documents by their numbering (Q1/S1, Q2/S2, etc.).
2. model_answer: copy the full ideal answer from Document 1 for that question.
3. key_concepts: list every distinct scoreable concept or point from Document 2.
   - Keep each concept as a short phrase (3–8 words max).
   - Do NOT list the same concept twice.
4. mandatory_concepts: the subset of key_concepts that the rubric marks as mandatory,
   essential, or "must mention". If none are explicitly marked, leave this list empty.
5. marks_per_concept: the marks awarded per concept as stated in the rubric.
   If different concepts carry different marks, use the most common value and note
   that in the feedback. If unclear, default to 1.
6. question_text: the question itself, extracted from either document. If not found, use "Question S{subjective_count}".
7. If a question cannot be found in the documents, return empty strings and empty lists for it.

RESPOND WITH ONLY THIS JSON — NO explanation, NO markdown fences, NO preamble:
{{
  "questions": [
    {{
      "question_id":         "S1",
      "question_text":       "full question text here",
      "model_answer":        "full model answer from Document 1",
      "key_concepts":        ["concept 1", "concept 2", "concept 3"],
      "mandatory_concepts":  ["concept 1"],
      "marks_per_concept":   2
    }}
  ]
}}

Extract all {subjective_count} question(s) now."""
