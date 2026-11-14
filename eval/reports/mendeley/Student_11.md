# Student_11 — reader comparison

Pages read: Student_11_p1.png, Student_11_p2.png, Student_11_p3.png, Student_11_p4.png, Student_11_p5.png, Student_11_p6.png  
Skipped as blank / show-through backs: none  
Answers located by the segmenter: 35/35  
Visual check by Claude: not yet

Page images: `eval/data/mendeley/images/` · crops: `eval/reports/mendeley/crops/` (local, not in git).

## MCQ (gold = letter in the teacher's CSV)

| Q | crop | gold | Qwen3.8 | Chandra | PaddleOCR | GLM-OCR | note |
|---|---|---|---|---|---|---|---|
| Q1 | ![Q1](crops/Student_11/Q1.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q2 | ![Q2](crops/Student_11/Q2.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q3 | ![Q3](crops/Student_11/Q3.jpg) | **D** | D ✅ | D ✅ | D ✅ | D ✅ |  |
| Q4 | ![Q4](crops/Student_11/Q4.jpg) | **D** | D ✅ | D ✅ | D ✅ | D ✅ |  |
| Q5 | ![Q5](crops/Student_11/Q5.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q6 | ![Q6](crops/Student_11/Q6.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q7 | ![Q7](crops/Student_11/Q7.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q8 | ![Q8](crops/Student_11/Q8.jpg) | **D** | D ✅ | ∅ | D ✅ | D ✅ |  |
| Q9 | ![Q9](crops/Student_11/Q9.jpg) | **D** | D ✅ | D ✅ | D ✅ | D ✅ |  |
| Q10 | ![Q10](crops/Student_11/Q10.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q11 | ![Q11](crops/Student_11/Q11.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q12 | ![Q12](crops/Student_11/Q12.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q13 | ![Q13](crops/Student_11/Q13.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q14 | ![Q14](crops/Student_11/Q14.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q15 | ![Q15](crops/Student_11/Q15.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q16 | ![Q16](crops/Student_11/Q16.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q17 | ![Q17](crops/Student_11/Q17.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q18 | ![Q18](crops/Student_11/Q18.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q19 | ![Q19](crops/Student_11/Q19.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q20 | ![Q20](crops/Student_11/Q20.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |

Correct per reader: Qwen3.8 20/20, Chandra 19/20, PaddleOCR 20/20, GLM-OCR 20/20

## Short answers (Q21–Q35)

Teacher mark is from the CSV (out of 2). CER/WER are against Claude's transcript where one exists (lower = better; struck-out text, punctuation, case and the question label are ignored).

### Q21 (S1) — teacher mark: 2.0

![S1](crops/Student_11/S1.jpg)
<sub>located on: Student_11_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | Supervised Learning is a type of machine ⏎ learning that are used to train and predict ⏎ data that are labeled. |  |  |
| Chandra | 20. ⏎  ⏎ 21. Supervised Learning is a type of machine learning that are used to train and predict data that are labeled. |  |  |
| PaddleOCR | Supervised learning is a type of machine learning that are used to train and predict data that are labeled. |  |  |
| GLM-OCR | Supervised Learning is a type of machine learning that are used to train and predict data that are labeled. |  |  |

### Q22 (S2) — teacher mark: 1.0

![S2](crops/Student_11/S2.jpg)
<sub>located on: Student_11_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 22. Model M1 is not a good model, despite being ⏎ able to get a 99% accuracy for tram dataset ⏎ it still fails at the testing dataset. This can ⏎ occur to certain reasons: ⏎ - Lack of Dataset ⏎ - Bad feature Selection ⏎ - Too many outliers ⏎ - No Feature Engineering. |  |  |
| Chandra | Model M1 is not a good model, despite being able to get a 99% accuracy for train dataset it still fails at the testing dataset. This can occur to certain reasons: ⏎  ⏎ - Lack of Dataset ⏎ - Bad feature Selection ⏎ - Too many outliers ⏎ - No Feature Engineering. |  |  |
| PaddleOCR | Model M1 is not a good model, despite being able to get a 99% accuracy for tram dataset. It still fails at the testing dataset. This can occur to certain reasons: ⏎ - Lack of Dataset ⏎ - Bad feature Selection ⏎ - Too many outliers ⏎ - No feature Engineering. |  |  |
| GLM-OCR | Model M1 is not a good model, despite being able to get a 99% accuracy for tram dataset it still fails at the testing dataset. This can occur to certain reasons: ⏎ - Lack of Dataset ⏎ - Bad feature Selection ⏎ - Too many outliers ⏎ - No Feature Engineering. |  |  |

### Q23 (S3) — teacher mark: 1.0

![S3](crops/Student_11/S3.jpg)
<sub>located on: Student_11_p5.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 23. Regression Analysis is the monitoring of the ⏎ relationship between variables with continuous ⏎ value. |  |  |
| Chandra | Regression Analysis is the monitoring of the relationship between variables with continuous value. |  |  |
| PaddleOCR | Regression Analysis is the monitoring of the relationship between variables with continuous value. |  |  |
| GLM-OCR | Regression Analysis is the monitoring of the relationship between variables with continuous value. |  |  |

### Q24 (S4) — teacher mark: 2.0

![S4](crops/Student_11/S4.jpg)
<sub>located on: Student_11_p5.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 24. 2 challenges of Machine Learning: ⏎ - Data: This is a major problem, even with ⏎ the best ML Algorithms with bad data the ⏎ output would also be bad. |  |  |
| Chandra | 2 challenges of Machine Learning: ⏎  ⏎ - Data: This is a major problem, even with the best ML Algorithms with bad data the output would also be bad. |  |  |
| PaddleOCR | 2 challenges of Machine Learning: ⏎ - Data: This is a major problem, even with ⏎ the best ML algorithms with bad data the ⏎ output would also be bad. |  |  |
| GLM-OCR | 2 challenges of Machine Learning: ⏎ Data: This is a major problem, even with the best ML Algorithms with bad data the output would also be bad. |  |  |

### Q25 (S5) — teacher mark: 2.0

![S5](crops/Student_11/S5.jpg)
<sub>located on: Student_11_p2.png, Student_11_p6.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 25. 2 major applications of data science: ⏎ - Heart - Failure Prediction ⏎ - Classifying of Tumor is Dormant or ⏎ Malignant. ⏎  ⏎ - Uncertainties: Despite having enough data to ⏎ train the model, this still could not ⏎ determine the performance. Since uncertainties ⏎ may occur, it may effect it's performance. |  |  |
| Chandra | 2 major applications of data science: ⏎ - Heart - Failure Prediction ⏎ - Classifying of Tumor is Dormant or Malignant. ⏎ - Uncertainties: Despite having enough data to train the model, this still could not determine the performance. Since uncertainties may occur, it may affect it's performance. |  |  |
| PaddleOCR | 2 major applications of data science: ⏎ - Heart - Failure Prediction ⏎ - Classifying of Tumor is Dormant or Malignant. ⏎ - Uncertainties: Despite having enough data to ⏎ from the model, this still could not ⏎ determine the performance. Since uncertainties ⏎ may occur, it may effect it's performance. |  |  |
| GLM-OCR | 2 major applications of data science: ⏎ - Heart - Failure Prediction ⏎ - Classifying of Tumor is Dormant or Malignant. ⏎ - Uncertainties: Despite having enough data to tram the model, this still could not determine the performance. Since uncertainties may occur, it may effect it's performance. |  |  |

### Q26 (S6) — teacher mark: 2.0

![S6](crops/Student_11/S6.jpg)
<sub>located on: Student_11_p6.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 26. Structured Data ⏎ - Are in tabular format ⏎ - Has all features that ⏎ builds up conclusion ⏎ - format of Excel, CSV ⏎ Semi-Structured Data ⏎ - Not in tabular format ⏎ - Has features all mixed ⏎ - format of image, video, ⏎ sound |  |  |
| Chandra | May clear, it may affect its performance. ⏎  ⏎ 26. ⏎  ⏎ Structured Data ⏎ - Are in tabular format ⏎ - Has all features that builds up conclusion ⏎ - format of Excel, CSV ⏎  ⏎ Semi-Structured Data ⏎ - Not in tabular format ⏎ - Has features all mixed ⏎ - format of image, video, sound |  |  |
| PaddleOCR | Structured Data ⏎ - Are in tabular format ⏎ - Has all features that build up conclusion ⏎ - format of Excel, CSV ⏎ Semi-Structured Data ⏎ - Not in tabular format ⏎ - Has features call mixed ⏎ - formed of image, video, ⏎ Sound |  |  |
| GLM-OCR | Structured Data ⏎ - Are in tabular format ⏎ - Has all features that builds up conclusion ⏎ - Format of Excel, CSV ⏎  ⏎ Semi - Structured Data ⏎ - Not in tabular format ⏎ - Has features all mixed ⏎ - Formed of image, video, sound |  |  |

### Q27 (S7) — teacher mark: 1.5

![S7](crops/Student_11/S7.jpg)
<sub>located on: Student_11_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 27: To find the outlier in the Data we could ⏎ perform a standard deviation by using the ⏎ mean as a middle point to determine ⏎ which data is furthest, the ~~fot~~ furthest ⏎ are the outliers. |  |  |
| Chandra | To find the outlier in the Data we could perform a standard deviation by using the mean as a middle point to determine which data is furthest, the ~~far~~ furthest are the outliers. |  |  |
| PaddleOCR | To find the outlier in the Data we could perform a standard deviation by using the mean as a middle point to determine which data is furthest, the fact furthest are the outliers. |  |  |
| GLM-OCR | To find the outlier in the Data we could perform a standard deviation by using the mean as a middle point to determine which data is furthest, the furthest are the outliers. |  |  |

### Q28 (S8) — teacher mark: 2.0

![S8](crops/Student_11/S8.jpg)
<sub>located on: Student_11_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 28. Data pre-processing is a stage in the ⏎ data science life-cycle. During this stage ⏎ is where we prepare the dataset in order ⏎ to feed it to the model for training ⏎ and Testing. In this stage, we perform: ⏎ - handling miss value ⏎ - Outlier Detection ⏎ - feature Selection ⏎ - feature Engineering |  |  |
| Chandra | Data pre-processing is a stage in the data science life-cycle. During this stage is where we prepare the dataset in order to feed it to the model for training and Testing. In this stage, we perform: ⏎ - handling miss value ⏎ - Outlier Detection ⏎ - Feature Selection ⏎ - Feature Engineering ⏎  ⏎ 29. |  |  |
| PaddleOCR | Dada pre-processing is a stage in the data science life-cycle. During this stage is where we prepare the dataset in order to feed it to the model for the training and testing. In this stage, we perform: ⏎ - handling miss value ⏎ - Outlier Detection ⏎ - feature Selection ⏎ - feature Engineering |  |  |
| GLM-OCR | Data pre-processing is a stage in the data science life-cycle. During this stage is where we prepare the dataset in order to feed it to the model for tramming and testing. In this stage, we perform: ⏎ - handling miss value ⏎ - Outlier Detection ⏎ - feature Selection ⏎ - feature Engineering |  |  |

### Q29 (S9) — teacher mark: 2.0

![S9](crops/Student_11/S9.jpg)
<sub>located on: Student_11_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 29. Data normalization is required in K-NN, ⏎ because we need to divide the dataset into ⏎ class or group that has similar property. ⏎ This will allow the K-NN model to precisely ⏎ train with labeled data and make ⏎ better prediction. |  |  |
| Chandra | 29. Data normalization is required in K-NN, because we need to divide the dataset into class or group that has similar property. This will allow the K-NN model to precisely train with ~~labeled~~ labeled data and make better prediction. ⏎  ⏎ Page 3 of 6 |  |  |
| PaddleOCR | Data normalization is required in K-NN, because we need to divide the dataset into class or group that has similar property. This will allow the K-NN model to precisely train with labeled data and make better prediction. |  |  |
| GLM-OCR | Data normalization is required in K-NN, because we need to divide the dataset into class or group that has similar property. This will allow the K-NN model to precisely train with labeled data and make better prediction. |  |  |

### Q30 (S10) — teacher mark: 2.0

![S10](crops/Student_11/S10.jpg)
<sub>located on: Student_11_p6.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 30. Continuous Attributes are discretized by ⏎ calculating the mean of the Attribute and ⏎ measure the distance from one another. |  |  |
| Chandra | Continuous Attributes are discretized by calculating the mean of the Attribute and measure the distance from one another. |  |  |
| PaddleOCR | Continuous Attributes are discretized by calculating the mean of the Attribute and measure the distance from one another. |  |  |
| GLM-OCR | Continuous Attributes are discretized by calculating the mean of the Attribute and measure the distance from one another. |  |  |

### Q31 (S11) — teacher mark: 2.0

![S11](crops/Student_11/S11.jpg)
<sub>located on: Student_11_p4.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 31. k in k-means algorithms refers to the ⏎ number of clusters that we will use to ⏎ divide the dataset into when fitting the ⏎ model. |  |  |
| Chandra | k in k-means algorithms refers to the number of clusters that we will use to divide the dataset into when fitting the model. |  |  |
| PaddleOCR | k in k-means algorithms refers to the number of clusters that we will use to divide the dataset into when fitting the model. |  |  |
| GLM-OCR | k in k-means algorithms refers to the number of clusters that we will use to divide the dataset into when fitting the model. |  |  |

### Q32 (S12) — teacher mark: 2.0

![S12](crops/Student_11/S12.jpg)
<sub>located on: Student_11_p4.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 32. A few hyperparameters of ML Algorithms: ⏎ - n-estimators ⏎ - mean ⏎ - medra ⏎ - neighbors ⏎ - k - number of clusters ⏎ - Tram-Test set ratio |  |  |
| Chandra | A few hyperparameters of ML Algorithms: ⏎  ⏎ - n - estimators ⏎ - mean ⏎ - media ⏎ - neighbors ⏎ - k - number of clusters ⏎ - Train-Test set ratio |  |  |
| PaddleOCR | 38. A few hyperparameters of ML Algorithms: ⏎ - n-estimators ⏎ - mean ⏎ - media ⏎ - neighbors ⏎ - k-number of clusters ⏎ - Tram-Test set ratio |  |  |
| GLM-OCR | A few hyperparameters of ML Algorithms: ⏎ - n-estimators ⏎ - mean ⏎ - medra ⏎ - neighbors ⏎ - k - number of clusters ⏎ - Tram-Test set ratio |  |  |

### Q33 (S13) — teacher mark: 1.5

![S13](crops/Student_11/S13.jpg)
<sub>located on: Student_11_p6.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 33. Gradient Descent is the derivative value of ⏎ the dependent variable, where it alters the ⏎ final output of every calculation with SVM. |  |  |
| Chandra | ... another. ⏎  ⏎ 33. Gradient Descent is the derivative value of the dependent variable, where it alters the final output of every calculation with SVM. |  |  |
| PaddleOCR | Gradient Descent is the derivative value of the dependent variable, where it alters the final output of every calculation with SVM. |  |  |
| GLM-OCR | Gradient Descent is the derivative value of the dependent variable , where it alters the final output of every calculation with SVM. |  |  |

### Q34 (S14) — teacher mark: 4.0

![S14](crops/Student_11/S14.jpg)
<sub>located on: Student_11_p4.png, Student_11_p5.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 34. Comment on the performance of the classifiers ⏎     - Classifier 1: this is a good classifier, whereas ⏎       there are no mis-classification ⏎       ~~and it remains a~~, able to sep ⏎       separate the data properly and ⏎       has a decent gap between the ⏎       linear boundaries. ⏎ 34. - Classifier 2: this is ~~a~~ not a good classifier. ⏎       There seems to be 2 different ⏎       types of data within the linear ⏎       boundaries gap. ~~But it~~ Despite ⏎       having a decent gap length, it ⏎       stills mis-classify data properly. ⏎  ⏎     - Classifier 3: this is an ok classifier. ⏎       Even though there are no ~~mis~~ ⏎       mis-classification with the data, ⏎       this classifier has a rather small ⏎       gap between the linear boundaries. |  |  |
| Chandra | Comment on the performance of the classifiers. ⏎ . Classifier 1 : this is a good classifier, whereas there are no mis-classification and ~~it remains a~~, able to separate the data properly and has a decent gap between the linear boundaries. ⏎ 34. - Classifier 2: this is ~~a~~ not a good classifier. ⏎ There seems to be 2 different types of data within the linear boundaries gap. ~~But if~~ Despite having a decent gap length, it stills mis-classify data properly. ⏎  ⏎ - Classifier 3: this is an ok classifier. ⏎ Even though there are no mis mis mis-classification with the data, this classifier has a rather small gap between the linear boundaries. |  |  |
| PaddleOCR | Comment on the performance of the Classifiers. Classifier 1: this is a good classifier, whereas there are no mis-classification and it remains a, able to seg separate the data properly and has a decent gap between the linear boundaries. ⏎ 34. Classifier 2: this is not a good classifier. ⏎ There seems to be 2 different types of data within the linear boundaries gap. But it despite having a decent gap length, it stills mis-classify data properly. ⏎  ⏎ Classifier 3: this is an ok classifier. ⏎ Even though there are no mis-classifications with the data, this classifier has a rather small gap between the linear boundaries. |  |  |
| GLM-OCR | Comment on the performance of the classifiers . Classifier 1: this is a good classifier, whereas there are no mis-classification and it remains a, able to segregate the data properly and has a decent gap between the linear boundaries. ⏎ 34. Classifier 2: this is not a good classifier. There seems to be 2 different types of data within the linear boundaries gap. Despite having a decent gap length, it still mis-classify data properly. ⏎  ⏎ Classifier 3: this is an ok classifier. Even though there are no mis-classification with the data, this classifier has a rather small gap between the linear boundaries. |  |  |

### Q35 (S15) — teacher mark: 1.5

![S15](crops/Student_11/S15.jpg)
<sub>located on: Student_11_p6.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 35. Radial Basis Function Kernel work in SVM by ⏎ measuring and comparing the Distance of the ⏎ data from the linear boundaries. |  |  |
| Chandra | Radial Basis Function Kernel work in SVM by measuring and comparing the distance of the data from the linear boundaries. |  |  |
| PaddleOCR | Radial Basis Function Kernel work in SVM by measuring and comparing the Distance of the data from the linear boundaries. |  |  |
| GLM-OCR | Radial Basis Function Kernel work in SVM by measuring and comparing the Distance of the data from the linear boundaries. |  |  |
