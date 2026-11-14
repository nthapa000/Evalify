# Student_6 — reader comparison

Pages read: Student_6_p1.png, Student_6_p2.png, Student_6_p3.png  
Skipped as blank / show-through backs: Student_6_p4.png  
Answers located by the segmenter: 29/35  
Visual check by Claude: MCQ only / disagreements

Page images: `eval/data/mendeley/images/` · crops: `eval/reports/mendeley/crops/` (local, not in git).

> Only the MCQ answers where a reader disagreed with the teacher CSV were checked by eye on this sheet.

## MCQ (gold = letter in the teacher's CSV)

| Q | crop | gold | Qwen3.8 | Chandra | PaddleOCR | GLM-OCR | note |
|---|---|---|---|---|---|---|---|
| Q1 | ![Q1](crops/Student_6/Q1.jpg) | **D** | ∅ | D ✅ | D ✅ | D ✅ |  |
| Q2 | ![Q2](crops/Student_6/Q2.jpg) | **C** | ∅ | C ✅ | C ✅ | E ❌ | Lower-case 'c'; CSV right; GLM-OCR read 'E' (wrong). |
| Q3 | ![Q3](crops/Student_6/Q3.jpg) | **C** | ∅ | ∅ | C ✅ | C ✅ | Lower-case 'c'; CSV right. |
| Q4 | ![Q4](crops/Student_6/Q4.jpg) | **C** | ∅ | ∅ | C ✅ | C ✅ | 'C'; CSV right. |
| Q5 | ![Q5](crops/Student_6/Q5.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q6 | ![Q6](crops/Student_6/Q6.jpg) | **B** | ∅ | B ✅ | B ✅ | B ✅ |  |
| Q7 | ![Q7](crops/Student_6/Q7.jpg) | **B** | ∅ | B ✅ | B ✅ | B ✅ |  |
| Q8 | ![Q8](crops/Student_6/Q8.jpg) | **C** | ∅ | C ✅ | C ✅ | ∅ | Lower-case 'c'; CSV right. |
| Q9 | ![Q9](crops/Student_6/Q9.jpg) | **A** | ∅ | A ✅ | A ✅ | A ✅ |  |
| Q10 | ![Q10](crops/Student_6/Q10.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q11 | ![Q11](crops/Student_6/Q11.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q12 | ![Q12](crops/Student_6/Q12.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q13 | ![Q13](crops/Student_6/Q13.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q14 | ![Q14](crops/Student_6/Q14.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q15 | ![Q15](crops/Student_6/Q15.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q16 | ![Q16](crops/Student_6/Q16.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q17 | ![Q17](crops/Student_6/Q17.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q18 | ![Q18](crops/Student_6/Q18.jpg) | **C** | C ✅ | C ✅ | ∅ | C ✅ |  |
| Q19 | ![Q19](crops/Student_6/Q19.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q20 | ![Q20](crops/Student_6/Q20.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |

Correct per reader: Qwen3.8 12/20, Chandra 18/20, PaddleOCR 19/20, GLM-OCR 18/20

## Short answers (Q21–Q35)

Teacher mark is from the CSV (out of 2). CER/WER are against Claude's transcript where one exists (lower = better; struck-out text, punctuation, case and the question label are ignored).

### Q21 (S1) — teacher mark: 2.0

![S1](crops/Student_6/S1.jpg)
<sub>located on: Student_6_p1.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | Supervised learning is a method of machine learning algorithm that provide ⏎ dependence input as well as correct the independence output for predictin ⏎ the result in a dataset. it aim is to find the mapping function to ⏎ map the dependence variable (x) with independence variable (y). |  |  |
| Chandra | Supervised learning is a method of machine learning algorithm that provide dependence input as well as correct the independence output for predicting the result in a dataset. it aims is to find the mapping function to map the dependence variable (x) with independence variable (y). |  |  |
| PaddleOCR | Supervised learning is a method of machine learning algorithm that provides dependence input as well as correct the independence output for predicting the result in a dataset. It aims to find the mapping function to map the dependence variable (x) with independence variable (y). |  |  |
| GLM-OCR | Supervised learning is a method of machine learning algorithm that provide dependence input as well as correct the independence output for predictin the result in a dataset. It aims is to find the mapping function to map the dependence variable (x) with independence variable (y). |  |  |

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

![S3](crops/Student_6/S3.jpg)
<sub>located on: Student_6_p1.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | Data preprocessing is the process to make raw data to become ⏎ a dataset that can understanded by machine. |  |  |
| Chandra | 28 Data preprocessing is the process to make raw data to become a data set that can understand by machine. |  |  |
| PaddleOCR | Data preprocessing is the process to make raw data to become a data set that can understand by machine. |  |  |
| GLM-OCR | 28 Data preprocessing is the process to make raw data to become a data set that can understand by machine. |  |  |

### Q24 (S4) — teacher mark: 2.0

![S4](crops/Student_6/S4.jpg)
<sub>located on: Student_6_p1.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | banking. ⏎ 24 Challenge of machine learning. ⏎ - Most of the data are raw so it is difficult and take time for ⏎ machine to learn ⏎ Select algorithm. ⏎ - it is very complex to study the large amount of data and hard to ⏎ 26 - structured data is the data that is predefined in dataset that |  |  |
| Chandra | - Banking. ⏎ 24 Challenge of machine learning.- Most of the data are raw so it is difficult and take time for machine to learn select algorithm. ⏎ - it is very complex to study the large amount of data and hard to ⏎  ⏎ 26 structured data is the data that is predefined in dataset that |  |  |
| PaddleOCR | Challenge of machine learning. ⏎ - Most of the data are raw so it is difficult and take time for machine to learn ⏎ - it is very complex to study the large amount of data and hard to structure data is the data that is predicted in dataset that |  |  |
| GLM-OCR | Challenge of machine learning. ⏎ - Most of the data are raw so it is difficult and take time to machine to learn select algorithm. ⏎ - it is very complex to study the large amount of data and hard to ⏎  ⏎ 26- structured data is the data that is predefined in dataset that |  |  |

### Q25 (S5) — teacher mark: 2.0

![S5](crops/Student_6/S5.jpg)
<sub>located on: Student_6_p1.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 25 Application of data science ⏎ - Transportation ⏎ - Financial ⏎ - Health ⏎ - Banking. |  |  |
| Chandra | Application of data science ⏎  ⏎ - Transportation ⏎ - Financial ⏎ - Health ⏎ - Banking. ⏎  ⏎ 26 Challenges of machine learning. |  |  |
| PaddleOCR | Application of data science ⏎ - Transportation ⏎ - Financial ⏎ - Health ⏎ - Booking ⏎  ⏎ Challenge of machine learning. |  |  |
| GLM-OCR | Application of data science ⏎ - Transportation ⏎ - Financial ⏎ - Health ⏎ - Banking. |  |  |

### Q26 (S6) — teacher mark: 1.0

![S6](crops/Student_6/S6.jpg)
<sub>located on: Student_6_p1.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 26 - structured data is the data that is predefined in dataset that ⏎ can be understand by machine. ⏎ - Semi-structured data is the combination of structured data and ⏎ unstructured data which is need to do the data preprocessing process ⏎ to be able for machine to understand it. |  |  |
| Chandra | it is very complex to study the large amount of data and hard to n ⏎ - structured data is the data that is predefined in dataset that can be understood by machine. ⏎ - Semi-structured data is the combination of structured data and unstructured data which is need to do the data preprocessing process to be able for machine to understand it. ⏎  ⏎ we find out the outlier in the data by compare all the |  |  |
| PaddleOCR | structured data is the data that is predefined in dataset that can be understand by machine. ⏎ Semi-structured data is the combination of structured data and unstructured data which is need to do the data preprocessing process to be able for machine to understand it. |  |  |
| GLM-OCR | structured data is the data that is predefined in dataset that can be understand by machine. ⏎ - Semi-structured data is the combination of structured data and unstructured data which is need to do the data preprocessing process to be able for machine to understand it. |  |  |

### Q27 (S7) — teacher mark: 1.0

![S7](crops/Student_6/S7.jpg)
<sub>located on: Student_6_p1.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | to be able for machine to understand it. ⏎ 27 we can find out the outlier in the data by compare all the ⏎ data, and the outlier is the abnormal data compare to the other ⏎ data in the dataset. |  |  |
| Chandra | to be able for machine to understand it. ⏎ 27 we can find out the outlier in the data by compare all the data, and the outlier is the abnormal data compare to the other data in the dataset. |  |  |
| PaddleOCR | We can find out the outlier in the data by compare all the data, and the outlier is the abnormal data compare to the other data in the dataset. |  |  |
| GLM-OCR | we can find out the outlier in the data by compare all the data. and the outlier is the abnormal data compare to the other data in the dataset. |  |  |

### Q28 (S8) — teacher mark: 1.0

_answer not located_
<sub>located on: —</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | ∅ |  |  |
| Chandra | ∅ |  |  |
| PaddleOCR | ∅ |  |  |
| GLM-OCR | ∅ |  |  |

### Q29 (S9) — teacher mark: None

_answer not located_
<sub>located on: —</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | ∅ |  |  |
| Chandra | ∅ |  |  |
| PaddleOCR | ∅ |  |  |
| GLM-OCR | ∅ |  |  |

### Q30 (S10) — teacher mark: None

![S10](crops/Student_6/S10.jpg)
<sub>located on: Student_6_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | The continuous attributes are discretized by changing to interval form. |  |  |
| Chandra | The continuous attributes are discretized by changing to interval form. |  |  |
| PaddleOCR | The continuous attributes are disretized by changing to internal form. |  |  |
| GLM-OCR | The continuous attributes are discretized by changing to interdial form. |  |  |

### Q31 (S11) — teacher mark: 1.0

![S11](crops/Student_6/S11.jpg)
<sub>located on: Student_6_p1.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | K in k-means algorithm is the number of predefined cluster that ⏎ need to be use in the process. |  |  |
| Chandra | K in k-means algorithm is the number of predefined clusters that need to be used in the process. |  |  |
| PaddleOCR | K in k-means algorithm is the number of predefined cluster that need to be use in the process. |  |  |
| GLM-OCR | K in k-means algorithm is the number of predefined cluster that need to be use in the process. |  |  |

### Q32 (S12) — teacher mark: 2.0

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

### Q34 (S14) — teacher mark: 2.0

![S14](crops/Student_6/S14.jpg)
<sub>located on: Student_6_p2.png, Student_6_p2.png, Student_6_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | P.1 : Good classification. all the data are separate ⏎ P.2 : Bad classification : the are some data left. ⏎ P.3 : Bad classification : Because the space between the boundary line ⏎ is small. |  |  |
| Chandra | P.1: Good classification. all the data are separate ⏎ p.2: Bad classification: there are some data left. ⏎ p.3: Bad classification : Because the space between the boundary line is small. |  |  |
| PaddleOCR | P.1: Good classification. all the data are separate ⏎ P.2: Bad classification: the are some clada left. ⏎ p.3: Bad classification: Because the space between the boundary line is small. |  |  |
| GLM-OCR | P.1: Good classification. all the data are separate ⏎ P.2: Bad classification: the are some data left. ⏎ P.3: Bad classification: Because the space between the boundary line is small. |  |  |

### Q35 (S15) — teacher mark: None

_answer not located_
<sub>located on: —</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | ∅ |  |  |
| Chandra | ∅ |  |  |
| PaddleOCR | ∅ |  |  |
| GLM-OCR | ∅ |  |  |
