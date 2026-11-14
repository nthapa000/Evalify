# Evalify v2 — pipeline plan

Status: **15 Nov 2026**, branch `pipeline-v2`. This replaces the Ollama/llama-vision design in
`EVALIFY_PLAN.md` and builds on `evalify_model_plan (1).md`. Every choice below comes from a measured
run (see [eval/reports/RESULTS.md](eval/reports/RESULTS.md)) or a decision with the user (see
[decision.md](decision.md)). Items marked **(pending)** are not decided or not implemented yet.

---

## 1. Principles

1. **Models read, code grades.** VLMs turn images into answers or per-point verdicts; marks are always
   computed in Python (MCQ exact set, numeric rule, rubric sums). No model decides a total.
2. **Two independent readings from different model families** for every auto-accepted answer; a third
   model breaks ties; whatever is still unsure goes to a **TA**. The target metric is **zero silent
   errors** (auto-accepted answers with wrong marks), then as few TA items as possible.
3. **Self-hosted and pinned.** All models run on our own GPUs (vLLM, IIT Jodhpur cluster, node cn07),
   pinned to an exact repo revision; every result records model versions and prompt version (MLflow).
4. **The teacher stays in control:** OMR templates, rubrics and (later) RAG-drafted answer keys are used
   only after the teacher confirms them.

## 2. Teacher's grading rules (from the user)

| Item | Rule |
|---|---|
| MCQ (handwritten or OMR) | exact set of letters; order does not matter; multiple-correct questions allowed |
| OMR bubble | a **partly filled** bubble counts as marked; sheets are always black & white print |
| Numerical | the **number in the key's unit**, within the key's tolerance (±0.001 on our test papers); the **unit is ignored** (missing / different unit is only flagged); **no unit conversion** (key 2500 m: `2500`, `2500 m`, `2500 km` ✔, `2.5 km`, `2500.5` ✘) |
| Subjective | marks per rubric point; spelling and grammar never cost marks |
| Students | write only final answers on type A/B papers; rough work is on a separate, ungraded sheet |

## 3. Pipeline

```
photo / scan ──► quality gate ──► per paper type ──► agreement / routing ──► code grading ──► result + TA queue
                 (flatten, deskew,                                                              (MLflow log)
                  blank / show-through)
```

### 3.1 Ingest — quality gate (`backend/app/pipeline/quality.py`)
Page detection + perspective flattening, deskew, blur / glare / contrast checks, blank-page and
show-through detection (blank backs are skipped). A page that fails the gate sends its sheet to a TA.
- **(pending fix)** the glare check rejects 9 of 30 phone photos that every reader handled → loosen it.
- **(pending fix)** ghost answers: show-through from the back of a blank answer sheet is read as answers
  by OCR models → detect mirrored text / rely on whole-page VLM reading (which ignores it).

### 3.2 Type A — MCQ on an OMR sheet
1. Once per paper: the teacher uploads a **blank sheet**; the bubble map is learned (bubbles, grouping,
   question numbers read by the VLM) and shown as a preview; **used only after the teacher confirms**.
2. Per student: align photo to the blank (ORB + homography) → **template bubble reader** (darkness above
   the blank, threshold 0.10; partial fills measured ≥ 0.46, empty ≤ 0.07).
3. **Qwen3.8 reads the same page** (which bubbles are filled) as an independent check.
4. Agree → accept; disagree, fill near the threshold, or page not aligned → TA.
5. Code grades: exact set.
Measured: template + Qwen check — 0 silent errors, 299/300 auto, 1 to TA. Template alone on the
Tamaulipas real scans: 99.3 %.

### 3.3 Type A (handwritten letters) and Type B — MCQ + numerical
1. **Gemma 4 31B** reads the whole page → JSON list of every answer.
2. **Qwen3.8 27B** reads the whole page independently.
3. Gemma and Qwen agree → accept.
4. Disagree / one abstains → **GLM-OCR** reads the whole page (lines parsed as "N. answer"); 2 of 3
   agree → accept (Chandra OCR 2 is the backup tie-breaker if GLM-OCR is down).
5. Still no majority → TA.
6. Code grades: MCQ exact set; numerical rule from §2 (`numeric.compare`).
Measured (own sheets): 0 silent errors; MCQ 147/150 auto, MCQ+numerical 73/75 auto. The old crop-based
pipeline was also safe but sent 22 and 32 answers to TAs.
- **(pending)** switch the code from the crop pipeline to this whole-page majority (needs the user's go-ahead
  after the type-C run).

### 3.4 Type C — MCQ + numerical + subjective
- MCQ and numerical parts: as §3.3.
- Subjective answers:
  1. **Segmentation** (Qwen3.8) finds each written answer by its question number → one crop per answer
     (answers continuing over pages are stitched).
  2. **Two transcriptions** per answer: Qwen3.8 (verbatim prompt; best on paragraphs, CER 0.071) and an
     OCR specialist (PaddleOCR-VL or GLM-OCR). Low similarity → flag.
  3. **Grader 1 + grader 2** from different families (Qwen3.8 and Gemma 4) judge **each rubric point**:
     quote the student's words, then verdict *present / partial / absent*. Code checks every quote really
     appears in the transcript.
  4. Python sums: 1 × marks per present point, 0.5 × per partial point, mandatory-point rule, cap at max.
  5. Graders disagree by more than the threshold, low confidence, missing evidence, or a transcript
     problem → TA.
