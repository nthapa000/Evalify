# Teacher calibration from 10 marked sheets (Mendeley)

Generated 2026-11-15 12:19 by `python eval/mendeley_calibrate.py --k 10 --grades sweep`. Grader Gemma + prompt v2; answers not located are left out (they go to a TA). 523 answers on 50 sheets; 20 random choices of the 10 calibration sheets, tested on the remaining sheets; mean (min–max over splits).

| method | MAE | exact | within 0.5 | QWK | bias |
|---|---|---|---|---|---|
| none | 0.602 (0.58–0.62) | 0.397 (0.37–0.41) | 0.557 (0.53–0.58) | 0.473 (0.43–0.50) | -0.502 (-0.53–-0.48) |
| global | 0.429 (0.42–0.44) | 0.370 (0.34–0.39) | 0.830 (0.81–0.85) | 0.589 (0.55–0.62) | -0.138 (-0.16–-0.11) |
| per-question | 0.417 (0.36–0.49) | 0.428 (0.36–0.53) | 0.795 (0.75–0.83) | 0.582 (0.54–0.62) | -0.114 (-0.26–0.02) |
| mapping | 0.401 (0.34–0.48) | 0.440 (0.29–0.62) | 0.787 (0.71–0.88) | 0.509 (0.47–0.57) | 0.025 (-0.19–0.19) |
