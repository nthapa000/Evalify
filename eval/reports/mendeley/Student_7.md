# Student_7 — reader comparison

Pages read: Student_7_p1.png, Student_7_p2.png, Student_7_p3.png  
Skipped as blank / show-through backs: Student_7_p4.png  
Answers located by the segmenter: 34/35  
Visual check by Claude: MCQ only / disagreements

Page images: `eval/data/mendeley/images/` · crops: `eval/reports/mendeley/crops/` (local, not in git).

> Only the MCQ answers where a reader disagreed with the teacher CSV were checked by eye on this sheet.

## MCQ (gold = letter in the teacher's CSV)

| Q | crop | gold | Qwen3.8 | Chandra | PaddleOCR | GLM-OCR | note |
|---|---|---|---|---|---|---|---|
| Q1 | ![Q1](crops/Student_7/Q1.jpg) | **D** | D ✅ | ∅ | D ✅ | ∅ | 'Ɗ'-style D; CSV right. |
| Q2 | ![Q2](crops/Student_7/Q2.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q3 | ![Q3](crops/Student_7/Q3.jpg) | **D** | ∅ | ∅ | ∅ | ∅ | 'Ɗ'-style D; all four abstained. |
| Q4 | ![Q4](crops/Student_7/Q4.jpg) | **B** | ∅ | B ✅ | B ✅ | B ✅ |  |
| Q5 | ![Q5](crops/Student_7/Q5.jpg) | **A** | A,C ❌ | A ✅ | A ✅ | A ✅ | Clearly 'A' only. Qwen3.8 answered 'A,C' — it invented a C (one of Qwen's 2 wrong letters). |
| Q6 | ![Q6](crops/Student_7/Q6.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q7 | ![Q7](crops/Student_7/Q7.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q8 | ![Q8](crops/Student_7/Q8.jpg) | **A** | ∅ | A ✅ | A ✅ | A ✅ |  |
| Q9 | ![Q9](crops/Student_7/Q9.jpg) | **C** | ∅ | C ✅ | C ✅ | C ✅ |  |
| Q10 | ![Q10](crops/Student_7/Q10.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q11 | ![Q11](crops/Student_7/Q11.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q12 | ![Q12](crops/Student_7/Q12.jpg) | **C** | ∅ | C ✅ | C ✅ | C ✅ |  |
| Q13 | ![Q13](crops/Student_7/Q13.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q14 | ![Q14](crops/Student_7/Q14.jpg) | **C** | ∅ | C ✅ | C ✅ | C ✅ |  |
| Q15 | ![Q15](crops/Student_7/Q15.jpg) | **B** | ∅ | B ✅ | B ✅ | B ✅ |  |
| Q16 | ![Q16](crops/Student_7/Q16.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q17 | ![Q17](crops/Student_7/Q17.jpg) | **A** | ∅ | A ✅ | A ✅ | A ✅ |  |
| Q18 | ![Q18](crops/Student_7/Q18.jpg) | **D** | ∅ | ∅ | ∅ | ∅ | 'Ɗ'-style D; all four abstained. |
| Q19 | ![Q19](crops/Student_7/Q19.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q20 | ![Q20](crops/Student_7/Q20.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |

Correct per reader: Qwen3.8 10/20, Chandra 17/20, PaddleOCR 18/20, GLM-OCR 17/20

## Short answers (Q21–Q35)

Teacher mark is from the CSV (out of 2). CER/WER are against Claude's transcript where one exists (lower = better; struck-out text, punctuation, case and the question label are ignored).

### Q21 (S1) — teacher mark: 2.0

![S1](crops/Student_7/S1.jpg)
<sub>located on: Student_7_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | Answer all questions. ⏎ 21. Supervised Learning is has a label, relationship and dependencies ⏎ between prediction target of input and output. |  |  |
| Chandra | Answer all questions ⏎  ⏎ 21. Supervised Learning is has a label , relationship and dependencies between prediction target of input and output. ⏎  ⏎ It is in the data |  |  |
| PaddleOCR | Supervised Learning is has a label, relationship and dependencies between prediction target of input and output. |  |  |
| GLM-OCR | Answer all questions ⏎ 21. Supervised Learning is has a label, relationship and dependencies between prediction target of input and output. |  |  |

### Q22 (S2) — teacher mark: 1.0

![S2](crops/Student_7/S2.jpg)
<sub>located on: Student_7_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 22. Comment on model M1. ⏎ A model M1 give 99% of accuracy for training but give 30% of ⏎ accuracy for testing so it's mean the testing dataset is not ⏎ accurate enough evantghough training get the higest percentage. |  |  |
| Chandra | Comment on model M1. ⏎  ⏎ A model M1 give 99% of accuracy for training but give 30% of accuracy for testing so it's mean the testing dataset is not accurate enough even though training get the highest percentage. ⏎  ⏎ challenges of ML. |  |  |
| PaddleOCR | Comment on model M1. ⏎ A model M1 give 99% of accuracy for training but give 30% of accuracy for testing so it's mean the testing dataset is not accurate enough even though training get the highest percentage challenges of ML. |  |  |
| GLM-OCR | Comment on model M1. ⏎ A model M1 give 99% of accuracy for training but give 30% of accuracy for testing so it's mean the testing dataset is not accurate enough eventhough training get the highest percentage. |  |  |

### Q23 (S3) — teacher mark: 1.0

![S3](crops/Student_7/S3.jpg)
<sub>located on: Student_7_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | group and should choose from ⏎ 23. Regression analysis is an analysis on continuous values. |  |  |
| Chandra | group and should choose from \pm ⏎  ⏎ 23. Regression analysis is an analysis on continuous values. ⏎  ⏎ Performance of the classifiers. |  |  |
| PaddleOCR | Regression analysis is an analysis on continuous values. |  |  |
| GLM-OCR | group and should choose from ⏎ 23 Regression analysis is an analysis on continuous values. |  |  |

### Q24 (S4) — teacher mark: 1.0

![S4](crops/Student_7/S4.jpg)
<sub>located on: Student_7_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | accurate enough eventhough training ⏎ 24. Elucidate any two challenges of ML. ⏎ + Some distance is nod accurate ⏎ + Slow |  |  |
| Chandra | accurate enough even though training ⏎  ⏎ 24. Elucidate any two challenges of ML. ⏎  ⏎ + Some distance is not accurate ⏎  ⏎ + Slow ⏎  ⏎ Two major applications of |  |  |
| PaddleOCR | accurate enough even though training ⏎ 24. Elucidate any two challenges of ML. ⏎ + Some distance is not accurate ⏎ + Slow ⏎ + The two major applications of |  |  |
| GLM-OCR | accurate enough eventhough training ⏎ 24. Elucidate any two challenges of ML. ⏎ + Some distance is not accurate ⏎ + Slow |  |  |

### Q25 (S5) — teacher mark: 2.0

![S5](crops/Student_7/S5.jpg)
<sub>located on: Student_7_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | + Slow ⏎ 25. List out any two major applications of data science. ⏎ + Finance ⏎ + Infrastructure ⏎ between Structured and Semi-Structured |  |  |
| Chandra | + slow ⏎  ⏎ 25. List out any two major applications of data science. ⏎  ⏎ + Finance ⏎ + Infrastructure ⏎  ⏎ 26. Explain the difference between Structured and Semi-Structured |  |  |
| PaddleOCR | + Slow ⏎ 25. List out any two major applications of data science ⏎ + Finance ⏎ + Infrastructure |  |  |
| GLM-OCR | + Slow ⏎ 25. List out any two major applications of data science. ⏎ + Finance ⏎ + Infrastructure |  |  |

### Q26 (S6) — teacher mark: 0.0

![S6](crops/Student_7/S6.jpg)
<sub>located on: Student_7_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | + Finance ⏎ + Infrastructure ⏎ 26. Distinguish between Structured and Semi-Structured data ⏎ + Structured data is high level ⏎ + Semi-structured data is low level ⏎ attributes are discretized by converted float |  |  |
| Chandra | + Finance ⏎ + Infrastructure ⏎  ⏎ 26. Distinguish between Structured and Semi-Structured data ⏎  ⏎ + Structured data is high level ⏎ + Semi-structured data is low level ⏎ + Semi-structured attributes are discretized by converted float |  |  |
| PaddleOCR | + Infrastructure ⏎ 26. Distinguish between Structured and Semi-Structured data ⏎ + Structured data is high level ⏎ + Semi-structured data is low level ⏎ Attitudes are discretized by converted float |  |  |
| GLM-OCR | + Infrastructure ⏎ 26. Distinguish between Structured and Semi- Structured data ⏎ + Structured data is high level ⏎ + Semi-structured data is low level |  |  |

### Q27 (S7) — teacher mark: 1.0

![S7](crops/Student_7/S7.jpg)
<sub>located on: Student_7_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 27. Find out an outlier in the data ⏎ + trimming/removing outlier ⏎ + quantile based on flooring and capping ⏎ + mean/medt imputation |  |  |
| Chandra | between prediction target or imputation ⏎  ⏎ 27. Find out an outlier in the data+ trimming / removing outlier ⏎ + quantile based on flooring and capping ⏎ + mean / median imputation ⏎  ⏎ 1. Data processing is process that first we |  |  |
| PaddleOCR | Find out an outlier in the clate ⏎ + trimming/removing outlier ⏎ + quantile based on flooring and capping ⏎ + mean/meant imputation |  |  |
| GLM-OCR | between prediction target ⏎ 27. Find out an outlier in the data ⏎ + trimming / removing outlier ⏎ + quantile based on flooring and capping ⏎ + mean / mean imputation |  |  |

### Q28 (S8) — teacher mark: 2.0

![S8](crops/Student_7/S8.jpg)
<sub>located on: Student_7_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | + quantile based on missing ⏎ + mean/median imputation ⏎ 28. Data pre-processing is process that first we collecting data, ⏎ cleaning, modeling and implement. ⏎ standardization is required in K-NN because its can scaling |  |  |
| Chandra | + quantile based imputation ⏎ + mean/median imputation ⏎  ⏎ 28. Data pre-processing is process that first we collecting data, cleaning, modeling and implement. ⏎  ⏎ 1. Normalization is required in K-NN because its can scaling |  |  |
| PaddleOCR | Data pre-processing is process that first we collecting data, cleaning, modeling and implement. |  |  |
| GLM-OCR | + quantile based on the ⏎ + mean / mean imputation ⏎ 28. Data pre-processing is process that first we collecting data, cleaning, modeling and implement. |  |  |

### Q29 (S9) — teacher mark: 2.0

![S9](crops/Student_7/S9.jpg)
<sub>located on: Student_7_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 29. Data normalization is required in K-NN because its can scaling ⏎ that data so that it can represent in the smaller range ⏎ and it can desd fast. |  |  |
| Chandra | 28. Data pre-processing includes cleaning, modeling and implement. ⏎  ⏎ 29. Data normalization is required in K-NN because its can scaling that data so that it can represent in the smaller range and it can desd fast. ⏎  ⏎ n represent the number of variable in |  |  |
| PaddleOCR | cleaning, modeling and implement. ⏎ 29. Data normalization is required in k-NN because its can scaling ⏎ that data so that it can represent in the smaller range ⏎ and it can test fast. |  |  |
| GLM-OCR | cleaning, modeling and implement. ⏎ 29. Data normalization is required in K-NN because its can scaling that data so that it can represent in the smaller range and it can desd fast. |  |  |

### Q30 (S10) — teacher mark: 0.0

![S10](crops/Student_7/S10.jpg)
<sub>located on: Student_7_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | + Semi-structured data is low level ⏎ 30. Continuous attributes are discretized by converted float or String ⏎ to Integer. |  |  |
| Chandra | + Semi-structured data is low level ⏎ 30. Continuous attributes are discretized by converted float or String to Integer. |  |  |
| PaddleOCR | Continuous attributes are discretized by converted float or String to Integer. |  |  |
| GLM-OCR | + Semi-structured data is low level ⏎ 30. Continuous attributes are discretized by converted float or String to Integer. |  |  |

### Q31 (S11) — teacher mark: 1.0

![S11](crops/Student_7/S11.jpg)
<sub>located on: Student_7_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | and it can test fast. ⏎ 31. K in k-means algorithm is represent the number of variable in ⏎ group and should choose from 1 to 10. |  |  |
| Chandra | and it can desd fast. ⏎  ⏎ 31. K in k-means algorithm is represent the number of variable in group and should choose from 1 to 10. ⏎  ⏎ Various values |  |  |
| PaddleOCR | and it can test fast. ⏎ 31. K in k-means algorithm is represented the number of variable in group and should choose from 1 to 10. |  |  |
| GLM-OCR | and it can desd fast. ⏎ 31. K in k-means algorithm is represent the number of variable in group and should choose from 1 to 10. |  |  |

### Q32 (S12) — teacher mark: 1.0

![S12](crops/Student_7/S12.jpg)
<sub>located on: Student_7_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 33. Gradient descent is a multiple descent ⏎ 32. Name few hyperparameters of ML ⏎ - Converted variable ⏎ - check null value ⏎ - train ⏎ - test |  |  |
| Chandra | 33. Gradient descent is a multiple descent ⏎  ⏎ 32. Name few hyperparameters of ML ⏎  ⏎ - converted variable ⏎ - check null value ⏎ - train ⏎ - test |  |  |
| PaddleOCR | 33. Gradient descent is a multiple descent ⏎ 32. Name few hyperparameters of ML ⏎ - Converted variable ⏎ - Check null value ⏎ - Train ⏎ - Test |  |  |
| GLM-OCR | 33. Gradient descent is a multiple descent ⏎ 32. Name few hyperparameters of ML ⏎ - Converted variable ⏎ - check null value ⏎ - train ⏎ - test |  |  |

### Q33 (S13) — teacher mark: 0.0

![S13](crops/Student_7/S13.jpg)
<sub>located on: Student_7_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 33. Gradient descent is a multiple descent. |  |  |
| Chandra | Gradient descent is a multiple descent. ⏎  ⏎ It is used to find the parameters of ML |  |  |
| PaddleOCR | Gradient descent is a multiple descent. |  |  |
| GLM-OCR | Gradient descent is a multiple descent. |  |  |

### Q34 (S14) — teacher mark: 1.0

![S14](crops/Student_7/S14.jpg)
<sub>located on: Student_7_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 23. Regression analysis is an analysis on continuous ⏎ 34. Comment on the performance of the classifiers. ⏎ + first SVM classifier: the two line is a little bit closer do the variable ⏎ but the gap between the line is good. ⏎ + second SVM classifier: it is not good because the variable ⏎ has inside the gap of the two line. ⏎ + third SVM classifier: the gap from the two line do the variable ⏎ is good but the two line is too close to each other. |  |  |
| Chandra | 23. Regression analysis is an analysis on continuous variables. ⏎  ⏎ 34. comment on the performance of the classifiers. ⏎  ⏎ + first SVM classifier: the two line is a little bit closer to the variable but the gap between the line is good. ⏎  ⏎ + second SVM classifier: it is not good because the variable has inside the gap of the two line. ⏎  ⏎ + third SVM classifier: the gap from the two line to the variable is good but the two line is too close to each other. |  |  |
| PaddleOCR | 23. Regression analysis is an analysis on continuous variables. ⏎ 34. Comment on the performance of the classifiers. ⏎ first SVM classifier: the two is a little bit closer to the variable but the gap between the line is good. ⏎ second SVM classifier: it is not good because the variable has inside the gap of the two line. ⏎ third SVM classifier: the gap from the two line to the variable is good but the two line is too close to each other. |  |  |
| GLM-OCR | 23. Regression analysis is an analysis on continuous values. ⏎ 34. Comment on the performance of the classifiers. ⏎ + first SVM classifier: the two line is a little bit closer to the variable but the gap between the line is good. ⏎ + second SVM classifier: it is not good because the variable has inside the gap of the two line. ⏎ + third SVM classifier: the gap from the two line to the variable is good but the two line is too close to each other. |  |  |

### Q35 (S15) — teacher mark: None

_answer not located_
<sub>located on: —</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | ∅ |  |  |
| Chandra | ∅ |  |  |
| PaddleOCR | ∅ |  |  |
| GLM-OCR | ∅ |  |  |
