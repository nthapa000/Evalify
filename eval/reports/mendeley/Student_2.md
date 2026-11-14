# Student_2 — reader comparison

Pages read: Student_2_p1.png, Student_2_p2.png, Student_2_p3.png  
Skipped as blank / show-through backs: Student_2_p4.png  
Answers located by the segmenter: 29/35  
Visual check by Claude: yes — transcripts for short answers below

Page images: `eval/data/mendeley/images/` · crops: `eval/reports/mendeley/crops/` (local, not in git).

> **Visual check (sheet):** Q26, Q27, Q30, Q31, Q32, Q34 not attempted (teacher CSV blank, consistent). Page 4 is a blank back.

> Transcribed by Claude from the page images (eval/data/mendeley/images). Struck-out text is written ~~like this~~; [?] = could not read. Spelling is kept as written. Please verify.

## MCQ (gold = letter in the teacher's CSV)

| Q | crop | gold | Qwen3.8 | Chandra | PaddleOCR | GLM-OCR | note |
|---|---|---|---|---|---|---|---|
| Q1 | ![Q1](crops/Student_2/Q1.jpg) | **A** | ∅ | ∅ | B ❌ | ∅ | DISPUTED: I read '1. B' (a '1' with a hook, then a clear B); the teacher CSV says A. Please check the crop / page 1. |
| Q2 | ![Q2](crops/Student_2/Q2.jpg) | **A** | ∅ | A ✅ | A ✅ | A ✅ |  |
| Q3 | ![Q3](crops/Student_2/Q3.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q4 | ![Q4](crops/Student_2/Q4.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q5 | ![Q5](crops/Student_2/Q5.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q6 | ![Q6](crops/Student_2/Q6.jpg) | **C** | ∅ | B,C ❌ | ∅ | B,C ❌ | Student wrote B, scribbled it out, wrote C. CSV C is right; Chandra and GLM-OCR reported 'B,C' (missed the strike-out). |
| Q7 | ![Q7](crops/Student_2/Q7.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q8 | ![Q8](crops/Student_2/Q8.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q9 | ![Q9](crops/Student_2/Q9.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q10 | ![Q10](crops/Student_2/Q10.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q11 | ![Q11](crops/Student_2/Q11.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q12 | ![Q12](crops/Student_2/Q12.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q13 | ![Q13](crops/Student_2/Q13.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q14 | ![Q14](crops/Student_2/Q14.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ | A letter was scribbled out before C — final answer C (matches CSV). |
| Q15 | ![Q15](crops/Student_2/Q15.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q16 | ![Q16](crops/Student_2/Q16.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q17 | ![Q17](crops/Student_2/Q17.jpg) | **A** | A ✅ | A ✅ | A ✅ | A ✅ |  |
| Q18 | ![Q18](crops/Student_2/Q18.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |
| Q19 | ![Q19](crops/Student_2/Q19.jpg) | **B** | B ✅ | B ✅ | B ✅ | B ✅ |  |
| Q20 | ![Q20](crops/Student_2/Q20.jpg) | **C** | C ✅ | C ✅ | C ✅ | C ✅ |  |

Correct per reader: Qwen3.8 17/20, Chandra 18/20, PaddleOCR 18/20, GLM-OCR 18/20

## Short answers (Q21–Q35)

Teacher mark is from the CSV (out of 2). CER/WER are against Claude's transcript where one exists (lower = better; struck-out text, punctuation, case and the question label are ignored).

### Q21 (S1) — teacher mark: 2.0

![S1](crops/Student_2/S1.jpg)
<sub>located on: Student_2_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 21. Supervised learning is to make the machine to do what we target it to do. For Example: [triangle] [square] triangle square we have a label for every sign so machince will learn by knowing it label. | — | — |
| Qwen3.8 | 21. Supervised learning is to make the machine to ⏎ do what we target it to do. ⏎ For Example:  ⏎ triangle square we have a label for every ⏎ sign so machine will learn by knowing it label. | 0.09 | 0.08 |
| Chandra | Supervised learning is to make the machine to do what we forget it to do. ⏎  ⏎ For Example: \triangle \square we have a label for every ⏎ triangle square ⏎  ⏎ sign so machine will learn by knowing it label. | 0.18 | 0.17 |
| PaddleOCR | Supervised learning is to make the machine to do what we target it to do. ⏎ For example: △ □ we have a label for every triangle square ⏎ Sign so has choice will learn by knowing it label. | 0.25 | 0.22 |
| GLM-OCR | Supervised learning is to make the machine to do what we target it to do. ⏎ For Example: triangle square we have a label for every sign so machine will learn by knowing it label. | 0.09 | 0.08 |

**Visual check:** Includes two drawn shapes (triangle, square) labelled in words; transcribed as [triangle] [square].

### Q22 (S2) — teacher mark: 1.5

![S2](crops/Student_2/S2.jpg)
<sub>located on: Student_2_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 22. Model M1 have 99 % of Acuracy which is give an highest linear regression that to predict. and for the other 30 % it really not good for the testing data set. | — | — |
| Qwen3.8 | 22. Model M1 have 94% of Accuracy which is ⏎ give an highest linear regression that to predict, ⏎ and for the other 30% it really not good ⏎ for the testing data set. | 0.01 | 0.07 |
| Chandra | Model M_1 have 94% of Accuracy which is give an highest linear regression that to predict, and for the other 30% it really not good for the testing data set. | 0.02 | 0.13 |
| PaddleOCR | Model M1 have 94% of Accuracy which is ⏎ give an highest linear regression that to predict. ⏎ and for the other 30% It really has good ⏎ for the testing data set. | 0.03 | 0.10 |
| GLM-OCR | Model M1 have 99% of Accuracy which is give an highest linear regression that to predict. and for the other 30% it really not good for the testing data set. | 0.01 | 0.03 |

### Q23 (S3) — teacher mark: 2.0

![S3](crops/Student_2/S3.jpg)
<sub>located on: Student_2_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 23. Regression analysis is for prediction and forcasting. there are 2 value in it which is independence and dependence value or we can call it as input and output | — | — |
| Qwen3.8 | 23. Regression analysis is for prediction and forecasting. ⏎ there are 2 Value in it which is independence ⏎ and dependence value or we can call it as ⏎ input and output | 0.01 | 0.04 |
| Chandra | Regression analysis is for prediction and forecasting. There are 2 values in it which is independence and dependence value or we can call it as input and output. | 0.01 | 0.07 |
| PaddleOCR | Regression analysis is for prediction and forcasting. ⏎ there are 2 value in it which is independence ⏎ and dependence value or we can call it as ⏎ Input and out put | 0.01 | 0.07 |
| GLM-OCR | Regression analysis is for prediction and forecasting. There are 2 Value in it which is Independence and dependence value or we can call it as Input and output | 0.01 | 0.04 |

### Q24 (S4) — teacher mark: 1.0

![S4](crops/Student_2/S4.jpg)
<sub>located on: Student_2_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 24. the two challage in Machine learning are. - It hard to make the Machine to learn what we want it to learn - take too ~~much time~~. much time | — | — |
| Qwen3.8 | 24. the two challenge in machine learning are. ⏎ - It hard to make the machine to learn what ⏎ we want it to learn ⏎ - take too much time | 0.02 | 0.04 |
| Chandra | the two challenge in Machine learning are. ⏎  ⏎ - It hard to make the Machine to learn what we want it to learn ⏎ - take too ~~much time~~. much time | 0.02 | 0.04 |
| PaddleOCR | the two Challenge In Machine Learning are. ⏎ — It hard to make the Machine to learn. Why ⏎ — We want it to learn ⏎ — take too much time | 0.03 | 0.08 |
| GLM-OCR | 2. the two challenge In Machine learning are. ⏎ — It hard to make the Machine to learn. What ⏎ we want it to learn ⏎ — take too much time. much time | 0.10 | 0.12 |

### Q25 (S5) — teacher mark: 0.0

![S5](crops/Student_2/S5.jpg)
<sub>located on: Student_2_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 25. two major application of data science - Linear regression - Logistic regression | — | — |
| Qwen3.8 | 25. Two major application of data science ⏎ - Linear regression ⏎ - Logistic Regression | 0.00 | 0.00 |
| Chandra | two major application of data science ⏎  ⏎ - Linear regression ⏎ - Logistic regression ⏎  ⏎ 35. Random Forest | 0.23 | 0.30 |
| PaddleOCR | Two major applications of data science ⏎ - Linear regression ⏎ - Logistic regression | 0.01 | 0.10 |
| GLM-OCR | two major application of data science ⏎ - Linear regression ⏎ - Logistic regression | 0.00 | 0.00 |

### Q26 (S6) — teacher mark: None

_answer not located_
<sub>located on: —</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** |  | — | — |
| Qwen3.8 | ∅ |  |  |
| Chandra | ∅ |  |  |
| PaddleOCR | ∅ |  |  |
| GLM-OCR | ∅ |  |  |

### Q27 (S7) — teacher mark: None

_answer not located_
<sub>located on: —</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** |  | — | — |
| Qwen3.8 | ∅ |  |  |
| Chandra | ∅ |  |  |
| PaddleOCR | ∅ |  |  |
| GLM-OCR | ∅ |  |  |

### Q28 (S8) — teacher mark: 2.0

![S8](crops/Student_2/S8.jpg)
<sub>located on: Student_2_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 28. Data pre processing is the way to Clean and make or prepare Data ~~[?]~~ before using and it have many step - Data Cleansing - Data transform - Data - | — | — |
| Qwen3.8 | 28. Data pre processing is the way to clean and make ⏎ or prepare Data before using and it have many step ⏎ - Data Cleansing ⏎ - Data transform ⏎ - Data ⏎ - | 0.00 | 0.00 |
| Chandra | data to scale. ⏎  ⏎ 28. Data pre processing is the way to clean and make ⏎ or prepare Data before using and it have many step ⏎  ⏎ - Data Cleansing ⏎ - Data transform ⏎ - Data ⏎ - | 0.13 | 0.16 |
| PaddleOCR | Data pre processing is the way to clean and make our prepare Data before using and it have many step-data cleansing ⏎ - Data transform ⏎ - Data | 0.01 | 0.04 |
| GLM-OCR | Data pre processing is the way to clean and make or prepare Data before using and it have many step ⏎ - Data Cleansing ⏎ - Data transform ⏎ - Data ⏎ - | 0.00 | 0.00 |

### Q29 (S9) — teacher mark: 1.0

![S9](crops/Student_2/S9.jpg)
<sub>located on: Student_2_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 29. data normalization is required KNN because. 1, to get the categories output (0, 1) from KNN. 2, and it will understand and can make the data to scale. | — | — |
| Qwen3.8 | 29. data Normalization is required KNN because. ⏎ 1. to get the Categories output (0,1) from KNN. ⏎ 2. and it will understand and can make the ⏎ data to scale. | 0.00 | 0.00 |
| Chandra | Input and output ⏎  ⏎ 29. data Normalization is required KNN because. ⏎  ⏎ 1. to get the categories output (0, 1) from KNN. ⏎  ⏎ 2. and it will understand and can make the data to scale. | 0.14 | 0.14 |
| PaddleOCR | Input and output ⏎ 29. data normalization is required KNN because ⏎ 1. to get the Categories output (Co, 1) from KNN ⏎ 2. and 1+ will understand any can make the data to scale. | 0.18 | 0.25 |
| GLM-OCR | data normalization is required KNN because. ⏎ 1. to get the categories output (0,1) from KNN. ⏎ 2. and it will under stand and can make the data to scale. | 0.01 | 0.07 |

### Q30 (S10) — teacher mark: None

_answer not located_
<sub>located on: —</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** |  | — | — |
| Qwen3.8 | ∅ |  |  |
| Chandra | ∅ |  |  |
| PaddleOCR | ∅ |  |  |
| GLM-OCR | ∅ |  |  |

### Q31 (S11) — teacher mark: None

_answer not located_
<sub>located on: —</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** |  | — | — |
| Qwen3.8 | ∅ |  |  |
| Chandra | ∅ |  |  |
| PaddleOCR | ∅ |  |  |
| GLM-OCR | ∅ |  |  |

### Q32 (S12) — teacher mark: None

_answer not located_
<sub>located on: —</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** |  | — | — |
| Qwen3.8 | ∅ |  |  |
| Chandra | ∅ |  |  |
| PaddleOCR | ∅ |  |  |
| GLM-OCR | ∅ |  |  |

### Q33 (S13) — teacher mark: 2.0

![S13](crops/Student_2/S13.jpg)
<sub>located on: Student_2_p2.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 33. gradient descent is an optimization algorithm which commonly uses to train machine learning and nereal network | — | — |
| Qwen3.8 | 33. Gradient descent is an optimization algorithm ⏎ which commonly uses to train machine learning and ⏎ Neural Network | 0.02 | 0.06 |
| Chandra | 32. Gradient descent is an optimization algorithm which commonly used to train machine learning and Neural Network. | 0.03 | 0.12 |
| PaddleOCR | Gradient descent is an Optimization algorithm which commonly uses to train machine learning and neural Network | 0.02 | 0.06 |
| GLM-OCR | gradient descent is an optimization algorithm which commonly uses to train machine learning are Neural Net work | 0.05 | 0.25 |

### Q34 (S14) — teacher mark: None

_answer not located_
<sub>located on: —</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** |  | — | — |
| Qwen3.8 | ∅ |  |  |
| Chandra | ∅ |  |  |
| PaddleOCR | ∅ |  |  |
| GLM-OCR | ∅ |  |  |

### Q35 (S15) — teacher mark: 1.5

![S15](crops/Student_2/S15.jpg)
<sub>located on: Student_2_p3.png</sub>

| reader | text | CER | WER |
|---|---|---|---|
| **Claude (visual check)** | 35. Radial Basis function kernel work ~~really~~ by finding the right thing to ~~sp~~ support and ~~the~~ making the good Classification and also the distance. | — | — |
| Qwen3.8 | 35. Radial Basis function kernel work ~~really~~ by ⏎ finding the right thing to ~~sff~~ support and ⏎ ~~the~~ making the good classification and also ⏎ the distance. | 0.00 | 0.00 |
| Chandra | Radial Basis function kernel work ~~reality~~ by finding the right thing to ~~support~~ support and ~~the~~ making the good classification and also the distance. ⏎  ⏎ Page (5) | 0.05 | 0.10 |
| PaddleOCR | Radial Basis function kernel work reality by finding the right thing to support one. ⏎  ⏎ The making the good Claस et exation are also the distance. ⏎  ⏎ Page (5) | 0.23 | 0.43 |
| GLM-OCR | Radial Basis Function Kernel work really by finding the right thing to support and making the good classification and also the distance. ⏎  ⏎ Page (5) | 0.11 | 0.14 |
