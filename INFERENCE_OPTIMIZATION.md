# Inference optimisation log

Goal: mark answer sheets faster on our own GPUs **without changing the marks**. Every technique is tested
through the real pipeline (`orchestrator.run`) on real labelled sheets and compared with the current set-up
(the *baseline*). Nothing here changes the UI or the default pipeline until a step is accepted.

- Test script: `eval/exp_inference.py` (`run` per set-up, `score` → `eval/reports/exp_inference/README.md`)
- Raw results: `eval/reports/exp_inference/runs/<set-up>__<workload>__c<N>.json` (every sheet's answers and marks)
- Serving profiles: `infra/models.yaml` (`opt-*`), job script `infra/cluster/serve_switch.sbatch`
- Client-side switches (off by default): `EVALIFY_IMAGE_MAX_PIXELS`, `EVALIFY_GRADE_LAYOUT`
- Tests: `backend/tests/test_inference_options.py`

## How each set-up is measured

| What | How |
|---|---|
| Workloads | **one-page**: 30 handwritten MCQ and MCQ + numerical phone photos (own sheets). **data-science**: 48 Mendeley exam sheets (20 MCQ + 15 written answers, 4-6 pages) |
| Load | 16 and 32 answer sheets marked at the same time (the earlier test showed the GPUs saturate around 8-16) |
| Speed | wall time → sheets per hour, tokens per second |
| Why | KV-cache use and requests waiting on each model server, sampled every 2 s from vLLM `/metrics` |
| Accuracy | MCQ / numerical read correctly vs labels; written-answer error vs the teacher (MAE, 0-2 per answer); number of TA items |
| Did the marks change? | answers and marks identical to the baseline, per question. Noise floor = the baseline against itself at the other load level (batching can change a few greedy outputs) |

## Starting point (16 Nov 2026)

GPU job 48707, profile `tier1-bakeoff`: Gemma 4 31B FP8 on the RTX A6000 (44 GB), Qwen 3.8 27B FP8 + GLM-OCR +
Chandra + PaddleOCR on the RTX PRO 6000. From the vLLM logs of the earlier throughput test:

| Server | KV cache (tokens it can hold) | Peak use | Peak waiting |
|---|---|---|---|
| Gemma (A6000) | 48,200 (≈ 1.5 full-length requests) | 100 % | 61 |
| Qwen (PRO 6000) | 178,176 | 98.5 % | - |

So the GPUs wait for memory, not compute. Chandra and PaddleOCR (26 GB) are loaded but never called.

Constraint found: the `mtech` QoS allows **2 GPUs per user** (`QOSMaxGRESPerUser`), so the optimised set-ups
cannot run next to job 48707; the baseline is measured first, then 48707 is released and one switchable job
(`serve_switch.sbatch`) runs the steps one after another on the same GPU pair.

## Techniques

| # | Technique | Where | Status |
|---|---|---|---|
| 1 | Stop loading Chandra + PaddleOCR; Qwen + GLM-OCR get the whole PRO 6000 | profile `opt-lean` | to measure |
| 1b | Give Gemma the big card instead (Gemma on PRO 6000, Qwen on A6000) | profile `opt-swap` | to measure |
| 2 | FP8 KV cache (`--kv-cache-dtype fp8`): about twice the tokens in the same memory | profile `opt-fp8kv` | **Qwen only**: not possible for Gemma on the A6000 (vLLM: native FP8 KV needs SM89+, A6000 is SM86) |
| 3 | Smaller page images for Qwen only (~2,730 tokens per page now) | `EVALIFY_IMAGE_MAX_PIXELS='{"qwen38-27b-fp8": N}'` | **rejected**: no speed gain, Qwen's readings change (see results) |
| 4 | Gemma prefill budget per step 2,496 → 4,096 tokens (`--max-num-batched-tokens`) | profile `opt-batch` | 8,192 does not start on the A6000 (too little KV left); 4,096 + request limit 16,384 measured |
| 5 | Grading prompt with the fixed part (rubric, rules) first, transcriptions last, so the server can reuse it | `EVALIFY_GRADE_LAYOUT=fixed_first` | +6-9 % speed but marks worse (MAE 0.650 → 0.67): **not kept** unless the user accepts that |
| 6 | Speculative decoding | - | not planned: our output is read from images, not copied from the prompt, so draft tokens rarely match |
| 8 | Second Gemma copy on the PRO 6000, requests to the least busy copy (user request) | profile `opt-gemma2` | after #3 and #5 |
| 9 | Whole-set batch for the teacher's "Start evaluation" (stages + model swap) | see section below | proposal, not built |
| 7 | Prefill / decode disaggregation (user idea) | - | researched, see below; **not implemented** (user decision, 16 Nov) |

Notes:
- #5 keeps the exact same words (checked by a test); only the order changes. The grader's fixed part is only
  ~330 tokens per answer, so the expected gain is small; it is measured because it costs nothing.
- #3 changes what Qwen sees, so reading accuracy is the main risk; two sizes are tried.

## #7 Prefill / decode disaggregation — research only (16 Nov)

Idea (user): our paper types stress the GPUs differently, so split the two phases of inference — *prefill*
(reading the prompt and page images, compute-heavy) and *decode* (writing the answer token by token,
memory-bound) — onto separate vLLM instances.

What we found:
- vLLM's own docs: "Disaggregated prefill DOES NOT improve throughput"; the gain is steadier time-per-token
  under strict latency targets (an online chat service). Our job is the opposite: a batch of sheets where only
  the total time counts.
- Each prefill and decode instance holds its **own full copy of the model**. We serve two big models (Gemma 31B,
  Qwen 27B) on two GPUs, so one prefill + one decode instance of each would need about 4 GPUs' worth of weights.
- The KV cache must be copied from the prefill GPU to the decode GPU. Our two GPUs have **no peer-to-peer link**
  (`nvidia-smi topo -p2p r` → `NS`), so it goes through host memory. vLLM's 2026 guide measured exactly this kind
  of box (2 x L40S, PCIe, P2P `NS`): each 8k-token transfer took about 1.3 s and time to first token got ~3x worse.
- Encoder disaggregation (vision encoder on its own instance, vLLM 0.32 has it) helped image/video-heavy loads on
  4-12 big GPUs; per GPU +7-10 % at high load, worse at low load.

Our workloads (measured in exp_tokens): one-page sheets are prefill-heavy (page image in, a few answers out);
Data Science sheets are decode-heavy (Qwen ~8k and Gemma ~8k output tokens per 10-page sheet; output tokens are
the slow part). Chunked prefill (already on) is what mixes the two inside one server.

Verdict: unlikely to help on 2 GPUs over PCIe with two different models; it is a multi-GPU / multi-node
technique. Alternatives considered (mixing paper types in one batch, priority scheduling, a prefill/decode split
of Qwen on 4 GPUs) were judged by the user not to help our application → **#7 and its alternatives are not
implemented or tested** (user decision, 16 Nov).

Sources: docs.vllm.ai/en/latest/features/disagg_prefill.html; vllm.ai/blog/2026-09-29-disaggregated-serving-guide;
vllm.ai/blog/2026-11-11-encoder-disaggregation-epd.

## #9 Whole-set batch: faster overnight marking without lowering quality (proposal, 16 Nov)

Planned UI flow (after these experiments): students upload in a 15-minute window, nothing is evaluated on
upload, the teacher clicks "Start evaluation" and the whole set is marked overnight. Then we know every sheet in
advance and only the total time counts, so work can be organised across sheets instead of sheet by sheet.
Quality stays the same because the models, prompts and inputs do not change.

Where Gemma's work goes on a Data Science sheet (exp_tokens, per sheet): grading 6,154 in / 1,617 out tokens;
reading MCQs 2,636 / 1,400; transcribing 2,247 / 615 → **grading is about half of Gemma's work**, and Gemma is
the bottleneck.

1. **Two stages for the whole set + model swap.** Stage 1: read and transcribe every sheet (Gemma + Qwen +
   GLM-OCR, as now). Stage 2: grade every written answer — only Gemma is needed, so Qwen and GLM-OCR are
   unloaded and a second Gemma gets the whole PRO 6000 (native FP8, large KV; #1b showed Gemma there is fast
   with spare capacity). Unlike #8 nothing has to be squeezed. Cost: one model reload (~5 min) per batch.
2. **Grade question by question across the class** (all answers to S1, then S2, ...): with #5 the rubric part
   of the prompt is identical for consecutive requests, so the prefix cache is reused.
3. **Constant load all night**: a queue keeps the best number of sheets in flight (from these experiments);
   longest sheets first, so the night does not end with one long sheet running alone.
4. **CPU work first**: page cleaning / quality gate for all sheets before the GPU stages, so GPUs never wait.

Not allowed because they would lower quality: smaller or fewer models, dropping a reader, smaller images unless
#3 shows no accuracy loss.

## Results

Full tables: `eval/reports/exp_inference/README.md`.

### Baseline (job 48707, profile `tier1-bakeoff`, 16 Nov 16:22-17:01)

| Workload | In flight | Sheets / h | Gemma KV peak / waiting | Qwen KV peak / waiting | MCQ / numerical correct | Written MAE | TA items |
|---|---|---|---|---|---|---|---|
| one-page (30) | 16 | 1,950 | 99 % / 1 | 49 % / 9 | 205/225 (91.1 %) | - | 8 |
| one-page (30) | 32 | 2,249 | 100 % / 12 | 93 % / 2 | 205/225 (91.1 %) | - | 7 |
| data-science (48) | 16 | **156** | 100 % / 50 | 99 % / 37 | 937/960 (97.6 %) | 0.650 | 6 |
| data-science (48) | 32 | **157** | 100 % / 128 | 100 % / 84 | 937/960 (97.6 %) | 0.650 | 13 |

- Data Science does not get faster from 16 to 32 sheets in flight: both models are out of KV memory and queue.
- Noise floor (baseline vs itself at the other load): one-page 100 % identical; Data Science 96.1 % of answers
  and marks identical (batching changes a few greedy outputs). A step "does not change the marks" if it stays
  near these numbers and the accuracy columns do not get worse.
- "MCQ / numerical correct" counts every answer read, also those sent to a TA, so it is lower than the
  "silent error" figures of earlier runs; only its change between steps matters here.

Then job 48707 was released (cn07 had 2 free GPUs besides ours) and job 48725 (`serve_switch.sbatch`) started
on the same pair (RTX A6000 + RTX PRO 6000), so the steps are comparable with the baseline.

### #1 and #1b (job 48725, 17:03-18:36)

| Set-up | one-page 16 / 32 (sheets/h) | data-science 16 / 32 (sheets/h) | DS written MAE | DS same as baseline |
|---|---|---|---|---|
| baseline | 1,950 / 2,249 | 156 / 157 | 0.650 / 0.650 | 96.1 % (noise floor) |
| #1 `opt-lean` | 2,111 / 2,226 | 155 / 158 | 0.647 / 0.644 | 96.2 % / 95.6 % |
| #1b `opt-swap` | 979 / 1,275 | 137 / 132 | 0.642 / 0.646 | 94.7 % / 96.2 % |

- #1: Qwen's KV 178,176 → 632,149 tokens, but speed unchanged: Gemma on the A6000 is still the bottleneck
  (KV 100 %, up to 121 waiting) while Qwen sits at 14-89 %. Marks unchanged. **Kept** (production `tier1`).
- #1b: whichever model is on the A6000 becomes the bottleneck — the A6000 has no native FP8, so vLLM uses the
  slower Marlin weight-only kernels there (Blackwell: CUTLASS / DeepGEMM FP8). Gemma on the PRO 6000 got only
  170,666 KV tokens from 76 GB (Gemma needs much more memory per token than Qwen). **Rejected.**

### Failed starts (19:16-19:31) and fixes

- `opt-batch` with 8,192: Gemma refused to start ("15.79 GiB KV needed for one 32,768-token request, 9.47 GiB
  available"). Re-done with 4,096 and `--max-model-len 16384` (longest Gemma request ≈ 9k tokens).
- `opt-fp8kv`: Gemma — FP8 KV unsupported on the A6000 (SM86). Qwen — FlashInfer's JIT kernel failed to link
  ("cannot find -lcudart"): the CUDA 13 pip wheel has only `lib/libcudart.so.13`, FlashInfer links via
  `lib64/libcudart.so`. Fixed with two symlinks (also added to `infra/cluster/setup_vllm_env.sh`).


### #4 and #2 (job 48725, 19:46-21:05)

| Set-up | one-page 16 / 32 (sheets/h) | data-science 16 / 32 (sheets/h) | DS written MAE | DS same as baseline | DS TA items |
|---|---|---|---|---|---|
| baseline | 1,950 / 2,249 | 156 / 157 | 0.650 / 0.650 | 96.1 % (noise floor) | 6 / 13 |
| #4 `opt-batch` (Gemma 4,096) | 1,828 / 2,202 | 153 / 154 | 0.645 / 0.647 | 95.6 % / 96.1 % | 7 / 9 |
| #2 `opt-fp8kv` (Qwen FP8 KV) | 2,172 / 2,244 | 155 / 156 | 0.638 / 0.644 | 95.1 % / 95.7 % | 15 / 18 |

- #4: the larger prefill budget costs activation memory on the A6000: Gemma's KV 48,200 → 20,252 tokens, still
  100 % full. No gain. **Rejected.**
- #2: Qwen's KV 632,149 → 1,114,112 tokens; no speed change (Qwen is not the bottleneck), reading and marks
  unchanged. TA items a little higher (15 / 18 vs 6 / 13) — TA items vary between runs (6-19 across set-ups),
  to watch. **Useful only where Qwen is short of memory** (e.g. #8, where it shares the PRO 6000).

Next (queued 21:10): #3 Qwen images capped at 1.4 and 1.0 MP (pages are 1414 x 2000 = 2.8 MP), #5
fixed-first grading prompt (data-science only), #8 second Gemma (`opt-gemma2`, `opt-gemma2-fp8`). Note: #8
profiles do not use the #4 flag on the A6000 Gemma (it does not start with 8,192).

### #3 and #5 (job 48725, 21:10-23:02)

| Set-up | one-page 16 / 32 (sheets/h) | data-science 16 / 32 (sheets/h) | DS written MAE | DS same as baseline | DS TA items |
|---|---|---|---|---|---|
| baseline | 1,950 / 2,249 | 156 / 157 | 0.650 / 0.650 | 96.1 % (noise floor) | 6 / 13 |
| #1 `opt-lean` (reference) | 2,111 / 2,226 | 155 / 158 | 0.647 / 0.644 | 96.2 % / 95.6 % | 6 / 17 |
| #3 Qwen images 1.4 MP | 2,112 / 2,531 | 156 / 156 | 0.650 / 0.648 | 86.3 % / 85.8 % | 15 / 11 |
| #3 Qwen images 1.0 MP | 2,091 / 2,323 | 156 / 157 | 0.656 / 0.655 | 83.4 % / 84.2 % | 23 / 22 |
| #5 fixed part first | - | **165 / 172** | 0.671 / 0.673 | 93.5 % / 93.7 % | 14 / 21 |

- #3: Qwen's tokens drop about 20 % (1.4 MP) and 30 % (1.0 MP), but Gemma stays the bottleneck, so the
  data-science speed does not move. Qwen reads differently from smaller pages: only 84-86 % of answers stay the
  same (noise floor 96 %) and TA items rise (up to 23). MCQ / numerical accuracy unchanged. **Rejected.**
- #5: the only client-side change that speeds up data science (+6 % at 16, +9 % at 32: the rubric and rules
  are cached between students). But Gemma grades a little differently when the rubric comes before the
  answers: MAE 0.650 → 0.671 / 0.673, agreement 93.5 % (below the 96 % noise floor). Quality drops, so it
  is **not kept** (user rule: faster only without lowering quality). A version that keeps the standard order
  but moves only the rules forward could be tried later.

### #8 second Gemma copy — first try failed (23:03), fixed and restarted (23:40)

The second copy (38 GB) was skipped at start: `serve.py` fills 92 % of each card's real size
(PRO 6000 = 97,887 MiB = 95.6 GB → 87.9 GB usable), and 42 + 8 + 38 = 88 GB was 0.1 GB too much. The profile
test used the nominal 96 GB, so it did not catch this; it now uses the sizes `nvidia-smi` reports. New sizes:
Qwen 38 GB, GLM-OCR 8 GB, second Gemma 41 GB (Qwen used at most 85 % of 632k tokens at 76 GB; at 38 GB it may
queue more, which `opt-gemma2-fp8` offsets with FP8 KV).

Second try (23:37): all four servers placed, but Gemma#2 failed at 23:42: at 41 GB only 6.25 GiB is left for
KV after the weights, and a 16,384-token request needs 13.76 GiB (Gemma's KV is large: ~0.86 MB per token).
`opt-gemma2` (BF16 KV) therefore cannot run usefully next to Qwen. `opt-gemma2-fp8` changed to request limit
8,192 with FP8 KV (Blackwell supports it): about 15k tokens of room, vs 48,200 for the A6000 copy.
