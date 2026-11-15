# Evalify — decision log

Decisions made while implementing `evalify_model_plan (1).md` (model + hardware plan,
14 Nov 2026). Newest at the bottom. Each entry: what was decided, why, and who decided.

## 2026-11-14

### Scope and hardware
- **Implement the plan on 2 GPUs of cn07** (user: "we have two cn07 gpu free"). Build and test on
  the cluster; no deployment yet.
- **cn07 GPUs are mixed and untyped.** Slurm gave us one RTX A6000 (48 GB, Ampere) and one
  RTX PRO 6000 Blackwell (96 GB). The gres has no type labels, so a job cannot ask for Blackwell
  only, and Slurm hands out the lowest free GPU index first (index 0 = the A6000).
  **User chose to keep the A6000 + Blackwell pair** (option 1) over a single Blackwell or
  asking the admin to label GPU types. Admin labelling (`gres.conf` `Type=`) remains the real fix.
- **Serving profiles use GB budgets, not per-GPU fractions.** `infra/cluster/serve.py` reads each
  allocated GPU's real memory and packs models largest-first; models that don't fit are skipped
  and logged. Reason: the GPU mix is not predictable.

### Environment and storage
- **No Apptainer on the cluster** → vLLM runs from a conda env on `/scratch`, pinned to
  **vLLM 0.32.0** (0.33.0 was only 12 days old). The pin replaces the plan's "pinned container".
- **Everything heavy lives on `/scratch`** (env, weights, caches): reading `/csehome` from cn07 is
  very slow (200 MB ≈ 130 s, `import torch` ≈ 3 min).
- **CUDA compiler wheels pinned to 13.0** to match the CUDA runtime; newer nvcc (13.5) broke
  FlashInfer's JIT builds.
- **`CUDA_DEVICE_ORDER=PCI_BUS_ID`** in the serving job: CUDA's default fastest-first order
  swapped the two cards relative to `nvidia-smi`, so models landed on the wrong GPU.
- **FlashInfer cache moved to `/scratch`** (`FLASHINFER_WORKSPACE_BASE`).

### Models
- **Downloads: stage 1 + stage 2** (user approved). Qwen3.8-27B-FP8, Chandra OCR 2,
  PaddleOCR-VL-1.6, GLM-OCR, Nanonets-OCR2-3B, Gemma 4 31B FP8, gpt-oss-20b ≈ 101 GB.
  **Stage 3 (Qwen3.5-122B) not downloaded**: only if the grader bake-off justifies it, and it
  needs ≥ 100 GB free (64 GB free now).
- **Every model pinned to a full commit SHA** in `infra/models.yaml` (reproducible bake-offs).
- **Default reader B = PaddleOCR-VL, not Chandra.** Chandra OCR 2 is a Qwen3.5 fine-tune, the same
  family as reader A (Qwen3.8), so its errors are less independent. The bake-off measures the
  shared-error rate per reader pair and decides.
- **Bake-off layout on 48 + 96 GB:** Qwen3.8 + PaddleOCR-VL + GLM-OCR + Chandra on the
  Blackwell; Gemma 4 alone on the A6000. Nanonets and gpt-oss-20b don't fit at the same time;
  gpt-oss runs in the separate `graders` profile.
- **Fallback if FP8 Gemma fails on the Ampere A6000:** `QuantTrio/gemma-4-31B-it-AWQ`
  (20.5 GB, Apache 2.0). Not downloaded unless needed.
- **Hugging Face cache uses a shared blob store** (huggingface_hub 2.x), so model sizes and
  deletion go through `scan_cache_dir`, not per-model folders.

### Pipeline design (follows plan §4)
- **One pipeline for all paper types; method chosen per question type.** OMR = OpenCV,
  MCQ/numeric = two readers + code, subjective = two readers + per-concept grader.
- **Numbers are compared in code** (`app/pipeline/numeric.py`: fractions, units, tolerance,
  scientific notation). Legacy exact-string keys still work; `3` now matches a key of `3.0`.
- **Subjective marks are summed in Python** from per-concept yes/no decisions; the model never
  reports the final mark. Evidence quotes are checked against the transcripts.
- **Readers must transcribe verbatim** (do-not-correct prompt). The bake-off also runs a
  plain prompt to measure the effect.
- **Routing to a TA** on: reader disagreement, unclear/low-confidence reads, thin OMR margin,
  unparseable numbers or unit problems, low concept confidence, evidence not found, graders
  differing by > 1 mark, failed quality gate. Thresholds are calibrated on the dev split
  (`eval/calibrate.py` → `infra/routing.yaml`).
- **Backend degrades instead of breaking:** each role has a fallback list of models; with no
  model server up, handwritten sheets use the legacy Ollama path (`EVALIFY_PIPELINE=legacy`
  forces it). OMR always uses the new path (no models needed).
