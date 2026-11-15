# EDU-CIRCUIT-HW — final numerical answers in real worked solutions

Generated 2026-11-15 08:54 by `python eval/edu_circuit.py score`. 213 solutions (Georgia Tech ECE 2040, 2025), 702 final values; 436 of them are correct under the teacher's rule.

- Gold = the student's final value from the **expert transcription**, extracted by Qwen and Gemma (kept only where both agree); expected values from the rubric notes (both must agree).
- *silent_errors* = auto-accepted values whose marks (correct / wrong under the teacher's rule) differ from the gold; *read_exact_auto* = accepted value equals the gold value.
- Readers: `qwen` / `gemma` read the image; `X>qwen` = OCR model X transcribes the image, Qwen extracts the final values from that text. *sec_per_solution* = model time summed over calls.
- Dataset licence not stated in the download → internal evaluation only.

## Single readers

| arch | readers | items | silent_errors | auto_rate | ta_items | read_exact_auto | sec_per_solution |
|---|---|---|---|---|---|---|---|
| single | chandra>qwen | 702 | 81 | 1.0 | 0 | 0.856 | 47.4 |
| single | qwen | 702 | 84 | 1.0 | 0 | 0.816 | 17.5 |
| single | gemma | 702 | 98 | 1.0 | 0 | 0.826 | 7.2 |
| single | glm>qwen | 702 | 113 | 1.0 | 0 | 0.778 | 20.1 |
| single | paddle>qwen | 702 | 198 | 1.0 | 0 | 0.64 | 21.5 |

## Best per architecture

| arch | readers | items | silent_errors | auto_rate | ta_items | read_exact_auto | sec_per_solution |
|---|---|---|---|---|---|---|---|
| pair | chandra>qwen + gemma | 702 | 30 | 0.795 | 144 | 0.943 | 54.7 |
| pair+tiebreak | chandra>qwen + gemma + qwen | 702 | 30 | 0.795 | 144 | 0.943 | 72.1 |
| pair+majority | chandra>qwen + gemma + qwen | 702 | 63 | 0.966 | 24 | 0.892 | 72.1 |
| single | chandra>qwen | 702 | 81 | 1.0 | 0 | 0.856 | 47.4 |

## Top 15

| arch | readers | items | silent_errors | auto_rate | ta_items | read_exact_auto | sec_per_solution |
|---|---|---|---|---|---|---|---|
| pair | chandra>qwen + gemma | 702 | 30 | 0.795 | 144 | 0.943 | 54.7 |
| pair+tiebreak | chandra>qwen + gemma + qwen | 702 | 30 | 0.795 | 144 | 0.943 | 72.1 |
| pair+tiebreak | chandra>qwen + gemma + glm>qwen | 702 | 30 | 0.795 | 144 | 0.943 | 74.8 |
| pair+tiebreak | chandra>qwen + gemma + paddle>qwen | 702 | 30 | 0.795 | 144 | 0.943 | 76.2 |
| pair | paddle>qwen + qwen | 702 | 30 | 0.613 | 272 | 0.921 | 39.0 |
| pair+tiebreak | paddle>qwen + qwen + gemma | 702 | 30 | 0.613 | 272 | 0.921 | 46.3 |
| pair+tiebreak | paddle>qwen + qwen + glm>qwen | 702 | 30 | 0.613 | 272 | 0.921 | 59.1 |
| pair+tiebreak | paddle>qwen + qwen + chandra>qwen | 702 | 30 | 0.613 | 272 | 0.921 | 86.4 |
| pair | chandra>qwen + paddle>qwen | 702 | 34 | 0.645 | 249 | 0.916 | 69.0 |
| pair+tiebreak | chandra>qwen + paddle>qwen + gemma | 702 | 34 | 0.645 | 249 | 0.916 | 76.2 |
| pair+tiebreak | chandra>qwen + paddle>qwen + qwen | 702 | 34 | 0.645 | 249 | 0.916 | 86.4 |
| pair+tiebreak | chandra>qwen + paddle>qwen + glm>qwen | 702 | 34 | 0.645 | 249 | 0.916 | 89.1 |
| pair | glm>qwen + qwen | 702 | 35 | 0.759 | 169 | 0.923 | 37.6 |
| pair+tiebreak | glm>qwen + qwen + gemma | 702 | 35 | 0.759 | 169 | 0.923 | 44.8 |
| pair+tiebreak | glm>qwen + qwen + paddle>qwen | 702 | 35 | 0.759 | 169 | 0.923 | 59.1 |
