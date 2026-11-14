# prompt_subjective_grading.py — legacy grading prompt for one subjective answer.
#
# Rubric fields: key_concepts, mandatory_concepts, marks_per_concept, model_answer.
# Max marks = len(key_concepts) × marks_per_concept; no mandatory concept → 0.

# Placeholder replaced by the student's answer when a stored template is used
STUDENT_ANSWER_PLACEHOLDER = "<<<STUDENT_ANSWER>>>"


def build_grading_prompt_template(question_text: str, key_concepts: list, mandatory_concepts: list,
                                  marks_per_concept: float, model_answer: str = "", subject: str = "") -> str:
    """Same prompt as below, with a placeholder instead of the student's answer."""
    return build_subjective_grading_prompt(question_text, STUDENT_ANSWER_PLACEHOLDER, key_concepts,
                                           mandatory_concepts, marks_per_concept, model_answer, subject)


def build_subjective_grading_prompt(question_text: str, student_answer: str, key_concepts: list,
                                    mandatory_concepts: list, marks_per_concept: float,
                                    model_answer: str = "", subject: str = "") -> str:
    """Text-only prompt; the LLM must reply with one JSON object."""
    # Rubric summary lines
    max_marks = len(key_concepts) * marks_per_concept
    optional = [c for c in key_concepts if c not in mandatory_concepts]
    mandatory_note = (f"MANDATORY concepts (at least one needed for any marks): {mandatory_concepts}"
                      if mandatory_concepts else "MANDATORY concepts: none")
    optional_note = f"OPTIONAL concepts ({marks_per_concept} marks each): {optional}"
    scaffold = ", ".join(f'"{c}": 0' for c in key_concepts)

    return f"""You are an expert academic evaluator. Grade one student answer.

SUBJECT: {subject or "General"}
QUESTION: {question_text or "(question text not provided)"}
MAX MARKS: {max_marks}  ({len(key_concepts)} concepts × {marks_per_concept} marks each)

RUBRIC:
{mandatory_note}
{optional_note}

MODEL ANSWER (reference only — accept different but correct wording):
{model_answer.strip() or "(not provided — grade on concepts alone)"}

STUDENT ANSWER (transcribed from handwriting; may contain OCR errors):
{student_answer.strip()}

RULES:
1. Accept paraphrases and semantically equivalent statements of each concept.
2. Be lenient with spelling errors that are clearly OCR artefacts.
3. Award {marks_per_concept} marks per concept found.
4. If no mandatory concept is present → marks_awarded = 0, mandatory_concepts_met = false.
5. Never exceed {max_marks}. Give 1–2 sentences of feedback.

RESPOND WITH ONLY THIS JSON:
{{
  "concept_scores": {{{scaffold}}},
  "concepts_found": [],
  "concepts_missing": [],
  "mandatory_concepts_met": true,
  "marks_awarded": 0,
  "max_marks": {max_marks},
  "feedback": "brief justification",
  "ocr_issues_detected": false
}}"""
