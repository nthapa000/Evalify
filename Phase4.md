# Phase 4 — MCQ + Numerical Evaluation

**Status:** Complete  
**Date:** April 2026

---

## What Phase 4 Adds

Phase 4 extends Evalify to support **Type 2 papers: MCQ + Numerical**.

Key design choices (kept simple by intent):

| Feature | Decision |
|---------|----------|
| Numerical answer matching | Exact string match against teacher's accepted-answer list |
| Multiple accepted answers | Teacher lists e.g. `["3", "3.0", "3.00"]` — any match = full marks |
| Partial credit | No — it's all-or-nothing per question |
| Answer sheet convention | MCQ section first (Q1..Qn), Numerical section after (N1..Nm) |
| Student labelling | Students don't write "N1:" — the system extracts section by section |

---

## Files Changed

### New Files

| File | Purpose |
|------|---------|
| `backend/app/prompts/prompt_mcq_numerical.py` | Separate prompt for combined MCQ + Numerical extraction sent to Ollama |
| `Phase4.md` | This documentation file |

### Renamed

| Old | New | Reason |
|-----|-----|--------|
| `backend/app/services/trocr_engine.py` | `backend/app/services/ollama_engine.py` | TrOCR was rejected in Phase 3. The engine now uses Ollama exclusively. Renaming removes the misleading name. |

### Modified Files

| File | What Changed |
|------|-------------|
| `backend/app/services/ollama_engine.py` | Complete rewrite: renamed class `OllamaEngine`, added `extract_mcq_numerical()`, added latency tracking to every Ollama call |
| `backend/app/services/evaluator.py` | Added `_grade_numerical()`, updated `evaluate_submission()` for Type 2, added `ollama_latency_s` to MLflow logs, updated all imports to `OllamaEngine` |
| `backend/app/main.py` | Updated warning message (TrOCR → Ollama) |
| `frontend/src/pages/teacher/CreatePaper.jsx` | Replaced old tolerance-based numerical UI with accepted-answer list UI; added convention guidance banner; updated `handleSubmit` to convert UI format to backend list format |

---

## Workflow Diagram

```
────────────────────────────────────────────────────────────────
  TEACHER CREATES TYPE 2 PAPER (MCQ + Numerical)
────────────────────────────────────────────────────────────────

  Step 1: Select "MCQ + Numerical" paper type

  Step 2: Set question counts and marks
            MCQ:       e.g. 10 questions × 2 marks
            Numerical: e.g. 5 questions  × 4 marks

  Step 3: Enter answer key
    ┌─── MCQ section ──────────────────────────────┐
    │  Q1: [A] [B] [C] [D]   ← click to select    │
    │  Q2: [A] [B] [C] [D]                         │
    │  ...                                          │
    └──────────────────────────────────────────────┘
    ┌─── Numerical section ────────────────────────┐
    │  Convention banner:                          │
    │   "MCQ section first, then Numerical"        │
    │                                              │
    │  N1  [Single answer ▼]  "3.5"               │
    │  N2  [Multiple accepted ▼]                   │
    │       1. "3"                                 │
    │       2. "3.0"          + Add accepted answer│
    │  ...                                          │
    └──────────────────────────────────────────────┘

  Step 4: Configuration (negative marking etc.)
  Step 5: Review → Create Paper

  Backend stores:
    numericalAnswers: { "N1": ["3.5"], "N2": ["3", "3.0"], ... }


────────────────────────────────────────────────────────────────
  STUDENT SUBMITS TYPE 2 ANSWER SHEET
────────────────────────────────────────────────────────────────

  Student uploads photo/scan of handwritten sheet
  (sheet has MCQ section first, then Numerical section)


────────────────────────────────────────────────────────────────
  EVALUATION PIPELINE
────────────────────────────────────────────────────────────────

  evaluator.evaluate_submission()
       │
       ├─ sheet_type = "omr"?
       │     └─ OMREngine.process_image()
       │          returns only Q1..Qn (OMR cannot detect numbers)
       │
       └─ sheet_type = "handwritten"?
             └─ numerical_count > 0?
                   YES → OllamaEngine.extract_mcq_numerical()
                         │
                         ├─ Build combined prompt
                         │   (prompt_mcq_numerical.py)
                         │
                         ├─ POST image to Ollama /api/generate
                         │   (llama3.2-vision:11b, ~14s on V100)
                         │
                         ├─ Track latency_s
                         │
                         └─ Parse JSON response:
                              { "mcq": {Q1..Qn},
                                "numerical": {N1..Nm} }
                              → merged dict {Q1..Qn, N1..Nm}

                   NO  → OllamaEngine.extract_mcq()
                         (Phase 3 path, Q keys only)

       │
       ├─ _grade_mcq()       → mcq_score, mcq_detail
       │   exact frozenset match; negative marking optional
       │
       ├─ _grade_numerical() → numerical_score, numerical_detail
       │   for each N1..Nm:
       │     student_answer.strip() in accepted_list? → full marks
       │     else → 0 (no partial credit)
       │
       ├─ total_score = mcq_score + numerical_score
       │
       ├─ Persist to MongoDB
       │   result.mcqScore, result.numericalScore, result.totalScore
       │   mcqDetail[], numericalDetail[]
       │
       └─ MLflow log_evaluation_run()
            metrics: mcq_score, numerical_score, total_score,
                     accuracy, eval_latency_s, ollama_latency_s,
                     ocr_confidence
            params:  engine, sheet_type, mcq_count, numerical_count,
                     ollama_mode


────────────────────────────────────────────────────────────────
  RESULT RETURNED TO STUDENT
────────────────────────────────────────────────────────────────

  {
    mcqScore:       8.0,
    numericalScore: 12.0,
    totalScore:     20.0,
    maxScore:       30.0,
    percentage:     66.7,
    engine:         "ollama_real_mcq_numerical"
  }
```

