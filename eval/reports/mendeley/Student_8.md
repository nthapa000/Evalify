# Student_8 — reader comparison

Pages read: Student_8_p1.png, Student_8_p2.png, Student_8_p3.png  
Skipped as blank / show-through backs: Student_8_p4.png  
Answers located by the segmenter: 30/35  
Visual check by Claude: not yet

Page images: `eval/data/mendeley/images/` · crops: `eval/reports/mendeley/crops/` (local, not in git).

## MCQ (gold = letter in the teacher's CSV)

| Q | crop | gold | Qwen3.8 | Chandra | PaddleOCR | GLM-OCR | note |
|---|---|---|---|---|---|---|---|
| Q1 | ![Q1](crops/Student_8/Q1.jpg) | **D** | D ✅ | D ✅ | D ✅ | D ✅ |  |
| Q2 | ![Q2](crops/Student_8/Q2.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q3 | ![Q3](crops/Student_8/Q3.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q4 | ![Q4](crops/Student_8/Q4.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q5 | ![Q5](crops/Student_8/Q5.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q6 | ![Q6](crops/Student_8/Q6.jpg) | **A** | ∅ | A ✅ | A ✅ | A ✅ |  |
| Q7 | ![Q7](crops/Student_8/Q7.jpg) | **A** | ∅ | A ✅ | A ✅ | A ✅ |  |
| Q8 | ![Q8](crops/Student_8/Q8.jpg) | **C** | ∅ | C ✅ | C ✅ | C ✅ |  |
| Q9 | ![Q9](crops/Student_8/Q9.jpg) | **C** | ∅ | C ✅ | C ✅ | C ✅ |  |
| Q10 | ![Q10](crops/Student_8/Q10.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q11 | ![Q11](crops/Student_8/Q11.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q12 | ![Q12](crops/Student_8/Q12.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q13 | ![Q13](crops/Student_8/Q13.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q14 | ![Q14](crops/Student_8/Q14.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q15 | ![Q15](crops/Student_8/Q15.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q16 | ![Q16](crops/Student_8/Q16.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q17 | ![Q17](crops/Student_8/Q17.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q18 | ![Q18](crops/Student_8/Q18.jpg) | **C** | C ✅ | C ✅ | ∅ | C ✅ |  |
| Q19 | ![Q19](crops/Student_8/Q19.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q20 | ![Q20](crops/Student_8/Q20.jpg) | **D** | ∅ | D ✅ | D ✅ | D ✅ |  |

Correct per reader: Qwen3.8 15/20, Chandra 20/20, PaddleOCR 19/20, GLM-OCR 20/20

## Short answers (Q21–Q35)

Teacher mark is from the CSV (out of 2). CER/WER are against Claude's transcript where one exists (lower = better; struck-out text, punctuation, case and the question label are ignored).

### Q21 (S1) — teacher mark: 2.0

![S1](crops/Student_8/S1.jpg)
<sub>located on: Student_8_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 21) Supervised learning is used to model relationship and dependencies ⏎ between the target per prediction output and input features. ⏎ Based on the relationship of previous dataset, we can ~~find~~ predict new values. ⏎ Data Science is used in Finance and Health care industry. |  |  |
| Chandra | 31) K ( ) ⏎ 21) Supervised learning is used to model relationship and dependencies between the target ~~per~~ prediction output and input features. Based on the relationship of previous dataset, we can ~~find~~ predict new value. ⏎ 23) Data Science is used in Finance and Health care industry. |  |  |
| PaddleOCR | 31) Supervised learning is used to model relationship and dependencies between the target per prediction output and input features. Based on the relationship of previous dataset, we can find predict new values. Data Science is used in Finance and Health Care Industry. |  |  |
| GLM-OCR | Supervised learning is used to model relationship and dependencies between the target per prediction output and input features Based on the relationship of previous dataset, we can predict new value. Data Science is used in Finance and Health care industry. |  |  |

### Q22 (S2) — teacher mark: None

_answer not located_
<sub>located on: —</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | ∅ |  |  |
| Chandra | ∅ |  |  |
| PaddleOCR | ∅ |  |  |
| GLM-OCR | ∅ |  |  |

### Q23 (S3) — teacher mark: None

_answer not located_
<sub>located on: —</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | ∅ |  |  |
| Chandra | ∅ |  |  |
| PaddleOCR | ∅ |  |  |
| GLM-OCR | ∅ |  |  |

### Q24 (S4) — teacher mark: 1.0

![S4](crops/Student_8/S4.jpg)
<sub>located on: Student_8_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 24  2 challenges of ML ⏎ - work with huge dataset ⏎ - |  |  |
| Chandra | 2 challenges of ML ⏎ - work with huge dataset ⏎ - |  |  |
| PaddleOCR | 2 challenges of mL ⏎ - work with huge dataset |  |  |
| GLM-OCR | 2 challenges of ML ⏎ - work with huge dataset ⏎ - |  |  |

### Q25 (S5) — teacher mark: 2.0

![S5](crops/Student_8/S5.jpg)
<sub>located on: Student_8_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | between the target per prediction value, ⏎ Based on the relationship of previous dataset, we can find prediction value. ⏎ 25) Data Science is used in Finance and Health Care industry. |  |  |
| Chandra | between the target and prediction. Based on the relationship of previous dataset, we can find previous value. ⏎  ⏎ 25) Data Science is used in Finance and Health care Industry. |  |  |
| PaddleOCR | 1 Data Science is used in Finance and Health Care Industry. |  |  |
| GLM-OCR | between the target per prediction Based on the relationship of previous dataset, we can find value. Data Science is used in Finance and Health care industry. |  |  |

### Q26 (S6) — teacher mark: 2.0

![S6](crops/Student_8/S6.jpg)
<sub>located on: Student_8_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 32) max depth tree, min dep ⏎ 26) Structured data is well structured and can understand ⏎ It includes csv files, db --- ⏎ Semi-structured need to transform to structured data. ⏎ It includes Json file, XML --- |  |  |
| Chandra | 32) max depth tree, min dep... ⏎ 26) structured data is well structured ~~and can understand~~ ⏎ It includes csv files, db - ... ⏎ Semi-structured need to transform to structured data. ⏎ It includes json file, XML - ... |  |  |
| PaddleOCR | 32) max depth tree, min acp ⏎ 26) Structured data Ts well structured and can understand ⏎ It includes csv files, db... ⏎ Semi-structured need to transform to structured data ⏎ It includes JSON file, XML... |  |  |
| GLM-OCR | 32) max depth tree, min ⏎ 26) Structured data is well structured and can understand ⏎ It includes csv files, db ... ⏎ Semi-structured need to transform to structured data. ⏎ It includes json file, xml ... |  |  |