- Grader prompt: **v2** (`grade_prompt_v2`, prompt version p4) fixes spelling-neutral marking, hedged /
  contradictory answers, bare keywords, instruction text inside answers, quote-before-verdict, half
  credit. **(pending)** v1 vs v2 and thinking on/off are to be measured on all 50 Mendeley sheets against
  the teacher's marks before v2 becomes the default.
- **(pending)** which models grade (Qwen + Gemma now; gpt-oss as text-only option) is decided by the same run.

### 3.5 Routing to a TA (`backend/app/pipeline/routing.py`, thresholds in `infra/routing.yaml`)
Page failed quality gate · readers disagree with no majority · OMR fill within 0.05 of the threshold ·
numeric value unparseable · grader disagreement / low confidence / evidence not found ·
answer not located. The TA sees the crop, every reading and the reason. **(pending)** TA review UI.

## 4. Models (cn07, 2 GPUs: RTX A6000 48 GB + RTX PRO 6000 96 GB)

| Role | Model (pinned in `infra/models.yaml`) |
|---|---|
| Page reader 1 / grader 2 | Gemma 4 31B FP8 |
| Page reader 2 / OMR check / segmenter / transcriber A / grader 1 | Qwen3.8 27B FP8 |
| Tie-break reader | GLM-OCR (backup: Chandra OCR 2) |
| Transcriber B (subjective) | PaddleOCR-VL 1.6 or GLM-OCR |
| Not used | legacy OpenCV OMR (83/300 wrong), Gemma for OMR (57/300 wrong), LLM numeric grading (Qwen broke the tolerance rule) |
| Not yet tested | Nanonets-OCR2-3B, gpt-oss-20b (not loaded in the current GPU job) |

## 5. Teacher setup flow

1. Create paper → type, question counts, marks, negative marking.
2. Answer key: MCQ letters, numerical value + unit + tolerance.
3. Subjective: question text, reference answer, rubric points (marks per point, mandatory points,
   half credit allowed or not).
4. OMR papers: upload the blank sheet → check the preview → confirm.
5. **(planned) RAG answer-key assistant** — §6.

## 6. Planned: RAG answer-key assistant (after the current evaluation runs)

**Purpose — one thing only:** help the teacher write the *sample answer key* (reference answer +
rubric points) for subjective questions. It is **never used while grading students**.

Flow:
1. On the subjective-question step the teacher may choose **"Draft answer from my reference material"**
   (optional; typing the answer by hand stays the default).
2. The teacher uploads reference files (PDF / DOCX / slides / notes / textbook chapter).
3. Ingest: text extraction (OCR for scanned pages) → chunks with page numbers → embeddings from a
   self-hosted embedding model → a per-paper vector index.
4. For each question: retrieve the top passages for the question text → an LLM (Qwen3.8 / Gemma 4)
   drafts, **only from those passages**, in Evalify's format: reference answer, rubric points with
   marks, suggested mandatory points — each point citing the passage/page it came from.
   If the material does not cover the question, it says so instead of inventing an answer.
5. The teacher sees the draft next to the cited passages, **edits freely**, and approves. Only the
   approved version is saved on the paper (`subjectiveRubrics`), with a note that it was RAG-drafted.
6. Logged: reference file hashes, retrieved chunks, model + prompt version (MLflow), teacher edits.

Open choices at implementation time: embedding model, vector store (e.g. FAISS / Chroma / MongoDB
vector index), chunk size; evaluation = how much teachers edit the drafts.

## 7. Evaluation and MLOps

- Harness in `eval/` (metrics, bake-offs, end-to-end, `arch_sweep.py`); every run's analysis is kept
  as Markdown in `eval/reports/` and indexed in [eval/reports/RESULTS.md](eval/reports/RESULTS.md).
- Metrics: silent errors, auto-accept rate, TA items, read accuracy, CER/WER (transcripts),
  QWK / MAE / exact-match vs teacher marks (subjective), seconds per sheet.
- Datasets: own test sheets (45; OMR, handwritten MCQ, MCQ+numerical), Tamaulipas OMR scans,
  **Mendeley exam set (50 sheets, type C — main set)**, **EDU-CIRCUIT-HW** (numerical with working,
  pending download by the user).
- MLflow: model repo@revision, prompt version, thresholds, per-sheet outputs.

## 8. Next steps (in order)

1. User reviews the 15 Mendeley rubrics (`eval/reports/mendeley/RUBRICS_REVIEW.md`).
2. Run all 50 Mendeley sheets: grader v1 vs v2, thinking on/off, Qwen vs Gemma graders → compare with
   teacher marks; pick the subjective setup.
3. EDU-CIRCUIT-HW (after the user downloads it): numerical answers with working.
4. Finalise the order; switch MCQ/numerical to whole-page majority; v2 grader default.
5. Fix the glare gate and show-through ghosts; calibrate routing thresholds.
6. TA review UI; then the RAG answer-key assistant (§6).
