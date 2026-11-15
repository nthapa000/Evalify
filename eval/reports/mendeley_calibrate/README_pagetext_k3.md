# Teacher calibration from 3 marked sheets (Mendeley)

Generated 2026-11-15 13:46 by `python eval/mendeley_calibrate.py --k 3 --grades pagetext`. Grader Gemma + prompt v2; answers not located are left out (they go to a TA). 555 answers on 50 sheets; 30 random choices of the 3 calibration sheets, tested on the remaining sheets; mean (min–max over splits).

| method | MAE | exact | within 0.5 | QWK | bias |
|---|---|---|---|---|---|
| none | 0.617 (0.61–0.62) | 0.368 (0.36–0.38) | 0.550 (0.54–0.56) | 0.468 (0.45–0.48) | -0.515 (-0.53–-0.50) |
| global | 0.425 (0.42–0.43) | 0.372 (0.36–0.38) | 0.835 (0.83–0.84) | 0.593 (0.57–0.61) | -0.140 (-0.15–-0.13) |
| per-question | 0.417 (0.35–0.49) | 0.423 (0.35–0.53) | 0.801 (0.74–0.83) | 0.580 (0.53–0.62) | -0.117 (-0.29–0.06) |
| mapping | 0.404 (0.34–0.53) | 0.453 (0.24–0.66) | 0.778 (0.58–0.90) | 0.524 (0.38–0.61) | -0.005 (-0.33–0.25) |
