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

## 16 Nov 2026 — discussion: few-shot prompting for Type 3, recap of the prompt experiments
- User asked whether few-shot prompting would help Type 3 if accuracy is the main goal, and for a recap of the
  prompt experiments. Answered from runs 6, 7 and 10 (no new run): prompt v2 vs v1 (Gemma MAE 0.702 → 0.665,
  significant; Qwen 0.782 → 0.726; thinking mode worse), and few-shot with 10 teacher-marked sheets
  (alone 0.45; + global shift 0.36, best; per-question shift alone 0.38; few-shot ~5× slower grading).
- Point made: few-shot needs teacher-marked examples (it is a form of calibration); without them it is not
  possible. Its own gain is mostly bias removal, which a shift does for free; few-shot + shift is ~0.02 MAE better.
- No decision; pipeline unchanged.

## 16 Nov 2026 — exploration: inference speed-ups, and when evaluation runs (user asked; nothing changed)
- Found from the vLLM logs of job 48707: both big models hit their KV-cache limit during the throughput run
  (Gemma 100 %, up to 61 requests waiting; Qwen 98.5 %). Gemma on the A6000 has room for only 48,200 tokens of
  KV cache (~1.5 full-length requests); Qwen 178,176. Chandra + PaddleOCR (26 GB) are loaded but unused.
  Prefix-cache hit rate 8-10 %, image cache 84 %.
- Proposed speed-ups (to measure with exp_throughput, accuracy re-checked): production profile without the unused
  OCR models (more KV for Qwen), FP8 KV cache, smaller Qwen page images, prompt order for prefix caching,
  larger Gemma prefill budget, a controlled evaluation queue. Speculative decoding: low priority.
- When evaluation runs: right after each student upload (FastAPI background task in the backend process, no
  queue, no limit on how many run at once, not resumed if the backend restarts — such sheets stay "processing").

## 16 Nov 2026 — why Chandra OCR 2 is ~5x slower than GLM-OCR (user asked; measured, nothing changed)
- Arch sweep (30 one-page sheets, whole page): GLM-OCR 1.14 s/page, Chandra 5.68 s/page (5.0x).
- Live probe on job 48707, same pages, real pipeline prompts: Chandra reads FEWER image tokens (2,730 vs 3,552)
  but writes far more: it outputs layout HTML with a bounding box and label for every line
  (`<div data-bbox=... data-label="Text"><p>1. D</p></div>`) even though our prompt asks for simple tags.
  Data Science page: 807 vs 123 output tokens (6.6x), and each token is ~2x slower (Chandra ~5B params,
  10.6 GB vs GLM-OCR 2.7 GB) → 5.9 s vs 0.44 s. One-page sheet: 93 vs 33 tokens, 0.81 vs 0.18 s.
- Removing PaddleOCR + Chandra from production is proposed but NOT yet decided (awaiting user).
- User: for a future subject with more complex text (e.g. Intro to CS, 700 sheets) Chandra might read better than
  GLM-OCR. Answer: possible (Chandra was best on EDU worked solutions, 86.6 %), but it was worst on Mendeley
  short answers (CER 0.181) and written answers are transcribed by Qwen + Gemma, not the third reader. Proposed:
  keep Chandra as an optional serving profile, decide per subject with a small labelled test set (e.g. 20-30
  handwritten code answers). Awaiting user.

## 16 Nov 2026 — inference-optimisation experiments started (user: test first through the pipeline, no UI change)
- User asked to test techniques 1-5 (drop Chandra/PaddleOCR, FP8 KV cache, smaller Qwen images, larger Gemma
  prefill budget, fixed-part-first grading prompt) against the previous run, restart the job on cn07, stop loading
  Chandra + PaddleOCR, give Gemma more room, and log everything in a new file → `INFERENCE_OPTIMIZATION.md`.
- Found: QoS `mtech` = 2 GPUs per user (`QOSMaxGRESPerUser`), so a second 2-GPU job cannot run next to 48707.
  Plan: measure the baseline on 48707 first (new script `eval/exp_inference.py`, speed + accuracy + KV/queue),
  then release 48707 and run all steps in one switchable job (`infra/cluster/serve_switch.sbatch`, ports 82xx,
  own endpoints file / logs). "Gemma more room" tested as profile `opt-swap` (Gemma on the 96 GB card).
