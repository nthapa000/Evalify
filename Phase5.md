# Phase 5 — MCQ + Numerical + Subjective Evaluation

## Overview

Phase 5 adds **subjective question grading** to the Evalify evaluation pipeline.  
Type 3 papers (`mcq_numerical_subjective`) now support:

- Section A: MCQ questions → exact-match letter grading (inherited from Phase 3/4)
- Section B: Numerical questions → exact-match/multi-accept grading (inherited from Phase 4)
- Section C: Subjective questions → **LLM rubric-based grading via Ollama** (new in Phase 5)

---

## Architecture

```
Student submits handwritten answer sheet image
          │
          ▼
   OllamaEngine.extract_mcq_numerical_subjective()
          │  (single vision call, parses 3 sections)
          ▼
   extracted = {
     "Q1": "C", ...,          ← MCQ answers
     "N1": "3.5", ...,        ← Numerical answers (remapped from sheet Q-labels)
     "S1": "full text...", ... ← Subjective answers (transcribed verbatim)
   }
          │
   ┌──────┴──────────────┐
   │                     │                      │
_grade_mcq()      _grade_numerical()    _grade_subjective()
   │                     │                      │
   └──────┬──────────────┘                      │
          │                          for each S_i:
          │                            grade_subjective_question(
          │                              student_answer = extracted["S_i"],
          │                              rubric         = paper.subjectiveRubrics[i],
          │                              ...
          │                            )
          │                              │
          │                          Ollama /api/generate (text-only, temp=0.1)
          │                              │
          ▼                          JSON response → marks_awarded
   ResultSummary persisted to MongoDB
```

---

## New Files

| File | Purpose |
|------|---------|
| `backend/app/prompts/prompt_mcq_numerical_subjective.py` | Vision extraction prompt for Type 3 answer sheets |
| `backend/app/prompts/prompt_subjective_grading.py` | Text-only LLM grading prompt per subjective question |
| `backend/app/services/subjective_grader.py` | Orchestrates Ollama LLM calls for subjective grading, fallback keyword matcher |

---

## Modified Files

| File | Change |
|------|--------|
| `backend/app/services/ollama_engine.py` | Added `extract_mcq_numerical_subjective()` method and `_parse_mcq_numerical_subjective_json()` parser |
| `backend/app/services/evaluator.py` | Added `_grade_subjective()`, wired Type 3 path, updated print helpers and MLflow logging |

---

## Rubric Schema (from RubricBuilder frontend)

Teachers define rubrics per question in the CreatePaper wizard (Step 4):

```json
{
  "key_concepts":        ["Newton's first law", "inertia", "net force"],
  "mandatory_concepts":  ["Newton's first law"],
  "marks_per_concept":   2,
  "model_answer":        "Newton's first law states that an object at rest..."
}
```

**Grading logic:**
- Each found concept → `marks_per_concept` marks
- Max per question = `len(key_concepts) × marks_per_concept`
- If ALL mandatory concepts absent → 0 marks
- Paraphrased answers are accepted (LLM semantic matching)
- OCR artefacts are tolerated (prompt instructs LLM not to penalise)

---

## Ollama Setup

### Vision model (extraction)
```bash
ollama pull llama3.2-vision:11b
```
Set via `OLLAMA_VISION_MODEL` env var (default: `llama3.2-vision:11b`).

### LLM model (grading)
By default uses the same vision model for text-only grading calls.  
To use a separate, lighter text model:
```bash
ollama pull llama3.1:8b
export OLLAMA_LLM_MODEL=llama3.1:8b
```

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_VISION_MODEL` | `llama3.2-vision:11b` | Vision model for sheet extraction |
| `OLLAMA_LLM_MODEL` | (same as vision model) | Text model for subjective grading |

---

## Evaluation Result Shape

```json
{
  "mcqScore":        8.0,
  "numericalScore":  6.0,
  "subjectiveScore": 14.0,
  "totalScore":      28.0,
  "maxScore":        40.0,
  "percentage":      70.0,
  "engine":          "ollama_real_mcq_numerical_subjective",
  "ocrConfidence":   0.9,
  "sheetType":       "handwritten"
}
```

MongoDB also stores `subjectiveDetail`:
```json
[
  {
    "question":         "S1",
    "question_text":    "Explain Newton's laws of motion.",
    "student_answer":   "Newton said objects at rest stay at rest...",
    "marks_available":  6.0,
    "marks_earned":     4.0,
    "status":           "graded_by_llm",
    "concepts_found":   ["Newton's first law", "inertia"],
    "concepts_missing": ["net force"],
    "mandatory_met":    true,
    "feedback":         "Good coverage of inertia but net force not addressed.",
    "ocr_issues":       false,
    "llm_detail":       { ... full LLM JSON response ... }
  }
]
```

---

## MLflow Metrics (new in Phase 5)

| Metric | Description |
|--------|-------------|
| `subjective_score` | Total subjective section marks |
| `llm_latency_s` | Total time spent on LLM grading calls |

New param: `subjective_count`

---

## Fallback Behaviour

If Ollama is unreachable or returns malformed JSON:
1. **Extraction** falls back to stub mode (random MCQ + numerical, placeholder subjective text)
2. **Grading** falls back to simple case-insensitive keyword matching

This ensures the pipeline never crashes — results are marked as evaluated even in degraded mode.

---

## Frontend (already implemented in Phase 1–4)

| Component | Status |
|-----------|--------|
| `CreatePaper.jsx` Step 4 | Subjective question inputs + RubricBuilder already wired |
| `RubricBuilder.jsx` | Concept editor with mandatory toggle already built |
| `Result.jsx` | `subjectiveScore` already rendered in Section Breakdown |
| `Submission.jsx` | Type 3 papers auto-select handwritten (OMR restricted to Type 1) |

---

## Testing Checklist

- [ ] Create a Type 3 paper with 5 MCQ + 3 Numerical + 2 Subjective questions
- [ ] Add rubric for each subjective question (at least 2 key concepts each)
- [ ] Upload a handwritten answer sheet image
- [ ] Verify extracted subjective text in server logs
- [ ] Verify LLM grading JSON in server logs
- [ ] Verify result page shows all three section scores
- [ ] Test with Ollama down → confirm keyword fallback runs without error
- [ ] Test blank subjective answer → confirm 0 marks, no crash
- [ ] Test missing mandatory concept → confirm 0 marks for that question
