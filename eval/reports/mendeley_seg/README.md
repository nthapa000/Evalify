# Type C — segmentation variants (Mendeley, 50 sheets)

Generated 2026-11-15 13:33 by `python eval/mendeley_seg.py score`. Grader Gemma + prompt v2 in every row; only how answers are found and transcribed changes.
- *baseline*: first run — Qwen draws one box per answer (old prompt), Qwen + GLM-OCR read the crops.
- *seg2*: new box prompt (check every label, skip crossed-out copy, ignore show-through, no mixed boxes).
- *pagetext*: no boxes — Qwen transcribes each whole page grouped by label (struck-out text left out); Gemma transcribes the whole page as plain text with [[Qnn]] markers, split in code (GLM-OCR drops margin labels).

| variant | answers found | MAE (not found = 0) | exact | bias | MAE (not found → TA) | bias | to TA |
|---|---|---|---|---|---|---|---|
| baseline | 523/564 | 0.665 | 0.374 | -0.571 | 0.601 | -0.5 | 41 |
| seg2 | 555/564 | 0.65 | 0.355 | -0.549 | 0.639 | -0.536 | 9 |
| pagetext | 555/564 | 0.63 | 0.365 | -0.531 | 0.615 | -0.514 | 9 |

MAE difference vs baseline (not found = 0), 95 % interval over sheets:

| variant | difference | 95 % interval |
|---|---|---|
| seg2 | -0.015 | [-0.050, +0.015] |
| pagetext | -0.035 | [-0.073, +0.001] |

Model seconds per paper (reading + grader):

| variant | reading | grader | wall (6 sheets in parallel) |
|---|---|---|---|
| seg2 | 80 | 242 | 85 |
| pagetext | 187 | 140 | 191 |
