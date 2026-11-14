# Student_10 — reader comparison

Pages read: Student_10_p1.png, Student_10_p2.png, Student_10_p3.png, Student_10_p4.png  
Skipped as blank / show-through backs: none  
Answers located by the segmenter: 29/35  
Visual check by Claude: MCQ only / disagreements

Page images: `eval/data/mendeley/images/` · crops: `eval/reports/mendeley/crops/` (local, not in git).

> Only the MCQ answers where a reader disagreed with the teacher CSV were checked by eye on this sheet.

## MCQ (gold = letter in the teacher's CSV)

| Q | crop | gold | Qwen3.8 | Chandra | PaddleOCR | GLM-OCR | note |
|---|---|---|---|---|---|---|---|
| Q1 | ![Q1](crops/Student_10/Q1.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q2 | ![Q2](crops/Student_10/Q2.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q3 | ![Q3](crops/Student_10/Q3.jpg) | **D** | D ✅ | D ✅ | D ✅ | ∅ |  |
| Q4 | ![Q4](crops/Student_10/Q4.jpg) | **D** | D ✅ | D ✅ | D ✅ | D ✅ |  |
| Q5 | ![Q5](crops/Student_10/Q5.jpg) | **A** | A ✅ | A ✅ | ∅ | A ✅ |  |
| Q6 | ![Q6](crops/Student_10/Q6.jpg) | **B** | ∅ | B ✅ | B ✅ | B ✅ |  |
| Q7 | ![Q7](crops/Student_10/Q7.jpg) | **B** | A,B ❌ | B ✅ | B ✅ | B ✅ | Clearly 'B'. Qwen3.8 answered 'A,B' — invented an A. |
| Q8 | ![Q8](crops/Student_10/Q8.jpg) | **A** | ∅ | A ✅ | A ✅ | A ✅ |  |
| Q9 | ![Q9](crops/Student_10/Q9.jpg) | **D** | D ✅ | ∅ | D ✅ | D ✅ |  |
| Q10 | ![Q10](crops/Student_10/Q10.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q11 | ![Q11](crops/Student_10/Q11.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q12 | ![Q12](crops/Student_10/Q12.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q13 | ![Q13](crops/Student_10/Q13.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q14 | ![Q14](crops/Student_10/Q14.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q15 | ![Q15](crops/Student_10/Q15.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q16 | ![Q16](crops/Student_10/Q16.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q17 | ![Q17](crops/Student_10/Q17.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q18 | ![Q18](crops/Student_10/Q18.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q19 | ![Q19](crops/Student_10/Q19.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q20 | ![Q20](crops/Student_10/Q20.jpg) | **C** | ∅ | ∅ | C ✅ | C ✅ | '20. C' (letter far right of the crop); CSV right. |

Correct per reader: Qwen3.8 16/20, Chandra 18/20, PaddleOCR 19/20, GLM-OCR 19/20

## Short answers (Q21–Q35)

Teacher mark is from the CSV (out of 2). CER/WER are against Claude's transcript where one exists (lower = better; struck-out text, punctuation, case and the question label are ignored).

### Q21 (S1) — teacher mark: 2.0

![S1](crops/Student_10/S1.jpg)
<sub>located on: Student_10_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 21. Supervised Learning is type of machine learning that ⏎ dataset predict on Lable Variable. It used to ⏎ from input (feature) into output (taget) Variable. |  |  |
| Chandra | Supervised Learning is type of machine learning that dataset predict on label variable. It used to from input (feature) into output (target) variable. ⏎  ⏎ 22. Regression analysis is Statistical method that |  |  |
| PaddleOCR | Supervised Learning is type of machine learning that dataset predict on Lable Variable. It used to from input (feature) into output (target) Variable. |  |  |
| GLM-OCR | Supervised Learning is type of machine learning that dataset predict on Lable Variable. It used to from input (feature) into output (taget) Variable. |  |  |

### Q22 (S2) — teacher mark: None

_answer not located_
<sub>located on: —</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | ∅ |  |  |
| Chandra | ∅ |  |  |
| PaddleOCR | ∅ |  |  |
| GLM-OCR | ∅ |  |  |

### Q23 (S3) — teacher mark: 2.0

![S3](crops/Student_10/S3.jpg)
<sub>located on: Student_10_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 23. Regression analysis is Statistic method that ⏎ model Relationship between dependent Variable ⏎ and independent Variable. In data Science, ⏎ we use regression analysis to predict the numerical ⏎ of Value best on there Variable. |  |  |
| Chandra | from input (feature) into output (target) Variable. ⏎  ⏎ 23. Regression analysis is Statistic method that model Relationship between dependent Variable and independent Variable. In data Science, we use regression analysis to predict the numerical of Value best on there Variable. ⏎  ⏎ 25 ⏎  ⏎ Two major applications of data Science |  |  |
| PaddleOCR | from input (feature) into output (target) Variable. ⏎ 23. Regression analysis is Statistic method that model Relationship between dependent Variable and independent Variable. In data science, we use regression analysis to predict the numberical of Value best on their Variable. |  |  |
| GLM-OCR | Pregression analysis is Statistic method that model Relationship between dependent Variable and independent Variable. In data science, we use regression analysis to predict the numberical of value best on their Variable. ⏎  ⏎ 25. Two major applications of data science |  |  |

### Q24 (S4) — teacher mark: 1.0

![S4](crops/Student_10/S4.jpg)
<sub>located on: Student_10_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 24. Two challenges of Machine learning: ⏎ - Supervise learning, it's predict on lable of variable ⏎ to find out the input of feature and output by ⏎ target.. ⏎ - clustering: Clustering is part of unsupervised ⏎ learning, that it learn as sub-group of variable ⏎ be like the K-means cdgorithm. |  |  |
| Chandra | Two challenges of Machine learning: ⏎  ⏎ - Supervise learning, it's predict on table of variable to find out the input of feature and output by target.. ⏎  ⏎ - Clustering: Clustering is part of unsupervised learning, that it learn as sub-group of variable be like the K-means algorithm. |  |  |
| PaddleOCR | Two challenges of Machine learning: ⏎ - Supervise learning, it's predict on table of variable ⏎ to find out the input of feature and output by ⏎ target. ⏎ - Clustering: Clustering is part of unsupervised ⏎ learning, that it learn as sub-group of variable ⏎ be like the k-means algorithm. |  |  |
| GLM-OCR | Two challenges of Machine learning: ⏎ - Supervise learning, it's predict on table of variable to find out the input of feature and output by target. ⏎ - Clustering: Clustering is part of unsupervised learning, that it learn as sub-group of variable be like the k-means algorithm. |  |  |

### Q25 (S5) — teacher mark: 2.0

![S5](crops/Student_10/S5.jpg)
<sub>located on: Student_10_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 25. Two major applications of data science. ⏎ - Hospitalities ⏎ - Agriculture |  |  |
| Chandra | of Value best on theire Variable. ⏎  ⏎ 25. Two major applications of data science. ⏎ - Hospitalities ⏎ - Agriculture |  |  |
| PaddleOCR | Two major applications of data Science. ⏎ - Hospitalities ⏎ - Agriculture |  |  |
| GLM-OCR | Two major applications of data science. ⏎ - Hospitalities ⏎ - Agriculture |  |  |

### Q26 (S6) — teacher mark: 2.0

![S6](crops/Student_10/S6.jpg)
<sub>located on: Student_10_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 20. Distinguish between the terms : ⏎ \| Structured data \| Semi-Structured data \| ⏎ \| - Full of Organization format \| - Organization format Such as HTML, XML, JSON \| ⏎ \| - Computer Can read and analyst. \| - Computer Can read as use HTML, XML, JSON \| ⏎ \| - No need to do data processing. \| - Need to do pre-processing \| ⏎ \| - Can take data and analyst \| - Before analyst need to do pre-process of data. \| ⏎ \| - Format in Rational database. \| - ~~Format in Rectional database~~ \| |  |  |
| Chandra | Distinguish between the terms : ⏎  ⏎ Structured dataSemi-Structured data- Full of Organization format ⏎ - Computer Can read and analyst. ⏎ - No need to do data processing. ⏎ - Can take data and analyst ⏎ - Format in Rational database. ⏎ - Organization Format Such as HTML, XML, JSON ⏎ - Computer Can read as use HTML, XML, JSON ⏎ - Need to do pre-processing ⏎ - Before analyst need to do pre-process of data. ⏎ - ~~Format in Rational data base~~ |  |  |
| PaddleOCR | Distinguish between the terms: ⏎  ⏎ - Structured data ⏎ - Full of Organization ⏎   format ⏎ - Computer Can read and analyst. ⏎ - No need to do data processing. ⏎ - Can take data and analyst ⏎ - Format in Rational database. ⏎  ⏎ Semi-Structured data ⏎ - Organization format ⏎   Such as HTML, XML, JSON ⏎ - Computer Can read as use HTML, XML, JSON ⏎ - Need to do pre-processing ⏎ - Before analyst need to do pre-process of data. ⏎ - Format in Rational database base |  |  |
| GLM-OCR | Distinguish between the terms: ⏎  ⏎ \| Structured data \| Semi-Structured data \| ⏎ \| :--- \| :--- \| ⏎ \| - Full of Organization format \| - Organization Format Such as HTML, XML, JSON \| ⏎ \| - Computer can read and analyst. \| - Computer can read as use HTML, XML, JSON \| ⏎ \| - No need to do data processing. \| - Need to do pre-processing \| ⏎ \| - Can take data and analyst \| - Before analyst need to do pre-process of data. \| ⏎ \| - Format in Rational database \| - Format in Rational database \| |  |  |

### Q27 (S7) — teacher mark: None

_answer not located_
<sub>located on: —</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | ∅ |  |  |
| Chandra | ∅ |  |  |
| PaddleOCR | ∅ |  |  |
| GLM-OCR | ∅ |  |  |

### Q28 (S8) — teacher mark: 1.0

![S8](crops/Student_10/S8.jpg)
<sub>located on: Student_10_p4.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | Data pre-processing is transforming data from raw data ⏎ into data that efficiency or structure data. |  |  |
| Chandra | Data pre-processing is transforming data from raw data into data that efficiency or structure data. |  |  |
| PaddleOCR | Data pre-processing is transforming data from raw data into data that efficiency or structure data. |  |  |
| GLM-OCR | Data pre-processing is transforming data from raw data into data that efficiency or structure data. |  |  |

### Q29 (S9) — teacher mark: 1.0

![S9](crops/Student_10/S9.jpg)
<sub>located on: Student_10_p4.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 29. We need Normalization data is required in k-NN because ⏎ K-nearest neighbor is use classification to identify the ⏎ dataset. K-NN Can pointed the nearest of variable ⏎ between two or more Clusters. |  |  |
| Chandra | We need normalization data is required in K-NN because K-nearest neighbor is use classification to identify the dataset. K-NN can pointed the nearest of variable between two or more clusters. |  |  |
| PaddleOCR | data ⏎ We need normalization is required in k-NN because ⏎ k-nearest neighbor is use classification to identify the ⏎ dataset. k-NN can point the nearest of variable ⏎ between two or more clusters. |  |  |
| GLM-OCR | We need normalization data is required in k-NN because k-nearest neighbor is use classification to identify the dataset. k-NN can pointed the nearest of variable between two or more clusters. |  |  |

### Q30 (S10) — teacher mark: None

_answer not located_
<sub>located on: —</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | ∅ |  |  |
| Chandra | ∅ |  |  |
| PaddleOCR | ∅ |  |  |
| GLM-OCR | ∅ |  |  |

### Q31 (S11) — teacher mark: 2.0

![S11](crops/Student_10/S11.jpg)
<sub>located on: Student_10_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 31. k is numerical of cluster. |  |  |
| Chandra | k is numerical of clusters. |  |  |
| PaddleOCR | k is numerical of cluster. |  |  |
| GLM-OCR | k is numberical of cluster. |  |  |

### Q32 (S12) — teacher mark: None

_answer not located_
<sub>located on: —</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | ∅ |  |  |
| Chandra | ∅ |  |  |
| PaddleOCR | ∅ |  |  |
| GLM-OCR | ∅ |  |  |

### Q33 (S13) — teacher mark: None

_answer not located_
<sub>located on: —</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | ∅ |  |  |
| Chandra | ∅ |  |  |
| PaddleOCR | ∅ |  |  |
| GLM-OCR | ∅ |  |  |

### Q34 (S14) — teacher mark: 1.0

![S14](crops/Student_10/S14.jpg)
<sub>located on: Student_10_p4.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 34. Now we point on three different SVM classifiers ⏎ by Fig.A, Fig.B and Fig.C ⏎ - Fig.A: It close to data cluster, we can said ~~it to~~ ⏎ its not good. ⏎ - Fig.B: The data cluster stay inside linear boundaries, ⏎ No good. ⏎ - Fig.c: The data cluster far from linear boundaries, ⏎ Good. ⏎ => Fig.c better than Fig.A and Fig.B. |  |  |
| Chandra | Now we point on three different SVM classifiers by Fig. A, Fig. B and Fig. C ⏎  ⏎ - Fig. A: It close to data cluster, we can said it ~~it~~ its not good. ⏎  ⏎ - Fig. B: The data cluster stay inside linear boundaries, No good. ⏎  ⏎ - Fig. C: The data cluster far from linear boundaries, Good. ⏎  ⏎ ⇒ Fig. C better than Fig. A and Fig. B. |  |  |
| PaddleOCR | Now we point on three different SUM classifies by Fig. A, Fig. B and Fig. C ⏎ - Fig. A: It close to data cluster, we can said it also its not good. ⏎ - Fig. B: The data cluster stay inside linear boundaries, no good. ⏎ - Fig. C: The data cluster far from Linear boundaries, Good. ⏎ ⇒ Fig. C better than Fig. A and Fig. B. |  |  |
| GLM-OCR | Now we point on three different SVM classifies by Fig.A , Fig.B and Fig.C ⏎ - Fig.A: It close to data cluster, we can said it is not good. ⏎ - Fig.B: The data cluster stay inside linear boundaries, no good. ⏎ - Fig.C: The data cluster far from linear boundaries, Good. ⏎ $ \Rightarrow $ Fig.C better than Fig.A and Fig.B. |  |  |

### Q35 (S15) — teacher mark: None

_answer not located_
<sub>located on: —</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | ∅ |  |  |
| Chandra | ∅ |  |  |
| PaddleOCR | ∅ |  |  |
| GLM-OCR | ∅ |  |  |
