# prompt_mcq_numerical_subjective.py — Extraction prompt for Type 3 answer sheets.
#
# Any section can have count = 0 (e.g. no MCQ, or no subjective).
# Sections with count = 0 are omitted from the prompt and from the JSON template.
#
# Numbering convention on the physical sheet:
#   MCQ       : Q1  … Q{mcq_count}           (letters)
#   Numerical : Q{mcq_count+1} … Q{total_ab} (numbers — students continue Q-numbering)
#   Subjective: S1  … S{subjective_count}    (paragraphs — separate S-label section)
#
# The parser in ollama_engine.py remaps numerical Q-labels → N-keys for the evaluator.


def build_mcq_numerical_subjective_prompt(
    mcq_count:        int,
    numerical_count:  int,
    subjective_count: int,
    options:          str = "A, B, C, D",
) -> str:
    """
    Build the combined extraction prompt for a mixed answer sheet.
    Any section with count = 0 is silently omitted from the prompt.
    Always returns at least the sections that exist on the sheet.
    """
    total_ab  = mcq_count + numerical_count
    num_start = mcq_count + 1

    has_mcq   = mcq_count > 0
    has_num   = numerical_count > 0
    has_subj  = subjective_count > 0

    # ── Build section descriptions ────────────────────────────────────────────
    section_lines = []
    section_count = 0

    if has_mcq:
        section_count += 1
        section_lines.append(
            f"SECTION A — MCQ (Q1 to Q{mcq_count}):\n"
            f"  Each answer is one or more option letters ({options})."
        )
    if has_num:
        section_count += 1
        label = chr(ord('A') + section_count - 1)  # A/B/C depending on what came before
        section_lines.append(
            f"SECTION {label} — Numerical (Q{num_start} to Q{total_ab}):\n"
            f"  Each answer is a number or a mathematical expression."
        )
    if has_subj:
        section_count += 1
        label = chr(ord('A') + section_count - 1)
        section_lines.append(
            f"SECTION {label} — Subjective (S1 to S{subjective_count}):\n"
            f"  Each answer is a paragraph of written text."
        )

    sections_desc = "\n\n".join(section_lines)

    # ── Build rules block ─────────────────────────────────────────────────────
    rule_lines = []

    if has_mcq:
        rule_lines.append(
            f"RULES FOR MCQ (Q1–Q{mcq_count}):\n"
            f"  • Single option circled/written (e.g. \"B\")        → value = \"B\"\n"
            f"  • Multiple options (e.g. \"A\" and \"C\" both marked)  → join sorted: \"A,C\"\n"
            f"  • Blank or completely unreadable                   → omit that key"
        )
    if has_num:
        rule_lines.append(
            f"RULES FOR Numerical (Q{num_start}–Q{total_ab}):\n"
            f"  • Copy the number or expression exactly as written (e.g. \"3\", \"1/2\", \"0.625\")\n"
            f"  • If two values separated by a comma (e.g. \"5/8, 0.625\") take only the FIRST\n"
            f"  • Blank or completely unreadable                   → omit that key"
        )
    if has_subj:
        rule_lines.append(
            f"RULES FOR Subjective (S1–S{subjective_count}):\n"
            f"  • Transcribe the student's FULL written answer word-for-word\n"
            f"  • Include every sentence — do NOT summarise\n"
            f"  • Blank or completely unreadable                   → omit that key"
        )

    rules_desc = "\n\n".join(rule_lines)

    # ── Build JSON template ───────────────────────────────────────────────────
    json_parts = []
    if has_mcq:
        last_q = f'"Q{mcq_count}": "A"'
        json_parts.append(f'  "mcq":        {{"Q1": "C", "Q2": "B,D", ..., {last_q}}}')
    if has_num:
        last_nq = f'"Q{total_ab}": "42"'
        json_parts.append(
            f'  "numerical":  {{"Q{num_start}": "3.5", ..., {last_nq}}}'
        )
    if has_subj:
        last_s = f'"S{subjective_count}": "full transcribed answer..."'
        json_parts.append(
            f'  "subjective": {{"S1": "full transcribed answer for question 1...", ..., {last_s}}}'
        )

    json_template = "{\n" + ",\n".join(json_parts) + "\n}"

    return f"""You are reading a student's handwritten answer sheet.

{sections_desc}

─────────────────────────────────────────────
{rules_desc}
─────────────────────────────────────────────

Return ONLY the following JSON — NO preamble, NO explanation, NO markdown fences:

{json_template}

Now extract all answers from the image."""
