# Mendeley short answers (Q21–Q35) — rubrics to review

Drafted by Claude from the dataset's `answerkey.txt` (the teacher's real rubric is not in the dataset).
Each question is out of **2 marks = 2 concepts × 1 mark**. The grader decides each concept yes/no with a quote
from the student's answer; Python adds the marks. Edit the concepts in `eval/build_mendeley.py` (`RUBRICS`).

**Please check for each question:** are these the 2 things the teacher gave marks for? Should one be mandatory?
Is a 1-mark half answer possible the way the teacher marks?

## Q21. Define Supervised Learning.

*Model answer (answerkey.txt):* A type of ML where the model is trained on labeled data with known inputs and outputs.

1. model is trained on labeled data — 1 mark
2. learns from known inputs and outputs to make predictions — 1 mark

☐ OK   ☐ change: ____________

## Q22. Evaluation Case Study: A model (M1) achieves 99% accuracy on the training set but only 30% accuracy on the testing set. What is happening to this model?

*Model answer (answerkey.txt):* Overfitting; the model has memorized the training data but failed to generalize.

1. identifies the problem as overfitting — 1 mark
2. model memorised training data and fails to generalise to new/test data — 1 mark

☐ OK   ☐ change: ____________

## Q23. What is Regression Analysis?

*Model answer (answerkey.txt):* A statistical process for estimating the relationships between a dependent variable and one or more independent variables.

1. a statistical method / process — 1 mark
2. estimates the relationship between a dependent and independent variable(s) — 1 mark

☐ OK   ☐ change: ____________

## Q24. List and elucidate two major challenges in Machine Learning.

*Model answer (answerkey.txt):* Data quality/missing values, overfitting/underfitting, data collection, or time consumption.

1. names and explains one valid machine-learning challenge — 1 mark
2. names and explains a second, different valid challenge — 1 mark

☐ OK   ☐ change: ____________

## Q25. List any two major real-world applications of Data Science.

*Model answer (answerkey.txt):* Healthcare/disease prediction, Finance/fraud detection, E-commerce recommendation systems.

1. one valid real-world application of data science — 1 mark
2. a second, different valid application — 1 mark

☐ OK   ☐ change: ____________

## Q26. Distinguish between Structured and Semi-structured data.

*Model answer (answerkey.txt):* Structured is organized in rows/columns (SQL, Excel); Semi-structured has some markers but isn't in a grid (JSON, XML, HTML).

1. structured data is organised in rows/columns or tables (e.g. SQL, Excel, CSV) — 1 mark
2. semi-structured data has tags/markers but no fixed table form (e.g. JSON, XML, HTML) — 1 mark

☐ OK   ☐ change: ____________

## Q27. Describe methods used to detect and handle outliers in a dataset.

*Model answer (answerkey.txt):* Detection: Z-score, IQR, Scatter plots, Box plots. Handling: Trimming, Capping, or Imputation.

1. a method to detect outliers (e.g. Z-score, IQR, box or scatter plot) — 1 mark
2. a method to handle outliers (e.g. trimming, capping, imputation) — 1 mark

☐ OK   ☐ change: ____________

## Q28. What is Data Pre-processing?

*Model answer (answerkey.txt):* The steps taken to clean and transform raw data into a format suitable for a machine learning model.

1. cleaning raw data (missing, incorrect or noisy values) — 1 mark
2. transforming data into a form suitable for a model — 1 mark

☐ OK   ☐ change: ____________

## Q29. Why is Data Normalization required for the K-Nearest Neighbors (K-NN) algorithm?

*Model answer (answerkey.txt):* K-NN is distance-based; features with larger scales will dominate the distance calculation if not normalized.

1. K-NN relies on distances between points — 1 mark
2. features with larger scales dominate the distance unless normalised — 1 mark

☐ OK   ☐ change: ____________

## Q30. How are continuous attributes discretized? Give an example.

*Model answer (answerkey.txt):* By grouping values into bins or intervals, e.g., turning ages 1-100 into 'Child,' 'Adult,' 'Senior.'

1. continuous values are grouped into bins / intervals — 1 mark
2. gives a valid example of discretisation — 1 mark

☐ OK   ☐ change: ____________

## Q31. What does the 'K' represent in the K-Means clustering algorithm?

*Model answer (answerkey.txt):* The predefined number of clusters or groups the data will be divided into.

1. K is the number of clusters — 1 mark
2. K is chosen / fixed beforehand — 1 mark

☐ OK   ☐ change: ____________

## Q32. Name three common Hyperparameters in Machine Learning algorithms.

*Model answer (answerkey.txt):* K in K-NN, Learning Rate, Number of Estimators/Trees, Max Depth, or Batch Size.

1. names at least two valid hyperparameters — 1 mark
2. names a third valid hyperparameter — 1 mark

☐ OK   ☐ change: ____________

## Q33. Define Gradient Descent.

*Model answer (answerkey.txt):* An optimization algorithm used to minimize the cost function by iteratively moving toward the steepest descent.

1. an optimisation algorithm that minimises a cost / loss function — 1 mark
2. iteratively updates parameters in the direction of steepest descent (negative gradient) — 1 mark

☐ OK   ☐ change: ____________

## Q34. Classifier Comparison: Compare three SVM classifiers based on their margins and boundaries.

*Model answer (answerkey.txt):* Discussion on maximizing the margin and ensuring no data points fall within the 'gutter' or margin.

1. compares the classifiers by margin width (wider margin is better) — 1 mark
2. considers whether data points fall inside the margin / gutter — 1 mark

☐ OK   ☐ change: ____________

## Q35. Explain how the Radial Basis Function (RBF) Kernel works in SVM.

*Model answer (answerkey.txt):* It transforms data into a higher-dimensional space to find a non-linear decision boundary.

1. maps data into a higher-dimensional space — 1 mark
2. allows a non-linear decision boundary — 1 mark

☐ OK   ☐ change: ____________