### Q27 (S7) — teacher mark: 1.0

![S7](crops/Student_8/S7.jpg)
<sub>located on: Student_8_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 27) To find an outlier in data, we can use : ⏎ - statistical method (z-score) ⏎ - Distance based method ⏎ - Density based method ⏎ - Clustering based method ⏎ - Classification based method ⏎ - Neural Network based method |  |  |
| Chandra | 25) Data Science ⏎  ⏎ 27) To find an outlier in data, we can use : ⏎  ⏎ - Statistical method (z-score) ⏎ - Distance based method ⏎ - Density based method ⏎ - Clustering based method ⏎ - Classification based method ⏎ - Neural Network based method ⏎  ⏎ transform data into |  |  |
| PaddleOCR | 251 Data science ⏎ 271 To find an outlier in data, we can use: ⏎ - Statistical method (Z-score) ⏎ - Distance based method ⏎ - Density based method ⏎ - Clustering based method ⏎ - Classification based method ⏎ - Neural Network based method ⏎ transform data into |  |  |
| GLM-OCR | 251 Data science ⏎  ⏎ 271 To find an outlier in data, we can use: ⏎ - Statistical method (z-score) ⏎ - Distance based method ⏎ - Density based method ⏎ - Clustering based method ⏎ - Classification based method ⏎ - Neural network based method |  |  |

### Q28 (S8) — teacher mark: 1.0

![S8](crops/Student_8/S8.jpg)
<sub>located on: Student_8_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 28) Data pre-processing is a phase where we transform data into ⏎ format that can be understand by computer. ⏎ to scale the value of the variable to be |  |  |
| Chandra | - Neural Network based ⏎  ⏎ 28) Data pre-processing is a phase where we transform data into format that can be understood by computer. ⏎  ⏎ 1. to scale the value of the variable to be |  |  |
| PaddleOCR | 7) Neural Network based on Data pre-processing is a phase where net transform data into format that can be understand by computer. |  |  |
| GLM-OCR | Data pre-processing is a phase where we transform data into format that can be understand by computer. the value of variable to be |  |  |

