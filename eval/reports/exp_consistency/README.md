# Grader consistency (Mendeley, experiment)

Generated 2026-11-15 14:23 by `python eval/exp_consistency.py score`. Grader Gemma + prompt v2, temperature 0; marks 0–2 in steps of 0.5. *≥1 apart* = the two marks differ by a mark or more.

| comparison | n | exact | within 0.5 | ≥ 1 apart | MAE | QWK |
|---|---|---|---|---|---|---|
| (a) same input graded twice | 555 | 99% | 100% | 0% | 0.005 | 0.997 |
| (b) transcripts A↔B swapped | 555 | 96% | 100% | 1% | 0.024 | 0.988 |
| (c) two reading methods (pagetext vs seg2) | 548 | 91% | 98% | 2% | 0.057 | 0.966 |
| (d) two graders, same transcripts (Gemma vs Qwen) | 522 | 66% | 94% | 6% | 0.2 | 0.883 |
| (e) our grader vs the teacher | 555 | 37% | 55% | 45% | 0.615 | 0.47 |
