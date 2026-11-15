# Upload kit for testing every flow

Built by `python eval/make_upload_kit.py` from the labelled sets used in our evaluations.
Download this folder to the computer you test from (VS Code: right-click > Download).

| Pattern | Paper | Teacher login | Students |
|---|---|---|---|
| `Pattern1/` | MCQ only: OMR (20 Q, 3 sheet layouts) and handwritten (10 Q) | physics.teacher@evalify.local | PH2025001 ... |
| `Pattern2/` | MCQ + numerical: papers 2A, 2B, 2C (2 MCQ + 3 numerical) | physics.teacher@evalify.local | PH2025001 ... PH2025005 |
| `Pattern3/` | MCQ + subjective: Data Science exam (20 MCQ + 15 written) | ds.teacher@evalify.local | DS2025001 ... DS2025006 |

Passwords: `demo.env` (demo accounts only).

For each pattern:
1. **Teacher**: follow `PatternN/Teacher/README.md` to create the paper (files to upload are next to it).
2. **Students**: each folder under `PatternN/Student/...` is one student login; upload the page(s) in it.
   `expected_results.md` next to them says what marks to expect.
3. **TA** (flagged answers): `ta.physics@evalify.local` for Patterns 1-2, `ta.ds1@evalify.local` for Pattern 3.
4. **Teacher**: results page > check > **Release results**; students then see marks and can ask for one re-evaluation.

To repeat a test with clean results, create the paper again and upload the sheets to the new paper.
