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
