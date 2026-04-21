# prompt_mcq_numerical.py — Prompt template for Type 2 (MCQ + Numerical) answer sheets.
#
# Key insight: Students write ALL questions with Q-labels in sequence (Q1..Q_total).
# The first mcq_count questions are MCQ (letter answers).
# The next numerical_count questions are Numerical (number/expression answers).
# Students do NOT write "N1", "N2" — they continue numbering as Q7, Q8, etc.
#
# The prompt therefore describes questions by their position range, not by N-labels.
# The parser in ollama_engine.py maps Q(mcq+1)..Q(total) → N1..Nm.


def build_mcq_numerical_prompt(
    mcq_count: int,
    numerical_count: int,
    options: str = "A, B, C, D",
) -> str:
    """
    Build the combined extraction prompt for a Type 2 answer sheet.

    Students write a single answer sheet with all questions numbered Q1..Q_total.
    - Q1  …  Q{mcq_count}                        → MCQ section (letter answers)
    - Q{mcq_count+1} … Q{mcq_count+numerical_count} → Numerical section (number/expression answers)

    The prompt uses this natural Q-numbering so Ollama matches what it sees on the sheet.
    """
    total = mcq_count + numerical_count
    num_start = mcq_count + 1

    return f"""You are reading a student's answer sheet with {total} questions total.

Questions Q1 to Q{mcq_count} are MCQ questions — answers are letters ({options}).
Questions Q{num_start} to Q{total} are Numerical questions — answers are numbers or expressions.

Rules for MCQ (Q1–Q{mcq_count}):
- Single option written (e.g. "B")             → value is "B"
- Multiple options written (e.g. "A" and "C")  → join sorted with comma: "A,C"
- Blank or unreadable                          → omit that key

Rules for Numerical (Q{num_start}–Q{total}):
- Copy the number or expression exactly as written (e.g. "3", "3.0", "1/2", "0.5")
- If two values are written separated by comma (e.g. "5/8, 0.625") take the FIRST one
- Blank or unreadable                          → omit that key

Return ONLY a JSON object — no explanation, no preamble.

{{
  "mcq":       {{"Q1": "C", "Q2": "B", ..., "Q{mcq_count}": "B"}},
  "numerical": {{"Q{num_start}": "3.5", "Q{num_start+1}": "1.5", ..., "Q{total}": "3"}}
}}

Now extract all answers from the image."""
