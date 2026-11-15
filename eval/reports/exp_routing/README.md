# TA-flagging rules for written answers (Mendeley, experiment)

Generated 2026-11-15 17:37 by `python eval/exp_routing.py score`. 437 answers on the 40 sheets not used for calibration. *Wrong* = ≥ 1 mark away from the teacher (out of 2). *Calibrated* = after the per-question shift learned on 10 sheets. A good rule sends few answers to a TA and catches many wrong ones.

| rule | to TA | wrong caught (raw) | wrong left auto (raw) | wrong caught (calibrated) | wrong left auto (calibrated) | wrong rate in TA vs auto (cal.) |
|---|---|---|---|---|---|---|
| nothing (all auto) | 0 (0%) | 0 | 195 | 0 | 76 | — |
| confidence < 0.5 | 0 (0%) | 0 | 195 | 0 | 76 | — |
| confidence < 0.6 | 0 (0%) | 0 | 195 | 0 | 76 | — |
| confidence < 0.7 | 0 (0%) | 0 | 195 | 0 | 76 | — |
| confidence < 0.8 | 6 (1%) | 2 | 193 | 0 | 76 | 0% vs 18% |
| confidence < 0.9 | 63 (14%) | 16 | 179 | 10 | 66 | 16% vs 18% |
| evidence not found | 0 (0%) | 0 | 195 | 0 | 76 | — |
| transcript problem | 2 (0%) | 1 | 194 | 0 | 76 | 0% vs 17% |
| transcripts differ (< 0.6) | 18 (4%) | 9 | 186 | 1 | 75 | 6% vs 18% |
| current defaults (conf < 0.7 + evidence + transcript problem) | 2 (0%) | 1 | 194 | 0 | 76 | 0% vs 17% |
| conf < 0.6 + evidence + transcript problem | 2 (0%) | 1 | 194 | 0 | 76 | 0% vs 17% |
| conf < 0.8 + evidence + transcript problem | 8 (2%) | 3 | 192 | 0 | 76 | 0% vs 18% |
