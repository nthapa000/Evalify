# Teacher calibration from 5 marked sheets (Mendeley)

Generated 2026-11-15 13:33 by `python eval/mendeley_calibrate.py --k 5 --grades seg2`. Grader Gemma + prompt v2; answers not located are left out (they go to a TA). 555 answers on 50 sheets; 20 random choices of the 5 calibration sheets, tested on the remaining sheets; mean (min–max over splits).

| method | MAE | exact | within 0.5 | QWK | bias |
|---|---|---|---|---|---|
| none | 0.640 (0.63–0.65) | 0.356 (0.35–0.37) | 0.539 (0.53–0.55) | 0.444 (0.42–0.46) | -0.536 (-0.55–-0.52) |
| global | 0.439 (0.43–0.45) | 0.367 (0.35–0.38) | 0.819 (0.81–0.83) | 0.569 (0.55–0.58) | -0.160 (-0.17–-0.15) |
| per-question | 0.417 (0.37–0.48) | 0.437 (0.39–0.51) | 0.788 (0.74–0.82) | 0.566 (0.48–0.59) | -0.120 (-0.26–0.01) |
| mapping | 0.410 (0.34–0.47) | 0.435 (0.25–0.65) | 0.780 (0.59–0.90) | 0.505 (0.34–0.58) | 0.008 (-0.18–0.19) |
