# Cost and time to mark a class: API vs the department's own servers

All numbers come from measurements on real answer sheets (`exp_tokens`, `exp_throughput`) and API prices
looked up on 16 Nov 2026 (`cost_compare.py`). ₹ at an assumed $1 = ₹88.

**Own servers:** the department already has the GPU servers, so there is **no purchase and no extra
maintenance cost**. The rental value and electricity below are shown only for completeness; in our use
they are not an extra charge.

## 1. 700 written exams (type C), 10 pages per answer sheet

Assumed per sheet: 10 pages, MCQs + 15 answered written questions (like the Data Science
exam, with longer answers). Estimated **109,092 tokens per sheet** (76.4 M for the class). The estimate is built from per-page and
per-answer costs; on the measured 4- and 6-page sheets it comes out 5-8 % high, so it is on the safe side.

| | Open-model API | Own servers |
|---|---|---|
| Money | **$14-22** (₹1,220-₹1,943) | **₹0 extra** |
| Time for all 700 sheets | about 1-3 h (limited by how many requests the provider accepts at once) | **about 12 h** (one overnight run on 2 GPUs) |
| Equivalent rental value of the GPU time | - | $25-34 (₹2,243-₹3,023) (not paid) |
| Electricity | - | 15 kWh, about ₹120-150 (already part of running the servers) |
| Student data | answer sheets sent to an outside company | stays on the college servers |

Tokens per sheet by model (what an API bill is computed from):

| Model | Input | Output |
|---|---|---|
| gemma4-31b-fp8 | 24,846 | 7,725 |
| glm-ocr | 5,089 | 173 |
| qwen38-27b-fp8 | 63,090 | 8,169 |

## 2. 700 handwritten quizzes (1 page each)

| Quiz | Tokens per sheet | API for 700 sheets | Own servers: time | Own servers: money |
|---|---|---|---|---|
| MCQ (10 questions) | 4,637 | $0.52-0.88 (₹46-₹78) | about 17 min | ₹0 extra |
| MCQ + numerical (5 questions) | 4,735 | $0.34-0.65 (₹30-₹57) | about 17 min | ₹0 extra |
| OMR bubble sheet (any number of questions) | 0 (read by code) | $0 | about 12 min on a CPU | ₹0 |

Own-server time uses the measured 2,404 one-page sheets per hour (16 at once; the GPUs were
not yet at their limit, so this is a safe figure). Longer quizzes cost about 4,600 tokens and the same GPU
time per extra page.

## What running it ourselves needs (no extra cost)

- The GPU job must be running while sheets are marked (one Slurm job; `infra/cluster/app.sh` starts the app).
- Model files on the shared disk (already downloaded).
- TAs check the answers the system flags; this is the same with an API.

## Assumptions you can change

`eval/scenario_cost.py`: number of sheets (700), pages per sheet (10), written answers per
sheet (15), exchange rate, power use and tariff. API prices and GPU rental: `eval/cost_compare.py`.
