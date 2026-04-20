# prompt_mcq.py — Prompt template for Type 1 (MCQ) handwritten answer sheet extraction.
#
# This prompt is sent to the Ollama vision model (llama3.2-vision:11b) along with
# a base64-encoded image of the student's handwritten answer sheet.
#
# Design decisions:
#   - We tell the model exactly how many questions are on the paper (mcq_count) so
#     it knows the valid range of question numbers and won't invent extra entries.
#   - We specify the allowed option values (A–D or A–E) to prevent hallucinations.
#   - We ask for strict JSON so parse_mcq_results() can use json.loads() first and
#     only fall back to regex if the model adds surrounding explanation text.
#   - "Do not guess" instruction reduces hallucinated answers for blank/skipped questions.


def build_mcq_prompt(mcq_count: int, options: str = "A, B, C, D") -> str:
    """
    Build the prompt for MCQ answer extraction.

    Args:
        mcq_count : Total number of MCQ questions on this paper.
        options   : Allowed answer options as a readable string, e.g. "A, B, C, D".

    Returns:
        A fully-formed prompt string ready to send to Ollama.
    """
    return f"""You are reading a student's handwritten MCQ answer sheet.

The paper has exactly {mcq_count} questions numbered 1 to {mcq_count}.
Valid options are: {options}.

IMPORTANT — a student may circle or write MORE THAN ONE option for a question.
- If only one option is written (e.g. "B"), the value is just "B".
- If multiple options are written (e.g. both "A" and "C"), join them with a comma in alphabetical order: "A,C".
- If a question is blank or completely unreadable, skip it entirely — do not include that key.

Return ONLY a JSON object — no explanation, no preamble, no trailing text.
Rules:
1. At most {mcq_count} key-value pairs.
2. Keys: "Q1", "Q2", ..., "Q{mcq_count}".
3. Values: one or more uppercase letters from [{options}], comma-separated and sorted (e.g. "A", "B", "A,C", "B,D").

Examples:
  Single answer  → {{"Q1": "A", "Q2": "C"}}
  Multi answer   → {{"Q1": "A,C", "Q2": "B"}}
  Mixed          → {{"Q1": "A", "Q2": "B,D", "Q3": "C"}}

Now extract the answers from the answer sheet image."""


# ── Prompt variants (for future use) ─────────────────────────────────────────

def build_mcq_verification_prompt(mcq_count: int, first_pass: dict) -> str:
    """
    Second-pass prompt: give the model its first-pass extraction and ask it
    to verify/correct. Use when confidence is low.

    Args:
        mcq_count  : Number of questions on the paper.
        first_pass : Dict of first-pass answers, e.g. {"Q1": "A", "Q3": "C"}.
    """
    import json
    first_json = json.dumps(first_pass)
    return f"""You are verifying a handwritten MCQ answer sheet extraction.

The paper has {mcq_count} questions (Q1 to Q{mcq_count}).
A first reading produced these answers: {first_json}

Look at the image again carefully.
- Confirm each answer is correct.
- Fill in any missing questions you can now read clearly.
- Correct any answers that look wrong.

Return ONLY a corrected JSON object with at most {mcq_count} entries.
Keys: "Q1" to "Q{mcq_count}".
Values: one or more uppercase letters (A–D), comma-separated if multiple (e.g. "A,C").
No explanation, just the JSON."""
