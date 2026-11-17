# reference_material_text.py — original study notes for the upload kit's answer-key assistant test (Pattern 3, Data Science).
# Written for this project (not copied from the dataset or a book). Each entry is (heading, paragraph); the notes cover
# the 15 written questions of the Data Science paper in more words than the one-line answers, plus a few topics
# the paper does not ask about, so the assistant has to pick the right passages.

NOTES_PART1 = ("Data Science lecture notes, part 1: data and basic ideas", [
    ("1. Supervised learning",
     "Supervised learning is a type of machine learning in which the model is trained on labeled data: every training "
     "example comes with an input and the known correct output. The model learns the mapping from inputs to outputs and "
     "is then used to predict the output for new inputs. Two main tasks belong here. Classification predicts a category, "
     "for example whether an email is spam or not spam. Regression predicts a number, for example the price of a house. "
     "Because the correct answers are known during training, the predictions can be compared with them and the model "
     "improved. Unsupervised learning, in contrast, works with unlabeled data."),
    ("2. Overfitting and underfitting",
     "A model is overfitting when it fits the training data too closely, including its noise, and so fails on new data. "
     "The typical sign is a large gap between training and testing performance. If a model M1 reaches 99% accuracy on the "
     "training set but only 30% on the testing set, it has memorized the training examples instead of learning a general "
     "pattern: this is overfitting, and the model has failed to generalize. Underfitting is the opposite: the model is too "
     "simple to capture the pattern and performs badly on both training and testing data. Overfitting can be reduced with "
     "more training data, a simpler model, regularization, early stopping or cross-validation."),
    ("3. Regression analysis",
     "Regression analysis is a statistical process for estimating the relationship between a dependent variable and one "
     "or more independent variables. In simple linear regression the relationship is a straight line, y = b0 + b1 x + e, "
     "where b0 is the intercept, b1 the slope and e the error. The coefficients are usually found by the method of least "
     "squares, which minimizes the sum of squared differences between actual and predicted values. Regression is used when "
     "the quantity to predict is continuous, such as temperature, sales or price."),
    ("4. Challenges in machine learning",
     "Several challenges limit what machine learning can do in practice. Data quality: real data contains missing values, "
     "duplicates, errors and noise, and a model trained on poor data gives poor predictions. Overfitting and underfitting "
     "make a model fail on new data. Data collection can be expensive, slow or restricted by privacy rules, and too little "
     "data gives unreliable models. Time and computing cost: training large models on large datasets takes hours or days "
     "and needs specialized hardware. Other challenges are bias in the data and models that are hard to interpret."),
    ("5. Applications of data science",
     "Data science is applied in almost every field. In healthcare it is used for disease prediction and diagnosis from "
     "patient records and medical images. In finance it is used for fraud detection, credit scoring and risk analysis. "
     "E-commerce companies use recommendation systems that suggest products from a customer's earlier behavior. Other "
     "applications include route planning in transport, demand forecasting in retail, and weather prediction."),
    ("6. Structured, semi-structured and unstructured data",
     "Structured data is organized in a fixed grid of rows and columns with a defined schema, for example a SQL table or an "
     "Excel sheet, so it is easy to search and analyze. Semi-structured data has some organizing markers such as tags or "
     "keys but does not fit a fixed table; examples are JSON, XML and HTML documents. Unstructured data has no predefined "
     "format at all, for example free text, images, audio and video. The main difference between structured and "
     "semi-structured data is therefore the rigid table layout of the first against the flexible, self-describing "
     "markers of the second."),
    ("7. Detecting and handling outliers",
     "An outlier is a value that lies far away from the rest of the data. Detection methods: the Z-score method flags "
     "values more than about 3 standard deviations from the mean; the IQR rule flags values below Q1 - 1.5 x IQR or above "
     "Q3 + 1.5 x IQR; box plots and scatter plots show outliers visually. Handling methods: trimming removes the outlying "
     "rows; capping (also called winsorizing) replaces extreme values by a chosen limit; imputation replaces them with a "
     "typical value such as the median. The choice depends on whether the outlier is an error or a genuine rare event."),
    ("8. Data pre-processing",
     "Data pre-processing is the set of steps that clean and transform raw data into a format suitable for a machine "
     "learning model. It includes data cleaning (handling missing values, removing duplicates and noise), data integration "
     "(combining several sources), data transformation (scaling, normalization, encoding categories) and data reduction "
     "(selecting features, reducing dimensions). Good pre-processing usually improves model accuracy more than changing "
     "the algorithm."),
    ("9. Normalization and the K-nearest neighbors algorithm",
     "Data normalization rescales features to a common range, for example min-max scaling x' = (x - min) / (max - min) "
     "to the range 0 to 1, or the z-score. It is needed for the K-nearest neighbors (K-NN) algorithm because K-NN is "
     "distance-based: it classifies a point by the distances to its nearest training points. If one feature has a much "
     "larger scale, such as income in thousands against age in tens, it dominates the distance calculation and the other "
     "features are practically ignored. Normalizing makes every feature contribute fairly."),
])

