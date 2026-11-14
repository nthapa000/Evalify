# prompt_extraction.py — one extraction prompt for every handwritten paper type.
#
# Sheet numbering: MCQ = Q1..Qm, numerical continues as Q(m+1)..Q(m+n),
# subjective = S1..Ss. Sections with count 0 are left out of the prompt.


def build_extraction_prompt(mcq_count: int, numerical_count: int = 0,
                            subjective_count: int = 0, options: str = "A, B, C, D") -> str:
    """Build the vision prompt that asks for all answers on one sheet as JSON."""
    # Question ranges as the student numbers them on the sheet
    num_start, num_end = mcq_count + 1, mcq_count + numerical_count

    # One description + rule block + JSON example per section that exists
    sections, rules, example = [], [], []
    if mcq_count:
        sections.append(f"MCQ (Q1 to Q{mcq_count}): one or more option letters ({options}).")
        rules.append("MCQ: one option → \"B\"; several → sorted and comma-joined, e.g. \"A,C\"; "
                     "blank or unreadable → omit the key.")
        example.append(f'"mcq": {{"Q1": "C", "Q2": "B,D", ..., "Q{mcq_count}": "A"}}')
    if numerical_count:
        sections.append(f"Numerical (Q{num_start} to Q{num_end}): a number or expression.")
        rules.append("Numerical: copy the value exactly as written (e.g. \"3\", \"1/2\", \"0.625\"); "
                     "if two values are written, take the FIRST; blank → omit the key.")
        example.append(f'"numerical": {{"Q{num_start}": "3.5", ..., "Q{num_end}": "42"}}')
    if subjective_count:
        sections.append(f"Subjective (S1 to S{subjective_count}): a paragraph of text.")
        rules.append("Subjective: transcribe the FULL answer word for word, do not summarise; "
                     "blank → omit the key.")
        example.append(f'"subjective": {{"S1": "full answer...", ..., "S{subjective_count}": "..."}}')

    # Assemble the final prompt
    nl = "\n"
    return f"""You are reading a student's handwritten answer sheet.

SECTIONS:
{nl.join('- ' + s for s in sections)}

RULES:
{nl.join('- ' + r for r in rules)}

Return ONLY this JSON — no explanation, no markdown fences:
{{{', '.join(example)}}}

Now extract all answers from the image."""
