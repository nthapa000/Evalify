# Teacher calibration from 20 marked sheets (Mendeley)

Generated 2026-11-15 13:46 by `python eval/mendeley_calibrate.py --k 20 --grades pagetext`. Grader Gemma + prompt v2; answers not located are left out (they go to a TA). 555 answers on 50 sheets; 30 random choices of the 20 calibration sheets, tested on the remaining sheets; mean (min–max over splits).

| method | MAE | exact | within 0.5 | QWK | bias |
|---|---|---|---|---|---|
| none | 0.616 (0.59–0.65) | 0.368 (0.33–0.41) | 0.546 (0.51–0.58) | 0.472 (0.42–0.50) | -0.514 (-0.55–-0.47) |
| global | 0.426 (0.41–0.45) | 0.366 (0.33–0.41) | 0.839 (0.81–0.86) | 0.597 (0.54–0.63) | -0.137 (-0.17–-0.11) |
| per-question | 0.393 (0.37–0.43) | 0.439 (0.39–0.50) | 0.821 (0.78–0.85) | 0.602 (0.55–0.64) | -0.074 (-0.13–-0.02) |
| mapping | 0.394 (0.36–0.46) | 0.425 (0.24–0.48) | 0.813 (0.78–0.91) | 0.522 (0.48–0.58) | 0.047 (-0.17–0.12) |
