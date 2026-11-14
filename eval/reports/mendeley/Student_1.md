# Student_1 — reader comparison

Pages read: Student_1_p1.png, Student_1_p2.png, Student_1_p3.png  
Skipped as blank / show-through backs: Student_1_p4.png  
Answers located by the segmenter: 35/35  
Visual check by Claude: yes — transcripts for short answers below

Page images: `eval/data/mendeley/images/` · crops: `eval/reports/mendeley/crops/` (local, not in git).

> **Visual check (sheet):** Answers are written out of order (page 2: 26, 28, 25, 34, 27, 30; page 3: 22, 24, 31, 29, 23, 32, 33, 35). Page 4 is the blank back of page 3 (show-through only).

> Transcribed by Claude from the page images (eval/data/mendeley/images). Struck-out text is written ~~like this~~; [?] = could not read. Spelling is kept as written. Please verify.

## MCQ (gold = letter in the teacher's CSV)

| Q | crop | gold | Qwen3.8 | Chandra | PaddleOCR | GLM-OCR | note |
|---|---|---|---|---|---|---|---|
| Q1 | ![Q1](crops/Student_1/Q1.jpg) | **D** | ∅ | D ✅ | D ✅ | ∅ | Student's 'D' is written like 'Ɗ'; CSV D is right — readers abstained (not wrong). |
| Q2 | ![Q2](crops/Student_1/Q2.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q3 | ![Q3](crops/Student_1/Q3.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q4 | ![Q4](crops/Student_1/Q4.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q5 | ![Q5](crops/Student_1/Q5.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q6 | ![Q6](crops/Student_1/Q6.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q7 | ![Q7](crops/Student_1/Q7.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q8 | ![Q8](crops/Student_1/Q8.jpg) | **D** | ∅ | D ✅ | D ✅ | D ✅ |  |
| Q9 | ![Q9](crops/Student_1/Q9.jpg) | **D** | ∅ | D ✅ | D ✅ | D ✅ |  |
| Q10 | ![Q10](crops/Student_1/Q10.jpg) | **D** | ∅ | ∅ | D ✅ | ∅ | Same 'Ɗ'-style D; CSV right; only PaddleOCR read it. |
| Q11 | ![Q11](crops/Student_1/Q11.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q12 | ![Q12](crops/Student_1/Q12.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q13 | ![Q13](crops/Student_1/Q13.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q14 | ![Q14](crops/Student_1/Q14.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q15 | ![Q15](crops/Student_1/Q15.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q16 | ![Q16](crops/Student_1/Q16.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q17 | ![Q17](crops/Student_1/Q17.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q18 | ![Q18](crops/Student_1/Q18.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q19 | ![Q19](crops/Student_1/Q19.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q20 | ![Q20](crops/Student_1/Q20.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |

Correct per reader: Qwen3.8 16/20, Chandra 19/20, PaddleOCR 20/20, GLM-OCR 18/20

## Short answers (Q21–Q35)

Teacher mark is from the CSV (out of 2). CER/WER are against Claude's transcript where one exists (lower = better; struck-out text, punctuation, case and the question label are ignored).

### Q21 (S1) — teacher mark: 2.0

![S1](crops/Student_1/S1.jpg)
<sub>located on: Student_1_p1.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 21. Supervised learning is a machine learning algorith which we give labeled data as input and expect output as prediction we want. | — | — |
| Qwen3.8 | 21. Supervised learning is a machine learning algorithm ⏎ which we give labeled data as input and expect ⏎ output as prediction we want. | 0.01 | 0.05 |
| Chandra | 20 C ⏎  ⏎ 21. Supervised learning is a machine learning algorithm which we give labeled data as input and expect output as prediction we want. | 0.07 | 0.19 |
| PaddleOCR | 20 C ⏎ 21. Supervised learning is a machine learning algorithm which we give labeled data as input and expect output as prediction we want. | 0.07 | 0.19 |
| GLM-OCR | 20. C ⏎ 21. Supervised learning is a machine learning algorithm which we give labeled data as input and expect output as prediction we want. | 0.05 | 0.14 |

### Q22 (S2) — teacher mark: 1.0

![S2](crops/Student_1/S2.jpg)
<sub>located on: Student_1_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 22. Comment on Model M1: This model doesn't have high accuracy, so it needs better training dataset. ~~The training dataset~~ or more than one training dataset. | — | — |
| Qwen3.8 | 22. Comment on Model M1: ⏎ This model doesn't have high accuracy, so it needs better ⏎ training dataset. ~~The training dataset~~ or more than one ⏎ training dataset. | 0.00 | 0.00 |
| Chandra | Comment on Model M1: ⏎  ⏎ This model doesn't have high accuracy, so it needs better training dataset. ~~The training dataset~~ or more than one training dataset. | 0.00 | 0.00 |
| PaddleOCR | Comment on Model M1: ⏎ This model doesn't have high accuracy, so it needs better training dataset. The training dataset or more than one training dataset. | 0.17 | 0.13 |
| GLM-OCR | Comment on Model M1: ⏎ This model doesn't have high accuracy, so it needs better training dataset. The training dataset or more than one training dataset. | 0.17 | 0.13 |

### Q23 (S3) — teacher mark: 1.0

![S3](crops/Student_1/S3.jpg)
<sub>located on: Student_1_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 23. Regression analysis is the method uses to analysis the output of regression. | — | — |
| Qwen3.8 | 23. Regression analysis is the method uses to analysis the ⏎ output of regression. | 0.00 | 0.00 |
| Chandra | Regression analysis is the method used to analyse the output of regression. | 0.04 | 0.17 |
| PaddleOCR | Regression analysis is the method used to analysis the output of regression. | 0.01 | 0.08 |
| GLM-OCR | Regression analysis is the method uses to analysis the output of regression. | 0.00 | 0.00 |

### Q24 (S4) — teacher mark: 2.0

![S4](crops/Student_1/S4.jpg)
<sub>located on: Student_1_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 24. Elucidate any 2 challenges of Machine learning: - Hard to find dataset to work on. (Dataset are expensive and confidentail. - Required large data to train in order to get accuracy. | — | — |
| Qwen3.8 | 24. Elucidate any 2 challenges of Machine Learning: ⏎ - Hard to find dataset to work on. (Dataset are ⏎ expensive and confidential. ⏎ - Required large data to train in order to get accuracy. | 0.01 | 0.03 |
| Chandra | Elucidate any 2 challenges of Machine Learning : ⏎ - Hard to find dataset to work on. (Dataset are expensive and confidential). ⏎ - Required large data to train in order to get accuracy. | 0.01 | 0.03 |
| PaddleOCR | Elucidate any 2 challenges of Machine learning: ⏎ - Hard to find dataset to work on. (Dataset are ⏎ - expensive and confidential. ⏎ - Required large data to train in order to get accuracy. | 0.01 | 0.03 |
| GLM-OCR | Elucidate any 2 challenges of Machine Learning: ⏎ - Hard to find dataset to work on. (Dataset are expensive and confidential. ⏎ - Required large data to train in order to get accuracy. | 0.01 | 0.03 |

### Q25 (S5) — teacher mark: 2.0

![S5](crops/Student_1/S5.jpg)
<sub>located on: Student_1_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 25 list out any 2 majar applications of data science: . Financial sector . Transportation sector. | — | — |
| Qwen3.8 | values. ⏎ 25 list out any 2 major applications of data science : ⏎ . Financial sector ⏎ . Transportation sector. | 0.09 | 0.14 |
| Chandra | values. ⏎  ⏎ 25 list out any 2 major applications of data science: ⏎  ⏎ • Financial sector ⏎ • Transportation sector. ⏎  ⏎ ... on the performance of the classifiers | 0.51 | 0.57 |
| PaddleOCR | list out any 2 major applications of data science: ⏎ - Financial sector ⏎ - Transportation sector | 0.04 | 0.14 |
| GLM-OCR | list out any 2 major applications of data science: ⏎ . Financial sector ⏎ . Transportation sector. | 0.04 | 0.14 |

### Q26 (S6) — teacher mark: 2.0

![S6](crops/Student_1/S6.jpg)
<sub>located on: Student_1_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 26. Distinguish between structured and semi-Structured data. - structured data are the well organized data such as csv file, excel file. - semi-structured data are the data which are half organized such as Json, html file. | — | — |
| Qwen3.8 | 26. Distinguish between structured and semi-structured data. ⏎ - structured data are the well organized data such as ⏎ csv file, excel file. ⏎ - semi-structured data are the data which are half ⏎ organized such as json, html file. | 0.00 | 0.00 |
| Chandra | Distinguish between structured and semi-structured data. ⏎  ⏎ - structured data are the well organized data such as csv file, excel file. ⏎  ⏎ - semi-structured data are the data which are half organized such as JSON, html file. | 0.00 | 0.00 |
| PaddleOCR | Distinguish between structured and semi-structured data. ⏎ structured data are the well organized data such as csv file, excel file. ⏎ semi-structured data are the data which are half organized such as JSON, html file. | 0.00 | 0.00 |
| GLM-OCR | Distinguish between structured and semi-structured data. ⏎ - structured data are the well organized data such as csv file, excel file. ⏎ - semi-structured data are the data which are half organized such as json, html file. | 0.00 | 0.00 |

### Q27 (S7) — teacher mark: 1.0

![S7](crops/Student_1/S7.jpg)
<sub>located on: Student_1_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 27. We find out an Outlier in the data by using Outlier detection technique such as Z-score and IOR. | — | — |
| Qwen3.8 | 27. We find out an outlier in the data by using Outlier ⏎ detection technique such as Z-score and IQR. | 0.01 | 0.05 |
| Chandra | is small. ⏎  ⏎ 27. We find out an Outlier in the data by using Outlier detection technique such as Z-score and IQR. | 0.14 | 0.21 |
| PaddleOCR | is small. ⏎  ⏎ 27. We find out an Outlier in the data by using Outlier detection technique such as Z-score and IOR. | 0.13 | 0.16 |
| GLM-OCR | is small. ⏎ 27. We find out an Outlier in the data by using Outlier detection technique such as Z-score and IOR. | 0.13 | 0.16 |

**Visual check:** Last word looks like 'IOR' (probably meant IQR); transcribed as written.

### Q28 (S8) — teacher mark: 2.0

![S8](crops/Student_1/S8.jpg)
<sub>located on: Student_1_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 28. Data pre-processing is the process for removing incomplete, incorrect and inaccurate data and replacing missing values. | — | — |
| Qwen3.8 | 28. Data pre-processing is the process for removing incomplete, ⏎ incorrect and inaccurate data and replacing missing ⏎ values. | 0.00 | 0.00 |
| Chandra | organized such as json, html file. ⏎  ⏎ 28. Data pre-processing is the process for removing incomplete, incorrect and inaccurate data and replacing missing values. ⏎  ⏎ Applications of data science: | 0.56 | 0.65 |
| PaddleOCR | Data pre-processing is the process for removing incomplete, incorrect and inaccurate data and replacing missing values. | 0.00 | 0.00 |
| GLM-OCR | Data pre-processing is the process for removing incomplete, incorrect and inaccurate data and replacing missing values. | 0.00 | 0.00 |

### Q29 (S9) — teacher mark: 1.0

![S9](crops/Student_1/S9.jpg)
<sub>located on: Student_1_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 29. Data normalization is required in K.NN because after data is normalized it is easy to give K. point, so it will not over fitting or underfitting. | — | — |
| Qwen3.8 | 29. Data normalization is required in k.NN because after ⏎ data is normalized it is easy to give k.point, so it ⏎ will not over fitting or underfitting. | 0.00 | 0.00 |
| Chandra | Data normalization is required in K-NN because after data is normalized it is easy to give K-point, so it will not over fitting or under fitting. | 0.01 | 0.07 |
| PaddleOCR | Data normalization is required in KNN because after data is normalized it is easy to give K.point, so it will not overfitting or underfitting. | 0.01 | 0.15 |
| GLM-OCR | Data normalization is required in K.NN because after data is normalized it is easy to give K. point, so it will not over fitting or under fitting. | 0.01 | 0.07 |

### Q30 (S10) — teacher mark: 2.0

![S10](crops/Student_1/S10.jpg)
<sub>located on: Student_1_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 30. Continuous attributes are discretized by converting to interval form. Example: 1, 5, 9, 10, 11, 12, 19, 20 → 1-10, 11-20. | — | — |
| Qwen3.8 | 30. Continuous attributes are discretized by converting to ⏎ interval form. Example: 1, 5, 9, 10, 11, 12, 19, 20 ⏎ → 1-10, 11-20. | 0.00 | 0.00 |
| Chandra | Continuous attributes are discretized by converting to interval form. Example: 1, 5, 9, 10, 11, 12, 19, 20 ⏎ → 1 - 10, 11 - 20. | 0.00 | 0.00 |
| PaddleOCR | continuous attributes are discretized by converting to interval form. Example: 1,5,9,10, 11, 12, 19, 20 ⏎ → 1-10, 11-20. | 0.00 | 0.00 |
| GLM-OCR | Continuous attributes are discretized by converting to interval form. Example: 1, 5, 9, 10, 11, 12, 19, 20 ⏎ → 1-10, 11-20. | 0.00 | 0.00 |

### Q31 (S11) — teacher mark: 1.0

![S11](crops/Student_1/S11.jpg)
<sub>located on: Student_1_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 31. k in k-means algorithm is the pre-defined cluster. | — | — |
| Qwen3.8 | 31. k in k-means algorithm is the pre-defined cluster. | 0.00 | 0.00 |
| Chandra | k in k-means algorithm is the pre-defined cluster. | 0.00 | 0.00 |
| PaddleOCR | k in k-means algorithm is the pre-defined cluster. | 0.00 | 0.00 |
| GLM-OCR | k in k-means algorithm is the pre-diefined cluster. | 0.02 | 0.10 |

### Q32 (S12) — teacher mark: None

![S12](crops/Student_1/S12.jpg)
<sub>located on: Student_1_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 32. Name few hyperparameters of machine learning algorithm | — | — |
| Qwen3.8 | 32. Name few hyperparameters of machine learning algorithm | 0.00 | 0.00 |
| Chandra | Name few hyperparameters of machine learning algorithm | 0.00 | 0.00 |
| PaddleOCR | Name few hyperparameters of machine learning algorithm | 0.00 | 0.00 |
| GLM-OCR | Name few hyperparameters of machince learning algorithm | 0.02 | 0.14 |

**Visual check:** Student only copied the question — no answer. Teacher CSV is blank (no mark), consistent.

### Q33 (S13) — teacher mark: 0.0

![S13](crops/Student_1/S13.jpg)
<sub>located on: Student_1_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 33. gradient descent is. | — | — |
| Qwen3.8 | 33. gradrent descent rs. | 0.11 | 0.67 |
| Chandra | gradient descent rs. | 0.05 | 0.33 |
| PaddleOCR | gradient descent is. | 0.00 | 0.00 |
| GLM-OCR | gradient descent is. | 0.00 | 0.00 |

**Visual check:** Answer stops after 'is.' — teacher gave 0.

### Q34 (S14) — teacher mark: 2.0

![S14](crops/Student_1/S14.jpg)
<sub>located on: Student_1_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 34. comment on the performance of the classifiers. . P1 : Good classification. The distance between gutters is large and no data between gutters . P2 : Bad classification. There are data between gutters. . P3 : Bad classification. The distance between gutters is small. | — | — |
| Qwen3.8 | 34. comment on the performance of the classifiers. ⏎ . P1 : Good classification. The distance between gutters ⏎ is large and no data between gutters ⏎ . P2 : Bad classification. There are data between ⏎ gutters. ⏎ . P3 : Bad classification. The distance between gutters ⏎ is small | 0.00 | 0.00 |
| Chandra | comment on the performance of the classifiers. ⏎  ⏎ . P1 : Good classification. The distance between gutters is large and no data between gutters ⏎  ⏎ . P2 : Bad classification. There are data between gutters. ⏎  ⏎ . P3 : Bad classification. The distance between gutters is small | 0.00 | 0.00 |
| PaddleOCR | comment on the performance of the classifiers. ⏎ P1: Good classification. The distance between gutters is large and no data between gutters ⏎ P2: Bad classification. There are data between gutters. ⏎ P3: Bad classification. The distance between gutters is small | 0.00 | 0.00 |
| GLM-OCR | comment on the performance of the classifiers. ⏎ . P1 : Good classification. The distance between gutters is large and no data between gutters ⏎ . P2 : Bad classification. There are data between gutters. ⏎ . P3 : Bad classification. The distance between gutters is small. | 0.00 | 0.00 |

### Q35 (S15) — teacher mark: 2.0

![S15](crops/Student_1/S15.jpg)
<sub>located on: Student_1_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 35. Radial Basis function kernel works by using margin vector to calculate distance margin point and hyperplane. | — | — |
| Qwen3.8 | 35. Radial Basis function kernel works by using margin vector ⏎ to calculate distance margin point and hyperplane. | 0.00 | 0.00 |
| Chandra | Radial Basis Function kernel works by using margin vector to calculate distance margin point and hyperplane. | 0.00 | 0.00 |
| PaddleOCR | Radial Basis function kernel works by using margin vector to calculate distance margin point and hyperplane. | 0.00 | 0.00 |
| GLM-OCR | Radial Basis function kernel works by using margin vector to calculate distance margin point and hyperplane. | 0.00 | 0.00 |