- **Glare check only on photos**, not on scans (a scan's white paper looked like glare).

### Code clean-up (user request: simplify, one-line comment per block, remove unused files)
- Removed unused code: `ml/` mock services, broken `tests/verify_phase3.py` + debug images,
  `prompt_rubric_extraction.py`, `mockData.js`, `UploadZone.jsx`; merged three extraction
  prompts into one and `pdf_extractor.py` into `pdf_utils.py`.
- Dropped unused dependencies: torch, transformers, easyocr, pdfplumber.
- `.gitignore` rule `models/` was hiding `backend/app/models` → changed to `/models/` and
  recreated the Pydantic models.
- Bugs fixed: keyword fallback graded an empty answer (always 0); teacher dashboard question
  count ignored subjective questions; `1.2e-3` was parsed as 1.2 with unit "e-3".
- Frontend: only comments + small safe simplifications (no visual testing possible here).
  Note: the repo has no ESLint config, so the frontend lint CI job cannot lint.

### Git and jobs
- **Work is on branch `pipeline-v2`, committed locally, never pushed** (CLAUDE.md: don't push
  unless told).
- **Cancelled job 48689** (submitted by another session; its download check could never
  pass) — user approved. Later serving jobs were cancelled/resubmitted by this session while
  fixing startup errors.

### Open items
- Real labelled sheets needed (30–50 to compare models; format in `eval/README.md`).
- Bake-off results will decide final readers/graders, then update `roles:` and the `tier1`
  profile in `infra/models.yaml` and delete losing weights.

### Serving fixes, continued (14:20)
- **`--max-num-seqs` capped** (128 for big models, 64 for OCR models): Qwen3.8's hybrid
  attention needs one cache block per parallel request and failed at vLLM's default of 1024.
  Grading never needs that many parallel requests.
- **FlashInfer sampler disabled** (`VLLM_USE_FLASHINFER_SAMPLER=0`): its JIT build kept failing,
  and we only use greedy decoding (temperature 0), which doesn't need it.
- Job 48694 cancelled by this session (Qwen and Gemma had failed in it); resubmitted as 48695.

### Test data (discussion with user, 14:20)
- User wants a **small, hand-checkable test set: 10–15 sheets per paper type** (A: MCQ only,
  B: MCQ + numerical, C: MCQ + numerical + subjective), with OCR validated separately on a
  bigger set if available. Proposal and open questions below in this file once agreed.
- Licences checked via the APIs: Tamaulipas OMR, FERMAT, Handwritten ASAP, SciEntsBank and
  Mohler are all **CC BY 4.0** (dataset.md had several as "not confirmed").
- Mendeley exam set: `Teacher_manual_marks_Anonymized.csv` columns 1–20 hold each student's
  **chosen MCQ letter**, so MCQ reading can be checked directly. **Privacy issue:**
  `Student_MCQ.csv` in the same dataset contains real student names and IDs, despite the
  README saying the data is anonymised, and the PDFs are named by real IDs. We will use only
  the anonymised CSV and never copy names into our files.

### Serving is up (14:30)
- Job **48695** started 5 servers on cn07: Gemma 4 FP8 on the RTX A6000 (FP8 works there,
  so the AWQ fallback is **not** needed); Qwen3.8, PaddleOCR-VL, GLM-OCR, Chandra on the
  RTX PRO 6000. Nanonets and gpt-oss-20b left out for space.

### Layout-independent OMR (user approved the recommended approach)
- **Problem:** each teacher may use a different bubble layout; the old engine guessed
  (options left→right, column-first numbering, ≤ 5 options, printed numbers ignored).
- **Decision: learn the layout once per paper from a blank sheet** (`app/pipeline/omr_template.py`):
  find bubbles → group them into questions, choosing options-in-a-row vs options-in-a-column
  by which gives consistent group sizes → the VLM reads the **printed** question numbers
  (fallback: reading order matched to the layout) → teacher checks a labelled preview.
  Student photos are aligned to the blank (ORB + homography); each bubble's darkness is
  measured **minus the blank's own darkness** (printed letters inside bubbles).
- Marking stays deterministic; the VLM only labels the printed template, so the
  silent-correction risk does not apply.
- **The template is used only after the teacher ticks "confirmed"** — a wrong map would
  mis-grade a whole class. Unconfirmed → layout-free engine as before.
- A page that cannot be aligned falls back to the layout-free engine and every question on it
  is routed to a TA.
- Darkness relative to local paper (not a binary ink mask), so light pencil (≈ 0.5) is read.
- Verified: synthetic sheets in two layouts (3 columns × horizontal options; vertical options
  in bands), photographed with tilt / perspective / uneven light, all answers read incl.
  light pencil, double mark and blank; live test: Qwen3.8 numbered a row-major sheet 24/24
  correctly where reading order would have been wrong.
- UI: "Blank OMR sheet" upload + preview + confirm checkbox added to the create-paper wizard
  (Step 3, MCQ papers).

### OMR tested on real scans: Tamaulipas (CC BY 4.0), 14 Nov
- Downloaded only the first 80 MB of the 6 GB zip (75 sheets + labels) into
  `/scratch/m25csa019/evalify/datasets/tamaulipas/`; labels give the human-read bubble per item
  (X = blank, M = multiple). The dataset has no answer key or marks — not needed for OMR, since
  marks are computed in code from the bubbles read.
- The dataset has **no blank sheet** → `eval/tamaulipas_omr.py` synthesises one from the 19
  Grade 12 sheets of the same form (align, keep the lightest value per pixel); the 12 test
  sheets (School001/Grade10) are not used to build it.
- Changes forced by real scans (thin, faint, orange printed bubbles with letters inside):
  darkest-colour-channel darkness; **Hough circles + edge ring check** (instead of contours);
  grouping by the regular option spacing; **grid completion** with one sheet-wide row pitch,
  shared row span across columns, and snapping filled-in rows onto their faint rings;
  **per-sheet print offset** (median bubble darkness) removed before the 0.10 threshold.
- **Result on 12 real sheets (1,080 items):** accuracy **99.3%**; **88%** auto-accepted with
  **99.9%** accuracy; **1 silent error** (a light mark on File0002 Q63); 7 other errors all went
  to a TA. The old layout-free engine scored 0% on this layout (it can't parse it).
- Routing threshold for OMR margin is still the default 0.05; calibrate on more sheets later.

### Handwritten pipeline smoke test (synthetic example set, live models), 14 Nov
- **User: spelling does not matter** (TAs ignore it in university exams). So the
  over-correction check now targets **content** corrections only (wrong number / fact / step);
  the example set plants a wrong fact ("water and nitrogen"), not a misspelling. Qwen3.8 did
  silently fix "proccess" → "process" despite the verbatim prompt — harmless for grading;
  neither reader corrected the planted wrong fact.
- **Prompts p2: label-independent.** Telling the reader "this is question Q1" made Qwen answer
  "blank" when the written label looked different (script "Q" ≈ "2"). Closed-form prompts now
  say "one answer, ignore the label"; copied labels are stripped in code.
- **Guided-JSON whitespace runaway** (Gemma 4 emitted whitespace until max_tokens; vLLM's
  per-request `disable_any_whitespace` did not stop it): the client now repairs truncated JSON
  and retries once without the schema.
- **A reader's value is graded even when it says "unclear"** (the question is still routed),
  so the TA sees what was read.
- **Contrast check** = paper brightness − darkest 1000 pixels (a sparse page has low global
  std but is perfectly readable).
- Result on 2 synthetic sheets (8 answers): every auto-accepted answer correct (MCQ, MCQ
  wrong-answer verdict, both subjective marks incl. both graders agreeing); PaddleOCR read all
  MCQ/numbers right; Qwen3.8 returned empty on some script-font crops → routed via reader
  disagreement. **The synthetic font is now the limit — real handwritten sheets are needed.**

### Third reader for abstentions (user decision), 14 Nov
- **Why routed before:** at grading time nobody knows which reader is right; exact answers need
  two independent readings, so a lone reading went to a TA.
- **User decision: abstentions get a tie-break reader instead of a TA.** If one reader answered
  and the other abstained (blank / unclear / failed / empty), a third reader (`reader_c` role:
  GLM-OCR → Gemma 4 → Chandra, never the same model as A or B) reads the answer. If it agrees
  with the answering reader (2 of 3), the answer is auto-accepted; otherwise it goes to a TA
  with "tie-break reader did not confirm".
- **Real conflicts still always go to a TA** (both answered, different values) — a third
  reader is not used to out-vote one of two confident readers.
- MCQ and numerical only; subjective keeps its transcript-similarity + grader checks.
- Smoke test after the change: all 8 synthetic answers auto-graded correctly, 0 routed
  (3 accepted by B + C after Qwen3.8 abstained).

### Reader comparison on 12 real Mendeley sheets (user request), 14 Nov
- Dataset downloaded directly (no browser needed): `https://data.mendeley.com/public-api/zip/sf3kvjwknt/download/1`
  (145 MB) → `/scratch/m25csa019/evalify/datasets/mendeley_sf3kvjwknt/`. Labelled set built by
  `eval/build_mendeley.py` (Student_1–12; gold from the anonymised CSV only — never `Student_MCQ.csv`).
- **User asked Claude to do the visual check itself; user will verify.** Claude transcribed the short
  answers of Student_1–3 from the page images and checked all 30 disputed MCQ crops. All of it is
  documented per sheet in `eval/reports/mendeley/` (Student_N.md, README.md, FINDINGS.md, review/).
  Answer crops and page images stay local (git-ignored). Claude is not part of the grading pipeline;
  the page images it viewed were sent through the conversation (fine for this public CC BY set; for
  real student sheets prefer a human transcriber).
- Pipeline changes forced by these real sheets: blank / show-through backs skipped (handwriting-ink
  fraction with ruled lines removed: backs ≤ 0.074 %, written pages ≥ 0.22 %); vertical crop padding
  capped at ¼ of the answer height (crops were picking up neighbouring MCQ lines); papers can use
  continuous numbering (short answers labelled 21–35 instead of S1…).
- Rubric for Q21–Q35 drafted by Claude from `answerkey.txt` (2 concepts × 1 mark) — to be reviewed.
- **Results:** MCQ — PaddleOCR 94.6 %, GLM-OCR 91.2 %, Chandra 89.2 %, Qwen3.8 76.7 % (mostly
  abstentions on unusual "D"s). Short answers (CER) — Qwen3.8 0.071 (best), GLM 0.097, Paddle 0.102,
  Chandra 0.181 (worst). Chandra is **not** better than Qwen3.8 as reader A on this data.
- **Pending user decision:** reader roles per question type (proposal in FINDINGS.md: MCQ/num A =
  PaddleOCR, B = GLM-OCR, tie-break = Qwen3.8; subjective A = Qwen3.8, B = PaddleOCR/GLM-OCR).

### Own test dataset — papers generated (user's plan), 14 Nov
- **Exam rule (user): students write ONLY the final answer** — option letter(s) for MCQ, the value
  (with unit) for numerical; rough work is on a separate, ungraded sheet. Keep this in mind for future
  prompts/parsing: anything other than letters or a value on an answer line is a reading problem.
- User will write: **OMR** 3 layouts × 5 sheets; **handwritten MCQ** 1 paper (10 Q, single + multiple
  correct) × 15 sheets; **MCQ + numerical** 3 papers (2 MCQ + 3 numerical each) × 5 sheets.
  All basic science.
- Generated by `eval/make_test_papers.py` → `eval/test_papers/` (PDF; OMR layouts also PNG), answer keys
  (PDF + Evalify JSON with numerical tolerance + unit), label CSV templates, README with edge-case
  checklist, photo and labelling instructions.
- OMR layouts deliberately differ: (1) 2 columns, horizontal options, letters inside black bubbles,
  roll-number grid, corner marks; (2) vertical options in two blue bands; (3) orange 4×5 grid of boxes
  numbered across rows, shaded rows. Verified: template OMR learns all three (20/20 numbered from the
  printed labels) and reads 20/20 from simulated phone photos.
- Bug found while preparing keys: "°" was registered as the angle unit → "−7 °C" would be flagged.
  Added °C (temperature, factor only) to `numeric.py`; test covers the paper answers' written forms.
- **User: no name / roll number written on any test sheet** (OMR roll-number grid left empty too).
  Fine: identity comes from the photo file name ↔ label-CSV row (in the app, from the student's
  login at upload); the pipeline never reads name / roll from the sheet. Empty roll grid also
  checks that the OMR template ignores non-answer bubbles.
- **User: OMR questions can have multiple correct answers.** OMR question paper now has 6 of 20
  "[one or more correct]" questions (Q5, Q9, Q13, Q14, Q17, Q20); sheet instructions say "fill every
  bubble you choose". Grading stays exact-set (full mark only if exactly the correct bubbles are
  filled; a double fill on a single-answer question scores 0). Verified on all 3 layouts from a
  simulated phone photo: 20/20 read incl. 2- and 3-bubble answers, 19/20 score with one planted
  double fill marked wrong_overfill.
- **Label CSV convention:** one answer `B`; multiple **`AC` (recommended, no commas)** or `A,C`; blank =
  empty cell; struck-out-and-rewritten = final answer + note in `edge_cases`; genuinely unclear = `?`
  (expected outcome: routed to a TA). Numerical: value as written incl. unit. The import script must
  accept all these variants.

## 15 Nov 2026 — own dataset received
- User uploaded the test sheets as 7 PDFs in `eval/test_papers/dataset_created/` (one sheet per page, in order; 45 sheets = 15 OMR + 15 MCQ + 3×5 MCQ+numerical).
- `eval/extract_test_photos.py` pulls the original phone photo from each page (largest embedded JPEG, not re-encoded; scanner-app logo strip dropped) → `eval/test_papers/photos/<set>_sNN_p1.jpg`; `photos_overview.pdf` is a labelled thumbnail sheet for the user to verify order/naming.
- Run starts only after the user confirms the names match the label CSVs.

## 15 Nov 2026 — grading rules from the user + architecture sweep
- **Git:** the user pushes to GitHub themselves; Claude only commits locally.
- **OMR:** a bubble that is not 100 % filled still counts as marked. OMR sheets are always printed black & white.
  Checked on the 15 real sheets: every labelled-filled bubble (incl. partial fills) has darkness ≥ 0.46 above the
  blank, every empty one ≤ 0.07 → the existing threshold 0.10 already marks partial fills; no change needed.
- **Numerical answers (teacher rule):** the question states the unit, so marks go on the **number in the key's unit,
  within the key's tolerance**; the unit itself is ignored (missing or different unit is fine, only flagged
  `unit_ignored`). **No unit conversion**: for a key of 2500 m, `2500`, `2500 m`, `2500.0001`, `2500 km` score;
  `2.5 km`, `2500.5` do not. Test-paper keys now use tolerance ±0.001 (was 0.01–0.5). Tolerance edge is inclusive
  (`0.626` vs 0.625 ± 0.001 scores). Implemented in `numeric.compare`; tests updated.
