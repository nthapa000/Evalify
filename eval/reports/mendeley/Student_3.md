# Student_3 — reader comparison

Pages read: Student_3_p1.png, Student_3_p2.png, Student_3_p3.png  
Skipped as blank / show-through backs: Student_3_p4.png  
Answers located by the segmenter: 32/35  
Visual check by Claude: yes — transcripts for short answers below

Page images: `eval/data/mendeley/images/` · crops: `eval/reports/mendeley/crops/` (local, not in git).

> **Visual check (sheet):** MCQ letters all match the teacher CSV. Q30, Q33, Q35 not attempted. Page 4 is a blank back (only a printed margin line + show-through).

> Transcribed by Claude from the page images (eval/data/mendeley/images). Struck-out text is written ~~like this~~; [?] = could not read. Spelling is kept as written. Please verify.

## MCQ (gold = letter in the teacher's CSV)

| Q | crop | gold | Qwen3.8 | Chandra | PaddleOCR | GLM-OCR | note |
|---|---|---|---|---|---|---|---|
| Q1 | ![Q1](crops/Student_3/Q1.jpg) | **D** | ∅ | ∅ | D ✅ | ∅ | Circled-style 'D' — all four readers abstained; CSV D is right. |
| Q2 | ![Q2](crops/Student_3/Q2.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q3 | ![Q3](crops/Student_3/Q3.jpg) | **D** | ∅ | ∅ | ∅ | ∅ | Circled-style 'D' — all four readers abstained; CSV D is right. |
| Q4 | ![Q4](crops/Student_3/Q4.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q5 | ![Q5](crops/Student_3/Q5.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q6 | ![Q6](crops/Student_3/Q6.jpg) | **D** | ∅ | ∅ | ∅ | ∅ | Circled-style 'D' — all four readers abstained; CSV D is right. |
| Q7 | ![Q7](crops/Student_3/Q7.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q8 | ![Q8](crops/Student_3/Q8.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q9 | ![Q9](crops/Student_3/Q9.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q10 | ![Q10](crops/Student_3/Q10.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q11 | ![Q11](crops/Student_3/Q11.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q12 | ![Q12](crops/Student_3/Q12.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q13 | ![Q13](crops/Student_3/Q13.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q14 | ![Q14](crops/Student_3/Q14.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q15 | ![Q15](crops/Student_3/Q15.jpg) | **D** | ∅ | ∅ | ∅ | ∅ | Circled-style 'D' — all four readers abstained; CSV D is right. |
| Q16 | ![Q16](crops/Student_3/Q16.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q17 | ![Q17](crops/Student_3/Q17.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q18 | ![Q18](crops/Student_3/Q18.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q19 | ![Q19](crops/Student_3/Q19.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q20 | ![Q20](crops/Student_3/Q20.jpg) | **D** | ∅ | ∅ | ∅ | ∅ | Circled-style 'D' — all four readers abstained; CSV D is right. |

Correct per reader: Qwen3.8 15/20, Chandra 15/20, PaddleOCR 16/20, GLM-OCR 15/20

## Short answers (Q21–Q35)

Teacher mark is from the CSV (out of 2). CER/WER are against Claude's transcript where one exists (lower = better; struck-out text, punctuation, case and the question label are ignored).

### Q21 (S1) — teacher mark: 2.0

![S1](crops/Student_3/S1.jpg)
<sub>located on: Student_3_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 21. Supervised learning is an algorithm that we use to classify the data that contains label. | — | — |
| Qwen3.8 | Q1. Supervised learning is an algorithm that we use to classify the data ⏎ that contains label. | 0.00 | 0.00 |
| Chandra | Supervised learning is an algorithm that we use to classify the data that contains label. | 0.00 | 0.00 |
| PaddleOCR | Supervised learning is an algorithm that we use to classify the data that contains label. | 0.00 | 0.00 |
| GLM-OCR | Supervised learning is an algorithm that we use to classify the data that contains label. | 0.00 | 0.00 |

### Q22 (S2) — teacher mark: 2.0

![S2](crops/Student_3/S2.jpg)
<sub>located on: Student_3_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | ~~22. based on mind the M1 need to do the classification matrix to find a~~ 22. based on mind the M1 model is not yet the best solution yet since it has only 30% accuracy the data set shold use another model then do classification matrix to find the best one. | — | — |
| Qwen3.8 | 29. based on mind the M1 need to do the classification matrix to find ⏎ a | 0.63 | 0.71 |
| Chandra | ~~22. based on mind the M1 need to do the classification matrix to find~~ ⏎  ⏎ a | 0.99 | 1.00 |
| PaddleOCR | based on mind the M1 need to do the classification matrix to find a | 0.63 | 0.71 |
| GLM-OCR | based on mind the M1 need to do the classification matrix to find a | 0.63 | 0.71 |

**Visual check:** First attempt is struck through, then rewritten.

### Q23 (S3) — teacher mark: 0.0

![S3](crops/Student_3/S3.jpg)
<sub>located on: Student_3_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 23. Regression analysis is a method that we use for search data and then grouping the data. and identifying the data. | — | — |
| Qwen3.8 | 23. Regression analysis is a method that we use for search data ⏎ and then grouping the data. and identifying the data. | 0.00 | 0.00 |
| Chandra | Regression analysis is a method that we use for search data and then grouping the data and identifying the data. ⏎  ⏎ 25. ... | 0.03 | 0.05 |
| PaddleOCR | Regression analysis is a method that we use for search data and then grouping the data and identifying the data. | 0.00 | 0.00 |
| GLM-OCR | Regression analysis is a method that we use for search data and then grouping the data and identifying the data. | 0.00 | 0.00 |

### Q24 (S4) — teacher mark: 0.0

![S4](crops/Student_3/S4.jpg)
<sub>located on: Student_3_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 24. Elucidate any two challenges of machine learning: - Linear regression - logistic regression | — | — |
| Qwen3.8 | 24. Elucidate any two challenges of machine learning: ⏎ - Linear regression ⏎ - logistic regression | 0.00 | 0.00 |
| Chandra | Elucidate any two challenges of machine learning: ⏎ - Linear regression ⏎ - logistic regression ⏎  ⏎ 27. to find the null | 0.23 | 0.45 |
| PaddleOCR | Elucidate any two challenges of machine learning: ⏎ - Linear regression ⏎ - Logistic regression ⏎ 27. to find the | 0.17 | 0.36 |
| GLM-OCR | Elucidate any two challenges of machine learning: ⏎ - Linear regression ⏎ - logistic regression ⏎ 27. to find the best one. | 0.28 | 0.55 |

### Q25 (S5) — teacher mark: 1.0

![S5](crops/Student_3/S5.jpg)
<sub>located on: Student_3_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 25. two major applications of data science = Mobile Bank application and Netflex. | — | — |
| Qwen3.8 | 25. two major applications of data science = Mobile Bank application ⏎ and Netflix. | 0.01 | 0.09 |
| Chandra | two major applications of data science = Mobile Bank application and Netflix. | 0.01 | 0.09 |
| PaddleOCR | two major applications of data science: Mobile Bank application and Netflix. | 0.01 | 0.09 |
| GLM-OCR | two masor applications of data science = Mobile Bank application and Netflex. | 0.01 | 0.09 |

### Q26 (S6) — teacher mark: 2.0

![S6](crops/Student_3/S6.jpg)
<sub>located on: Student_3_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 26. Structured data is the data that contains in row and column. semi-structurd data is the data ~~that we know~~ like language letters, etc. | — | — |
| Qwen3.8 | 26. structured data is the data that contains in row and column. ⏎ Semi-structured data: is the data ~~that we know~~ like language ⏎ letters,etc. | 0.01 | 0.05 |
| Chandra | structured data is the data that contains in row and column. ⏎  ⏎ semi-structured data is the data ~~that we know~~ like language letters, etc. | 0.01 | 0.05 |
| PaddleOCR | Structured data is the data that contains in row and column. Semi-Structured data is the data like language letters, etc. | 0.01 | 0.05 |
| GLM-OCR | Structured data is the data that contains in row and column. ⏎ Semi-structured data is the data that we know like language ⏎ letters, etc. | 0.12 | 0.19 |

### Q27 (S7) — teacher mark: 1.0

![S7](crops/Student_3/S7.jpg)
<sub>located on: Student_3_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 27. to find the outlier in the data we need to use [?] [?] | — | — |
| Qwen3.8 | 27. to find the outlier in the data we need to look at the ⏎ math | 0.33 | 0.36 |
| Chandra | Logistic regression ⏎  ⏎ 27. to find the outlier in the data we need to look at the residuals ⏎  ⏎ math 1 | 1.07 | 0.82 |
| PaddleOCR | to find the outlier in the data we need to look | 0.09 | 0.09 |
| GLM-OCR | to find the outlier in the data we need to loca | 0.09 | 0.09 |

**Visual check:** The answer runs off the bottom of the scanned page 2; only the first line is visible ('…we need to use' + an unreadable word). Teacher gave 1.0, so the rest may be on paper but not in the scan.

### Q28 (S8) — teacher mark: 1.0

![S8](crops/Student_3/S8.jpg)
<sub>located on: Student_3_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 28. Data pre-processing is the process for collecting the data source before going to analysis. | — | — |
| Qwen3.8 | 28. Data pre-processing is the process for collecting the data source ⏎ before going to analysis. | 0.00 | 0.00 |
| Chandra | Data pre-processing is the process for collecting the data source before going to analysts. | 0.01 | 0.07 |
| PaddleOCR | Data pre-processing is the process for collecting the data source before going to analysis. | 0.00 | 0.00 |
| GLM-OCR | Data pre-processing is the process for collecting the data source before going to analysts. | 0.01 | 0.07 |

### Q29 (S9) — teacher mark: 2.0

![S9](crops/Student_3/S9.jpg)
<sub>located on: Student_3_p2.png, Student_3_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 29. ~~Dat~~ Data normalization is required in k-NN because normalization help to scale all the same data for easier to analysis so that k-NN easy for classification. | — | — |
| Qwen3.8 | 29. ~~That~~ Data normalization is required in k-NN because normalization ⏎ help to scale all the same data for easier to analysis so that k-NN easy ⏎ for classification. ⏎  ⏎ 29. based on mind the M1 model is not yet the best solution yet since it has ⏎ only 30% accuracy the data set shold use another model then do ⏎ classification matrix to find the best one. | 1.19 | 1.33 |
| Chandra | ~~That~~ Data normalization is required in k-NN because normalization help to scale all the same data for easier to analysis so that k-NN easy for classification. ⏎ 22. based on mind the M1 model is not yet the best solution yet since it has only 30% accuracy the data set should use another model then do classification matrix to find the best one. ⏎  ⏎ 9.4 | 1.22 | 1.41 |
| PaddleOCR | Data normalization is required in k-NN because normalization ⏎ help to scale all the same data for easier to analysis so that k-NN easy ⏎ for classification. ⏎ 29. based on mind the M1 model is not yet the best solution yet since it has only 30% accuracy the data set should use another model then do classification matrix to find the best one. | 1.20 | 1.33 |
| GLM-OCR | Data normalization is required in k-NN because normalization help to scale all the same data for easier to analysis so that k-NN easy for classification. ⏎ 29. based on mind the M4 model is not yet the best solution yet since it has only 30% accuracy the data set should use another model then do classification matrix to find the best one. | 1.20 | 1.33 |

### Q30 (S10) — teacher mark: None

_answer not located_
<sub>located on: —</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** |  | — | — |
| Qwen3.8 | ∅ |  |  |
| Chandra | ∅ |  |  |
| PaddleOCR | ∅ |  |  |
| GLM-OCR | ∅ |  |  |

### Q31 (S11) — teacher mark: 1.0

![S11](crops/Student_3/S11.jpg)
<sub>located on: Student_3_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 31. k is a range for does the classfy the data in k-means algorithm mean that k-means algorithm do the process based on k. | — | — |
| Qwen3.8 | 31. k is arange for does the classify the data in k-means algorithm ⏎ mean that k-means algorithm do the process based on k. | 0.02 | 0.12 |
| Chandra | k is a range for does the classify the data in k-means algorithm mean that k-means algorithm do the process based on k. ⏎  ⏎ 32. Name few hyperparameters of model training algorithms. | 0.50 | 0.36 |
| PaddleOCR | k is a range for does the classify the data in k-means algorithm mean that k-means algorithm do the process based on k. ⏎ 32. Name few hyperparameters of models | 0.33 | 0.28 |
| GLM-OCR | k is a range for does the classfy the data in k-means algorithm ⏎ mean that k-means algorithm do the process based on k. ⏎  ⏎ 32. Name few hyperparameters of algorithms | 0.36 | 0.24 |

### Q32 (S12) — teacher mark: 0.0

![S12](crops/Student_3/S12.jpg)
<sub>located on: Student_3_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 32. Name few hyperparameters of machine learning algorithms is the best hyperline to make different between classes. | — | — |
| Qwen3.8 | 39. Name few hyperparameters of machine learning algorithms is the ⏎ best hyperline to make different between classes. | 0.00 | 0.00 |
| Chandra | the process based on k. ⏎  ⏎ 32. Name few hyperparameters of machine learning algorithms is the best hyperline to make different between classes. ⏎  ⏎ ~~22. based on mind the M1~~ | 0.23 | 0.38 |
| PaddleOCR | Name few hyperparameters of machine learning algorithms is the best hyperline to make different between classes. | 0.00 | 0.00 |
| GLM-OCR | Name few hyperparameters of machine learning algorithms is the best hyperline to make different between classes. | 0.00 | 0.00 |

### Q33 (S13) — teacher mark: None

_answer not located_
<sub>located on: —</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** |  | — | — |
| Qwen3.8 | ∅ |  |  |
| Chandra | ∅ |  |  |
| PaddleOCR | ∅ |  |  |
| GLM-OCR | ∅ |  |  |

### Q34 (S14) — teacher mark: 1.0

![S14](crops/Student_3/S14.jpg)
<sub>located on: Student_3_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 34. based on mind I thought the bellow was: the first and last are classify clear but the middle is not clear. | — | — |
| Qwen3.8 | 34. based on mind I thought the bellow was : ⏎ the first and last are classify clear but the middle is not ⏎ clear. | 0.00 | 0.00 |
| Chandra | based on mind I thought the below was : ⏎  ⏎ the first and last are classify clear but the middle is not clear. | 0.01 | 0.05 |
| PaddleOCR | based on mind I thought the bellow was: ⏎ the first and last are classify clear but the middle is not clear. | 0.00 | 0.00 |
| GLM-OCR | based on mind I thought the bellow was = ⏎ the first and last are classify clear but the middle is not clear. | 0.00 | 0.00 |

### Q35 (S15) — teacher mark: None

_answer not located_
<sub>located on: —</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** |  | — | — |
| Qwen3.8 | ∅ |  |  |
| Chandra | ∅ |  |  |
| PaddleOCR | ∅ |  |  |
| GLM-OCR | ∅ |  |  |
