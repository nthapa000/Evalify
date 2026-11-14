# Evalify: Model and Hardware Plan (14 Nov 2026)

Goal: maximize grading accuracy so the fewest sheets go back to TAs. Build and test on the IIT Jodhpur college server (not deploying yet).

## 1. Constraints

- Slurm partition: mtech. All GPU nodes (cn02, cn03, cn04, cn05, cn07) are on it. Wall time does not matter.
- Limits: 2 running jobs at a time (3 submitted, CPU jobs count), 2 GPUs in use at once across running jobs.
- GPUs: cn02 to cn05 have 2x A30 24 GB each. cn07 has 6x RTX PRO 6000 Blackwell 96 GB. Your cap is 2 GPUs, so the best case is 2x RTX PRO 6000 (192 GB).
- Disk: 200 GB scratch, 70 GB CSE home. Scratch purge policy unknown.
- Everything must be open weights and self-hosted.

## 2. Main findings from the research

- Most grading errors on handwritten work come from reading (transcription), not from applying the rubric. A study on handwritten grading attributed up to 87% of errors in the best model to transcription (arXiv 2605.19043).
- General VLMs silently "fix" student mistakes while transcribing. 42 to 66% of multi-line handwritten math transcriptions had at least one over-correction (arXiv 2604.22774). A "transcribe exactly, do not correct" prompt reduces this by roughly 30 to 50% but does not remove it.
- Rewrite tendency does not fall with model size above about 4B parameters, so a bigger single model is not the fix. Redundancy (two different readers) is.
- Handwriting is not solved: the best model on WildHandBench scored 71.85% vs a human 77.09%.
- Per-concept yes/no rubric checks, deterministic decoding, and self-reported confidence work better than free-form grading and voting.
- Template-based OMR is more reliable than a VLM for bubbles and gives a measurable margin.
- Many 2026 figures are vendor-reported. Verify sizes and scores yourself.

## 3. Approaches compared

| Approach | Strength | Weakness | Verdict |
|---|---|---|---|
| 1. OCR then text LLM | Exact strings for numbers and MCQ; separates reading from judging | Loses diagrams and layout; OCR errors propagate | Good for short, exact answers |
| 2. Image straight to VLM with rubric | Sees diagrams and context; simple | Silent correction; reading and grading errors are mixed; no confidence signal | Unsafe as the only reader |
| 3. Hybrid (recommended) | Two independent readers, code for closed-form checks, rubric-decomposed grading, routing on disagreement | More engineering and about 2 to 3x compute | Best accuracy |

## 4. Recommended pipeline

1. Ingest and quality gate: page ordering, perspective correction, deskew, resize to about 1500 to 2000 px, blur and glare checks. Ask the student to re-upload bad pages. Keep the original colour image for the VLM and use binarization only for OMR.
2. Segmentation: use printed answer boxes where possible. For free-form sheets, have the VLM return question labels with boxes, then crop per answer and stitch multi-page answers by question label.
3. Type 1 OMR: template plus corner markers (OMRChecker style) with per-bubble fill ratio and margin. For handwritten MCQ, constrain output to A, B, C, D, blank or unclear from two readers.
4. Transcription with two readers from different families: Reader A is a general VLM with a strict verbatim prompt (preserve strike-throughs, mark illegible tokens). Reader B is an OCR specialist.
5. Numeric grading in code: normalize minus signs, commas, fractions, scientific notation and units; compare with tolerance from the teacher key. Never let an LLM decide numeric equality.
6. Subjective grading: the grader sees the question, model answer, concept list, both transcripts and the cropped image. Output is JSON per concept with present (yes or no), an evidence quote and a confidence. Mandatory-concept logic and marks are summed in Python. Temperature 0.
7. Routing to TAs when any of these hold: readers disagree on a number or MCQ, large transcript disagreement, thin OMR margin, low grader confidence on a concept, two graders differ by more than 1 mark, or the page failed the quality gate. Send only the flagged questions, with the model's evidence.
8. Log every output, model version and prompt hash to MLflow.

### Which method handles which paper type

Decision: one shared set of models and one pipeline for all three paper types. The method is chosen per question type, not per paper type. The three paper types are only different combinations of the same question types.