- **Bug found by the user's sheets:** label stripping ate the integer part of decimals (`3. 4.01` → `01`,
  `0.626` → `626`) in `readers.strip_label` / `parse_final_number` / `read_general`. Fixed + regression test.
- **Architecture sweep** (`eval/arch_sweep.py`, user asked for "all reader × grader combinations, all patterns"):
  import (label CSVs → `eval/data/own_{omr,mcq,mcqnum}`), read (each live model once per sheet, cached in
  `eval/reports/arch_sweep/raw/`), score (offline). Sources: crop reading with segmenter Qwen/Gemma × reader
  Qwen/Gemma/PaddleOCR/GLM/Chandra; whole-page reading by each model; direct VLM grading (read+grade in one call);
  OMR template / legacy / VLM. Architectures: single, pair, pair+tie-break (current), pair+majority; numerical
  grader code vs Qwen vs Gemma. For MCQ, grading is always the exact-set code rule (an LLM adds nothing there);
  the LLM-grader alternative for MCQ/OMR is the direct-grading source. Nanonets and gpt-oss are not loaded in the
  current GPU job, so they are not in this sweep.
- New prompts (TEMPLATE_VERSION p3): page_prompt, omr_page_prompt, direct_grade_prompt, numeric_grade_prompt.
- Label edge cases kept as written: mcq_s09 has digits as answers (`1`, `A3`, `4`), 2A_s04 Q1 `50`; blank answer
  sheets (omr_L*_s03, mcq_s08, 2A_s05, 2B_s05, 2C_s04), some with show-through from the back.
