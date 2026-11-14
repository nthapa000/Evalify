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
