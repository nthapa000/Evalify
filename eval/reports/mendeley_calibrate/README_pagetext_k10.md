# Teacher calibration from 10 marked sheets (Mendeley)

Generated 2026-11-15 13:46 by `python eval/mendeley_calibrate.py --k 10 --grades pagetext`. Grader Gemma + prompt v2; answers not located are left out (they go to a TA). 555 answers on 50 sheets; 30 random choices of the 10 calibration sheets, tested on the remaining sheets; mean (min–max over splits).

| method | MAE | exact | within 0.5 | QWK | bias |
|---|---|---|---|---|---|
| none | 0.617 (0.60–0.64) | 0.367 (0.35–0.38) | 0.549 (0.53–0.57) | 0.470 (0.43–0.49) | -0.516 (-0.54–-0.49) |
| global | 0.425 (0.41–0.44) | 0.370 (0.35–0.40) | 0.836 (0.82–0.85) | 0.595 (0.56–0.62) | -0.139 (-0.16–-0.12) |
| per-question | 0.408 (0.36–0.48) | 0.438 (0.38–0.51) | 0.799 (0.73–0.84) | 0.586 (0.53–0.62) | -0.102 (-0.24–0.04) |
| mapping | 0.389 (0.33–0.46) | 0.449 (0.24–0.64) | 0.802 (0.67–0.91) | 0.527 (0.48–0.60) | 0.041 (-0.14–0.19) |
