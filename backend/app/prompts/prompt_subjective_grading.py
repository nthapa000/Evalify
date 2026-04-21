# prompt_subjective_grading.py — LLM grading prompt for one subjective question.
#
# Used by subjective_grader.py (text-only call, no image).
# The rubric comes from RubricBuilder and has these fields:
#   key_concepts       — list of concepts the teacher expects
#   mandatory_concepts — subset that must appear to get any marks at all
#   marks_per_concept  — marks awarded per concept found
#   model_answer       — reference answer for the LLM
#
# Max marks = len(key_concepts) * marks_per_concept.
# Partial credit is always on (one concept = marks_per_concept marks).
# If any mandatory concept is missing → total = 0.


STUDENT_ANSWER_PLACEHOLDER = "<<<STUDENT_ANSWER>>>"


def build_grading_prompt_template(
    question_text:     str,
    key_concepts:      list,
    mandatory_concepts: list,
    marks_per_concept: float,
    model_answer:      str = "",
    subject:           str = "",
) -> str:
    """
    Build a reusable grading prompt with <<<STUDENT_ANSWER>>> as placeholder.
    At evaluation time, replace the placeholder with the actual student answer.
    """
    return build_subjective_grading_prompt(
        question_text      = question_text,
        student_answer     = STUDENT_ANSWER_PLACEHOLDER,
        key_concepts       = key_concepts,
        mandatory_concepts = mandatory_concepts,
        marks_per_concept  = marks_per_concept,
        model_answer       = model_answer,
        subject            = subject,
    )


def build_subjective_grading_prompt(
    question_text: str,
    student_answer: str,
    key_concepts: list,
    mandatory_concepts: list,
    marks_per_concept: float,
    model_answer: str = "",
    subject: str = "",
) -> str:
    """
    Build the text-only grading prompt for a single subjective question.

    Returns a prompt string. The LLM must respond with a JSON object only.
    """
    max_marks        = len(key_concepts) * marks_per_concept
    optional_list    = [c for c in key_concepts if c not in mandatory_concepts]
    mandatory_note   = (
        f"MANDATORY concepts (student must address at least one of these to earn any marks): {mandatory_concepts}"
        if mandatory_concepts else
        "MANDATORY concepts: none — all concepts are optional"
    )
    optional_note    = (
        f"OPTIONAL concepts (each earns {marks_per_concept} marks if present): {optional_list}"
        if optional_list else
        f"All concepts carry {marks_per_concept} marks each."
    )

    # Build the empty concept scaffold for the response template
    concept_keys = ", ".join(f'"{c}": 0' for c in key_concepts)

    return f"""You are an expert academic evaluator. Your task is to grade one student answer.

SUBJECT: {subject or "General"}
QUESTION: {question_text or "(question text not provided)"}

MAX MARKS: {max_marks}  ({len(key_concepts)} concepts × {marks_per_concept} marks each)

── RUBRIC ────────────────────────────────────────────────────────────────
{mandatory_note}
{optional_note}
──────────────────────────────────────────────────────────────────────────

MODEL ANSWER (use only as reference — do NOT penalise different but correct wording):
{model_answer.strip() if model_answer.strip() else "(not provided — grade based on concepts alone)"}

STUDENT ANSWER (transcribed from handwritten sheet via OCR — may contain minor spelling errors or OCR artefacts):
{student_answer.strip()}

── EVALUATION RULES ──────────────────────────────────────────────────────
1. Accept paraphrased or semantically equivalent versions of each concept.
2. Be lenient with spelling mistakes that are clearly OCR artefacts.
3. Award {marks_per_concept} marks for EACH key concept found in the answer.
4. If ALL mandatory concepts are absent → set marks_awarded = 0 and mandatory_concepts_met = false.
5. Cap marks_awarded at {max_marks} (cannot exceed max).
6. Provide a brief 1-2 sentence feedback explaining what was done well and what was missed.
──────────────────────────────────────────────────────────────────────────

RESPOND WITH ONLY THIS JSON — NO explanation, NO markdown, NO preamble:
{{
  "concept_scores":        {{{concept_keys}}},
  "concepts_found":        [],
  "concepts_missing":      [],
  "mandatory_concepts_met": true,
  "marks_awarded":         0,
  "max_marks":             {max_marks},
  "feedback":              "brief justification",
  "ocr_issues_detected":   false
}}"""
