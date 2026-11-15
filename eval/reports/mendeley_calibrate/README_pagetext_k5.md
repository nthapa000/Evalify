# Teacher calibration from 5 marked sheets (Mendeley)

Generated 2026-11-15 13:25 by `python eval/mendeley_calibrate.py --k 5 --grades pagetext`. Grader Gemma + prompt v2; answers not located are left out (they go to a TA). 555 answers on 50 sheets; 20 random choices of the 5 calibration sheets, tested on the remaining sheets; mean (min–max over splits).

| method | MAE | exact | within 0.5 | QWK | bias |
|---|---|---|---|---|---|
| none | 0.617 (0.60–0.63) | 0.368 (0.36–0.38) | 0.550 (0.54–0.56) | 0.468 (0.45–0.48) | -0.515 (-0.53–-0.50) |
| global | 0.425 (0.41–0.44) | 0.373 (0.36–0.39) | 0.834 (0.83–0.84) | 0.592 (0.57–0.61) | -0.140 (-0.15–-0.12) |
| per-question | 0.409 (0.35–0.47) | 0.436 (0.37–0.52) | 0.800 (0.75–0.83) | 0.588 (0.51–0.63) | -0.116 (-0.24–0.04) |
| mapping | 0.406 (0.34–0.46) | 0.426 (0.26–0.66) | 0.799 (0.66–0.90) | 0.529 (0.38–0.61) | -0.010 (-0.14–0.14) |
