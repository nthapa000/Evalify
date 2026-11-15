# Teacher calibration from 5 marked sheets (Mendeley)

Generated 2026-11-15 13:46 by `python eval/mendeley_calibrate.py --k 5 --grades pagetext`. Grader Gemma + prompt v2; answers not located are left out (they go to a TA). 555 answers on 50 sheets; 30 random choices of the 5 calibration sheets, tested on the remaining sheets; mean (min–max over splits).

| method | MAE | exact | within 0.5 | QWK | bias |
|---|---|---|---|---|---|
| none | 0.616 (0.60–0.63) | 0.368 (0.36–0.38) | 0.550 (0.54–0.57) | 0.469 (0.45–0.49) | -0.515 (-0.53–-0.50) |
| global | 0.425 (0.41–0.44) | 0.372 (0.36–0.39) | 0.835 (0.83–0.85) | 0.594 (0.57–0.61) | -0.139 (-0.15–-0.12) |
| per-question | 0.411 (0.35–0.48) | 0.432 (0.36–0.52) | 0.801 (0.75–0.83) | 0.587 (0.51–0.63) | -0.114 (-0.24–0.04) |
| mapping | 0.413 (0.34–0.49) | 0.421 (0.26–0.66) | 0.790 (0.66–0.90) | 0.500 (0.23–0.61) | 0.008 (-0.14–0.17) |
