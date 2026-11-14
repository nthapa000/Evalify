# Student_5 — reader comparison

Pages read: Student_5_p1.png, Student_5_p2.png, Student_5_p3.png  
Skipped as blank / show-through backs: Student_5_p4.png  
Answers located by the segmenter: 31/35  
Visual check by Claude: MCQ only / disagreements

Page images: `eval/data/mendeley/images/` · crops: `eval/reports/mendeley/crops/` (local, not in git).

> Only the MCQ answers where a reader disagreed with the teacher CSV were checked by eye on this sheet.

## MCQ (gold = letter in the teacher's CSV)

| Q | crop | gold | Qwen3.8 | Chandra | PaddleOCR | GLM-OCR | note |
|---|---|---|---|---|---|---|---|
| Q1 | ![Q1](crops/Student_5/Q1.jpg) | **A** | ∅ | A ✅ | A ✅ | A ✅ |  |
| Q2 | ![Q2](crops/Student_5/Q2.jpg) | **D** | ∅ | ∅ | D ✅ | ∅ | 'Ɗ'-style D; CSV right. |
| Q3 | ![Q3](crops/Student_5/Q3.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q4 | ![Q4](crops/Student_5/Q4.jpg) | **C** | ∅ | C ✅ | C ✅ | C ✅ |  |
| Q5 | ![Q5](crops/Student_5/Q5.jpg) | **C** | ∅ | ∅ | C ✅ | C ✅ | 'C.'; CSV right; Qwen/Chandra abstained. |
| Q6 | ![Q6](crops/Student_5/Q6.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q7 | ![Q7](crops/Student_5/Q7.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q8 | ![Q8](crops/Student_5/Q8.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q9 | ![Q9](crops/Student_5/Q9.jpg) | **C** | ∅ | C ✅ | C ✅ | C ✅ |  |
| Q10 | ![Q10](crops/Student_5/Q10.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q11 | ![Q11](crops/Student_5/Q11.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q12 | ![Q12](crops/Student_5/Q12.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q13 | ![Q13](crops/Student_5/Q13.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q14 | ![Q14](crops/Student_5/Q14.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q15 | ![Q15](crops/Student_5/Q15.jpg) | **D** | ∅ | D ✅ | D ✅ | ∅ | 'Ɗ'-style D; CSV right. |
| Q16 | ![Q16](crops/Student_5/Q16.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q17 | ![Q17](crops/Student_5/Q17.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q18 | ![Q18](crops/Student_5/Q18.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q19 | ![Q19](crops/Student_5/Q19.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q20 | ![Q20](crops/Student_5/Q20.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |

Correct per reader: Qwen3.8 14/20, Chandra 18/20, PaddleOCR 20/20, GLM-OCR 18/20

## Short answers (Q21–Q35)

Teacher mark is from the CSV (out of 2). CER/WER are against Claude's transcript where one exists (lower = better; struck-out text, punctuation, case and the question label are ignored).

### Q21 (S1) — teacher mark: 1.0

![S1](crops/Student_5/S1.jpg)
<sub>located on: Student_5_p1.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | Supervised Learing is machine Learing that need to take lable ⏎ data. They are take variate(f~~~~) as the input and return as the ⏎ target. |  |  |
| Chandra | Supervised Learning is machine ~~lear~~ Learning that need to take label data, they are take variable(~~feature~~) as the input and return as the target. |  |  |
| PaddleOCR | Supervised Learning is machine learning that need to take lable data. they are take variatte as the input and return as the target. |  |  |
| GLM-OCR | Supervised Learning is machine Learning that need to take labie data. they are take variable as the input and return as the target. |  |  |

### Q22 (S2) — teacher mark: 1.0

![S2](crops/Student_5/S2.jpg)
<sub>located on: Student_5_p1.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 22. on model M1, we got 99% accuracy for training dataset but ⏎ with testing data it provide only 30% so ~~it's~~ it's mean this model ⏎ is accuracy for training and for testing dataset is may have null valu ⏎ or any outlier data. |  |  |
| Chandra | On model M1, we got 99% accuracy for training dataset but with testing data it provide only 30% so ~~the~~ it's mean this model is accuracy for training and for testing dataset is may have null value or any outlier data. ⏎  ⏎ The first outcome of |  |  |
| PaddleOCR | on model M1, we got 99% accuracy for training dataset but with testing data it provic @only 3.0% so it's mean this model is accuracy for training and for testing dataset is may have hual value or any outlier data. |  |  |
| GLM-OCR | on model M1, we got 99% accuracy for training dataset but with testing data it provice only 3.0% so it's mean this model is accuracy for training and four testing dataset is may have null value or any outlier data. |  |  |

### Q23 (S3) — teacher mark: 1.0

![S3](crops/Student_5/S3.jpg)
<sub>located on: Student_5_p1.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 23. Regression analysis is the way to analysis the predict outcome of ⏎ result after we made Regression. |  |  |
| Chandra | or any outlier data. ⏎  ⏎ 23, Regression analysis is the way to analyse the predict outcome of resuite after we made Regression. |  |  |
| PaddleOCR | , Regression analysis is the way to analys the predict outcome of ⏎ resute after we made Regression. |  |  |
| GLM-OCR | Regression analysis is the way to analyze the predict outcome of resute after we made Regression. |  |  |

### Q24 (S4) — teacher mark: 2.0

_answer not located_
<sub>located on: —</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | ∅ |  |  |
| Chandra | ∅ |  |  |
| PaddleOCR | ∅ |  |  |
| GLM-OCR | ∅ |  |  |

### Q25 (S5) — teacher mark: 2.0

![S5](crops/Student_5/S5.jpg)
<sub>located on: Student_5_p1.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 25. two major application of data science ⏎ - Face recognition ⏎ - language recognition |  |  |
| Chandra | two major application of data science ⏎  ⏎ - Face recognition ⏎  ⏎ - Language recognition |  |  |
| PaddleOCR | , two major application of data science ⏎ - Face recongition ⏎ - language recongition |  |  |
| GLM-OCR | two major application of data science ⏎ - Face recognition ⏎ - Language recognition |  |  |

### Q26 (S6) — teacher mark: 2.0

![S6](crops/Student_5/S6.jpg)
<sub>located on: Student_5_p1.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 26. structured data is the data that have well-structur or well ⏎ Formate. on the other hand the semi-structured is the data that ⏎ not well-struct yet, it's still have other Formate exist on data. |  |  |
| Chandra | Structured data is the data that have well-structure or well format. on the other hand the semi-structured is the data that not well-struct yet, it's still have other format exist on data. |  |  |
| PaddleOCR | Structured data is the data that have well-Structur or well Formate. on the other hand the Semi-Structured is the data that not well-Struct yet, it's Still have other Formate exist on data. |  |  |
| GLM-OCR | Structured data is the data that have well-structur or well Formate. on the other hand the semi-structured is the data that not well-struct yet, it's still have other Formate exist on data. |  |  |

### Q27 (S7) — teacher mark: 0.0

![S7](crops/Student_5/S7.jpg)
<sub>located on: Student_5_p1.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 27. in other to find outlier in data: we have serveral methods but one ⏎ approche to find outlier is to use cross-validation. |  |  |
| Chandra | , in other to find outlier in data: we have several methods but one approach to find outlier is to use cross-validation. |  |  |
| PaddleOCR | , in other to Find outlier in data: we have Serverval methods but one approche to Find outlier is to use cross-Validation. |  |  |
| GLM-OCR | in other to Find outlier in data: we have serveral methods but one approach to Find outlier is to use cross-validation. |  |  |

### Q28 (S8) — teacher mark: 2.0

![S8](crops/Student_5/S8.jpg)
<sub>located on: Student_5_p1.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 28) Data Pre-Processing : is the Process to Validate data to make sure that ⏎ data Before Processing is clean, organize, doesn't have null Value and ⏎ well format in order to traine into model. |  |  |
| Chandra | Data Pre-processing : is the Process to Validate data to make sure that data Before processing is clean, ~~organize~~ organize, doesn't have null Value and well format in order to train into model. |  |  |
| PaddleOCR | , Data Pre-Processing: is the Process to Validate data to make sure that data Before Processing is clean, orange, doesn't have null value and well formate inother to traime into novel. |  |  |
| GLM-OCR | Data Pre-processing : is the Process to validate data to make sure that data Before processing is clean, orange, does it have null value and well formate another to train into model. |  |  |

### Q29 (S9) — teacher mark: 1.0

![S9](crops/Student_5/S9.jpg)
<sub>located on: Student_5_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 29. why data normalization is required in K-NN, Because in K-NN is the Machine ⏎ learning to find the near close of difference class with the distance, while ⏎ the normalization is the way to find the output as 0 or 1 So that ⏎ we can use ~~normalization~~ K-NN to support normalization to find the ⏎ output. |  |  |
| Chandra | why data normalization is required in K-NN, Because in K-NN is the Machine learning to find the near close of difference class with the distance, while the normalization is the way to find the output as 0 or 1 so that we can use ~~normalization~~ K-NN to support normalization to find the output. |  |  |
| PaddleOCR | Why data normalization is required in K-NN, Because in K-NN is the Machine learning to Fine the near close of difference Class with the distance, while the Normalization is the way to Fine the Output as O or 1 so that we Com Use K-NN to Support Normalization to Fine the Output. |  |  |
| GLM-OCR | why data normalization is required in K-NN, Because in K-NN is the machine learing to Fine the near close of difference class with the distance, while the normalization is the way to Fine the Output as 0 or 1 so that we can use normalization K-NN to support normalization to Fine the Output. |  |  |

### Q30 (S10) — teacher mark: 2.0

![S10](crops/Student_5/S10.jpg)
<sub>located on: Student_5_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | two Challenges of machine learning ⏎ - Follow the Pattern or Follow rule and we ~~need~~ need to test the output ⏎ value with actual value if the our actual value is big and large it's ⏎ consume a lot of cost and ~~less~~ resource. ⏎ - one machine learning algorithm is support only special problem ⏎ if we face different issue we need to use another algorithm. |  |  |
| Chandra | 24 ⏎ two challenges of machine learning ⏎  ⏎ - Follow the Pattern or Follow rule and we ~~need~~ need to test the output value with ~~the~~ actual value if the our actual value is big and large it's consume a lot of cost and ~~less~~ resource. ⏎  ⏎ - one machine learning algorithm is support only special problem if we face different issue we need to use another algorithm. |  |  |
| PaddleOCR | 24. two Challenges of machine learning ⏎ - Follow the Pattern or Follow rule and we need to test the Output Value with actual Value if the our actule value is big and large it is Consume a lot of Cost and \(\underline{\text{resource}}\). ⏎ - One machine learning algorithm is support only Special Problem If we face different issue we need to use and other algorithm |  |  |
| GLM-OCR | two challenges of machine learning ⏎ - Follow the pattern or Follow rule and we need to test the output value with actule value if the our actule value is big and large it is consume a lot of cost and resource. ⏎ - One machine learning algorithm is support only special problem if we face different issue we need to use another algorithm. |  |  |

### Q31 (S11) — teacher mark: 1.0

![S11](crops/Student_5/S11.jpg)
<sub>located on: Student_5_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | 30, continuous attributes are discretized by using the step time ⏎ so that we can have continuous attributes. |  |  |
| Chandra | 30, continuous attributes are discretized by using the step time so that we can have continuous attributes. |  |  |
| PaddleOCR | 30, continuous attributes are discretized by using the step time ⏎ So that we can have continuous attributes. |  |  |
| GLM-OCR | 30, continuous attributes are discretized by using the step time so that we can have continuous attributes. |  |  |

### Q32 (S12) — teacher mark: None

![S12](crops/Student_5/S12.jpg)
<sub>located on: Student_5_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | K in K-means algorithm is the number of time that we find ⏎ the mean values in K-means. |  |  |
| Chandra | 31, ⏎ K in K-means algorithm is the number of ~~time~~ time that we find the mean values in K-means. |  |  |
| PaddleOCR | 31, K in K-means algorithm is the number of time that we fine the mean values in K-means. |  |  |
| GLM-OCR | 31, K in K-means algorithm is the number of time that we fine the mean values in K-means. |  |  |

### Q33 (S13) — teacher mark: None

_answer not located_
<sub>located on: —</sub>

| reader | text | CER | WER |
|---|---|---|---|
| Qwen3.8 | ∅ |  |  |
| Chandra | ∅ |  |  |
| PaddleOCR | ∅ |  |  |
| GLM-OCR | ∅ |  |  |

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