---

## Numerical Grading Logic

```python
def _grade_numerical(extracted, answer_key, numerical_count, default_marks, per_q_marks):
    """
    For each N1..Nm:
      accepted = answer_key[nid]   # e.g. ["3", "3.0", "3.00"]
      student  = extracted[nid]    # e.g. "3"

      if student.strip() in accepted → status="correct", earn full marks
      else                           → status="wrong",   earn 0
    """
```

**Why exact string match?**
The teacher is responsible for listing all accepted forms. This keeps the logic deterministic — there is no ambiguity about whether "3.0" equals "3". If both should be accepted, the teacher adds both.

---

## Ollama Prompt (MCQ + Numerical)

File: `backend/app/prompts/prompt_mcq_numerical.py`

```
You are reading a student's handwritten answer sheet.

The sheet has TWO sections in this order:

SECTION 1 — MCQ (N questions, Q1 to QN)
SECTION 2 — Numerical (M questions, N1 to NM)

Return ONLY:
{
  "mcq":       {"Q1": "A", "Q2": "B,C", ...},
  "numerical": {"N1": "3.5", "N2": "42", ...}
}
```

The two-key structure prevents the parser from confusing a numerical answer like `"1"` with a MCQ choice `"A"`.

---

## MLflow Changes (Phase 3 backfill + Phase 4)

Previously, Ollama call latency was not tracked separately. Phase 4 adds:

| Metric | Description |
|--------|-------------|
| `ollama_latency_s` | Wall-clock time for the Ollama HTTP call |
| `numerical_score` | Marks earned on numerical section |
| `eval_latency_s` | Total evaluation time (extraction + grading + DB write) |

New params logged:

| Param | Description |
|-------|-------------|
| `numerical_count` | Number of numerical questions |
| `ollama_mode` | `"real"` (GPU) or `"stub"` (Ollama down) |

---

## What Phase 4 Does NOT Include

- **Partial credit for numerical** — out of scope by design.
- **Tolerance/range matching** — removed in favour of teacher-defined accepted lists.
- **OMR for numerical** — OMR bubble sheets cannot represent numbers; Type 2 requires handwritten sheet type.
- **Type 3 subjective grading** — Phase 5.

---

*Last updated: April 21, 2026*
