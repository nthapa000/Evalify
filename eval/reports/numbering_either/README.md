# Written answers under either numbering: re-measurement (17 Nov 2026)

Change measured: each written question also accepts the other numbering (S1 <-> Q21), the transcribers are told both
labels, S-labels are no longer turned into Q-labels, and a sheet with no written answer at all is flagged for the TA.
Question: does telling the transcribers the extra labels change the marks on a paper that uses Q21-Q35 numbering?

Set-up: Data Science set (Mendeley, 48 sheets, 20 MCQ + 15 written, numbering Q21-Q35), 32 sheets in flight, GPU job
48725 with the production layout (opt-gemma2-fp8 = tier1, two Gemma copies). Compared with the run of the same layout
before the change (`opt-gemma2-fp8`, c32). Command:
`python eval/exp_inference.py run --config numbering-either --workloads data-science --levels 32`, then `score`.

| Run | Sheets/h | MCQ correct | Written MAE (0-2 per answer) | TA items | Same as baseline | Errors |
|---|---|---|---|---|---|---|
| Before (opt-gemma2-fp8, c32) | 217 | 937/960 (97.6 %) | 0.639 | 15 | 95.1 % | 0 |
| After (numbering-either, c32) | 218 | 938/960 (97.7 %) | 0.648 | 20 | 93.4 % | 0 |
| Noise floor (baseline vs itself) | | | | | 96.1 % | |

Reading: marks, MCQ accuracy and speed unchanged within run-to-run noise (MAE 0.639 vs 0.648, the original baseline
was 0.650). Of the 5 extra TA items 4 are MCQ questions (Q13, Q17, Q18, Q19), whose reading the change does not touch,
so the difference is model run-to-run variation; on written answers one flag went (S5) and two came (S2, S13).
The safety net did not fire (every sheet has written answers). Decision: keep the change.

Run file: `eval/reports/exp_inference/runs/numbering-either__data-science__c32.json`.
