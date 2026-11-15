# Teacher calibration from 5 marked sheets (Mendeley)

Generated 2026-11-15 12:18 by `python eval/mendeley_calibrate.py --k 5 --grades sweep`. Grader Gemma + prompt v2; answers not located are left out (they go to a TA). 523 answers on 50 sheets; 20 random choices of the 5 calibration sheets, tested on the remaining sheets; mean (min–max over splits).

| method | MAE | exact | within 0.5 | QWK | bias |
|---|---|---|---|---|---|
| none | 0.602 (0.58–0.62) | 0.398 (0.39–0.41) | 0.559 (0.54–0.58) | 0.473 (0.45–0.49) | -0.500 (-0.51–-0.48) |
| global | 0.430 (0.42–0.44) | 0.371 (0.36–0.39) | 0.829 (0.82–0.84) | 0.588 (0.56–0.60) | -0.136 (-0.15–-0.12) |
| per-question | 0.415 (0.35–0.47) | 0.435 (0.36–0.54) | 0.793 (0.72–0.85) | 0.584 (0.54–0.62) | -0.111 (-0.26–0.06) |
| mapping | 0.406 (0.34–0.49) | 0.440 (0.28–0.61) | 0.793 (0.69–0.90) | 0.514 (0.25–0.60) | 0.028 (-0.15–0.20) |