NOTES_PART2 = ("Data Science lecture notes, part 2: models and optimization", [
    ("10. Discretization of continuous attributes",
     "Discretization converts a continuous attribute into a small number of categories. Continuous values are grouped "
     "into bins or intervals. Equal-width binning makes intervals of the same size; equal-frequency binning puts about the "
     "same number of values in each bin. Example: the ages 1 to 100 can be turned into the labels Child (0-12), Teenager "
     "(13-19), Adult (20-59) and Senior (60 and above). Discretization simplifies the data and can make some algorithms, "
     "such as decision trees and naive Bayes, work better."),
    ("11. K-Means clustering",
     "K-Means is an unsupervised algorithm that divides data into groups called clusters. The letter K stands for the "
     "predefined number of clusters the data will be divided into; it is chosen before the algorithm runs. The algorithm "
     "starts with K centroids, assigns every point to the nearest centroid, recomputes each centroid as the mean of its "
     "points, and repeats until the assignments no longer change. A common way to choose K is the elbow method."),
    ("12. Hyperparameters",
     "Hyperparameters are settings chosen before training that control how a model learns; unlike parameters they are not "
     "learned from the data. Common examples: the value of K in K-NN, the learning rate in gradient descent, the number "
     "of estimators (trees) in a random forest, the maximum depth of a decision tree, the batch size and the number of "
     "epochs, and the regularization strength C in an SVM. Hyperparameters are tuned with grid search, random search "
     "and cross-validation."),
    ("13. Gradient descent",
     "Gradient descent is an optimization algorithm used to minimize a cost (loss) function. It starts from an initial "
     "guess and repeatedly moves the parameters a small step in the direction of the steepest descent, which is the "
     "negative of the gradient: theta = theta - alpha x gradient of J(theta). The step size alpha is the learning rate. "
     "If alpha is too large the steps overshoot and may diverge; if it is too small, learning is very slow. Variants are "
     "batch, stochastic and mini-batch gradient descent, which differ in how many examples are used for each step."),
    ("14. Support vector machines and the margin",
     "A support vector machine (SVM) separates two classes with the hyperplane that has the largest margin. The margin is "
     "the distance between the boundary and the closest training points of each class; those closest points are the "
     "support vectors and they lie on the edge of the margin, sometimes called the gutter. When comparing several SVM "
     "classifiers, the better one has the wider margin, because a boundary that passes close to points is sensitive to "
     "noise and generalizes worse. A hard-margin classifier allows no point inside the margin and works only for "
     "separable data. A soft-margin classifier allows some points inside the margin or misclassified, controlled by the "
     "parameter C: a large C gives a narrow margin and few violations, a small C gives a wider margin and more violations."),
    ("15. Kernels and the Radial Basis Function (RBF) kernel",
     "When the classes cannot be separated by a straight line, an SVM uses a kernel. A kernel function computes the "
     "similarity of two points as if the data had been transformed into a higher-dimensional space where a linear "
     "separation exists, without computing that transformation (the kernel trick). The RBF kernel is K(x, x') = "
     "exp(-gamma x ||x - x'||^2). The similarity is 1 for identical points and falls towards 0 as the distance grows; "
     "gamma sets how quickly. Working in this implicit higher-dimensional space, the SVM finds a linear boundary that "
     "appears as a non-linear decision boundary in the original space. A very large gamma makes the boundary too "
     "wiggly and causes overfitting."),
    ("16. Decision trees (not asked in the paper)",
     "A decision tree classifies an example by asking a sequence of questions about its features, one at each node, until "
     "a leaf gives the class. The question at each node is chosen to give the largest drop in impurity, measured by "
     "entropy or the Gini index. Deep trees overfit, so the depth is limited or the tree is pruned."),
    ("17. Cross-validation (not asked in the paper)",
     "In k-fold cross-validation the data is split into k equal parts. The model is trained k times, each time holding "
     "out a different part for testing, and the k scores are averaged. This gives a more reliable estimate of how the "
     "model will perform on new data than a single train-test split."),
])

# A short revision sheet: bullet points that mix the topics (answers are partial, so the assistant must combine files)
REVISION = """Data Science revision sheet (quick points, not complete answers)

- Supervised = labeled data; unsupervised = no labels. Clustering is unsupervised.
- Train 99% / test 30% means the model memorized the training data (overfitting). Use more data or regularization.
- Regression predicts a number from one or more independent variables; classification predicts a category.
- Missing values, noise and small datasets are the usual data problems; training time grows with data size.
- Fraud detection (finance), disease prediction (healthcare), recommendations (e-commerce).
- JSON and XML are semi-structured; a SQL table is structured; images and free text are unstructured.
- Outlier rules: |z| > 3, or outside Q1 - 1.5 IQR to Q3 + 1.5 IQR. Cap, trim or impute.
- Always scale features before K-NN or K-Means because both use distances.
- Hyperparameters are set by you (K, learning rate, depth, trees, batch size); parameters are learned.
- SVM: maximize the margin; support vectors sit on the margin; C trades margin width against errors.
- RBF kernel: similarity decays with distance; gamma controls the width; equivalent to an infinite-dimensional mapping.
- Principal component analysis (PCA) reduces the number of features while keeping most of the variance.
- The bias-variance trade-off: simple models have high bias, complex models have high variance.
"""

# The scanned page: a topic the paper does not ask about, saved as an image (no text layer)
SCANNED = ("Chapter 6: Ensemble methods", [
    "An ensemble combines several models to get a better prediction than any single model.",
    "Bagging trains each model on a random sample of the data and averages the results (random forest).",
    "Boosting trains models one after another, each one focusing on the mistakes of the previous one.",
    "Ensembles usually reduce variance and are less likely to overfit than one deep decision tree.",
])
