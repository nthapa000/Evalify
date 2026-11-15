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
- MCQ and numerical parts: as §3.3 (Mendeley: ~1 real error in 1,000 MCQ, 98.7 % auto, 157 s/paper).
- Subjective answers (measured on 50 Mendeley sheets, `eval/reports/mendeley_sweep/FINDINGS.md`):
  1–2. **No crops: whole-page transcription grouped by question label** (run 9): Qwen3.8 (`page_text_prompt`,
     JSON) and Gemma 4 (`page_text_plain_prompt`, plain text with [[Qnn]] markers — its JSON mode runs away)
     each transcribe every page; code joins pages by label, drops a crossed-out attempt when there is a
     rewrite. All labels (MCQ too) are passed so "7. A" is not taken for Q27. Finds 555/564 answers (old box
     segmentation 523). ~187 s/paper. Fallback: `segment_prompt_v2` boxes + Qwen/GLM crops (80 s/paper).
     GLM-OCR is not used for subjective answers (drops margin labels).
  3. **One grader: Gemma 4 + prompt v2** (`grade_prompt_v2`, p4) judges each rubric point: quote, then
     *present / partial / absent*. Best of 5 set-ups (MAE 0.665 / 2, QWK 0.41; better than Qwen v1/v2,
     Qwen thinking, Gemma v1 at 95 %). A second grader added no accuracy → not used. Thinking off.
  4. Python sums: 1 × marks per present point, 0.5 × per partial point, mandatory-point rule, cap at max.
  5. TA: answer not located (never an automatic 0), transcript problem, low confidence / missing evidence.
- **Teacher calibration** (run 9): the teacher marks 3–5 sheets; the mean difference teacher − grader is added
  to every mark (rounded to 0.5, clipped): MAE 0.62 → 0.43, within 0.5: 55 % → 83 %. Teacher setting; both
  the rubric mark and the calibrated mark are kept.
- Known gap (before run 9): the grader is 0.57 marks stricter than the Mendeley teacher (lenient teacher ≈ half; segmentation
  faults; some over-strictness). **(pending, needs go-ahead)** segmentation fixes (struck-out text,
  out-of-order answers, mixed crops) and **teacher calibration** (teacher marks ~5 sheets → examples in the
  grader prompt). Type C stays TA-reviewed until these are measured.
- Numbers inside free working (EDU-CIRCUIT-HW): best pair Chandra→Qwen + Gemma still 30 / 702 silent → papers
  should give a **final-answer box** for numerical questions.

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
  **Mendeley exam set (50 sheets, type C — main set)**, **EDU-CIRCUIT-HW** (numerical with working).
- MLflow: model repo@revision, prompt version, thresholds, per-sheet outputs.

## 8. Next steps (in order)

1. ~~Rubric review; 50 Mendeley sheets; EDU-CIRCUIT-HW~~ — done 15 Nov (`eval/reports/RESULTS.md` runs 7, 8).
2. ~~Segmentation fixes for type C + teacher calibration~~ — done (run 9). Next: UI review to match the pipeline (user asked, after models load).
3. Switch MCQ/numerical to whole-page majority; v2 grader (Gemma) default for subjective.
4. Fix the glare gate and show-through ghosts; calibrate routing thresholds.
5. TA review UI; then the RAG answer-key assistant (§6).
6. (later, user request) Student-facing marking breakdown: per question and rubric point — evidence quote,
   verdict, marks (+ one-line reason); calibration shown as a separate adjustment; TA overrides shown; visible
   after the teacher releases results; per-point re-evaluation request → TA queue.