### Q29 (S9) — teacher mark: 2.0

![S9](crops/Student_8/S9.jpg)
<sub>located on: Student_8_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 29) Because we want to scale the value of the variable to be ⏎ similar. ⏎ used to find coefficient. |  |  |
| Chandra | 28) Data pre-processing ⏎ format that can be understood by computers. ⏎  ⏎ 29) Because we want to scale the value of the variable to be similar. ⏎  ⏎ \mu is used to find coefficient. |  |  |
| PaddleOCR | format that can be understand by the ⏎ Because we want to scale the value of variable to be ⏎ similar. |  |  |
| GLM-OCR | format that can be understand by the Because we want to scale the value of variable to be similar. used to find coefficient. |  |  |

### Q30 (S10) — teacher mark: None

_answer not located_
<sub>located on: —</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | ∅ |  |  |
| Chandra | ∅ |  |  |
| PaddleOCR | ∅ |  |  |
| GLM-OCR | ∅ |  |  |

### Q31 (S11) — teacher mark: 1.0

![S11](crops/Student_8/S11.jpg)
<sub>located on: Student_8_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 31) K is user specified parameter. ⏎ 21) Superrvised learning is used to model relationship and dependencies ⏎ between the target per prediction output and input features. ⏎ Based on the relationship of previous dataset, we can predict new value. ⏎ and Health care industry. |  |  |
| Chandra | 20) K is user specified parameter. ⏎  ⏎ 21) Supervised learning is used to model relationship and dependencies between the target ~~per~~ prediction output and input features. Based on the relationship of previous dataset, we can ~~find~~ predict new value. ⏎  ⏎ Source and Health care industry. |  |  |
| PaddleOCR | 201 ⏎ 31) K is user specified parameter. ⏎ 21) Supervised learning is used to model relationship and dependencies between the target per prediction output and input features. Based on the relationship of previous dataset, we can find predict new values and Health care industry. |  |  |
| GLM-OCR | 21) Supervised learning is used to model relationship and dependencies between the target per prediction output and input features Based on the relationship of previous dataset, we can predict new value. |  |  |

### Q32 (S12) — teacher mark: 2.0

![S12](crops/Student_8/S12.jpg)
<sub>located on: Student_8_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 33) Gradient Descent is used to find coeffi ⏎ 32) max depth tree, min depth tree and can be used for data ⏎ analysis. ⏎ is well structured and can understand |  |  |
| Chandra | 33) Gradient Descent is used to find coefficients ⏎ 32) max depth tree, min depth tree and can be used for data analysis. ⏎ Decision tree is well structured and ~~can~~ understand |  |  |
| PaddleOCR | 331 Gradient Descent is used to find cost for data analysis. ⏎ 32) max depth tree, min depth tree and can be used for data analysis. |  |  |
| GLM-OCR | 331 Gradient Descent is used to find coefficient ⏎ 32) max depth tree, min depth tree and can be used for data analysis. |  |  |

### Q33 (S13) — teacher mark: 0.0

![S13](crops/Student_8/S13.jpg)
<sub>located on: Student_8_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 33) Gradient Descent is used to find coefficient. |  |  |
| Chandra | similar. ⏎  ⏎ 33) Gradient Descent is used to find coefficient. ⏎  ⏎ It can be used |  |  |
| PaddleOCR | 1 \| Similar. Gradient Descent is used to find coefficient. |  |  |
| GLM-OCR | similar. ⏎ 331 Gradient Descent is used to find coefficient. |  |  |

### Q34 (S14) — teacher mark: None

_answer not located_
<sub>located on: —</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | ∅ |  |  |
| Chandra | ∅ |  |  |
| PaddleOCR | ∅ |  |  |
| GLM-OCR | ∅ |  |  |

### Q35 (S15) — teacher mark: None

_answer not located_
<sub>located on: —</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | ∅ |  |  |
| Chandra | ∅ |  |  |
| PaddleOCR | ∅ |  |  |
| GLM-OCR | ∅ |  |  |
