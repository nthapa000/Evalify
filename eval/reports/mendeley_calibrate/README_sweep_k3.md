# Teacher calibration from 3 marked sheets (Mendeley)

Generated 2026-11-15 12:18 by `python eval/mendeley_calibrate.py --k 3 --grades sweep`. Grader Gemma + prompt v2; answers not located are left out (they go to a TA). 523 answers on 50 sheets; 20 random choices of the 3 calibration sheets, tested on the remaining sheets; mean (min–max over splits).

| method | MAE | exact | within 0.5 | QWK | bias |
|---|---|---|---|---|---|
| none | 0.602 (0.59–0.61) | 0.397 (0.39–0.41) | 0.558 (0.55–0.57) | 0.473 (0.45–0.49) | -0.501 (-0.51–-0.48) |
| global | 0.439 (0.42–0.61) | 0.371 (0.35–0.39) | 0.816 (0.56–0.84) | 0.583 (0.48–0.61) | -0.155 (-0.51–-0.12) |
| per-question | 0.432 (0.36–0.51) | 0.412 (0.37–0.52) | 0.789 (0.69–0.83) | 0.573 (0.52–0.63) | -0.135 (-0.35–0.06) |
| mapping | 0.405 (0.35–0.56) | 0.470 (0.31–0.64) | 0.762 (0.63–0.88) | 0.520 (0.41–0.58) | 0.015 (-0.40–0.20) |
