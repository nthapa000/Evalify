# Student_9 — reader comparison

Pages read: Student_9_p1.png, Student_9_p2.png, Student_9_p3.png, Student_9_p4.png  
Skipped as blank / show-through backs: none  
Answers located by the segmenter: 35/35  
Visual check by Claude: MCQ only / disagreements

Page images: `eval/data/mendeley/images/` · crops: `eval/reports/mendeley/crops/` (local, not in git).

> Only the MCQ answers where a reader disagreed with the teacher CSV were checked by eye on this sheet.

## MCQ (gold = letter in the teacher's CSV)

| Q | crop | gold | Qwen3.8 | Chandra | PaddleOCR | GLM-OCR | note |
|---|---|---|---|---|---|---|---|
| Q1 | ![Q1](crops/Student_9/Q1.jpg) | **D** | D ✅ | A,D ❌ | D ✅ | D ✅ | Student wrote 'D, All of the…' — Chandra took the A of 'All' (wrong 'A,D'). |
| Q2 | ![Q2](crops/Student_9/Q2.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q3 | ![Q3](crops/Student_9/Q3.jpg) | **D** | D ✅ | D ✅ | D ✅ | D ✅ |  |
| Q4 | ![Q4](crops/Student_9/Q4.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q5 | ![Q5](crops/Student_9/Q5.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q6 | ![Q6](crops/Student_9/Q6.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q7 | ![Q7](crops/Student_9/Q7.jpg) | **B** | ∅ | ∅ | B ✅ | B ✅ | 'B. one…'; CSV right. |
| Q8 | ![Q8](crops/Student_9/Q8.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q9 | ![Q9](crops/Student_9/Q9.jpg) | **C** | C ✅ | ∅ | C ✅ | C ✅ |  |
| Q10 | ![Q10](crops/Student_9/Q10.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q11 | ![Q11](crops/Student_9/Q11.jpg) | **B** | ∅ | A,B ❌ | A,B ❌ | B ✅ | 'B, a real…' — Chandra and PaddleOCR took the 'a' (wrong 'A,B'). |
| Q12 | ![Q12](crops/Student_9/Q12.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q13 | ![Q13](crops/Student_9/Q13.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q14 | ![Q14](crops/Student_9/Q14.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q15 | ![Q15](crops/Student_9/Q15.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q16 | ![Q16](crops/Student_9/Q16.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q17 | ![Q17](crops/Student_9/Q17.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q18 | ![Q18](crops/Student_9/Q18.jpg) | **D** | D ✅ | ∅ | D ✅ | D ✅ |  |
| Q19 | ![Q19](crops/Student_9/Q19.jpg) | **A** | ∅ | A ✅ | A ✅ | A ✅ |  |
| Q20 | ![Q20](crops/Student_9/Q20.jpg) | **C** | ∅ | C ✅ | B,C ❌ | B,C ❌ | B struck out, then 'C' — PaddleOCR and GLM-OCR reported 'B,C' (wrong); Chandra right. NB: PaddleOCR and GLM agree here, so the pipeline would have auto-accepted a wrong answer. |

Correct per reader: Qwen3.8 16/20, Chandra 15/20, PaddleOCR 18/20, GLM-OCR 19/20

## Short answers (Q21–Q35)

Teacher mark is from the CSV (out of 2). CER/WER are against Claude's transcript where one exists (lower = better; struck-out text, punctuation, case and the question label are ignored).

### Q21 (S1) — teacher mark: 2.0

![S1](crops/Student_9/S1.jpg)
<sub>located on: Student_9_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 2) Supervised learning is the machine learning that ⏎ train model with labeled data, that the correct output ⏎ are known, then to predict the new output, of dataset ⏎ that didn't seen before. Example: linear regression, Decision tree ⏎ KNN, SVM. |  |  |
| Chandra | 2), Supervised learning is the machine learning that train model with labeled data, that the correct output are known, then to predict the new output, of dataset that didn't seen before. Example: linear regression, Decision tree, KNN, SVM. |  |  |
| PaddleOCR | 2), Supervised learning is the machine learning that train model with labeled data, that the correct output. are known, then to predict the new output, of dataset. that didn't seen before. Example: linear regression, Decision tree KNN, SVM. |  |  |
| GLM-OCR | 2), Supervised learning is the machine learning that train model with labeled data, that the correct output. are known, then to predict the new output, of dataset. that didn't seen before. Example: linear regression, Decision tree KNN, SVM. |  |  |

### Q22 (S2) — teacher mark: 1.0

![S2](crops/Student_9/S2.jpg)
<sub>located on: Student_9_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 22. the model M2 are. good output for accuracy since. ⏎ the training set are more accuracy than testing dataset. |  |  |
| Chandra | , the model M_1 are good ~~st~~ output for accuracy since the training set data are more accuracy than testing dataset. |  |  |
| PaddleOCR | , the model ml are. good output for accuracy since. the training set are more accuracy than testing dataset. |  |  |
| GLM-OCR | the model ML are. good output For accuracy since. the training data set are more accuracy than testing dataset. |  |  |

### Q23 (S3) — teacher mark: 1.0

![S3](crops/Student_9/S3.jpg)
<sub>located on: Student_9_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 23, Regression analysis is the process between two attribute. ⏎ that can predict the another one if we know one. |  |  |
| Chandra | , Regression analysis is the process between two attribute. that can predict the another one if we know one. |  |  |
| PaddleOCR | , Regression analysis is the process between two attributes that can predict the another one if we know one. |  |  |
| GLM-OCR | Regression analysis is the process between two attribute that can predict the another one if we know one. |  |  |

### Q24 (S4) — teacher mark: 1.0

![S4](crops/Student_9/S4.jpg)
<sub>located on: Student_9_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 24. Two challenge of machine learning. ⏎ - the dataset are not well structure. ⏎ - didn't know the specific goal. |  |  |
| Chandra | Two challenges of machine learning. ⏎ - the dataset are not well structure. ⏎ - didn't know the specific goal. |  |  |
| PaddleOCR | No Challaange of Machine learning. ⏎ - the dataset are not well structured. ⏎ - didn't know the specific goal. |  |  |
| GLM-OCR | NO challaange of machine learning. ⏎ - the dataset are not well structure. ⏎ - didn't know the specific goal. |  |  |

### Q25 (S5) — teacher mark: 2.0

![S5](crops/Student_9/S5.jpg)
<sub>located on: Student_9_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 25 Two major application of data science: ⏎ - Finance. ⏎ - Health care. |  |  |
| Chandra | two major application of data science: ⏎  ⏎ - Finance. ⏎ - Health care. |  |  |
| PaddleOCR | two major application of data science. ⏎ - Finance. ⏎ - Health care. |  |  |
| GLM-OCR | Two major application of data science. ⏎ - Finance. ⏎ - Healthcare. |  |  |

### Q26 (S6) — teacher mark: 2.0

![S6](crops/Student_9/S6.jpg)
<sub>located on: Student_9_p4.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 26. Distinguish between the terms: structure and semi-structure data. ⏎ - Structured data: is the high level data, that is well prepare. ⏎ - Semi-structure: is the low level data, that the data still ⏎ have missing value, and not well prepared. |  |  |
| Chandra | Distinguish between the terms: structure and semi-structure data. ⏎ - Structured data: is the high level data, that is well prepared. ⏎ - Semi-structure is the low level data, that the data still have missing value, and not well prepared. ⏎  ⏎ These are discarded because it is |  |  |
| PaddleOCR | Distinguish between the terms: structure and semi-structure data. ⏎ - Structured data: is the high level data that is well prepared. ⏎ - Semi-structure is the low level data that the data still have missing value, and not well prepared. |  |  |
| GLM-OCR | Distinguish between the terms: structure and semi-structure data. ⏎ - Structured data: is the high level data, that is well prepared. ⏎ - Semi-structure: is the low level data, that the data still have missing value, and not Well prepared. |  |  |

### Q27 (S7) — teacher mark: 2.0

![S7](crops/Student_9/S7.jpg)
<sub>located on: Student_9_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 27) outlier is the data that abnormal from other structure. ⏎ data, we can find out by use the library of code. ⏎ which is box plot, |  |  |
| Chandra | Outlier is the data that abnormal from other structure. data, we can find out by use the library of code. which is box plot, |  |  |
| PaddleOCR | Outlier is the data that abnormal from other structure. ⏎ data, we can find out by use the library of code. ⏎ which is box plot, |  |  |
| GLM-OCR | Outlier is the data that abnormal from other structure. ⏎ data, we can find out by use the library of code. ⏎ which is box plot, |  |  |

### Q28 (S8) — teacher mark: 1.0

![S8](crops/Student_9/S8.jpg)
<sub>located on: Student_9_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | KNN, SVM. ⏎ 28. Data pre-processing is the process of taking raw data, ⏎ transform to format data, that can be understand ⏎ and analyzed by computer. |  |  |
| Chandra | KNN, SVM. ⏎  ⏎ 28. Data pre-processing is the process of taking raw data, transform to format data, that can be understand and analyzed by computer. |  |  |
| PaddleOCR | KNN, SVM. ⏎ 28. Data pre-processing is the process of taking raw data, ⏎ transform to format data, that can be understand. ⏎ and analyzed by computer. |  |  |
| GLM-OCR | Data pre-processing is the process of taking raw data transform to format data, that can be understand and analyzed by computer. |  |  |

### Q29 (S9) — teacher mark: 2.0

![S9](crops/Student_9/S9.jpg)
<sub>located on: Student_9_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 29. the data normalization is required in KNN because it need. ⏎ to scaling data and it can represent within smaller range. |  |  |
| Chandra | 2g. the data normalization is required in KNN because it need to scaling data and it can represent within smaller range. |  |  |
| PaddleOCR | 2g. the data normalization is required in KNN because it need to scaling data and it can represent within smaller range. |  |  |
| GLM-OCR | the data normalization is required in KNN because it need to scaling data and it can represent within smaller range. |  |  |

### Q30 (S10) — teacher mark: 1.0

![S10](crops/Student_9/S10.jpg)
<sub>located on: Student_9_p4.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 30. the continuous attribute are discretized because it is ⏎ need to transform to set of data interval. |  |  |
| Chandra | have missing value, and not well defined. ⏎ 30, the continuous attribute are discretized because it is need to transform to set of data interval. ⏎  ⏎ time learning algorithm. |  |  |
| PaddleOCR | , the continuous attribute are discretized because it is need to transform to set of data interval. |  |  |
| GLM-OCR | have missing value, and not the continuous attribute are discretized because it is need to transform to set of data interval. |  |  |

### Q31 (S11) — teacher mark: 1.0

![S11](crops/Student_9/S11.jpg)
<sub>located on: Student_9_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 31. K in K-mean algorithm is represent Variable of number. ⏎ that it can be express from 1 to 10. |  |  |
| Chandra | K in K-mean algorithm is represent variable of number that it can be express from 1 to 10. |  |  |
| PaddleOCR | K in K-mean algorithm is represent.Variable of number. ⏎ that it can be express from 1 to 20. |  |  |
| GLM-OCR | K in K-mean algorithm is represent Variable of number that it can be express from 1 to 10. |  |  |

### Q32 (S12) — teacher mark: 0.0

![S12](crops/Student_9/S12.jpg)
<sub>located on: Student_9_p4.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 32, hyperparameters of machine learning algorithm. ⏎ - low level hyperparameters. ⏎ - medium level hyperparameter. |  |  |
| Chandra | need to train. ⏎  ⏎ 32, hyperparameters of machine learning algorithm. ⏎  ⏎ - low level hyper parameter. ⏎ - medium level hyper parameter. |  |  |
| PaddleOCR | , hyperparameters of machine learning algorithm. ⏎ - low level hyper parameter. ⏎ - medium level hyper parameter. |  |  |
| GLM-OCR | hyperparameters of machine learning algorithm. ⏎ - low level hyper parameter. ⏎ - medium level hyper parameter. |  |  |

### Q33 (S13) — teacher mark: 1.0

![S13](crops/Student_9/S13.jpg)
<sub>located on: Student_9_p4.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | - medium level hyper parameter. ⏎ - high level hyper parameter. ⏎ 20. gradient descent is the the data got error while processing. |  |  |
| Chandra | - medium level hyper parameter. ⏎  ⏎ - high level hyper parameter. ⏎  ⏎ Gradient descent is the the data got error while processing. |  |  |
| PaddleOCR | - medium level hyper parameter. ⏎ - high level hyper parameter. ⏎ - constant descent is the data got error while processing. |  |  |
| GLM-OCR | - medium level hyper parameter ⏎ - high level hyper parameter |  |  |

### Q34 (S14) — teacher mark: 2.0

![S14](crops/Student_9/S14.jpg)
<sub>located on: Student_9_p4.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 35, it's set the data and preference the best data. ⏎ 34. Comment on performance of classifiers. ⏎ - First the boundary are near the line so it's not a good performance. ⏎ - Second the boundary are in the line so it's also not a good performance. ⏎ - third the boundary are far from line so it's a good performance. |  |  |
| Chandra | 35, it's set the data and preference the best data. ⏎  ⏎ 34. Comment on performance of classifiers. ⏎  ⏎ - First the boundary are near the line so it's not a good performance. ⏎  ⏎ - Second the boundary are in the line so it's also not a good performance. ⏎  ⏎ - Third the boundary are far from line so it's a good performance. |  |  |
| PaddleOCR | 35, it's set the data and preference the best data. ⏎ 34. Comment on performance of classifiers. ⏎ - First the boundary are near the line so it's not a good performance. ⏎ - Second the boundary are in the line so it's also not a good performance. ⏎ - Third the boundary are far from line so it's a good performance. |  |  |
| GLM-OCR | 35. it's set the data and preference the best data. ⏎ 34. Comment on performance of classifiers. ⏎ - First the boundary are near the line so it's not a good performance. ⏎ - Second the boundary are in the line so it's also not a good performance. ⏎ - Third the boundary are far from line so it's a good performance. |  |  |

### Q35 (S15) — teacher mark: 0.0

![S15](crops/Student_9/S15.jpg)
<sub>located on: Student_9_p4.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 33. gradient descent is the the data got error while ⏎ 25 it's set the data and preference the best data. |  |  |
| Chandra | 33, - high level hyper parameter. ⏎ gradient descent is the the data got error while ⏎  ⏎ 25 it's set the data and preference the best data. |  |  |
| PaddleOCR | 33. gradient descent is the data got error while it's set the data and preference the best data. |  |  |
| GLM-OCR | 33. gradient descent is the the data got error while it's set the data and preference the best data. |  |  |