| Question type | Method | Model involvement |
|---|---|---|
| MCQ on an OMR sheet | Template-based OMR with corner markers and fill margins | None (OpenCV code) |
| MCQ handwritten ("Q1: B") | Two readers, output constrained to A, B, C, D, blank or unclear | General VLM plus an OCR model |
| Numerical | Two readers extract the number, then Python normalizes and compares with tolerance | Readers only; no LLM judges equality |
| Subjective | Two readers transcribe, then a grader checks each rubric concept yes or no with an evidence quote and confidence | General VLM as grader (and a second grader on bigger tiers) |

| Paper type | Paths that run | Grader used |
|---|---|---|
| Type 1: MCQ only | OMR code, or the two readers for handwritten MCQ | No |
| Type 2: MCQ + numerical | MCQ path plus numerical path | No |
| Type 3: MCQ + numerical + subjective | MCQ, numerical and subjective paths | Yes, only for subjective answers |

- Why not one model for everything: bubbles and numbers have exact right answers, so deterministic code is more accurate than any model and gives a measurable margin for routing. A general VLM on those would bring back the silent-correction problem exactly where exactness matters most.
- Shared in the app: the same upload, preprocessing and quality gate, the same model servers (a paper type only decides which paths run), and the same routing logic and MLflow logging.
- Hardware impact: Type 1 and Type 2 papers mostly use code and the OCR models, so even a single A30 can handle them. The large models matter mainly for Type 3 subjective answers, which is also where most TA flags will come from.

## 5. Model candidates

### Readers and OCR

| Model | Size (params, BF16 disk) | License | Notes |
|---|---|---|---|
| Qwen3.8-27B | 27.8B, about 55.6 GB (FP8 about 30 GB, estimate) | Apache 2.0 | Newest Qwen open VLM (Aug 2026), native vision, thinking mode. Main reader and grader candidate |
| Qwen3.6-27B | 27B, 54.7 GB (FP8 30.9 GB, Q4_K_M about 17 GB) | Apache 2.0 | Safe fallback if 3.8 tooling lags |
| Gemma 4 31B | 30.7B, about 63 GB (8-bit about 34 GB, 4-bit about 20 GB) | Apache 2.0 | Different family, good for cross-checking |
| Chandra OCR 2 | 5.3B, about 10.6 GB | Weights restricted commercially (free for research and small orgs) | Vendor-reported olmOCR-Bench 85.8; no independent handwriting evidence found. Contender, not proven best |
| PaddleOCR-VL-1.6 | 0.9B, about 1.9 GB | Apache 2.0 | Strong on printed documents; test on phone photos |
| GLM-OCR | 0.9B, about 2.65 GB | MIT | Small, permissive |
| Nanonets-OCR2-3B | 3B, size not verified | not verified | Best OCR-specialist handwriting score in OmniHandwritingOCR |
| Tesseract / docTR | under 1 GB | Apache 2.0 | 0% rewrite rate; useful as a faithfulness anchor for digits |
| olmOCR 2 | 7B, 16.6 GB | Apache 2.0 | Highest rewrite rate (58.6%); not recommended for verbatim reading |

### Graders

| Model | Size | Notes |
|---|---|---|
| Qwen3.8-27B (thinking) | same weights as reader | No extra disk |
| Qwen3.5-122B-A10B | FP8 about 125 GB, 4-bit about 79 GB | Multimodal, can see the image. Only worth it if the bake-off shows a gain |
| gpt-oss-120b | about 61 to 65 GB | Text only; best calibrated in one study |
| gpt-oss-20b | about 13 to 14 GB | Cheap text grader |
| Gemma 4 31B | see above | Independent second grader |

Too large for your disk: Qwen3.5-397B, Kimi K3, Qwen3.8-2.4T. Superseded: Llama 3.2 Vision 11B (current). Not recommended: InternVL3.5 for verbatim reading.

### Other tools

- OMR: OMRChecker (and the badalsura fork with confidence queue and silent-error benchmark).
- Handwritten math: read with the main VLM first. Add Uni-MuMER on equation crops only if math reading dominates errors. Score faithfulness with the PINK metric.

## 6. Hardware tiers (all options, max 2 GPUs)

### Tier 1: 2x RTX PRO 6000 (best case, 192 GB)

| GPU | Models | Weights VRAM |
|---|---|---|
| 0 | Qwen3.8-27B FP8 (reader A, grader 1) + Chandra OCR 2 + PaddleOCR-VL-1.6 | about 30 + 12.5 GB |
| 1 | Qwen3.5-122B-A10B 4-bit (primary multimodal grader), optionally Gemma 4 31B 8-bit | about 79 GB (+34 GB) |