- **Sweep results (15 Nov):** see `eval/reports/arch_sweep/FINDINGS.md`. Recommended (pending user approval):
  OMR = template + Qwen page cross-check (0 silent, 299/300 auto); handwritten MCQ and MCQ+numerical = whole-page
  Gemma + Qwen + GLM-OCR page majority (0 silent, 98 % / 97 % auto) vs current crop pipeline 85 % / 57 % auto.
  Qwen as numerical grader violates the tolerance rule → keep code grading. Glare gate too strict for phone
  photos; show-through ghost answers on blank sheets are a real risk. Comma-label parse bug (`4, 440 W`) fixed.

## 15 Nov 2026 — dataset for paper type C (MCQ + numerical + subjective)
- User cannot write type-C sheets themselves. Decision: **Mendeley sf3kvjwknt (all 50 sheets)** is the main type-C
  set (20 MCQ + 15 short answers, teacher marks per answer, CC BY 4.0; no numerical questions).
  Rubrics for Q21–Q35 were drafted by Claude → user reviews `eval/reports/mendeley/RUBRICS_REVIEW.md` first.
- Numerical-with-working: **EDU-CIRCUIT-HW** (arXiv 2602.00095, Georgia Tech ECE 2040, 1,334 handwritten circuit
  solutions, 29 students, rubrics + per-aspect deductions E/M/U/C/NC, transcripts for 513). Caveats: no problem
  statements (textbook copyright), answers are often expressions/phasors not single numbers, its rules penalise
  units (ours ignore them), dataset licence not confirmed. Download page (DOI 10.35090/gatech/81252) blocks
  automated access → the user downloads it via browser. (An earlier link I gave, arXiv 2603.24961, was a different
  dataset — ScratchMath — corrected.)

## 15 Nov 2026 — grader prompt v2, v2 plan, RAG plan, results index
- **Grader prompt v2** (`grade_prompt_v2`, TEMPLATE_VERSION p4) added next to v1, chosen per call with
  `grade(..., version="v1"|"v2")`; default stays **v1 until the 50-sheet Mendeley comparison** shows v2 is better.
  v2: spelling/grammar ignored; contradiction → not present; bare keyword is not enough; student text marked as
  data (anti-injection); evidence quote before verdict; verdict present/partial/absent; **partial = half the
  point's marks** (rubric `allow_partial`, default true; the Mendeley teacher gave 0.5/1.5 on ~3 % of answers);
  mandatory points need a full "present". Smoke test: v2 makes Qwen and Gemma agree on a bare keyword (0.5).
- **V2_EVALIFY_PLAN.md** written (user request): the pipeline as decided so far, with pending items marked.
- **RAG (user request, later — after the current runs):** only to draft the *sample answer key* for subjective
  questions from the teacher's reference files; optional; the LLM formats the draft into reference answer +
  rubric points with citations; the teacher edits and approves; never used when grading students.
- **Results of every dataset run are kept in Markdown**; index at `eval/reports/RESULTS.md` (user request).
- Tie-break reader: user asked GLM-OCR vs Chandra → **GLM-OCR** (equal or better on every metric except one
  answer, ~5× faster, better on Mendeley); Chandra = backup.

