# Throughput of our own GPUs

Hardware: one node, 2 GPUs (RTX A6000 48 GB: Gemma 4 31B FP8; RTX PRO 6000 96 GB: Qwen 3.8 27B FP8 +
GLM-OCR + two OCR models not used by the pipeline), vLLM. Same real sheets as `exp_tokens`.
*Concurrency* = answer sheets being marked at the same time.

| Workload | Concurrency | Sheets | Wall time | **Sheets / hour** | Time per sheet | Tokens / s |
|---|---|---|---|---|---|---|
| Handwritten MCQ / MCQ+numerical (1 page) | 4 | 30 | 95 s | **1136** | 12 s | 1,556 |
| Handwritten MCQ / MCQ+numerical (1 page) | 8 | 30 | 60 s | **1784** | 15 s | 2,391 |
| Handwritten MCQ / MCQ+numerical (1 page) | 16 | 30 | 45 s | **2404** | 22 s | 3,219 |
| Data Science exam (20 MCQ + 15 written, 4-6 pages) | 4 | 24 | 730 s | **118** | 114 s | 1,376 |
| Data Science exam (20 MCQ + 15 written, 4-6 pages) | 8 | 24 | 596 s | **145** | 179 s | 1,660 |
| Data Science exam (20 MCQ + 15 written, 4-6 pages) | 16 | 24 | 577 s | **150** | 312 s | 1,698 |