- 122B at FP8 would span both GPUs and leave almost no room for readers, so use 4-bit on one GPU.
- Option: BF16 Qwen3.8-27B (about 56 GB) on GPU 0 for zero quantization loss, if disk allows.

### Tier 2: 1x RTX PRO 6000 (96 GB)

- Qwen3.8-27B FP8 (about 30 GB) + Gemma 4 31B 8-bit (about 34 GB) + Chandra OCR 2 (10.6 GB) + PaddleOCR-VL-1.6 (1.9 GB): about 77 GB plus KV cache.
- Separate vLLM servers with memory fractions.

### Tier 3: 2x A30 (24 GB each, 48 GB total)

- Recommended: one model per GPU. GPU 0: Qwen3.8-27B 4-bit (about 18 GB), GPU 1: Chandra OCR 2 + PaddleOCR-VL-1.6 (about 12.5 GB).
- Alternative: Qwen3.8-27B FP8 (about 30 GB) with tensor parallel across both GPUs for less quantization loss, then run OCR afterwards.
- Loses the second subjective grader.

### Tier 4: 1x A30 (24 GB)

- Qwen3.8-27B 4-bit (about 18 GB) as reader and grader; load PaddleOCR-VL-1.6 or GLM-OCR only when needed.
- Roughly 1 to 3 subjective answers per minute (estimate); run batches overnight.

### Hardware notes

- A30 (Ampere): no native FP8, so FP8 checkpoints run as weight-only and give no speed-up. AWQ and GPTQ work. BF16 works. Prefer 8-bit or AWQ over very low-bit GGUF for the grader.
- RTX PRO 6000 (Blackwell, sm_120): needs CUDA 12.8 or later and driver R580 or newer. FP8 and NVFP4 run natively, but some FP8 paths on SM120 were broken in some 2026 builds. Pin a known-good vLLM container and compare against BF16 on your test sheets.
- cn07 availability: 5 of 6 GPUs were in use in your screenshot, so getting 2 on demand is not guaranteed. Make the backend read model endpoints per role from config so it degrades instead of breaking.

## 7. Job layout under your Slurm limits

- Job 1: model servers (vLLM), holding both GPUs.
- Job 2: backend, MongoDB and MLflow as a CPU job, reached through an SSH tunnel. Or run them inside Job 1 to keep a slot free for experiments.
- With only 3 submitted jobs, run bake-offs as sequential steps inside one job.

## 8. Serving stack

| Stack | Verdict |
|---|---|
| vLLM | Primary: schema-constrained JSON, multi-image, best batching, FP8, AWQ. Run in Apptainer built from the vllm-openai Docker image |
| SGLang | Good alternative |
| llama.cpp server | Best for a single A30 with GGUF; Q8 is near lossless, Q4 loses accuracy |
| Ollama | Dev only; replace in production |

- FastAPI calls each server through the OpenAI-compatible endpoint (base URL per role), sends the JSON schema in response_format, and validates replies with Pydantic.
- Keep a model registry (name, endpoint, version) in MongoDB or MLflow.

## 9. Storage plan

| Item | Location | Size |
|---|---|---|
| Hugging Face cache (HF_HOME), Apptainer cache, vLLM and torch caches | scratch | per stage below |
| vLLM container image, conda env, code, prompts | home | about 20 to 30 GB (estimate) |
| Labelled sheets, crops, eval outputs, re-download script with pinned revisions | home | about 5 to 15 GB |

Staged downloads (the full set is about 155 GB of weights, which is tight once downloads, variants and caches are counted):

| Stage | Keep on scratch | Approx. use |
|---|---|---|
| 1. Build and bake-off | Qwen3.8-27B FP8, Chandra OCR 2, PaddleOCR-VL-1.6, plus GLM-OCR and Nanonets-OCR2-3B | about 50 GB |
| 2. Second grader | add Gemma 4 31B 8-bit (or 4-bit at about 20 GB) | about 85 GB |
| 3. Only if justified | add Qwen3.5-122B-A10B 4-bit | about 165 GB |

- Delete losing models after each bake-off.
- Require at least 100 GB free before pulling the 122B.
- Point APPTAINER_CACHEDIR and the vLLM and torch cache directories to scratch so home does not fill.
- All sizes are estimates from model cards and third-party listings. Check the Hugging Face file listing before downloading.