## 15 Nov 2026 — EDU-CIRCUIT-HW downloaded
- User supplied the direct link (https://repository.gatech.edu/bitstreams/09496897-10b3-4675-bcf5-73b5b9802cd2/download).
  The server cuts each connection after ~1 GB → resumed with `curl -C -` 8 times; complete zip 9.1 GB, 34,841 files
  → `/scratch/m25csa019/evalify/datasets/edu_circuit_hw/`. Only images, rubrics, TA labels and expert transcripts
  extracted (~1.9 GB); the other 7.1 GB are the paper's own GPT-5.1 / Gemini / Claude / Qwen-VL outputs (kept zipped).
- **No licence file in the zip** (repo code is Apache-2.0; dataset licence still unconfirmed) → internal evaluation only.
- Contents: 3,735 solution images (9 homeworks, ~29 students), 62 rubric JSONs (criteria M/E/C/U/NC with deduction
  rules, `notes` hold the **final expected results**, e.g. "R = 12 Ω, v1 = −4 V"), TA-checked deductions
  (`valset1.csv` 232 rows / 18 students / 58 questions; `obset.xlsx`), expert Markdown transcripts. Grading is
  deduction-based on a 1.0-point scale (typical deductions 0.005–0.085). No problem statements (textbook copyright).

## 15 Nov 2026 — type C (Mendeley 50) and EDU-CIRCUIT-HW results (runs 7, 8)
- All runs finished on cn07; results in `eval/reports/mendeley_sweep/FINDINGS.md`, `eval/reports/edu_circuit/FINDINGS.md`,
  indexed in `eval/reports/RESULTS.md` (combination tables with time per paper).
- **Grader prompt v2 helped** (user asked): Gemma MAE 0.702 → 0.665 (significant), Qwen 0.782 → 0.726. Exact match
  drops because half credit gives 1 where the teacher gave 0/2. Thinking mode: worse and 5× slower → off.
- **Type C choice:** short answers = Qwen segmentation → transcripts **Qwen + GLM-OCR** (all 10 pairs within MAE
  0.659–0.672, this one 30 % faster) → **one grader, Gemma 4 + prompt v2** (a second grader added no accuracy).
  MCQ part = whole-page Gemma + Qwen + GLM-OCR majority (as type B).
- **Grader is 0.57 marks (of 2) stricter than the teacher.** Hand review of 20 big disagreements: 10 teacher
  lenient (wrong answers given 2/2), 6 grader too harsh, 4 segmentation faults (crossed-out attempt picked, mixed /
  cut crops); 41 answers not found by segmentation → 0. Proposals: segmentation fixes; answer not found → TA;
  **teacher calibration** (teacher marks ~5 sheets, used as examples in the grader prompt) — needs user go-ahead.
- **Mendeley MCQ:** 12 of 13 "errors" where Gemma and Qwen agree are teacher-CSV errors (Student_34 row garbled,
  Student_46 blanks, 6 typos) → ~1 real error / 1000 (Student_15 Q19, looped "A" read as "B").
- **Gemma on single-answer crops fails** (guided JSON → "unclear" / runaway on 994/1000) → Gemma reads whole pages only.
- **Reader accuracy (user asked "how good is the reader")**: own sheets whole-page Qwen/Gemma 94.5–100 %;
  Mendeley MCQ Gemma 98.3 %, Qwen 97.7 %; EDU final numbers Chandra→Qwen 86.6 %, Gemma 83.9 %, Qwen 82.9 %,
  GLM 78.9 %, Paddle 66 %. Short-answer grading is limited by the grader, not the reader.
- **EDU-CIRCUIT-HW:** best = pair Chandra→Qwen + Gemma (30 silent / 702, 79.5 % auto, 55 s/solution); majority
  doubles silent errors (63). Numbers inside free working are hard → numerical questions need a final-answer box.

## 15 Nov 2026 — segmentation fixes and teacher calibration (user: "start Step 1, Step 2 … continue exploring")
- User's concern: calibration is hard because we do not have the teacher's real rubric. Approach chosen: learn
  from the **teacher's own marks** on a few sheets (needs no rubric) — tested on held-out sheets.
- **Bug found and fixed — page cleaning cut off margin labels** (`quality.find_page`): a ruled box printed on the
  sheet was taken for the paper edge and the page was cropped to it, removing the question numbers written in
  the margin (7 of 200 Mendeley pages; Student_46 lost answers 27–32). Now a quadrilateral counts as the paper
  only if the area outside it is darker (a desk), not white paper. Own phone photos unaffected. Unit test added.
- Segmentation experiment (`eval/mendeley_seg.py`, results `eval/reports/mendeley_seg/`), grader fixed to Gemma v2:
  - *seg2*: new box prompt `segment_prompt_v2` (check every label, skip crossed-out copy, ignore show-through,
    no two answers in one box);
  - *pagetext*: no boxes — Qwen transcribes each whole page grouped by label (`page_text_prompt`, JSON) and Gemma
    does the same as plain text with `[[Qnn]]` markers (`page_text_plain_prompt`; Gemma's JSON mode runs away).
    All question labels (MCQ too) are passed so "7. A" is not read as Q27. GLM-OCR was dropped here: it loses
    labels written in the margin.
  - Answers not located → TA (no automatic 0) in the scoring.
- Calibration, post-hoc (`eval/mendeley_calibrate.py`, CPU only): 5 teacher-marked sheets, tested on the other 45,
  20 random splits. Global shift: MAE 0.602 → 0.430, within-0.5 56 % → 83 %, QWK 0.47 → 0.59, stable over splits;
  3 sheets ≈ 10 sheets. Per-question shift / mark mapping slightly lower MAE but unstable.
- Calibration, few-shot (prompt p6): `grade(..., examples=[(answer, teacher mark)])` shows the grader the
  calibration sheets' answers to the same question with the teacher's marks. Running.

## 15 Nov 2026 — GPU job restarted; UI review queued
- User asked to restart the GPU job for a fresh 36 h window after the runs finished: job 48695 cancelled,
  **48707** submitted (cn07, A6000 48 GB + PRO 6000 96 GB again — cn07 GPUs are untyped in Slurm, so a
  2 × 96 GB pair cannot be requested).
- Bug in my experiment script: seg2 and pagetext grading wrote one shared `grades.json` at the same time →
  293 seg2 grades overwritten. Fixed with one cache file per variant; the missing grades are regraded.
- **Next (user, not started yet):** once the models are loaded, review the UI so it matches the new pipeline
  (whole-page reading, TA routing for answers not found, grader v2, teacher calibration, etc.).

## 15 Nov 2026 — run 9 results: segmentation + calibration chosen
- Segmentation (`eval/reports/mendeley_seg/README.md`): both new variants find 555/564 answers (old: 523);
  TA items 41 → 9. MAE: pagetext 0.630, seg2 0.650, old 0.665 (not significant) → **pagetext chosen**
  (Qwen JSON + Gemma plain-text whole-page transcription by label; picks the rewrite over a crossed-out attempt;
  no GLM-OCR for subjective answers). seg2 kept as fallback (faster reading, 80 vs 187 s/paper).
- Calibration: **global shift from 3–5 teacher-marked sheets** (MAE 0.62 → 0.43, within 0.5: 55 → 83 %, stable).
  Few-shot examples: more exact matches but still strict and 4× slower → not chosen now.
- Proposal for the product: calibration is a teacher setting; keep both the rubric mark and the calibrated mark.
- Testing approach (user asked): 25 DB-free unit tests + 10 MongoDB tests + dataset evaluation; proposed
  test-first for the UI phase (API tests, Vitest component tests, one end-to-end test with fake model replies).

## 15 Nov 2026 — product workflow for large classes (user idea)
- User: teacher gives rubric + answer key + reference solution + ~10 strictly hand-checked papers; the pipeline
  learns how the teacher grades and marks the remaining ~690; should also reduce inconsistency between TAs.
- Clarified: the main gain came from the **global shift** (no fine-tuning; model weights unchanged); few-shot
  examples helped less (MAE 0.48 vs 0.43) and are 4× slower.
- Agreed direction + safeguards proposed: split the 10 papers into 5 calibrate / 5 hidden check and show the
  teacher the agreement before the batch runs; auto-accept only confident answers, TA for the rest; random 5 %
  spot-check of auto-accepted answers. Consistency ≠ correctness (systematic errors repeat on every paper);
  calibration also copies the teacher's leniency.
- Proposed measurements (awaiting go-ahead): grader self-consistency (grade twice), 5 vs 10 vs 15 calibration
  sheets, few-shot + shift combined. Then the UI phase with a "teacher calibration" step.

## 15 Nov 2026 — feature for later: student-facing marking breakdown (user request)
- After evaluation, students see per question and per rubric point how marks were given, e.g. Q4 "What is solar
  energy": "energy derived from the sun → +1", "gave an example → +1", with the student's own words as evidence.
- Already available from grader v2: rubric point, evidence quote, verdict present/partial/absent (1 / 0.5 / 0).
- To decide when built: add a one-line reason per point (re-measure accuracy); how to show teacher calibration
  (it is per answer, not per point — separate "teacher adjustment" line or per-point calibration); TA overrides
  replace the grader's decision in the breakdown; shown only after the teacher releases results (teacher decides
  whether the reference answer is visible); per-point re-evaluation request → TA queue.
- Not started (user: "for later").

## 15 Nov 2026 — run 10: calibration experiments (user: "experiment first, don't change the pipeline")
- Consistency: same input twice 99 % exact; transcripts swapped 96 %; two reading methods 91 %; two different
  graders (Gemma vs Qwen, "two TAs") 66 % exact / 6 % ≥ 1 mark apart → one fixed grader removes most
  grader-to-grader variation (supports the user's point about TA irregularity). Earlier "humans agree 50–70 %"
  was from memory, unverified — not to be quoted.
- Teacher sheets: global shift saturates at 3; per-question shift improves up to 20 (0.417 → 0.393).
- With 10 teacher sheets: **few-shot + global shift best** (MAE 0.36, within 0.5 86 %, QWK 0.65, bias ≈ 0) but the
  grader is ~5× slower (60 vs 12.6 s/answer); **per-question shift alone** 0.38–0.39 at no extra cost.
- Pipeline NOT changed; choice left to the user.

## 15 Nov 2026 — TA role and TA view (user design; keep TA checking simple)
- New third user type **TA** (today only teacher + student exist). TA sees only the subjects they are TA of.
- Two tabs: **Flagged by AI** and **Re-evaluation requests** (from students). Same item view in both: the
  student's full answer sheet, question paper, teacher's answer key / reference solution, grading rubric (if
  subjective), AI's mark + one-line reason; TA enters re-evaluated marks and submits. Request tab also shows the
  student's remark ("this question was wrongly evaluated because …").
- Consequence for the pipeline: routing only needs to flag a question with ONE short reason (answer not found,
  readers disagree, unclear handwriting, grader unsure, random quality check). Random spot-checks appear in the
  Flagged tab; no separate queue. Student side needs a per-question "Request re-evaluation" + reason box.
- Open (to decide at UI time): who assigns TAs (proposed: teacher, by email); TA mark final or teacher-approved
  (proposed: final + audit log); re-evaluation limits (once per question? time window?); student sees new mark
  + optional TA comment?; can TAs mark the calibration papers?

## 15 Nov 2026 — user decisions on TA / re-evaluation / calibration (final)
1. **Users from `demo.env`**: teachers with their subjects; per subject a list of TAs and sample student
   credentials (10–50 students per subject). No UI/logic for assigning TAs or creating teachers/students/TAs now.
   (Replaces the hard-coded demo teacher + students in `backend/app/db/seed.py`.)
2. **TA marks are final**; every TA decision is logged (old mark, new mark, TA, time, optional remark).
3. **Re-evaluation: at most ONE request per student per question paper**, one text box with the student's remarks
   / concerns; the TA reads it and re-evaluates only those parts.
4. After the TA submits, the student sees the updated marks and a **history of previously awarded marks**
   (AI → TA); TA remark optional.
5. **Calibration (teacher-evaluated answer sheets) is optional and teacher-only.** Without it the rubric marks are
   used as they are (measured: ≈ 0.5 marks/answer stricter than a lenient teacher) → setup screen should say so.
- Still open: calibration method when used (per-question shift vs few-shot + shift); order of work
  (pipeline into the main code vs UI review).

## 15 Nov 2026 — calibration method, order of work, test-first
- Calibration (optional, teacher-only): **per-question shift** is the method; **few-shot + shift** kept as the
  documented alternative (MAE 0.36 vs 0.38, ~5× grader time) in V2_EVALIFY_PLAN.md.
- Order: **(a) move the new pipeline into the main backend first**, then the UI.
- **From now on test-centric for UI and backend flow** (user): tests first; tests that run without MongoDB/GPUs
  (fake model replies), frontend tests (Vitest), one end-to-end flow, small tests for eval helpers — closing the
  gaps found today pragmatically, not necessarily all at once.

## 15 Nov 2026 — v2 pipeline moved into the backend (test-first)
- Tests written first: `test_page_reading.py` (14), `test_calibration.py` (5), `test_pipeline_flow.py` (6, whole
  orchestrator on a type-C paper with fake model replies, no GPU / MongoDB). 69 DB-free tests pass.
- New `app/pipeline/page_reading.py` (whole-page readers A/B + C on disagreement, majority; subjective
  transcription by label, crossed-out attempt dropped when rewritten) and `app/pipeline/calibration.py`
  (per-question shift; optional `paper["calibration"]`). `orchestrator.py` now uses them: one grader (Gemma v2,
  transcripts only), rubric mark + calibrated mark kept, each flagged question has ONE `review_reason` for the TA.
  New roles in `infra/models.yaml`: page_reader_a/b/c, transcriber_a/b, grader (old roles kept).
- Live check on real models: own sheet 2A_s01 all correct, 0 flagged, 7 s; Mendeley Student_3 all 20 MCQ correct,
  rewrite of Q22 used, 74 s / 4 pages.
- Open (asked user): unanswered questions. "Not found → TA" flags 170 items on Mendeley to catch 9 real misses
  (161 truly unanswered). Alternative: not found by both transcribers → "no answer found", 0, not flagged; the
  student sees it and can use the one re-evaluation request.
- **Decided (user):** when both transcribers / readers find no answer, the student did not answer → **0 marks, not
  sent to a TA**. (Mendeley: avoids 161 useless TA items; the 9 real misses can come back via the student's
  re-evaluation request.) Test `test_unanswered_question_is_zero_and_not_flagged` written first.

## 15 Nov 2026 — UI phase, backend part (user: "do everything in UI first … test-centric … previous code must have tests too … read CLAUDE.md")
- CLAUDE.md now says: never credit/mention Claude in commits; every test gets a one-line "why" comment. The 10
  unpushed commits were rewritten to drop the co-author line (code unchanged; old refs kept on branch
  `backup/pre-msg-cleanup`).
- **Tests run without MongoDB/GPUs**: conftest uses an in-memory MongoDB (mongomock-motor); EVALIFY_TEST_REAL_MONGO=1
  uses a real server (always database `evalify_test`). CI no longer needs a MongoDB service. 155 backend tests.
- **demo.env** (repo root, committed — fake credentials): 4 teachers (Computer Science, Physics, Mathematics, Data
  Science), 7 TAs (one in two subjects), students per subject 30 / 20 / 15 / 50 (Data Science = 50 to match the
  Mendeley sheets). Format and parser in `app/db/demo_users.py`; seeding is idempotent.
  `.gitignore` inline comments were silently breaking its `!` exceptions — fixed.
- New backend: TA login (`/auth/ta/login`, own JWT secret); students see/submit only enrolled subjects; answer-sheet
  pages for student / paper's teacher / subject TA; one re-evaluation request per paper; TA router (`/ta/subjects`,
  `/ta/queue?tab=flagged|reevaluation`, `/ta/items/{id}`, `/ta/items/{id}/marks` — final marks, history,
  `ta_log` audit); results with marks history (students do not see TA names); optional teacher calibration
  (`/papers/{id}/calibration/marks/{sid}`, `/apply`, DELETE) — hand-marked sheets final, TA marks never overwritten.
- Bugs found by the new tests and fixed: any user could read any student's result; upload response crashed on the
  Mongo `_id`; 422 handler crashed on custom validation messages; Gemma whitespace runaway skipped the JSON retry and
  looked like a blank answer; `any_live()` checked the old reader role.

## 15 Nov 2026 — UI phase, frontend part + live end-to-end check
- **Frontend tests (Vitest + Testing Library)**, every test with a one-line "why": utilities, stores, UI components,
  layout, route guards, all existing pages (student dashboard/subject/upload/result, teacher dashboard/paper
  view/create wizard/results, logins) and the new TA pages. 55 tests; `npm test`; added to the frontend CI build.
- **New UI**: TA login (`/login/ta`, links from the other logins); TA dashboard (`/ta/dashboard`: subjects with
  counts, tabs "Flagged by AI" / "Re-evaluation requests", one-line reasons or the student's remark); TA review
  (`/ta/review/:id?tab=`: full answer sheet, question paper / answer key / solution links, MCQ + numerical keys,
  rubric points, every question's AI mark + reason + evidence, mark inputs with 0…max check, optional remark;
  only changed marks are sent; TA marks final). Student result: question-wise marks, marks history (role, not
  TA name), the one re-evaluation request (form → pending → resolved with TA response). Teacher results: status
  badges (n flagged / TA pending / TA reviewed / re-evaluation pending / re-evaluated / hand-marked) and optional
  calibration (Hand-mark dialog, Apply / Remove calibration).
- Bug found by the new tests: teacher PaperView expected subjective questions as objects but the wizard saves
  strings → questions showed empty; fixed (both shapes). ESLint has no config in the repo, so the existing lint
  workflow cannot pass — left as is (to decide).
- **EVALIFY_INMEMORY_DB=1**: backend runs without MongoDB (data lost on restart) — for UI testing on the cluster.
- **Live end-to-end run with the real models** (API): DS teacher creates the Mendeley paper → DS2025003 uploads
  Student_3 (4 pages) → v2 pipeline 142 s, 16/50 → re-evaluation request → TA Data Science sees it (4 pages, 35
  questions, key) → TA sets S2 = 1 → student sees 17/50, history "S2 0 → 1 (TA)", request resolved.

## 15 Nov 2026 — UI redesign: no emoji, "marked paper" style (user: sleek, unique, not AI-looking)
- **No emoji anywhere in the frontend** (also ✓ ✕ ★ ↗); enforced by `src/__tests__/no-emoji.test.js`. Icons
  replaced by words (Required / Optional, Remove, Dismiss, Close, met / partial / missed, PDF / KEY).
- **Style "marked paper"**, from the domain (answer sheets + a teacher's red pen): warm paper background, ink text,
  ink-blue actions, one red-pen accent for marks and flags, square corners, hairline rules instead of shadows, no
  gradients; Source Serif 4 headings, IBM Plex Sans text, IBM Plex Mono for numbers, roll numbers and labels; a
  thin red margin rule down every page like an exam booklet; numbered "Contents" side menu; split login page
  (ink panel + form). Tokens in `tailwind.config.js` remap the old palette so every page changed consistently.
- New shared pieces with tests: StatLedger (ruled number row), ScoreMark (red-pen score box), AuthShell.
  Teacher dashboard is now a paper register (one ruled row per paper); student dashboard a numbered subject index.
- Found while checking screenshots: the TA queue flashed "Nothing to review" while loading — fixed. The Vite dev
  server caches the Tailwind config: restart it after config changes.
- 58 frontend tests, production build OK.

## 15 Nov 2026 — quality gate and show-through fixes (user: "implement 3 and 4")
- **Glare gate** rejected 9 of 30 good phone photos: it counted bright, evenly lit paper as glare. Now glare =
  area ≥ 40 levels brighter than the paper (paper level ignores blown-out pixels, so a hotspot cannot hide
  itself); reject only extreme glare (≥ 33 % of the page; good photos reach 24.5 % with uneven light). Milder glare
  is left to the readers ("unclear" → TA). Measured: own 45 photos 0 rejected (was 9), Mendeley 200 scans 0
  rejected, blank backs still detected (22/22).
- **Blur** score now scale-free (detail lost by a slight blur; good ≥ 3.98, blurred ≤ 2.47 → limit 3.0); the old
  Laplacian variance depended on the upload size.
- **Bug found:** a heavily blurred written page was classed as a blank back and skipped — its answers would score 0
  with no TA. A page is blank only if < 0.8 % of it is darker than the paper (blank backs ≤ 0.55 %, blurred written
  pages ≥ 0.93 %); otherwise it is rejected as blurry.
- **Show-through:** with whole-page majority reading no ghost answer was accepted on the known sheets (one reader
  saw a mirrored "A", the other two saw nothing). New rule: a blank vote while one reader saw an answer → TA
  ("only one reader saw an answer — faint writing or show-through?"), so faint real answers are never silently 0.
  Fires on 3/225 own-sheet answers (all on blank sheets). Consistent with the user's rule (0 only when readers agree
  there is no answer).

## 15 Nov 2026 — TA-flagging thresholds, student breakdown, RAG answer-key assistant
- **TA-flagging for written answers measured** (run 11, `eval/exp_routing.py`): grader confidence, evidence check,
  transcript problem and transcript disagreement do not predict wrong marks (confidence < 0.9 → 14 % to TA, wrong
  16 % vs 18 % auto). Thresholds unchanged. Added a **random 5 % spot-check** of auto-accepted written answers
  (`EVALIFY_SPOT_CHECK_RATE`, reproducible per submission + question, "random quality check" in the Flagged tab).
- **Student breakdown per rubric point** (`MarkBreakdown`): Met / Partly met / Missed, the student's words (or "Not
  found in your answer"), marks per point; teacher's calibration adjustment and a TA/teacher re-evaluation shown as
  separate lines; "required point missing → 0" explained. No new grader field (no extra reason line, so grading is
  unchanged and needs no re-measurement). No "release results" step exists yet, so it is visible as soon as the
  result is.
- **RAG answer-key assistant** (optional, teacher-only, never used to grade): reference files (PDF with text layer or
  .txt; scanned pages are reported) → passages with file + page → BM25 retrieval (no extra model) → Gemma drafts a
  reference answer and rubric points, each citing its passages (prompt p7); "not covered" instead of inventing.
  Endpoint `POST /api/papers/answer-key/draft`; wizard step 4 panel: question texts, files, drafts with citations,
  "Use this draft" → editable RubricBuilder. Live check on the Mendeley answer key: 2 covered questions drafted
  correctly, an off-topic question correctly reported as not covered. Citations show the passage sentences closest
  to the point. `.txt` uploads now allowed.
- Tests: backend 184, frontend 72 (all with a "why" line); production build OK.

## 15 Nov 2026 — permanent database on the cluster; release results (user decisions)
- **Database on the cluster** (user): MongoDB 7.0.15 in user space (`/scratch/$USER/evalify/mongodb`), data in
  `/scratch/$USER/evalify/mongo-db`, port 27027 on 127.0.0.1 only, **password authentication always on** (the
  login node is shared; anonymous access refused — checked). Random password in `/scratch/$USER/evalify/run/mongo.env`
  (chmod 600, not in git). Scripts: `infra/cluster/mongo.sh init|start|stop|status`, `infra/cluster/app.sh
  start|stop|status` (database + backend :47823 on it + frontend :5173; logs in /scratch/$USER/evalify/logs).
  Checked: data survives a backend restart.
- Found an older MongoDB **8.3** data folder `/scratch/$USER/evalify/mongo-data` (Nov 14, 302 MB, not created in this
  session, nothing running on it). Left untouched; asked the user whether it is needed.
- **Release results** (user): new papers start unreleased; students see "Your answer sheet is being evaluated" while
  marking and until the teacher releases (status `awaiting_release`, no marks in status / result / paper list);
  teacher "Release results" / "Withdraw release" with a warning about sheets still flagged for TAs and pending
  re-evaluations; TAs and the teacher work on results before release; re-evaluation requests only after release;
  papers created before this feature count as released. Live check: hidden (409) → released → visible.
- Also fixed: the submission status endpoint returned any submission's result to any logged-in user (now the same
  access rule as results). Upload page no longer says "Ollama Vision".
- Tests: backend 192, frontend 77.

## 15 Nov 2026 — token use of the whole pipeline (user request)
- User asked how many tokens the pipeline uses, for every question type.
- The model client now keeps the token counts vLLM returns with each reply (retry requests included) and a
  per-sheet meter adds them up by step (`read_mcq_numerical`, `transcribe_subjective`, `grade_subjective`,
  `answer_key_draft`) and model. The meter follows the pipeline's worker threads and never mixes two sheets
  graded at the same time. Each submission now stores `pipeline.usage`; MLflow gets prompt/completion/total tokens.
- Measured on real labelled sheets with `eval/exp_tokens.py` (all 15 handwritten MCQ, 15 OMR, 15 MCQ+numerical,
  12 of the 50 Data Science sheets); report in `eval/reports/exp_tokens/README.md`.
- 16 Nov: user asked why the old `mongo-data` folder would be deleted. Explained: optional only (302 MB space, and the
  name is easy to confuse with the live `mongo-db`). Decision: **keep it untouched**; nothing uses it.
- 16 Nov: user then approved deleting it. Checked first: no process and no project script used it. Deleted
  `/scratch/$USER/evalify/mongo-data` (302 MB). Live data stays in `mongo-db`.

## 16 Nov 2026 — upload kit for testing every flow (user request)
- User asked for one folder with everything to upload when testing each flow: `uploads/Pattern{1,2,3}/{Teacher,Student}`,
  built from the datasets used in our evaluations. Built by `python eval/make_upload_kit.py` (101 files, 20 MB):
  - Pattern1 (MCQ only): OMR paper (20 Q, question paper, answer key PDF, 3 blank OMR layouts; 5 student sheets per
    layout) and handwritten paper (10 Q; 15 student photos).
  - Pattern2 (MCQ + numerical): papers 2A/2B/2C (question paper, answer key PDF; 5 student photos each).
  - Pattern3 (MCQ + subjective): Data Science exam (Mendeley, CC BY 4.0): question paper, MCQ key PDF, detailed
    answer + grade rubric PDFs in the format "Extract Rubric from PDFs" reads, reference notes for the answer-key
    assistant; 6 student sheets (4-6 pages, teacher totals 14-43) re-saved as JPEG (quality gate still passes).
  - Teacher README per pattern = what to pick / type / upload at each wizard step; one folder per student login
    (PH2025xxx under the Physics teacher, DS2025xxx under the Data Science teacher) with `expected_results.md`.
- Found while building it, fixed:
  - "Extract Answers from PDF" kept only the first letter of a multi-answer key ("A, C" -> "A"), which would mark every
    correct multi-answer wrong. Now keeps all letters.
  - The teacher form had no way to say written answers continue the Q-numbering (the Data Science students wrote
    21-35); the pipeline supported it but a paper made in the UI expected S1..S15. New Step-2 choice
    "S1, S2, ..." / "Q21, Q22, ... (numbers continue)", shown on the review step.
- Checked live: OMR layout-1 sheets aligned and read 20/20 as labelled (5/5); a Data Science sheet from the JPEG kit
  gave the same written-answer marks as the earlier PNG run.

## 16 Nov 2026 — cost comparison: own GPUs vs open-model API (user request)
- User wants token use to compare hosting the models ourselves with paying an API for the same open models.
- Measured throughput on our node (A6000 + RTX PRO 6000, vLLM), `eval/exp_throughput.py`: one-page sheets
  1,136 / 1,785 / 2,404 per hour at 4 / 8 / 16 in parallel (not saturated); Data Science sheets 118 / 145 / 150.
- `eval/cost_compare.py`: tokens x API prices (web lookup 16 Nov, low / typical) vs GPU rental per hour / throughput.
  Per 1,000 sheets: handwritten MCQ API $0.74-1.26 vs rented GPUs $0.85-1.14; Data Science API $7.46-11.74 vs
  rented $13.62-18.36. Our cluster GPUs cost nothing extra; with an API the student sheets leave the university.

## 16 Nov 2026 — class-scale cost for the proposal to the teacher (user request)
- User: the college already has the GPU servers, so self-hosting has no purchase or extra maintenance cost (rental
  value may be shown, but it is not consumed). Asked for: 700 type-C sheets of ~10 pages, and 700 handwritten
  MCQ / numerical quizzes: time and money, API vs own servers.
- `eval/scenario_cost.py` -> `eval/reports/scenario_cost/README.md`. Type-C 10-page sheet estimated from measured
  per-page (reading + transcription) and per-answer (grading) tokens, 15 written answers assumed: ~109k tokens per
  sheet (estimate 5-8 % above measured 4/6-page sheets). 700 sheets: API $14-22 (~₹1,200-1,900), own servers
  ₹0 extra and ~12 h of GPU time. 700 one-page quizzes: API under $1, own servers ~17 min. OMR: no model at all.
