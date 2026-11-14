# prompt_pipeline.py — prompts + JSON schemas for the two-reader pipeline.
#
# Rule from the research (plan §2): readers must transcribe *verbatim* — VLMs
# silently fix student mistakes, so every reader prompt forbids correction.
# TEMPLATE_VERSION is logged to MLflow; bump it whenever a prompt changes.

TEMPLATE_VERSION = "p2"   # p2: label-independent closed-form prompts

# ── Segmentation: find each answer's label + box on a page ──────────────────

SEGMENT_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["answers"],
    "properties": {"answers": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "required": ["label", "bbox", "continues_from_previous_page"],
        "properties": {
            "label": {"type": "string"},
            "bbox": {"type": "array", "items": {"type": "integer"}, "minItems": 4, "maxItems": 4},
            "continues_from_previous_page": {"type": "boolean"}}}}}}


def segment_prompt(labels: list) -> str:
    """Ask for one box per answer, labelled with the sheet's own question labels."""
    return f"""This is one page of a student's handwritten answer sheet.
The expected question labels are: {", ".join(labels)}.

Find every answer on this page. For each one return:
- "label": the question label it answers, exactly one of the expected labels
  (the student may write "1.", "Q1", "Ans 1" — map it to the expected label);
- "bbox": [x0, y0, x1, y1] of the whole answer including the label, in 0–1000
  coordinates relative to the page width and height; include struck-out text;
- "continues_from_previous_page": true if the text at the very top of the page
  continues an answer from the previous page without a new label (use the label
  it continues).
Return only answers that are present. Do not read or correct the content."""


# ── Reader A (general VLM): verbatim transcription ──────────────────────────

TRANSCRIBE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["text", "illegible_tokens", "confidence"],
    "properties": {"text": {"type": "string"},
                   "illegible_tokens": {"type": "integer"},
                   "confidence": {"type": "number"}}}

VERBATIM_RULES = """Transcribe EXACTLY what the student wrote, character for character.
- Do NOT correct spelling, grammar, arithmetic, units, signs or facts — even if obviously wrong.
- Do NOT complete unfinished sentences or add missing steps.
- Keep line breaks. Write maths in plain text or simple LaTeX as written.
- Struck-out text: wrap it as ~~like this~~.
- A word or symbol you cannot read: write [?] in its place; count these in illegible_tokens.
- confidence: 0–1, how sure you are the transcription is exact."""


def transcribe_prompt(kind: str, verbatim: bool = True) -> str:
    """Reader A prompt for one cropped answer; verbatim=False is the bake-off control."""
    what = {"mcq": "a multiple-choice answer (option letters)",
            "numerical": "a numerical answer (possibly with working)",
            "subjective": "a written answer"}[kind]
    rules = VERBATIM_RULES if verbatim else "Transcribe the student's answer."
    return f"This image is {what} cropped from a handwritten answer sheet.\n{rules}\nReturn JSON."


# ── Constrained extraction for closed-form answers ──────────────────────────

MCQ_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["status", "options", "confidence"],
    "properties": {"status": {"type": "string", "enum": ["answered", "blank", "unclear"]},
                   "options": {"type": "array", "items": {"type": "string", "enum": list("ABCDE")}},
                   "confidence": {"type": "number"}}}


def mcq_prompt(label: str) -> str:
    """Letters only; 'unclear' is the safe answer instead of guessing."""
    # label is unused on purpose: models that cannot match a messy written label answered "blank"
    return """This image is ONE answer cropped from a handwritten multiple-choice answer sheet.
Its question label may be hard to read — ignore the label.
Which option letter(s) did the student choose as the FINAL answer?
- Ignore letters that are struck out or overwritten by another letter.
- status "blank" if nothing is written, "unclear" if you cannot tell for sure.
- Never guess: prefer "unclear" over a guess. Return JSON."""


NUMBER_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["status", "final_answer", "confidence"],
    "properties": {"status": {"type": "string", "enum": ["answered", "blank", "unclear"]},
                   "final_answer": {"type": "string"},
                   "confidence": {"type": "number"}}}


def number_prompt(label: str) -> str:
    """Copy the final number exactly as written — never compute or fix it."""
    # label unused on purpose (see mcq_prompt)
    return """This image is ONE answer cropped from a handwritten answer sheet. Ignore the question label.
Copy the student's FINAL numerical answer exactly as written (without the label), including sign, decimal point,
fraction bar, exponent and unit (e.g. "-3.50 m/s", "5/8", "1.2×10^-3").
- If several values appear, take the one marked as final (boxed, underlined, "Ans", last line).
- Do NOT calculate, simplify, round or correct anything.
- status "blank" if nothing is written, "unclear" if the value cannot be read with certainty.
Return JSON."""


# ── Reader B (OCR specialists): each model has its own fixed prompt ─────────

OCR_PROMPTS = {
    "paddleocr_vl": "OCR:",
    "glm_ocr": "Text Recognition:",
    "chandra": "OCR this image to HTML.\n\nOnly use simple tags (p, br, del, math). "
               "Inline math: surround with <math>...</math>. Mark struck-out text with <del>.",
    "nanonets": "Extract the text from the above document as if you were reading it naturally. "
                "Return the equations in LaTeX representation.",
    "general": "Transcribe all handwritten text in this image exactly as written. Do not correct "
               "anything. Write [?] for unreadable words. Output only the transcription.",
}


# ── Grader: one yes/no decision per rubric concept, with evidence ───────────

GRADE_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["concepts", "transcript_problem"],
    "properties": {
        "concepts": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["concept", "present", "evidence", "confidence"],
            "properties": {"concept": {"type": "string"},
                           "present": {"type": "boolean"},
                           "evidence": {"type": "string"},
                           "confidence": {"type": "number"}}}},
        "transcript_problem": {"type": "boolean"}}}


def grade_prompt(question: str, model_answer: str, concepts: list, transcript_a: str,
                 transcript_b: str, subject: str = "") -> str:
    """Per-concept binary checks; marks are summed in Python, never by the model."""
    concept_lines = "\n".join(f"{i + 1}. {c}" for i, c in enumerate(concepts))
    return f"""You are checking a student's handwritten answer against a rubric.
Subject: {subject or "General"}
Question: {question}

Model answer (reference only — other correct wording is fine):
{model_answer or "(not provided)"}

Two independent transcriptions of the student's answer (the image is attached too;
if they disagree, trust the image):
--- Transcription A ---
{transcript_a or "(empty)"}
--- Transcription B ---
{transcript_b or "(empty)"}

Rubric concepts:
{concept_lines}

For EACH concept, in the same order, decide independently:
- "present": true only if the student's answer clearly states it (paraphrase is fine,
  a vague or incorrect statement is not);
- "evidence": a short exact quote from the student's answer that shows it ("" if absent);
- "confidence": 0–1.
Set "transcript_problem" true if the image and transcriptions disagree in a way that
matters for grading. Do not award marks; just judge each concept. Return JSON."""