## 10. Ground truth and metrics

- Labelled set: ideally 150 to 300 sheets double-graded by two TAs. For build and test, 30 to 50 sheets with known correct marks is enough to compare models. Hand-transcribe the answers, freeze about 30% as a test split, and include deliberately wrong answers to measure silent correction.
- Readers: CER and WER, plus over-correction rate (PINK-style).
- MCQ and numeric: exact match after normalization.
- Subjective: QWK, MAE, exact and within-1-mark agreement, per-concept accuracy. Human-human agreement is the ceiling (one study found human-pair QWK of only 0.551).
- System level: coverage (share auto-accepted), accuracy on auto-accepted items, silent error rate (wrong but auto-accepted), and TA routing rate.
- Calibrate routing thresholds on the dev split to hit a target auto-accept accuracy.

## 11. Ranked alternatives to the main pipeline

1. Simpler: one VLM as reader and grader plus a small OCR model as second reader only for numbers and MCQ. Nearly as good on small hardware.
2. Largest tier: Qwen3.5-122B as end-to-end multimodal grader, cross-checked by Qwen3.8-27B and gpt-oss-120b as text graders. Higher ceiling, uses most of the disk.
3. With labelled data: LoRA-tuned Qwen VLM grader. A published open-model setup beat human-pair agreement, but it is tuned to one examiner. A 27B LoRA in BF16 fits on one RTX PRO 6000; on A30s use QLoRA on 7 to 9B models.

## 12. Phased rollout

1. Phase 0: build the labelled set and an evaluation harness logged to MLflow. Run the current llama3.2-vision baseline for a reference number.
2. Phase 1: deterministic wins. Preprocessing and quality gate, template OMR with margins, numeric normalizer with tolerance. Fix the blocking repo issues (missing app/models, env files, dockerignore, tests).
3. Phase 2: reader bake-off on hand-transcribed sheets: Qwen3.8-27B, Qwen3.6-27B, Gemma 4 31B, Chandra OCR 2, PaddleOCR-VL-1.6, GLM-OCR, Nanonets-OCR2-3B, with and without the do-not-correct prompt. Keep the two most accurate readers from different families.
4. Phase 3: grader bake-off on gold transcripts: Qwen3.8-27B thinking, gpt-oss-20b and 120b, Qwen3.5-122B-A10B, using per-concept binary prompts with confidence.
5. Phase 4: end-to-end pipeline plus routing. Calibrate thresholds and report the TA routing rate per paper type.
6. Phase 5 (optional): LoRA the grader on TA corrections, add Uni-MuMER for equation crops, re-run the bake-off when new open models ship.

## 13. Risks and open questions

- Vendor-reported benchmarks and estimated sizes need verification.
- The strongest handwritten-grading results in the literature used proprietary models; open models will likely score lower on your sheets.
- No published head-to-head of open VLMs vs template OMR on phone photos, and no measured throughput for these exact models on your GPUs.
- Blackwell FP8 and NVFP4 support in vLLM has been unstable in some builds.
- Chandra OCR 2 weights restrict commercial use.
- Scratch purge policy is unknown.
- LLM grading varies between sampled runs, so use temperature 0, a second model for uncertainty, and keep TAs as final authority on disputed marks.

## 14. Key sources

- Levine et al., handwritten grading transcription errors: https://arxiv.org/html/2605.19043
- Seong et al., "When VLMs Fix Students": https://arxiv.org/html/2604.22774v1
- FaithC4 (OCR rewrite rates): https://arxiv.org/pdf/2607.21617
- WildHandBench: https://arxiv.org/html/2608.22959
- OmniHandwritingOCR: https://arxiv.org/pdf/2608.18586
- Tonmoy et al., LoRA VLM grading: https://arxiv.org/html/2609.14284v2
- Ferrer et al., confidence calibration: https://arxiv.org/html/2603.29559v1
- Autorubric: https://arxiv.org/html/2603.00077v1
- Chandra OCR 2: https://huggingface.co/datalab-to/chandra-ocr-2
- PaddleOCR-VL-1.6: https://huggingface.co/PaddlePaddle/PaddleOCR-VL-1.6
- GLM-OCR: https://huggingface.co/zai-org/GLM-OCR
- OMRChecker fork: https://github.com/badalsura/OMRChecker
- vLLM structured outputs: https://docs.vllm.ai/en/latest/features/structured_outputs/
