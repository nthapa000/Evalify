# Numerical grader check (on the labelled values)

Each grader judges the value the student actually wrote (from the label CSV), so reading errors play no part. Rule: number within the key tolerance (±0.001), unit ignored, no unit conversion. **Please verify the ✔/✘ column for `code`.**

| sheet | Q | key | student wrote | code | Qwen | Gemma |
|---|---|---|---|---|---|---|
| 2A_s01 | Q3 | 50 km/h | 50km/hr | ✔ | ✔ | ✔ |
| 2A_s01 | Q4 | 2500 m | 2500m | ✔ | ✔ | ✔ |
| 2A_s01 | Q5 | 19.6 m/s | 19 | ✘ | ✘ | ✘ |
| 2A_s02 | Q3 | 50 km/h | 50km/hr | ✔ | ✔ | ✔ |
| 2A_s02 | Q4 | 2500 m | 2500.5m | ✘ | ✘ | ✘ |
| 2A_s02 | Q5 | 19.6 m/s | 19.61m/s | ✘ | ✔ | ✘ |
| 2A_s03 | Q3 | 50 km/h | 50.01km/hr | ✘ | ✘ | ✘ |
| 2A_s03 | Q4 | 2500 m | ∅ | ✘ | ✘ | ✘ |
| 2A_s03 | Q5 | 19.6 m/s | 19m/s | ✘ | ✘ | ✘ |
| 2A_s04 | Q3 | 50 km/h | ∅ | ✘ | ✘ | ✘ |
| 2A_s04 | Q4 | 2500 m | 2500m | ✔ | ✔ | ✔ |
| 2A_s04 | Q5 | 19.6 m/s | ∅ | ✘ | ✘ | ✘ |
| 2A_s05 | Q3 | 50 km/h | ∅ | ✘ | ✘ | ✘ |
| 2A_s05 | Q4 | 2500 m | ∅ | ✘ | ✘ | ✘ |
| 2A_s05 | Q5 | 19.6 m/s | ∅ | ✘ | ✘ | ✘ |
| 2B_s01 | Q3 | 4 g/cm3 | 4g/cm3 | ✔ | ✔ | ✔ |
| 2B_s01 | Q4 | -7 °C | -7C | ✔ | ✔ | ✔ |
| 2B_s01 | Q5 | 0.625 | 0.625 | ✔ | ✔ | ✔ |
| 2B_s02 | Q3 | 4 g/cm3 | 4.01 | ✘ | ✘ | ✘ |
| 2B_s02 | Q4 | -7 °C | ∅ | ✘ | ✘ | ✘ |
| 2B_s02 | Q5 | 0.625 | 0.626 | ✔ | ✔ | ✔ |
| 2B_s03 | Q3 | 4 g/cm3 | -4g/cm3 | ✘ | ✘ | ✘ |
| 2B_s03 | Q4 | -7 °C | +7C | ✘ | ✘ | ✘ |
| 2B_s03 | Q5 | 0.625 | 0.6 | ✘ | ✘ | ✘ |
| 2B_s04 | Q3 | 4 g/cm3 | ∅ | ✘ | ✘ | ✘ |
| 2B_s04 | Q4 | -7 °C | ∅ | ✘ | ✘ | ✘ |
| 2B_s04 | Q5 | 0.625 | D | ✘ | ✘ | ✘ |
| 2B_s05 | Q3 | 4 g/cm3 | ∅ | ✘ | ✘ | ✘ |
| 2B_s05 | Q4 | -7 °C | ∅ | ✘ | ✘ | ✘ |
| 2B_s05 | Q5 | 0.625 | ∅ | ✘ | ✘ | ✘ |
| 2C_s01 | Q3 | 0.5 A | 0.5A | ✔ | ✔ | ✔ |
| 2C_s01 | Q4 | 440 W | 440W | ✔ | ✔ | ✔ |
| 2C_s01 | Q5 | 9 J | 9J | ✔ | ✔ | ✔ |
| 2C_s02 | Q3 | 0.5 A | 0.505A | ✘ | ✔ | ✘ |
| 2C_s02 | Q4 | 440 W | ∅ | ✘ | ✘ | ✘ |
| 2C_s02 | Q5 | 9 J | 8J | ✘ | ✘ | ✘ |
| 2C_s03 | Q3 | 0.5 A | 0.5A | ✔ | ✔ | ✔ |
| 2C_s03 | Q4 | 440 W | 440W | ✔ | ✔ | ✔ |
| 2C_s03 | Q5 | 9 J | 99J | ✘ | ✘ | ✘ |
| 2C_s04 | Q3 | 0.5 A | ∅ | ✘ | ✘ | ✘ |
| 2C_s04 | Q4 | 440 W | ∅ | ✘ | ✘ | ✘ |
| 2C_s04 | Q5 | 9 J | ∅ | ✘ | ✘ | ✘ |
| 2C_s05 | Q3 | 0.5 A | 0.5A | ✔ | ✔ | ✔ |
| 2C_s05 | Q4 | 440 W | 440W | ✔ | ✔ | ✔ |
| 2C_s05 | Q5 | 9 J | 9J | ✔ | ✔ | ✔ |
