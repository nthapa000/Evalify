# Student_4 — reader comparison

Pages read: Student_4_p1.png, Student_4_p2.png, Student_4_p3.png  
Skipped as blank / show-through backs: Student_4_p4.png  
Answers located by the segmenter: 35/35  
Visual check by Claude: MCQ only / disagreements

Page images: `eval/data/mendeley/images/` · crops: `eval/reports/mendeley/crops/` (local, not in git).

> Only the MCQ answers where a reader disagreed with the teacher CSV were checked by eye on this sheet.

## MCQ (gold = letter in the teacher's CSV)

| Q | crop | gold | Qwen3.8 | Chandra | PaddleOCR | GLM-OCR | note |
|---|---|---|---|---|---|---|---|
| Q1 | ![Q1](crops/Student_4/Q1.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q2 | ![Q2](crops/Student_4/Q2.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q3 | ![Q3](crops/Student_4/Q3.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q4 | ![Q4](crops/Student_4/Q4.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q5 | ![Q5](crops/Student_4/Q5.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q6 | ![Q6](crops/Student_4/Q6.jpg) | **C** | ∅ | ∅ | C ✅ | C ✅ | Plain 'C' that looks a bit like 'L'; CSV right; Qwen and Chandra abstained. |
| Q7 | ![Q7](crops/Student_4/Q7.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q8 | ![Q8](crops/Student_4/Q8.jpg) | **C** | ∅ | C ✅ | C ✅ | C ✅ |  |
| Q9 | ![Q9](crops/Student_4/Q9.jpg) | **A** | ∅ | A ✅ | A ✅ | A ✅ |  |
| Q10 | ![Q10](crops/Student_4/Q10.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q11 | ![Q11](crops/Student_4/Q11.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q12 | ![Q12](crops/Student_4/Q12.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q13 | ![Q13](crops/Student_4/Q13.jpg) | **B** | ∅ | B ✅ | B ✅ | B ✅ |  |
| Q14 | ![Q14](crops/Student_4/Q14.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q15 | ![Q15](crops/Student_4/Q15.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q16 | ![Q16](crops/Student_4/Q16.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q17 | ![Q17](crops/Student_4/Q17.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q18 | ![Q18](crops/Student_4/Q18.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q19 | ![Q19](crops/Student_4/Q19.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q20 | ![Q20](crops/Student_4/Q20.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |

Correct per reader: Qwen3.8 16/20, Chandra 19/20, PaddleOCR 20/20, GLM-OCR 20/20

## Short answers (Q21–Q35)

Teacher mark is from the CSV (out of 2). CER/WER are against Claude's transcript where one exists (lower = better; struck-out text, punctuation, case and the question label are ignored).

### Q21 (S1) — teacher mark: 2.0

![S1](crops/Student_4/S1.jpg)
<sub>located on: Student_4_p1.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | Answer all Question ⏎ 21. Supervised Learning is the machine Learning algorithm ⏎ in which dataset is label for the model so that it have ⏎ has the target to predict. |  |  |
| Chandra | Answer all Question ⏎ 21. Supervised Learning is the machine learning algorithm in which dataset is label for the model so that it have has the target to predict. |  |  |
| PaddleOCR | Supercruised Learning is the machine learning algorithm in which dataset is labeled for the model so that it has the target to predict. |  |  |
| GLM-OCR | Supervised Learning is the machine learning algorithm in which dataset is label for the model so that it have has the target to predict. |  |  |

### Q22 (S2) — teacher mark: 2.0

![S2](crops/Student_4/S2.jpg)
<sub>located on: Student_4_p1.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | has the target to predict. ⏎ 22. Model M1 seem do be overfitted that's the reason ⏎ that is so well in predict the data on the train set ⏎ however it's so poorly predict what they haven't train ⏎ which is not good for real time prediction. |  |  |
| Chandra | has the target to predict. ⏎  ⏎ 22. Model M1 seem to be overfitted that's the reason that is so well in predict the data on the train set however it's so poorly predict what they haven't train which is not good for real time prediction. |  |  |
| PaddleOCR | Model M1 seem to be overfitted that's the reason that is so well in predict the data on the train set however it's so poorly predict what they haven't train which is not good for real time prediction. |  |  |
| GLM-OCR | Model M1 seem to be overfitted that 's the reason that is so well in predict the data on the train set however it's so poorly predict what they haven't train which is not good for real time prediction. |  |  |

### Q23 (S3) — teacher mark: 1.0

![S3](crops/Student_4/S3.jpg)
<sub>located on: Student_4_p1.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 23. Regression analysis is the process of choosing ⏎ and reducing the feature in the dataset so that it ⏎ can increase the accuracy of the ML model. |  |  |
| Chandra | Regression analysis is the process of choosing and reducing the feature in the dataset so that it can increase the accuracy of the ML model. |  |  |
| PaddleOCR | 2.3. Regression analysis is the process of choosing and reducing the feature in the dataset so that it can increase the accuracy of the ML model. |  |  |
| GLM-OCR | Regression analysis is the process of choosing and reducing the feature in the dataset so that it can increase the accuracy of the ML model. |  |  |

### Q24 (S4) — teacher mark: 2.0

![S4](crops/Student_4/S4.jpg)
<sub>located on: Student_4_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 24. The challenges in Machine Learning are to find the data ⏎ set to train the model and to know which model is best for ⏎ the problem that we're solving. |  |  |
| Chandra | The challenges in Machine Learning are to find the data set to train the model and to know which model is best for the problem that we're solving. |  |  |
| PaddleOCR | The challenges in machine learning are to find the data set to train the model and to know which model is best for the problem that we're solving. |  |  |
| GLM-OCR | The challenges in Machine Learning are to find the data set to train the model and to know which model is best for the problem that we're solving. |  |  |

### Q25 (S5) — teacher mark: 2.0

![S5](crops/Student_4/S5.jpg)
<sub>located on: Student_4_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 25. Major applications of data science : ⏎ - Health-Care : with enough data data scientist can use ⏎ Machine Learning to predict and prevent the patient from ⏎ heart attack or detect any symptom of some serious illness. ⏎ also they can use machine learning to come up with new cure for ⏎ new diseases. ⏎ - ~~Self-driving car: with~~ the o. ⏎ - Artificial Intelligeny: with machine learning we can create ⏎ intelligent machine which know and sometime thinks like human. ⏎ 26. Structured data |  |  |
| Chandra | Major applications of data science: ⏎  ⏎ - Health-Care: with enough data data scientist can use Machine Learning to predict and prevent the patient from heart attack or detect any symptom of some serious illness. also they can use machine learning to come up with new cure for new diseases. ⏎  ⏎ ~~- Self-driving car: with the v.~~ ⏎  ⏎ - Artificial Intelligent: with machine learning we can create intelligent machine which know and sometime thinks like human. ⏎  ⏎ 26. Structured data is the organized data. |  |  |
| PaddleOCR | Major applications of data science: ⏎ - Health-Care: with enough data data scientist can use ⏎ Machine Learning to predict and prevent the patient from ⏎ heart attack or defect any symptom of some serious illness. ⏎ also they can use machine learning to come up with new core for ⏎ new diseases. ⏎ - Self-driving car: with the ⏎ - Artificial Intelligence: with machine learning we can create ⏎ intelligent machine which knows and sometimes thinks like human. |  |  |
| GLM-OCR | Major applications of data science: ⏎ - Health-Care: with enough data data scientist can use Machine Learning to predict and prevent the patient from heart attack or detect any symptom of some serious illness. Also they can use machine learning to come up with new core for new diseases. ⏎ - Self-driving car: with the v. ⏎ - Artificial Intelligent: with machine learning we can create intelligent machine which know and sometime thinks like human. |  |  |

### Q26 (S6) — teacher mark: 2.0

![S6](crops/Student_4/S6.jpg)
<sub>located on: Student_4_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 26. Structured data is the organized data that mostly ⏎ recorded in the form of spreadsheet, database, comma seperated ⏎ value (CSV). While Semi-Structured data is a somewhat organize ⏎ data that store the data with the help of tag and it mostly ⏎ in xml or html form. |  |  |
| Chandra | Structured data is the organized data that mostly recorded in the form of spreadsheet, database, comma separated value (CSV). While semi-structured data is a somewhat organized data that store the data with the help of tag and it mostly in xml or html form. |  |  |
| PaddleOCR | Structured data is the organized data that mostly recorded in the form of spreadsheet, database, comma separated value (csv). While Semi-Structured data is a somewhat organized data that store the data with the help of tag and it mostly in xml or html form. |  |  |
| GLM-OCR | Structured data is the organized data that mostly recorded in the form of spreadsheet, database, comma separated value (csv). While Semi-structured data is a somewhat organize data that store the data with the help of tag and it mostly in xml or html form. |  |  |

### Q27 (S7) — teacher mark: 2.0

![S7](crops/Student_4/S7.jpg)
<sub>located on: Student_4_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 27. We can find an outlier in the data by identify ⏎ whether the data is out of the norm or we can use formula ⏎ Q_1 - 1.5 IQR to find lower boundary or Q_3 + 1.5 IQR for ⏎ upper boundary |  |  |
| Chandra | We can find ~~an~~ an outlier in the data by identify whether the data is out of the norm or we ~~can~~ use formula Q_1 - 1.5 IQR to find lower boundary or Q_3 + 1.5 IQR for upper boundary |  |  |
| PaddleOCR | We can find an outlier in the data by identify ⏎ whether the data is out of the norm or we can use formula ⏎ \(Q_{1-1.5IQR}\) to find lower boundary or \(Q_{3+1.5IQR}\) for ⏎ upper boundary |  |  |
| GLM-OCR | We can find an outlier in the data by identify whether the data is out of the norm or we can use formula $ Q_{1}-1.5 I Q R $ to find lower boundary or $ Q_{3}+1.5 I Q R $ for upper boundary |  |  |

### Q28 (S8) — teacher mark: 2.0

![S8](crops/Student_4/S8.jpg)
<sub>located on: Student_4_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 28. Data pre-processing is the method to clean the data ⏎ and reduce the unnecessary feature before we can used it ⏎ for training the model. ⏎ 29. Data normalization is required in K-NN because it help |  |  |
| Chandra | Data pre-processing is the method to clean the data and reduce the unnecessary feature before we can use it for training the model. ⏎  ⏎ a Data normalization is required in K-MN because it helps |  |  |
| PaddleOCR | Data pre-processing is the method to clean the data and reduce the unnecessary feature before we can use it for training the model. ⏎ Data normalization is required in K-NN because it helps |  |  |
| GLM-OCR | Data pre-processing is the method to clean the data and reduce the unnecessary feature before we can used it for training the model. ⏎ Data normalization is requerred in K-NN because it help |  |  |

### Q29 (S9) — teacher mark: 2.0

![S9](crops/Student_4/S9.jpg)
<sub>located on: Student_4_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | for training the model. ⏎ 29. Data normalization is required in K-MN because it help ⏎ to maximize and minimize the value of the data. |  |  |
| Chandra | for training the model. ⏎  ⏎ eg. Data normalization is required in K-NN because it helps ⏎  ⏎ to maximize and minimize the value of the data. |  |  |
| PaddleOCR | For training the model. ⏎ 29. Data normalization is required in K-NN because it helps to maximize and minimize the value of the data. |  |  |
| GLM-OCR | for training the model. ⏎ 29. Data normalization is requered in K-NN because it help ⏎ to maximize and minimize the value of the data. |  |  |

### Q30 (S10) — teacher mark: None

![S10](crops/Student_4/S10.jpg)
<sub>located on: Student_4_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 20. |  |  |
| Chandra | 20. |  |  |
| PaddleOCR | 20. |  |  |
| GLM-OCR | ∅ |  |  |

### Q31 (S11) — teacher mark: 2.0

![S11](crops/Student_4/S11.jpg)
<sub>located on: Student_4_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 21. k in k-mean algorithm is the number of clustering ⏎ that the algorithm should use. |  |  |
| Chandra | 21. k in k-mean algorithm is the number of clustering that the algorithm should use. |  |  |
| PaddleOCR | k in k-mean algorithm is the number of clustering that the algorithm should use. |  |  |
| GLM-OCR | 21. k in k-mean algorithm is the number of clustering that the algorithm should use. |  |  |

### Q32 (S12) — teacher mark: 0.0

![S12](crops/Student_4/S12.jpg)
<sub>located on: Student_4_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 32. hyperparameters are weight, k in k-mean, ⏎ number of neighbor in KNN. |  |  |
| Chandra | hyperparameters are weight, k in k-mean, number of neighbor in KNN. |  |  |
| PaddleOCR | hyperparameters are weight, k in k-mean, number of neighbor in KMG. |  |  |
| GLM-OCR | hyperparameters are weight, k in k-mean, number of neighbor in KMA. |  |  |

### Q33 (S13) — teacher mark: None

![S13](crops/Student_4/S13.jpg)
<sub>located on: Student_4_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 33, |  |  |
| Chandra | ∅ |  |  |
| PaddleOCR | ∅ |  |  |
| GLM-OCR | ∅ |  |  |

### Q34 (S14) — teacher mark: 2.0

![S14](crops/Student_4/S14.jpg)
<sub>located on: Student_4_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | Q4. The first one rn good as the line has large margin ⏎ an near the support vectors. While the second one rs not ⏎ as in between the lrne we cian see some data that is out ⏎ of the good. And the last one seem good but the lrne is ⏎ so close each other. |  |  |
| Chandra | 84. The first one is good as the line has large margin and near the support vectors. While the second one is not as is between the line we can see ~~some~~ data that is out of the good. And the last one seem good but the line is so close each other. |  |  |
| PaddleOCR | 84. The first one in good cos the line has large margin ⏎ an near the support vectors. While the second one is not ⏎ as in between the line we can see some data that is out ⏎ of the good. And the last one seem good but the line is ⏎ so close each other. |  |  |
| GLM-OCR | 84. The first one in good as the line has large margin an near the support vectors . While the second one is not as in between the line we can see some data that is out of the good . And the last one seem good but the line is so close each other. |  |  |

### Q35 (S15) — teacher mark: None

![S15](crops/Student_4/S15.jpg)
<sub>located on: Student_4_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 35. |  |  |
| Chandra | ∅ |  |  |
| PaddleOCR | ∅ |  |  |
| GLM-OCR | ∅ |  |  |
