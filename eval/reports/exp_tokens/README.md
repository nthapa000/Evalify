# Token use of the v2 pipeline

Real labelled sheets run through `orchestrator.run` with the live models; tokens are the counts the
vLLM servers return (`usage`), summed over every request, retries included. Input tokens include the
page images.

## Per answer sheet

| Paper type | Sheets | Pages read / sheet | Questions | Model calls / sheet | Input tokens / sheet | Output tokens / sheet | **Total / sheet** | Min – max | Time / sheet |
|---|---|---|---|---|---|---|---|---|---|
| A  MCQ only (handwritten) | 15 | 1.0 | 10 mcq | 2.1 | 4,097 | 540 | **4,637** | 3,876 – 8,126 | 15 s |
| A  MCQ only (OMR sheet) | 15 | 0.0 | 20 mcq | 0.0 | 0 | 0 | **0** | 0 – 0 | 1 s |
| B  MCQ + numerical | 15 | 0.9 | 2 mcq + 3 numerical | 2.2 | 4,446 | 289 | **4,735** | 3,206 – 7,980 | 9 s |
| C  MCQ + subjective (Data Science exam) | 12 | 3.5 | 20 mcq + 15 subjective | 26.8 | 34,899 | 6,553 | **41,451** | 32,881 – 63,123 | 100 s |

## Per pipeline step (average per sheet)

**A  MCQ only (handwritten)**

| Step | Model | Calls / sheet | Input / sheet | Output / sheet | Total / sheet |
|---|---|---|---|---|---|
| Read MCQ / numerical answers (readers A, B, C) | gemma4-31b-fp8 | 1.0 | 611 | 223 | 835 |
| Read MCQ / numerical answers (readers A, B, C) | glm-ocr | 0.1 | 252 | 2 | 254 |
| Read MCQ / numerical answers (readers A, B, C) | qwen38-27b-fp8 | 1.0 | 3,234 | 314 | 3,548 |

**B  MCQ + numerical**

| Step | Model | Calls / sheet | Input / sheet | Output / sheet | Total / sheet |
|---|---|---|---|---|---|
| Read MCQ / numerical answers (readers A, B, C) | gemma4-31b-fp8 | 1.0 | 544 | 115 | 659 |
| Read MCQ / numerical answers (readers A, B, C) | glm-ocr | 0.2 | 746 | 7 | 753 |
| Read MCQ / numerical answers (readers A, B, C) | qwen38-27b-fp8 | 1.0 | 3,156 | 167 | 3,323 |

**C  MCQ + subjective (Data Science exam)**

| Step | Model | Calls / sheet | Input / sheet | Output / sheet | Total / sheet |
|---|---|---|---|---|---|
| Grade written answers against the rubric | gemma4-31b-fp8 | 12.3 | 6,154 | 1,617 | 7,771 |
| Read MCQ / numerical answers (readers A, B, C) | gemma4-31b-fp8 | 3.5 | 2,636 | 1,400 | 4,036 |
| Read MCQ / numerical answers (readers A, B, C) | glm-ocr | 0.5 | 1,781 | 60 | 1,842 |
| Read MCQ / numerical answers (readers A, B, C) | qwen38-27b-fp8 | 3.5 | 11,088 | 1,396 | 12,484 |
| Transcribe written answers (2 transcribers) | gemma4-31b-fp8 | 3.5 | 2,247 | 615 | 2,862 |
| Transcribe written answers (2 transcribers) | qwen38-27b-fp8 | 3.5 | 10,994 | 1,464 | 12,457 |

## Per question

Page reading reads all MCQ / numerical answers of a page in one request, so its cost is shared by
those questions. Written answers are transcribed page by page and then graded one by one.

| Question type | Measured on | Tokens per question |
|---|---|---|
| MCQ | A  MCQ only (handwritten) | 464 |
| MCQ (OMR) | A  MCQ only (OMR sheet) | 0 |
| MCQ / numerical | B  MCQ + numerical | 947 |
| MCQ | C  MCQ + subjective (Data Science exam) | 918 |
| Written answer: transcription | C  MCQ + subjective (Data Science exam) | 1,021 |
| Written answer: grading | C  MCQ + subjective (Data Science exam) | 518 |
| Written answer: one grading call (answered only) | C  MCQ + subjective (Data Science exam) | 630 |

## What one page image costs

One Data Science page after the quality gate (1414 x 2000 px):

| Model | Input tokens for the image |
|---|---|
| gemma4-31b-fp8 | 268 |
| qwen38-27b-fp8 | 2,730 |
| glm-ocr | 3,552 |
