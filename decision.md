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