- Client-side switches added, off by default (pipeline unchanged unless set): `EVALIFY_IMAGE_MAX_PIXELS`
  (per-model image cap), `EVALIFY_GRADE_LAYOUT=fixed_first` (same words, rubric before transcriptions; standard
  layout verified byte-identical). serve.py: per-profile extra vLLM args. 20 new tests; 233 backend tests pass.
- User rule: release the current GPU job only when cn07 has 2 free GPUs apart from ours (saved to memory).
- User asked to research prefill/decode disaggregation for our paper types, to experiment AFTER techniques 1-5.
  Findings logged in INFERENCE_OPTIMIZATION.md (#7): vLLM says it does not raise throughput; needs a full model
  copy per instance; our GPUs have no P2P link (KV copies via host). Cheaper alternatives proposed: mixing paper
  types in one batch, priority scheduling; true P/D split only if 4 GPUs (fat_gpu QoS).
- User decision: prefill/decode disaggregation and the proposed alternatives (mixed paper-type batches, priority
  scheduling, Qwen P/D split on 4 GPUs) do not help our application → not implemented, not tested. Only
  techniques 1-5 are run.

## 16 Nov 2026 — user decisions: production without Chandra/PaddleOCR, test 2nd Gemma, UI exam flow later
- User: Chandra and PaddleOCR must not run on the GPUs (had been said before). Done: production profile `tier1`
  = Gemma (A6000) + Qwen + GLM-OCR (PRO 6000); `page_reader_c` = GLM-OCR only (down → TA); default profile of
  serve_models.sbatch / serve.py is now `tier1`; V2_EVALIFY_PLAN.md model table updated. Models stay in
  models.yaml for experiments only.
- User: test how well a second copy of Gemma works → #8. Added: profile entries with `replica: N` (published as
  `model#N`, served under the model's name); the backend sends each request to the least busy copy. Profile
  `opt-gemma2` (Gemma 44 GB on A6000; Qwen 42 + GLM 8 + Gemma#2 38 on PRO 6000). Runs after #3 and #5.
- UI changes AFTER the experiments (user asked to be reminded; saved to memory): exam window → students upload
  under TA supervision (15 min); uploads stored only; teacher view with the paper + all entries and a
  "Start evaluation" button that sends the whole set overnight; "Release results" locked until all TA queries are
  resolved. User asked how to make that whole-set batch faster without lowering grading quality (answered in chat
  and in INFERENCE_OPTIMIZATION.md "Whole-set batch" section).
- 16 Nov evening: #1b (Gemma on PRO 6000) rejected (slower: the A6000 has no native FP8, whichever model is
  there becomes the bottleneck). #4 with 8,192 does not start on the A6000 → measured with 4,096 + max-model-len
  16,384. #2 FP8 KV impossible for Gemma on the A6000 (SM86) → measured for Qwen only; FlashInfer link error fixed
  with lib64 / libcudart.so symlinks in the vLLM env (setup_vllm_env.sh updated).

## 16 Nov — Dummy data in MongoDB
- User asked: "can you add dummy data from backend in mongo db".
- Added `backend/app/db/demo_data.py` (`python -m app.db.demo_data`, `--clear` to remove). It uses the demo.env users
  and writes 6 papers (2 CS, 2 Physics, 1 Maths, 1 Data Science) with 70 submissions covering every state:
  evaluated, flagged for TA, TA reviewed, re-evaluation pending / resolved, and still processing; 3 papers released.
- Every dummy document has `demo: true`; re-running replaces only those, real papers and submissions stay.
- MCQ / numerical marks use the real scoring code on random answers; written-answer marks are random rubric
  decisions (not model output). All dummy sheets show one placeholder page image.
- Tests: backend/tests/test_demo_data.py (16); full suite 256 passed. Seeded into evalify_db on the login node.
- Follow-up (user): "can you use the dataset created by me as the dummy dataset" → demo_data.py now loads the
  user's own labelled sets (eval/data/own_omr, own_mcq, own_mcqnum: 45 photographed sheets) instead of random
  papers. 5 Physics papers (OMR 20 Q, handwritten MCQ 10 Q, 2A, 2B, 2C) for physics.teacher@evalify.local;
  sheet sNN submitted by PH2025<NNN> (same mapping as uploads/Pattern1-2). Marks = real scoring code on the gold
  labels, so they match expected_results.md. To show the TA / re-evaluation screens, flagged and re-evaluation
  sheets carry one MCQ deliberately misread; the TA or re-evaluation decision restores the gold mark.
  Real photos and question papers are copied to backend/uploads/demo and uploads/papers/demo_* (git-ignored).
  OMR, handwritten MCQ, 2A and 2C released; MCQ and 2B not released. Re-seeded evalify_db: 5 papers, 45 sheets.
- 16 Nov 23:40 — Experiments #3 and #5 done. #3 (smaller Qwen images) rejected: no speed gain, Qwen's readings
  change (agreement 84-86 % vs 96 % noise floor, more TA items). #5 (fixed part first) +6-9 % data-science speed
  but MAE 0.650 → 0.67 and agreement 93.5 % → not kept (quality must not drop); user can decide otherwise.
  #8 first start failed: second Gemma (38 GB) did not fit the 92 % of the PRO 6000's real 95.6 GB; test used
  nominal 96 GB → test now uses nvidia-smi sizes, profile resized (Qwen 38, Gemma#2 41). #8 restarted.
- 17 Nov 00:10 — #8 second Gemma failed again (41 GB → 6.25 GiB KV, 16k request needs 13.76 GiB). opt-gemma2
  (BF16 KV) gives no data; opt-gemma2-fp8 changed to request limit 8,192 + FP8 KV (starts ~00:13 via the
  other session's driver, evalify-45, which was told). GPUs idle 23:42-00:13 while that driver waited.

## 17 Nov — "Start evaluation" button (teacher) — whole-set batch
- User: "there is no need to implement the exam window i mean upload window for now or exam schedule. All i want is
  that their should be start evaluation button from teacher end. which starts the execution". So: no schedule, no
  upload window, no release lock for now.
- Uploads are only stored (status "submitted"); nothing is evaluated on upload any more.
- Teacher results page has an Evaluation panel: "N answer sheets waiting", **Start evaluation**, then progress
  "Stage 1 of 2: Reading answer sheets" / "Stage 2 of 2: Grading answers" with counts; table reloads at the end.
  Students see "Submitted / Waiting for evaluation", then "Being evaluated".
- Backend: POST /api/papers/{id}/evaluate, GET /api/papers/{id}/evaluation; app/services/batch_runner.py runs #9:
  every sheet read first (orchestrator.read_sheet, readings stored on the submission), then every sheet graded
  (orchestrator.grade_sheet); 32 sheets in flight per stage. State in MongoDB (batches + submission status) →
  resumes after a backend restart. A failed sheet becomes "error" and is picked up by the next Start evaluation.
- Optional model swap between the stages (EVALIFY_BATCH_PROFILE_FILE / _READ_PROFILE / _GRADE_PROFILE) is built
  but off: to be measured with a grader-only GPU profile before turning it on.
- Demo data: its "processing" sheets are now "submitted" (MCQ Basic Science, 2B) so the button can be tried.
- Tests: backend test_batch_evaluation.py (11), frontend EvaluationPanel.test.jsx (5) + notice / subject / results
  page tests; backend 266 passed, frontend 88 passed.
- 17 Nov — User: teacher's subject was not visible on the home page. Teacher dashboard header now shows
  "Teacher / <name>" and "Subject: <subject>" from the login (shown even with no papers). Test added.
- 17 Nov 01:31 — #8 + FP8 KV measured (Data Science part re-run after the other session's driver died at 00:21):
  206 / 217 DS sheets/h vs 156 / 157 (+32 / +38 %), MAE 0.646 / 0.639, MCQ accuracy unchanged, no errors. One-page
  no gain (Qwen at 38 GB now busiest). Recommended as production layout; user to decide.

## 17 Nov 2026 — README rewritten

- User asked for a new README.md: no emoji, explain the directory layout and the use of each file, and explain
  clearly how to set the project up on a new machine.
- The old README described the Ollama-based version (start.sh, Ollama models, emoji headings). Rewritten for the
  current v2 pipeline: how it works (roles, paper types, Start evaluation batch flow, components), requirements,
  setup on any machine (Docker / own / in-memory MongoDB, backend, frontend, dummy data, optional vLLM model
  servers with download + endpoints file), setup on the IIT Jodhpur cluster (scratch env, user-space MongoDB,
  Slurm GPU job, app.sh, port forwarding), demo accounts, tests, configuration variables, full directory layout
  with a table per folder, troubleshooting, and links to the plan / decision / experiment documents.
- docker-compose.dev.yml: README says to start only its mongodb + mlflow services (its backend/frontend
  services are still the Ollama version). Not changed.
- 17 Nov — User asked for a checkbox .md file for checking every part of the project by hand. Added
  MANUAL_CHECKLIST.md (14 sections: set-up, login, teacher home, paper wizard per type, paper page, student upload,
  Start evaluation, results / hand-marking / calibration, TA, release, student results and re-evaluation, look and
  feel, security, GPU job; expected result per item, notes per section, summary table). Linked from README.
- 17 Nov — User: "yes i agree #8 in production layout". Done:
  - `tier1` (production) = the measured #8 layout: A6000 Gemma 44 GB; PRO 6000 Qwen 38 GB FP8 KV, GLM-OCR 8 GB,
    Gemma copy 2 41 GB FP8 KV max 8,192 tokens (port 8112). Old production kept as `tier1-single` to go back.
  - Safeguard (my recommendation, agreed): a request refused by a copy as too long is resent to another copy of the
    model (llm.chat). Tests first: tier1 equals opt-gemma2-fp8, tier1 fits our GPUs, too-long resend, one server
    still errors. Backend 270 tests pass.
  - App connected to the running servers (job 48725 still on opt-gemma2-fp8 = same layout, 82xx ports): backend
    restarted with EVALIFY_ENDPOINTS_FILE=endpoints-opt.json. When this job ends, start production with
    `sbatch infra/cluster/serve_models.sbatch` (tier1, writes endpoints.json) and restart the backend without the
    override.
  - "Start evaluation" run on the 4 waiting dummy sheets (MCQ Basic Science 3, 2B 1): all evaluated, 0 errors,
    every mark equal to the gold labels (RESULTS.md row 15).
- 17 Nov — User: remove the red line between the dark panel and the form on the login pages. Removed the margin-rule class from AuthShell (the same red margin rule stays on the logged-in pages, PageWrapper; not asked).
- 17 Nov — User: "is there a teacher with two subjects?" (no) then "yes quickly build a teacher which has two subjects".
  Built: demo.env teacher line takes Physics;Mathematics like a TA's; new demo teacher science.teacher@evalify.local
  (Dr. Anita Desai, Physics and Mathematics). The login returns both subjects; creating a paper takes the chosen
  subject if the teacher teaches it, else their first (never another subject); the wizard shows a drop-down for two
  subjects (fixed text for one, new SubjectField component); the home page header shows "Subjects: Physics,
  Mathematics". Tests first (backend 275, frontend 92 pass). Backend restarted and checked: Mathematics paper
  created for Mathematics, Chemistry request fell back to Physics (test papers deleted).
- 17 Nov — User: give Prof. Ramesh Kumar two subjects. teacher@evalify.local now teaches Computer Science and Data Science (the user did not name the second subject; Data Science chosen as the natural pair, change it in demo.env if another is wanted). README and checklist updated; backend restarted.
- 17 Nov — User: enrol Aarav Sharma (CS2025001) in Data Science too. demo.env: Computer Science;Mathematics;Data Science. To keep Data Science at the 50-student limit (matches the 50 Mendeley sheets) the generated Data Science students are now DS2025001 to DS2025048 (was 049); 48 + Aarav + Priya = 50.
- 17 Nov — User: add reference material to the uploads folder for teachers to generate answer keys (the RAG
  assistant is for subjective papers only). Added uploads/Pattern3/Teacher/reference_material/: two original
  lecture-note PDFs (15 topics of the Data Science paper in full paragraphs plus 2 extra topics), a revision sheet,
  a scanned page without text layer (tests the "skipped" message) and questions_for_assistant.txt (S1-S15). Not for
  Pattern 1 and 2 (no written answers). Built by eval/make_upload_kit.py (reference_material(), text in
  eval/reference_material_text.py); only this folder was generated, the rest of the kit was left as it was.
  Tests first (backend/tests/test_reference_material.py, 18): files readable, scan skipped, search puts the right
  passage in the top 3 for each of the 15 questions. Tried with the live models: drafts cite the right file and
  page. The old reference_notes.txt (the answers themselves) is kept as the easy case.
- 17 Nov — User: do not write tests for everything; only a few reference documents are needed to try the RAG answer-key
  feature, and it must be shown only for type C papers. Checked: the assistant is already inside the type C block of
  wizard step 4 (isType3), nothing to change. Downloaded one real file, wikipedia_data_science_basics.txt (9 Wikipedia
  articles, CC BY-SA 4.0, 120 KB); a second download was rate limited (HTTP 429), and since few files are enough it was
  not repeated. Shrunk the scanned test page from 3.5 MB to 54 KB. No new tests for this (the 18 from the earlier step
  stay). The kit script empties uploads/ when run, so the downloaded file is not rebuilt by it (noted in uploads/README.md).
- 17 Nov — User's review notes (System design discussion.pdf), five items, fixed:
  1. Top bar: more space between "Evalify" and "ANSWER SHEETS, MARKED" (gap 8 -> 16 px). My reading of the note; the
     user may mean another spacing.
  2. Red line removed from the logged-in pages too (login pages done earlier); the unused margin-rule style is deleted
     and the page padding reduced (was made room for the rule).
  3. Question count: the wizard asks the server (POST /papers/detect-questions) to count the numbered questions in the
     uploaded question paper PDF. MCQ-only papers get the MCQ count set to it; other types only get a hint that the
     sections should add up to it; a scan gets "could not be counted". Checked on real papers: Data Science paper 35
     (20 + 15), MCQ paper 10. Best effort, the teacher can always change the number.
  4. MCQ-only papers now ask "OMR bubble sheet or Handwritten" (wizard step 2, new paper field answerSheetFormat,
     default OMR). The blank OMR sheet upload shows only for OMR (it used to show for every paper type). The student's
     upload page offers only that sheet type and the server refuses the other one; papers without the field accept both.
  5. Paper page: the answer key PDF uploaded in step 3 for extraction (answerKeyPdfUrl) was not listed, only the
     separate reference copy; both are listed now, plus the detailed answers and grading rubric PDFs of type C papers.
  Tests: backend 300, frontend 100 pass. MANUAL_CHECKLIST.md updated.
- 17 Nov — User: delete the "Quiz" paper (Computer Science, MCQ only, no submissions) to create it again. Deleted through the API as its owner, and its two uploaded PDFs (question paper, answer key) removed from backend/uploads/papers.
- 17 Nov — User started "Start evaluation" on their new Quiz paper (Prof. Kumar, MCQ-only, OMR): the sheet scored 0/20
  with no TA flag. Cause: the paper's blank OMR sheet was added but its bubbles were never confirmed, so the pipeline
  (by design, a wrong map would mis-grade everyone) ignored it and the layout-free reader read nearly every question as
  "A,B,C,D all filled". With the template confirmed the same sheet scores 20/20 (checked by re-running the pipeline).
  Fixes: (1) wizard step 3 cannot continue until the template is confirmed (hint shown), and a note appears when no
  blank sheet is added; (2) a question read as every option filled is flagged for the TA; (3) when a template exists but
  was not confirmed every question is flagged with that reason. Tests first (backend 303, frontend 102). The user's
  existing Quiz sheet keeps its stored 0 and needs re-creating the paper with the box ticked (the user said they
  would create it again), or re-running the evaluation after confirming.
- 17 Nov — User's second review notes (System design discussion (1).pdf) and a follow-up message:
  1. "Answer Sheet PDF" (the teacher's worked solution upload) renamed "Detailed Solution" in the wizard (upload label,
     review row and button) and on the paper page.
  2. Paper page MCQ answer key overflowed the card: grid now uses columns of at least 15 rem that fit the width.
     Found while checking the screenshot: keys with two correct options ("A,C") lit no option at all; both light now.
  3. Uploaded documents of the paper page also list the OMR layout (the blank OMR sheet) of an OMR paper.
  4. The blank OMR sheet is compulsory for OMR papers: the wizard cannot leave step 3 until it is uploaded and its
     bubbles are confirmed, and the server refuses an OMR paper without a confirmed template (400), so no client can
     create one. Handwritten and other paper types are unaffected. Replaces the earlier "recommended" wording.
  Tests first (backend 307, frontend 105 pass). Pattern 1 kit instructions and MANUAL_CHECKLIST.md updated.
- 17 Nov — User: for the Quiz paper (Prof. Kumar, OMR) select the OMR layout and delete the Aarav submission so it can be resubmitted. Set omrTemplate.confirmed = true on that paper (the 80 detected bubbles unchanged), deleted Aarav Sharma (CS2025001) submission (score 0.0), its page image and its finished batch record. The paper now has 0 sheets; Aarav can upload again, then Start evaluation.
- 17 Nov — User: the evaluation panel looked static while running ("0 / 1") and asked "is the accuracy correct" (meaning
  Aarav's Quiz sheet). Panel: now says "Evaluation is running" with a pulsing dot, the stage, "running for N min",
  that the teacher can leave the page, a pulsing bar for the active stage, a "taking longer than usual" warning after
  10 minutes with no finished sheet, and a clear "Evaluation did not finish" state with the reason for a failed batch.
  Robustness fix found on the way: when a batch crashed its unfinished sheets stayed "reading"/"grading" forever and
  Start evaluation stayed disabled; they now become errors (finished sheets keep their marks) and are picked up
  again by the next Start evaluation. Tests first (backend 308, frontend 108).
  Aarav's sheet (omr_L1_s01 of the user's labelled set): 20/20 is correct, gold labels equal the paper key.
  OPEN: a quick re-measurement of the template OMR on the user's 15 labelled sheets (blank sheets of the upload kit,
  template built without the wizard's confirm step) gave layout 1 and 2: 10/10 sheets perfect; layout 3: 3 of 5 sheets
  badly wrong and NOT flagged (alignment looks fine, bubbles read wrong). RESULTS.md row 3 says 99.7 % on these. To be
  investigated: is the kit's layout-3 blank the one the photos were made from, or a regression.
- 17 Nov — User: "how much time did it take to evaluate Aarav's sheet?" Answer 66 s (reading 5 s, grading 62 s), but
  only ~5 s was real work. Cause: MLflow is not running on the cluster (localhost:5005 unreachable) and each evaluated
  sheet waited ~60 s for its retries; worse, the call ran on the server's main thread, so it froze the whole backend
  (API and page loads too) and the waits would add up one sheet after another in a class batch. Fixes: MLflow calls
  run in a worker thread (evaluator), no retries and a 5 s timeout, and after one failed call MLflow is skipped for
  60 s before trying again (tracking resumes by itself once MLflow is started). Tests first (backend 312 pass).
  MLflow itself is still not installed or started on the cluster, so nothing is tracked; start it if tracking is wanted.
- 17 Nov — User asked what MLflow is for and how to use it here; MLflow package is installed (2.13.0) but no server runs and no data folder exists on the cluster. Setting it up (start under /scratch, add to infra/cluster/app.sh, forward port 5005) is postponed: "we will do it later". The app works without it (logging now fails fast).
- 17 Nov — User: create a detailed high level design, Mermaid diagrams and sequence diagrams in a folder called
  "Architecture Diagram". Added Architecture Diagram/ with README.md (index), 01_High_Level_Design.md (14 sections),
  02_Mermaid_Diagrams.md (11 diagrams: context, layers, backend modules, frontend routes, pipeline, ER model, sheet and
  batch life cycles, cluster deployment, GPU layout, access map) and 03_Sequence_Diagrams.md (13 flows). Written from
  the code as it is today (tier1 layout with two Gemma copies, two-stage batch, confirmed OMR template rule). All 29
  diagrams checked with the Mermaid 10.9 parser, 0 errors. Linked from the main README. No tests (documentation only).
- 17 Nov — User: make the Mermaid and sequence diagrams "simple but effective". Replaced the 11 + 13 detailed
  diagrams with 5 architecture diagrams (system architecture, marking pipeline, data model, answer sheet life cycle,
  deployment) and 4 sequence diagrams (exam round end to end, evaluation batch, TA review and re-evaluation,
  answer-key assistant). Short labels, one message per diagram, the same colour key everywhere (people grey,
  application blue, data yellow, models green), stages shaded in the sequences. All 14 diagrams (with the 5 in the
  design document) parse with Mermaid 10.9. The detailed design document is unchanged.
- 17 Nov — User: give the diagrams as JPG inside the Architecture Diagram folder. Rendered all 9 diagrams with the Mermaid CLI 10.9.1 (Chrome cached under /scratch) at 3x scale and converted to JPG in Architecture Diagram/images/ (01 to 09). Checked each picture; reworked the layout of the system architecture and deployment diagrams (group boxes neutral instead of the default yellow, one arrow per group, no crossing lines) and styled the decision diamonds. Listed the images in the folder README.
- 17 Nov — User: make diagrams 06 and 07 simpler and more accurate. 06 (exam round): 11 steps, no shaded phases; says only handwritten reading and written grading use the AI models (MCQ, numerical and OMR are marked in code) and no longer implies the release waits for the TA. 07 (start evaluation): the batch and the 5-second progress checks are drawn running at the same time (par), stage 2 shown starting after every sheet is read, third reader mentioned. Re-rendered both JPGs.
- 17 Nov — User: diagram 06 without the stick-figure people, drawn as if in Excalidraw. Mermaid cannot draw sequence diagrams hand-drawn, so 06 is drawn with roughjs (Excalidraw's sketch library) and the Virgil font: hachured coloured boxes in the usual colour key, dashed lifelines, solid requests, dashed replies, numbered steps, a yellow note. Saved as images/06_sequence_exam_round.jpg; the drawing script is kept in Architecture Diagram/sketch/ with how to re-run it. The Mermaid version of 06 now uses plain boxes (participant) instead of stick figures.
- 17 Nov — User: check Aarav's current submission. "Subjective" paper (Student_19 of the Mendeley set, kit DS2025001):
  MCQ 19/20 readings right, Q5 misread (A as B) but flagged for the TA; all 15 written answers 0 with no flag. Cause:
  paper set to S1.. numbering, student wrote 21-35. Found on the way: norm_label turned "S1" into "Q1" (the MCQ label),
  so S-numbered written answers could never be found at all; every evaluation so far used continuous numbering.
- 17 Nov — User asked to implement (1) the safety net and (2) "accept either numbering", and to draw hand-drawn RAG
  diagrams. (1) orchestrator.flag_missing_written: when no written answer is found anywhere on a sheet, every written
  question goes to the TA with "no written answer found under S1 to S15 or Q21 to Q35; check the question numbering".
  (2) each written question has an alternate label (S1 <-> Q21); the transcribers are told both, either is accepted
  (both joined if both used); norm_label keeps S-labels; [[S2]] markers are split. Tests first (backend 318).
  Diagrams: Architecture Diagram/images/10_rag_architecture.jpg and 11_rag_sequence.jpg, drawn with
  sketch/sketch_lib.mjs, rag_architecture.mjs, rag_sequence.mjs.
- 17 Nov — User: remove the shading from the boxes in the two RAG diagrams. sketch_lib.mjs got a flat style (one light fill colour per kind, same colour key, no hachure lines); 10_rag_architecture.jpg and 11_rag_sequence.jpg redrawn with it, including the yellow note.
- 17 Nov — Re-measured "either numbering" on the Data Science set (48 sheets, c32, production layout): 218 sheets/h, MCQ 97.7 %, written MAE 0.648 vs 0.639 before (baseline 0.650), 0 errors; extra TA items are on MCQ questions the change does not touch (noise). Kept. Report eval/reports/numbering_either/README.md, RESULTS.md row 16. Backend restarted with the change.
- 17 Nov — Correction while explaining the bottleneck: "Gemma ~0.86 MB KV per token" (from the 13.76 GiB / 16,384-token error) is not a constant; another error gave 15.79 GiB for 32,768 tokens (Gemma mixes full and sliding-window layers). Reliable like-for-like from the server logs: whole PRO 6000 (76 GB) holds 170,666 Gemma tokens vs 632,149 Qwen tokens, so Gemma needs ~3.7x more memory per token. INFERENCE_OPTIMIZATION.md note corrected. Calls per Data Science sheet (3-page sheet): Gemma 21 (3 read, 3 transcribe, 15 grade), Qwen 6, GLM-OCR 0; tokens Gemma ~15.3k, Qwen ~21.1k.
- 17 Nov — User: make a file explaining the whole system flow and where every feature's code lives, exploring all features and directories. Added CODE_MAP.md (flow table, directory tree, feature map with screen / endpoint / backend / tests per feature, pipeline file by file, data, cluster scripts, eval harness, tests, documents, where to change things). Linked from README.
