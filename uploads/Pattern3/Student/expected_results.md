# Expected results: Data Science exam

Each sub-folder is one student. Log in with that roll number (password in `demo.env`), open the paper,
choose **Handwritten** and upload **all pages** of the folder in order (page1, page2, ...).

Expected marks are the **real teacher's marks** from the dataset. Written answers are judged, so expect
the AI to be close but not identical (our measured average difference is a few marks per sheet).

**MCQ by the key** is what the answer key gives for the answers we labelled on the sheet: the app should
match it. The dataset's teacher sometimes marked MCQs differently from the key (found in run 7).
Without calibration the AI marks written answers about 0.5 per answer stricter than this teacher.

| Student login | Sheet | Pages | MCQ by the key / 20 | Teacher: MCQ / 20 | Teacher: written / 30 | Teacher: total / 50 |
|---|---|---|---|---|---|---|
| DS2025001 | Student_19 | 4 | 10 | 11 | 3 | 14 |
| DS2025002 | Student_2 | 4 | 12 | 10 | 13 | 23 |
| DS2025003 | Student_9 | 4 | 8 | 9 | 19 | 28 |
| DS2025004 | Student_1 | 4 | 11 | 12 | 21 | 33 |
| DS2025005 | Student_29 | 4 | 14 | 16 | 24 | 40 |
| DS2025006 | Student_13 | 6 | 18 | 19 | 24 | 43 |
