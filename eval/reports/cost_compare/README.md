# Cost per 1,000 answer sheets: open-model API vs own GPUs

Tokens: measured per sheet (`exp_tokens`). Throughput: measured on our node (`exp_throughput`), best
concurrency. Prices: web lookups 16 Nov 2026, see the sources list; they change often (edit the constants
in `eval/cost_compare.py`). OMR sheets are read by code: 0 tokens, about 1 s of CPU per sheet.

| Paper type | API, low | API, typical | Our GPUs: sheets / hour | Rented GPUs, low | Rented GPUs, typical |
|---|---|---|---|---|---|
| Handwritten MCQ (10 Q, 1 page) | $0.74 | $1.26 | 2404 | $0.85 | $1.14 |
| MCQ + numerical (5 Q, 1 page) | $0.49 | $0.93 | 2404 | $0.85 | $1.14 |
| Data Science exam (20 MCQ + 15 written, ~3.5 pages) | $7.46 | $11.74 | 150 | $13.62 | $18.36 |

Rented GPUs = the node's hourly price / sheets per hour, assuming it is kept busy. An idle rented node
still costs $2.04-$2.75 per hour.

## Prices used ($ per 1M tokens, input / output)

| Model | Low | Typical |
|---|---|---|
| gemma4-31b-fp8 | 0.09 / 0.34 | 0.14 / 0.4 |
| qwen38-27b-fp8 | 0.04 / 1.5 | 0.15 / 1.88 |
| glm-ocr | 0.03 / 0.03 | 0.03 / 0.03 |

GPU node per hour (A6000 + RTX PRO 6000): low $2.04, typical $2.75.

## Sources (16 Nov 2026)

- https://computeprices.com/models/gemma-4-31b-it
- https://models.litellm.ai/models/gemma-4-31b
- https://openrouter.ai/qwen/qwen3.8-27b
- https://pricepertoken.com/pricing-page/model/qwen-qwen3.8-27b
- https://docs.z.ai/guides/overview/pricing
- https://www.thundercompute.com/blog/nvidia-rtx-a6000-pricing
- https://flopper.io/pricing/nvidia-rtx-pro-6000-blackwell
- https://gpu.ai/gpus/rtx-pro-6000
