# Teacher calibration from 15 marked sheets (Mendeley)

Generated 2026-11-15 13:46 by `python eval/mendeley_calibrate.py --k 15 --grades pagetext`. Grader Gemma + prompt v2; answers not located are left out (they go to a TA). 555 answers on 50 sheets; 30 random choices of the 15 calibration sheets, tested on the remaining sheets; mean (min–max over splits).

| method | MAE | exact | within 0.5 | QWK | bias |
|---|---|---|---|---|---|
| none | 0.619 (0.58–0.65) | 0.366 (0.34–0.39) | 0.546 (0.52–0.57) | 0.470 (0.43–0.51) | -0.521 (-0.55–-0.48) |
| global | 0.426 (0.41–0.44) | 0.368 (0.34–0.40) | 0.838 (0.82–0.86) | 0.596 (0.55–0.63) | -0.143 (-0.17–-0.10) |
| per-question | 0.412 (0.36–0.47) | 0.419 (0.35–0.50) | 0.809 (0.75–0.84) | 0.588 (0.54–0.63) | -0.115 (-0.23–0.03) |
| mapping | 0.396 (0.34–0.46) | 0.419 (0.24–0.61) | 0.815 (0.75–0.91) | 0.521 (0.47–0.58) | 0.033 (-0.16–0.20) |
