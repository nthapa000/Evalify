# Student_12 — reader comparison

Pages read: Student_12_p1.png, Student_12_p2.png, Student_12_p3.png, Student_12_p4.png  
Skipped as blank / show-through backs: none  
Answers located by the segmenter: 32/35  
Visual check by Claude: MCQ only / disagreements

Page images: `eval/data/mendeley/images/` · crops: `eval/reports/mendeley/crops/` (local, not in git).

> Only the MCQ answers where a reader disagreed with the teacher CSV were checked by eye on this sheet.

## MCQ (gold = letter in the teacher's CSV)

| Q | crop | gold | Qwen3.8 | Chandra | PaddleOCR | GLM-OCR | note |
|---|---|---|---|---|---|---|---|
| Q1 | ![Q1](crops/Student_12/Q1.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q2 | ![Q2](crops/Student_12/Q2.jpg) | **D** | ∅ | D ✅ | D ✅ | ∅ | SEGMENTATION ERROR: the crop shows a block of answer text, not Q2. |
| Q3 | ![Q3](crops/Student_12/Q3.jpg) | **D** | ∅ | ∅ | D ✅ | C ❌ | SEGMENTATION ERROR: the crop shows the Q33 'Gradient descent…' answer; a stray 'D' at its corner was read. |
| Q4 | ![Q4](crops/Student_12/Q4.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q5 | ![Q5](crops/Student_12/Q5.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q6 | ![Q6](crops/Student_12/Q6.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q7 | ![Q7](crops/Student_12/Q7.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q8 | ![Q8](crops/Student_12/Q8.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q9 | ![Q9](crops/Student_12/Q9.jpg) | **D** | ∅ | ∅ | D ✅ | ∅ | 'Ɗ'-style D; CSV right. |
| Q10 | ![Q10](crops/Student_12/Q10.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q11 | ![Q11](crops/Student_12/Q11.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q12 | ![Q12](crops/Student_12/Q12.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q13 | ![Q13](crops/Student_12/Q13.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q14 | ![Q14](crops/Student_12/Q14.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q15 | ![Q15](crops/Student_12/Q15.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q16 | ![Q16](crops/Student_12/Q16.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q17 | ![Q17](crops/Student_12/Q17.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q18 | ![Q18](crops/Student_12/Q18.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q19 | ![Q19](crops/Student_12/Q19.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q20 | ![Q20](crops/Student_12/Q20.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |

Correct per reader: Qwen3.8 17/20, Chandra 18/20, PaddleOCR 20/20, GLM-OCR 17/20

## Short answers (Q21–Q35)

Teacher mark is from the CSV (out of 2). CER/WER are against Claude's transcript where one exists (lower = better; struck-out text, punctuation, case and the question label are ignored).

### Q21 (S1) — teacher mark: None

![S1](crops/Student_12/S1.jpg)
<sub>located on: Student_12_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | data into higher dimension like polynomial. ⏎ 21. supervised learning is a machine learning algorithm that ⏎ take the label input data as input and train the data and ⏎ make prediction based on the previous dataset. |  |  |
| Chandra | data into higher dimension like polynomial. ⏎  ⏎ 21. supervised learning is a machine learning algorithm that take the label input data as input and train the data and make prediction based on the previous dataset. |  |  |
| PaddleOCR | data into higher dimension like polynomial. ⏎ 21. supervised learning is a machine learning algorithm that ⏎ take the label input data as input and train the data and ⏎ make prediction based on the previous dataset. |  |  |
| GLM-OCR | supervised learning is a machine learning algorithm that take the label input data as input and train the data and make prediction based on the previous dataset. |  |  |

### Q22 (S2) — teacher mark: 1.0

_answer not located_
<sub>located on: —</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | ∅ |  |  |
| Chandra | ∅ |  |  |
| PaddleOCR | ∅ |  |  |
| GLM-OCR | ∅ |  |  |

### Q23 (S3) — teacher mark: 1.0

![S3](crops/Student_12/S3.jpg)
<sub>located on: Student_12_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | - R2-score ⏎ 23. Regression analysis is the process of analyzing the ⏎ numerical data. |  |  |
| Chandra | - R2-score ⏎  ⏎ 23. Regression analysis is the process of analyzing the numerical data. |  |  |
| PaddleOCR | Regression analysis is the process of analyzing the numerical data. |  |  |
| GLM-OCR | Regression analysis is the process of analyzing the numerical data. |  |  |

### Q24 (S4) — teacher mark: 2.0

![S4](crops/Student_12/S4.jpg)
<sub>located on: Student_12_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 24. Two challenges of Machine learning: ⏎ - Model not accuracy ⏎ - wrong prediction due to data not cleanse |  |  |
| Chandra | numerical data. ⏎  ⏎ 24. Two challenges of Machine learning: ⏎ - Model not accuracy ⏎ - wrong prediction due to data not cleanse ⏎  ⏎ ... same structure data: |  |  |
| PaddleOCR | Two challenges of Machine learning: ⏎ - Model not accuracy ⏎ - wrong prediction due to data not cleanse |  |  |
| GLM-OCR | Two challenges of Machine learning: ⏎ - Model not accuracy ⏎ - wrong prediction due to data not cleanse |  |  |

### Q25 (S5) — teacher mark: 2.0

![S5](crops/Student_12/S5.jpg)
<sub>located on: Student_12_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | make prediction based on the ⏎ 25. Two major applications of ⏎ - House price prediction ⏎ - chatbot language detection |  |  |
| Chandra | make prediction based on the ⏎ 25. Two major applications of ⏎ - House price prediction ⏎ - chatbot language detection |  |  |
| PaddleOCR | Two major applications at ⏎ - House price prediction ⏎ - Chatbot language detection |  |  |
| GLM-OCR | Two major applications of ⏎ - House price prediction ⏎ - chatbot language detection |  |  |

### Q26 (S6) — teacher mark: 2.0

![S6](crops/Student_12/S6.jpg)
<sub>located on: Student_12_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | - wrong prediction due to data not cleanse ⏎ 26. structured and semi-structure data: ⏎ - structured is a well define land place in at table ⏎ for mat. Ex: RDBMS, spread sheet. ⏎ - semi-structure data is a well define data but not in ⏎ a tabular format. Ex: XML, HTML. |  |  |
| Chandra | - wrong prediction due to data not cleanse ⏎ 26. structured and semi-structure data: ⏎ - structured is a well define land place in at table format. EX: RDBMS, spreadsheet. ⏎ - semi-structure data is a well define data but not in a tabular format. EX: XML, HTML. |  |  |
| PaddleOCR | - wrong prediction due to data not cleanse ⏎ 26. structured and semi-structure data: ⏎ - structured is a well define and place in at table ⏎ for mat.Ex: RDBAs, spread sheet. ⏎ - semi-structure data is a well define data but not in ⏎ a tabular format.Ex: XML, HTML. |  |  |
| GLM-OCR | structured and semi-structure data: ⏎ - structured is a well define and place in at table for mat. EX: RDBAS, spread sheet. ⏎ - semi-structure data is a well define data but not in a tabular format. EX: XML, HTML. |  |  |

### Q27 (S7) — teacher mark: 2.0

![S7](crops/Student_12/S7.jpg)
<sub>located on: Student_12_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 27. There are two ways to find an outlier: ⏎ - Box plot ⏎ - Scatter plot |  |  |
| Chandra | Section 2 ⏎ 27. There are two ways to find an outlier: ⏎ - Box plot ⏎ - Scatter plot |  |  |
| PaddleOCR | There are two ways to find an outlier: ⏎ - Box Plot ⏎ - Scatter Plot |  |  |
| GLM-OCR | There are two ways to find an outlier: ⏎ - Box Plot ⏎ - Scatter plot |  |  |

### Q28 (S8) — teacher mark: 1.5

![S8](crops/Student_12/S8.jpg)
<sub>located on: Student_12_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | a tabular format. Ex: XML, HTML. ⏎ 28. Data pre-processing is the process of cleaning data and ⏎ make the dataset ready to use by machine learning. |  |  |
| Chandra | a tabular format. Ex: XML, HTML. ⏎  ⏎ 28. Data pre-processing is the process of cleaning data and make the dataset ready to use by machine learning. |  |  |
| PaddleOCR | a tabular format. Ex: XML, HTML. ⏎ Data pre-processing is the process of cleaning data and make the dataset ready to use by machine learning. |  |  |
| GLM-OCR | a tabular format. EX: XML, HTML. ⏎ 28. Data pre-processing is the process of cleaning data and make the dataset ready to use by machine learning. |  |  |

### Q29 (S9) — teacher mark: 2.0

![S9](crops/Student_12/S9.jpg)
<sub>located on: Student_12_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | eg. Data normalization is required in K-NN because some data ⏎ point is too big and hard to handle therefore we need to ⏎ make our data into a smaller range. |  |  |
| Chandra | Data normalization is required in K-NN because some data point is too big and hard to handle therefore we need to make our data into a smaller range. |  |  |
| PaddleOCR | Data normalization is required in KNN because some data point is too big and hard to handle there for we need to make our data into a smaller range. |  |  |
| GLM-OCR | Data normalization is required in K-NN because some data point is too big and hard to handle therefore we need to make our data into a smaller range. |  |  |

### Q30 (S10) — teacher mark: 1.0

_answer not located_
<sub>located on: —</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | ∅ |  |  |
| Chandra | ∅ |  |  |
| PaddleOCR | ∅ |  |  |
| GLM-OCR | ∅ |  |  |

### Q31 (S11) — teacher mark: 2.0

![S11](crops/Student_12/S11.jpg)
<sub>located on: Student_12_p2.png, Student_12_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 31. K in k-means algorithm is the number of partition to be ⏎ devided out data into. ⏎ 31. ~~K-means algorithm is a clustering problem that~~ |  |  |
| Chandra | k in k-means algorithm is the number of partition to be divided out data into. ⏎ 31. ~~K-means algorithm is a clustering problem that~~ |  |  |
| PaddleOCR | k in k-means algorithm is the number of partition to be devised out data into. ⏎ 31. H-means algorithm is a clustering problem that |  |  |
| GLM-OCR | K in k-means algorithm is the number of partition to be divided out data into. ⏎ 31. H-means algorithm is a clustering problem that |  |  |

### Q32 (S12) — teacher mark: 1.0

![S12](crops/Student_12/S12.jpg)
<sub>located on: Student_12_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 32. Few hyperparameters of machine learning algorithm: ⏎ - n-estimator ⏎ - RMSE ⏎ - R2-score |  |  |
| Chandra | Few hyperparameters of machine learning algorithm: ⏎  ⏎ - n_estimator ⏎ - RMSE ⏎ - R^2-score |  |  |
| PaddleOCR | Few hyperparameters of machine learning algorithm: ⏎ - n-estimator ⏎ - RMSE ⏎ - R2-score |  |  |
| GLM-OCR | few hyperparameters of machine learning algorithm: ⏎ - n-estimator ⏎ - RMSE ⏎ - R2-score |  |  |

### Q33 (S13) — teacher mark: 0.5

_answer not located_
<sub>located on: —</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | ∅ |  |  |
| Chandra | ∅ |  |  |
| PaddleOCR | ∅ |  |  |
| GLM-OCR | ∅ |  |  |

### Q34 (S14) — teacher mark: 1.5

![S14](crops/Student_12/S14.jpg)
<sub>located on: Student_12_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 34. -For the first classification, is the best performance since the ⏎ distance between two line is far and their is no data ⏎ point in between the line. ⏎ - For second and third classification is not really good since ⏎ the lines are near to each other and their are points in ⏎ between the line. |  |  |
| Chandra | - For the first classification, is the best performance since the distance between two line is far and there is no data point in between the line. ⏎  ⏎ - For second and third classification is not really good since the lines are near to each other and there are points in between the line. |  |  |
| PaddleOCR | For the first classification, is the best performance since the distance between two line is far and their is no data point in between the line. ⏎ For second and third classification is not really good since the lines are near to each other and their are points in between the line. |  |  |
| GLM-OCR | - For the first classification, is the best performance since the distance between two line is far and their is no data point in between the line. ⏎ - For second and third classification is not really good since the lines are near to each other and their are points in between the line. |  |  |

### Q35 (S15) — teacher mark: 1.5

![S15](crops/Student_12/S15.jpg)
<sub>located on: Student_12_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | between the line. ⏎ 35. Radial Basis function kernel will turn the dimension of the ⏎ data into higher dimension like polynomial. ⏎ Supervised learning is a machine learning algorithm that |  |  |
| Chandra | between the line. ⏎  ⏎ 35. Radial Basis function kernel will turn the dimension of the data into higher dimension like polynomial. ⏎  ⏎ 9. Supervised learning is a machine learning algorithm that |  |  |
| PaddleOCR | Radial Basis function kernel will turn the dimension of the data into higher dimension like polynomial. |  |  |
| GLM-OCR | Radial Basis function kernel will turn the dimension of the data into higher dimension like polynomial. |  |  |
