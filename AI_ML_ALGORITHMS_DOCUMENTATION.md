# AI/ML Algorithms and Statistical Tests Documentation

## Overview
This document provides a comprehensive explanation of all Large Language Models (LLMs), machine learning algorithms, scoring methods, and statistical tests used in the SkillScreen text service, along with the mathematical foundations and rationale for each.

---

## 1. Large Language Models (LLMs)

### 1.1 Google Gemini Pro
**Location:** `backend/text-service/services/llm_service.py`

**Purpose:** Primary LLM for generating personalized interview questions

**Why Used:**
- **Contextual Understanding:** Gemini Pro excels at understanding candidate backgrounds, job requirements, and interview context
- **Personalization:** Generates questions tailored to specific candidate experience levels and skills
- **Natural Language Generation:** Produces conversational, human-like questions rather than robotic templates
- **Multi-turn Context:** Maintains context across previous questions to avoid repetition

**Mathematical Foundation:**
- Transformer architecture with attention mechanisms
- Probability distribution over vocabulary: P(word|context) = softmax(W·h + b)
- Context encoding: h = TransformerEncoder(candidate_context, job_context, previous_questions)

**Usage:**
```python
# Generates questions like:
"Hi John! With your 5 years of experience, how would you approach 
architecting a scalable backend solution?"
```

---

### 1.2 Hugging Face Transformers Models

#### 1.2.1 Sentence Transformer: `all-MiniLM-L6-v2`
**Location:** `backend/text-service/services/nlp_service.py`, `rag_service.py`

**Purpose:** Semantic similarity and embedding generation

**Why Used:**
- **Efficiency:** Lightweight (80MB) with 384-dimensional embeddings
- **Semantic Understanding:** Captures meaning beyond keyword matching
- **Fast Inference:** Optimized for production use
- **Cosine Similarity:** Enables relevance scoring between questions and responses

**Mathematical Foundation:**
- **Embedding Generation:** E(text) = SentenceTransformer(text) → R^384
- **Cosine Similarity:** 
  ```
  similarity(q, r) = (E(q) · E(r)) / (||E(q)|| × ||E(r)||)
  ```
  Where q = question, r = response
- **Relevance Score:** score = similarity(q, r) × 10 (normalized to 0-10 scale)

**Usage:**
- Question-response relevance scoring
- RAG-based evidence retrieval
- Semantic search in knowledge base

---

#### 1.2.2 Sentiment Analysis: `cardiffnlp/twitter-roberta-base-sentiment-latest`
**Location:** `backend/text-service/services/nlp_service.py`

**Purpose:** Analyze sentiment and tone of interview responses

**Why Used:**
- **Professional Tone Detection:** Identifies positive, neutral, or negative sentiment
- **Communication Quality:** Helps assess candidate's communication style
- **Engagement Indicators:** Positive sentiment correlates with candidate engagement

**Mathematical Foundation:**
- **Classification:** P(sentiment|text) = softmax(W·RoBERTa(text) + b)
- **Score Mapping:**
  - POSITIVE: score = 7.0 + (confidence × 3.0) → [7.0, 10.0]
  - NEUTRAL: score = 5.0 + (confidence × 2.0) → [5.0, 7.0]
  - NEGATIVE: score = max(0, 5.0 - (confidence × 5.0)) → [0.0, 5.0]

**Usage:**
- Evaluates if responses demonstrate positive, professional communication
- Flags overly negative or unprofessional responses

---

#### 1.2.3 Question-Answering: `distilbert-base-cased-distilled-squad`
**Location:** `backend/text-service/services/nlp_service.py`

**Purpose:** Context understanding and answer extraction

**Why Used:**
- **Context Comprehension:** Understands if responses address the question
- **Answer Extraction:** Identifies relevant parts of responses
- **Efficiency:** DistilBERT provides faster inference than full BERT

**Mathematical Foundation:**
- **Span Prediction:** P(start, end|question, context) = softmax(W·BERT(question, context))
- **Answer Extraction:** answer = context[start:end] where (start, end) = argmax(P)

**Usage:**
- Validates that responses contain relevant information
- Extracts key points from candidate responses

---

#### 1.2.4 Text Summarization: `facebook/bart-large-cnn`
**Location:** `backend/text-service/services/nlp_service.py`

**Purpose:** Generate concise feedback summaries

**Why Used:**
- **Conciseness:** Creates brief, actionable feedback
- **Key Point Extraction:** Identifies most important aspects of responses
- **Readability:** Produces human-readable summaries

**Mathematical Foundation:**
- **Sequence-to-Sequence:** P(summary|response) = BART_decoder(BART_encoder(response))
- **Beam Search:** Generates most likely summary sequences

**Usage:**
- Generates executive summaries of interview evaluations
- Creates concise feedback for candidates

---

## 2. Machine Learning Scoring Algorithms

### 2.1 XGBoost (Extreme Gradient Boosting)
**Location:** `backend/text-service/services/quality_prediction_service.py`

**Purpose:** Primary model for predicting response quality scores

**Why Used:**
- **High Performance:** State-of-the-art performance on tabular data
- **Feature Importance:** Provides interpretable feature contributions
- **Handles Non-linearity:** Captures complex interactions between features
- **Robust to Overfitting:** Regularization prevents overfitting

**Mathematical Foundation:**
- **Objective Function:**
  ```
  L(θ) = Σ l(y_i, ŷ_i) + Σ Ω(f_k)
  ```
  Where:
  - l = loss function (squared error for regression)
  - Ω = regularization term
  - f_k = k-th tree

- **Gradient Boosting:**
  ```
  ŷ_i^(t) = ŷ_i^(t-1) + η × f_t(x_i)
  ```
  Where:
  - η = learning rate (0.1)
  - f_t = t-th tree
  - t = iteration number

- **Tree Construction:** Minimizes loss using gradient descent on tree structure

**Hyperparameters:**
- `n_estimators=100`: Number of boosting rounds
- `max_depth=6`: Maximum tree depth
- `learning_rate=0.1`: Shrinkage parameter
- `objective='reg:squarederror'`: Regression with squared error loss

**Usage:**
- Predicts quality scores (0-10) for interview responses
- Ensemble member with 25% weight in final prediction

---

### 2.2 LightGBM (Light Gradient Boosting Machine)
**Location:** `backend/text-service/services/quality_prediction_service.py`

**Purpose:** Alternative gradient boosting model for ensemble prediction

**Why Used:**
- **Speed:** Faster training and inference than XGBoost
- **Memory Efficiency:** Lower memory footprint
- **Accuracy:** Competitive performance with XGBoost
- **Ensemble Diversity:** Different algorithm provides complementary predictions

**Mathematical Foundation:**
- **Leaf-wise Growth:** Grows trees leaf-by-leaf instead of level-by-level
- **Gradient-based One-Side Sampling (GOSS):** Focuses on samples with large gradients
- **Exclusive Feature Bundling (EFB):** Reduces feature space efficiently

**Hyperparameters:**
- `n_estimators=100`: Number of boosting iterations
- `max_depth=6`: Maximum tree depth
- `learning_rate=0.1`: Learning rate
- `objective='regression'`: Regression task

**Usage:**
- Ensemble member with 25% weight in final prediction
- Provides alternative perspective to XGBoost

---

### 2.3 Random Forest Regressor
**Location:** `backend/text-service/services/quality_prediction_service.py`

**Purpose:** Fallback ensemble model for quality prediction

**Why Used:**
- **Robustness:** Less sensitive to outliers than gradient boosting
- **No Overfitting:** Bagging reduces overfitting risk
- **Feature Importance:** Provides interpretable feature contributions
- **Always Available:** No external dependencies

**Mathematical Foundation:**
- **Bootstrap Aggregating (Bagging):**
  ```
  ŷ = (1/B) × Σ f_b(x)
  ```
  Where:
  - B = number of trees (100)
  - f_b = b-th tree trained on bootstrap sample

- **Feature Selection:** `max_features='sqrt'` randomly selects √n features per split
- **Variance Reduction:** Averaging reduces prediction variance

**Hyperparameters:**
- `n_estimators=100`: Number of trees
- `max_depth=10`: Maximum tree depth
- `min_samples_leaf=1`: Minimum samples per leaf
- `max_features='sqrt'`: Features considered per split

**Usage:**
- Fallback model when XGBoost/LightGBM unavailable
- Ensemble member with 5% weight

---

### 2.4 Gradient Boosting Regressor (Scikit-learn)
**Location:** `backend/text-service/services/quality_prediction_service.py`

**Purpose:** Additional ensemble member for quality prediction

**Why Used:**
- **Standard Implementation:** Well-tested scikit-learn implementation
- **Consistency:** Provides stable baseline predictions
- **Ensemble Diversity:** Different implementation adds diversity

**Mathematical Foundation:**
- **Sequential Boosting:**
  ```
  F_m(x) = F_{m-1}(x) + γ_m × h_m(x)
  ```
  Where:
  - h_m = weak learner (decision tree)
  - γ_m = step size (learning rate = 0.1)

- **Loss Minimization:** Minimizes squared error loss

**Hyperparameters:**
- `n_estimators=100`: Number of boosting stages
- `max_depth=6`: Maximum tree depth
- `learning_rate=0.1`: Learning rate

**Usage:**
- Ensemble member with 5% weight
- Provides additional prediction stability

---

### 2.5 Isolation Forest (Anomaly Detection)
**Location:** `backend/text-service/services/behavioral_analysis_service.py`

**Purpose:** Detect anomalous behavioral patterns in candidate responses

**Why Used:**
- **Unsupervised Learning:** No labeled anomaly data required
- **Efficiency:** O(n log n) time complexity
- **High-dimensional Data:** Works well with multiple behavioral features
- **Interpretability:** Provides anomaly scores for each response

**Mathematical Foundation:**
- **Isolation Principle:** Anomalies are easier to isolate (fewer splits needed)
- **Path Length:** 
  ```
  anomaly_score = 2^(-E(h(x))/c(n))
  ```
  Where:
  - h(x) = average path length to isolate x
  - c(n) = normalization constant
  - E = expected value

- **Decision Rule:**
  - score < 0 → anomaly (outlier)
  - score > 0 → normal

**Hyperparameters:**
- `contamination=0.1`: Expected proportion of anomalies (10%)
- `n_estimators=100`: Number of trees
- `random_state=42`: Reproducibility

**Usage:**
- Detects unusual response patterns (e.g., sudden quality drop, erratic behavior)
- Flags candidates with inconsistent performance

---

### 2.6 K-Means Clustering
**Location:** `backend/text-service/services/behavioral_analysis_service.py`

**Purpose:** Classify candidate behavior into distinct patterns

**Why Used:**
- **Behavior Classification:** Groups similar behavioral patterns
- **Unsupervised Learning:** No labeled behavior data required
- **Interpretability:** Clear cluster assignments
- **Efficiency:** Fast clustering algorithm

**Mathematical Foundation:**
- **Objective Function:**
  ```
  J = Σ Σ ||x_i - μ_k||²
  ```
  Where:
  - x_i = i-th data point (behavioral features)
  - μ_k = k-th cluster centroid
  - Minimize sum of squared distances

- **Centroid Update:**
  ```
  μ_k = (1/|C_k|) × Σ x_i
  ```
  Where C_k = k-th cluster

- **Assignment:**
  ```
  c_i = argmin_k ||x_i - μ_k||²
  ```

**Hyperparameters:**
- `n_clusters=4`: Four behavior types (engaged, declining, consistent, erratic)
- `n_init=10`: Number of random initializations
- `random_state=42`: Reproducibility

**Behavior Types:**
1. **Engaged:** High engagement, consistent quality
2. **Declining:** Decreasing engagement over time
3. **Consistent:** Stable but moderate performance
4. **Erratic:** Inconsistent patterns

**Usage:**
- Classifies candidate behavior patterns
- Helps identify candidates who may need additional support

---

## 3. Statistical Tests

### 3.1 Independent Samples T-Test
**Location:** `backend/text-service/services/bias_detection_service.py`

**Purpose:** Test for significant differences in mean scores between demographic groups

**Why Used:**
- **Mean Comparison:** Detects systematic scoring differences
- **Statistical Rigor:** Provides p-values for significance testing
- **Standard Test:** Well-established statistical method
- **Hypothesis Testing:** Tests H₀: μ₁ = μ₂ vs H₁: μ₁ ≠ μ₂

**Mathematical Foundation:**
- **Test Statistic:**
  ```
  t = (x̄₁ - x̄₂) / (s_p × √(1/n₁ + 1/n₂))
  ```
  Where:
  - x̄₁, x̄₂ = sample means
  - s_p = pooled standard deviation
  - n₁, n₂ = sample sizes

- **Pooled Standard Deviation:**
  ```
  s_p = √(((n₁-1)s₁² + (n₂-1)s₂²) / (n₁+n₂-2))
  ```

- **Degrees of Freedom:** df = n₁ + n₂ - 2

- **P-value:** Probability of observing t-statistic under null hypothesis

**Interpretation:**
- p < 0.05 → Significant difference (reject H₀)
- p ≥ 0.05 → No significant difference (fail to reject H₀)

**Usage:**
- Compares mean scores across demographic groups
- Detects systematic bias in scoring

---

### 3.2 Mann-Whitney U Test (Non-parametric)
**Location:** `backend/text-service/services/bias_detection_service.py`

**Purpose:** Non-parametric alternative to t-test for non-normal distributions

**Why Used:**
- **No Distribution Assumptions:** Works with non-normal data
- **Robustness:** Less sensitive to outliers
- **Ordinal Data:** Works with ordinal (ranked) data
- **Small Samples:** More reliable with small sample sizes

**Mathematical Foundation:**
- **Rank Sum Test:**
  ```
  U₁ = n₁n₂ + (n₁(n₁+1)/2) - R₁
  U₂ = n₁n₂ + (n₂(n₂+1)/2) - R₂
  ```
  Where:
  - R₁, R₂ = sum of ranks for groups 1 and 2
  - U = min(U₁, U₂)

- **Z-score (for large samples):**
  ```
  z = (U - μ_U) / σ_U
  ```
  Where:
  - μ_U = n₁n₂/2
  - σ_U = √(n₁n₂(n₁+n₂+1)/12)

- **P-value:** Probability of observing U-statistic under null hypothesis

**Interpretation:**
- p < 0.05 → Significant difference in distributions
- p ≥ 0.05 → No significant difference

**Usage:**
- Validates t-test results when data is non-normal
- Provides robust bias detection

---

### 3.3 Cohen's d (Effect Size)
**Location:** `backend/text-service/services/bias_detection_service.py`

**Purpose:** Quantify the magnitude of differences between groups

**Why Used:**
- **Practical Significance:** P-values don't indicate effect size
- **Standardized Measure:** Allows comparison across different metrics
- **Interpretability:** Clear thresholds for small/medium/large effects
- **Complement to P-values:** Provides context for statistical significance

**Mathematical Foundation:**
- **Cohen's d:**
  ```
  d = (x̄₁ - x̄₂) / s_pooled
  ```
  Where:
  - x̄₁, x̄₂ = group means
  - s_pooled = pooled standard deviation

- **Pooled Standard Deviation:**
  ```
  s_pooled = √(((n₁-1)s₁² + (n₂-1)s₂²) / (n₁+n₂-2))
  ```

**Interpretation (Cohen's Conventions):**
- |d| < 0.2 → Negligible effect
- 0.2 ≤ |d| < 0.5 → Small effect
- 0.5 ≤ |d| < 0.8 → Medium effect
- |d| ≥ 0.8 → Large effect

**Usage:**
- Quantifies bias magnitude when significant differences are detected
- Helps prioritize which biases need immediate attention

---

### 3.4 Demographic Parity
**Location:** `backend/text-service/services/bias_detection_service.py`

**Purpose:** Ensure equal pass rates across demographic groups

**Why Used:**
- **Fairness Metric:** Core fairness principle in ML/AI
- **Equal Opportunity:** Ensures all groups have equal chances of passing
- **Regulatory Compliance:** Required by many fairness regulations
- **Transparency:** Clear, interpretable fairness measure

**Mathematical Foundation:**
- **Pass Rate:**
  ```
  pass_rate_g = (number of candidates with score ≥ threshold) / total_candidates_g
  ```

- **Parity Check:**
  ```
  violation = |pass_rate_g1 - pass_rate_g2| > threshold
  ```
  Where threshold = 0.1 (10% difference)

- **Demographic Parity:**
  ```
  P(score ≥ threshold | group=g₁) = P(score ≥ threshold | group=g₂)
  ```

**Interpretation:**
- Difference ≤ 10% → No violation (fair)
- Difference > 10% → Violation (potential bias)

**Usage:**
- Monitors fairness across demographic groups
- Flags when pass rates differ significantly

---

### 3.5 Equal Opportunity
**Location:** `backend/text-service/services/bias_detection_service.py`

**Purpose:** Ensure equal true positive rates (pass rates for qualified candidates)

**Why Used:**
- **Qualified Candidates:** Focuses on candidates who meet minimum qualifications
- **More Nuanced:** Considers qualification levels, not just raw scores
- **Fairness Principle:** Ensures qualified candidates have equal opportunities
- **Complement to Demographic Parity:** Provides additional fairness check

**Mathematical Foundation:**
- **True Positive Rate (TPR):**
  ```
  TPR_g = P(score ≥ pass_threshold | qualified=true, group=g)
  ```

- **Qualification Threshold:** score ≥ 6.0 (qualified)
- **Pass Threshold:** score ≥ 7.0 (pass)

- **Equal Opportunity:**
  ```
  TPR_g1 = TPR_g2
  ```

- **Violation Check:**
  ```
  violation = |TPR_g1 - TPR_g2| > threshold
  ```
  Where threshold = 0.15 (15% difference)

**Interpretation:**
- Difference ≤ 15% → No violation
- Difference > 15% → Violation (potential bias)

**Usage:**
- Ensures qualified candidates from all groups have equal pass rates
- More targeted than demographic parity

---

## 4. Feature Engineering and Preprocessing

### 4.1 StandardScaler (Feature Normalization)
**Location:** `backend/text-service/services/quality_prediction_service.py`, `behavioral_analysis_service.py`

**Purpose:** Normalize features to zero mean and unit variance

**Why Used:**
- **Algorithm Requirements:** Many ML algorithms require normalized features
- **Convergence:** Helps gradient-based algorithms converge faster
- **Feature Comparability:** Allows comparison of features on different scales
- **Distance Metrics:** Essential for distance-based algorithms (K-Means, Isolation Forest)

**Mathematical Foundation:**
- **Z-score Normalization:**
  ```
  z = (x - μ) / σ
  ```
  Where:
  - μ = mean of feature
  - σ = standard deviation of feature

- **Fit:** Calculate μ and σ from training data
- **Transform:** Apply normalization to new data

**Usage:**
- Normalizes 20+ features before ML model training
- Ensures all features contribute equally to predictions

---

### 4.2 Cosine Similarity
**Location:** `backend/text-service/services/nlp_service.py`

**Purpose:** Measure semantic similarity between question and response

**Why Used:**
- **Semantic Understanding:** Captures meaning beyond keyword matching
- **Normalized:** Returns values in [-1, 1] range
- **Efficient:** Fast computation for embeddings
- **Interpretable:** Higher values = more similar

**Mathematical Foundation:**
- **Cosine Similarity:**
  ```
  similarity = (A · B) / (||A|| × ||B||)
  ```
  Where:
  - A, B = embedding vectors
  - · = dot product
  - || || = L2 norm

- **Geometric Interpretation:** Cosine of angle between vectors
- **Range:** [-1, 1] (typically [0, 1] for normalized embeddings)

**Usage:**
- Measures question-response relevance
- Ranks evidence in RAG system

---

### 4.3 Jaccard Similarity (Set-based)
**Location:** `backend/text-service/services/anti_cheating_service.py`

**Purpose:** Detect duplicate responses using word overlap

**Why Used:**
- **Simplicity:** Easy to compute and interpret
- **Efficiency:** Fast for duplicate detection
- **Set Operations:** Natural for text comparison
- **Threshold-based:** Clear cutoff for duplicates (0.85)

**Mathematical Foundation:**
- **Jaccard Similarity:**
  ```
  J(A, B) = |A ∩ B| / |A ∪ B|
  ```
  Where:
  - A, B = sets of words
  - ∩ = intersection
  - ∪ = union

- **Range:** [0, 1]
  - 0 = no overlap
  - 1 = identical sets

**Usage:**
- Detects duplicate/near-duplicate responses
- Flags candidates copying previous answers

---

## 5. Feature Extraction

### 5.1 Behavioral Features
**Location:** `backend/text-service/services/behavioral_analysis_service.py`

**Features Extracted:**
1. **Response Length:** Number of words
2. **Complexity Score:** 
   ```
   complexity = 0.3×avg_word_length + 0.3×avg_sentence_length + 0.4×vocab_diversity×10
   ```
3. **Engagement Score:** Count of engagement indicators
4. **Personal Pronoun Ratio:** personal_pronouns / total_words
5. **Example Ratio:** specific_examples / total_words
6. **Uncertainty Ratio:** uncertainty_markers / total_words
7. **Confidence Ratio:** confidence_markers / total_words
8. **Response Time:** Time taken to respond (seconds)

**Why These Features:**
- **Behavioral Patterns:** Capture candidate engagement and consistency
- **ML Input:** Required for Isolation Forest and K-Means
- **Interpretability:** Human-understandable metrics

---

### 5.2 Quality Prediction Features
**Location:** `backend/text-service/services/quality_prediction_service.py`

**Features Extracted (20+ features):**
1. **Text Features:**
   - Response length, sentence count, avg sentence length, avg word length
   - Vocabulary diversity (unique_words / total_words)

2. **Content Features:**
   - Keyword overlap with question
   - Personal pronouns, specific examples, quantifiers, technical terms
   - Engagement score, structure indicators, conclusion markers

3. **Complexity Features:**
   - Complexity score (same as behavioral analysis)

4. **Context Features:**
   - Candidate experience years, skill count
   - Job skill requirements, experience level

**Why These Features:**
- **Comprehensive Coverage:** Captures multiple aspects of response quality
- **ML Performance:** More features improve model accuracy
- **Interpretability:** Feature importance provides insights

---

## 6. Ensemble Methods

### 6.1 Weighted Ensemble Averaging
**Location:** `backend/text-service/services/quality_prediction_service.py`

**Purpose:** Combine predictions from multiple models

**Why Used:**
- **Robustness:** Reduces variance and overfitting
- **Performance:** Typically outperforms single models
- **Diversity:** Different algorithms capture different patterns

**Mathematical Foundation:**
- **Weighted Average:**
  ```
  ŷ_ensemble = Σ (w_i × ŷ_i) / Σ w_i
  ```
  Where:
  - w_i = weight for model i
  - ŷ_i = prediction from model i

- **Weights:**
  - Primary model: 0.4 (40%)
  - XGBoost: 0.25 (25%)
  - LightGBM: 0.25 (25%)
  - Gradient Boosting: 0.05 (5%)
  - Random Forest: 0.05 (5%)

**Usage:**
- Combines predictions from 4-5 models
- Produces final quality score prediction

---

## 7. Evaluation Metrics

### 7.1 Mean Squared Error (MSE)
**Location:** `backend/text-service/services/quality_prediction_service.py`

**Purpose:** Measure prediction accuracy during model training

**Mathematical Foundation:**
```
MSE = (1/n) × Σ (y_i - ŷ_i)²
```

**Why Used:**
- **Sensitivity to Outliers:** Penalizes large errors more
- **Standard Metric:** Widely used in regression
- **Differentiable:** Required for gradient-based optimization

---

### 7.2 Mean Absolute Error (MAE)
**Location:** `backend/text-service/services/quality_prediction_service.py`

**Purpose:** Measure average prediction error

**Mathematical Foundation:**
```
MAE = (1/n) × Σ |y_i - ŷ_i|
```

**Why Used:**
- **Interpretability:** Average error in same units as target
- **Robustness:** Less sensitive to outliers than MSE
- **Complement to MSE:** Provides different perspective

---

### 7.3 R² Score (Coefficient of Determination)
**Location:** `backend/text-service/services/quality_prediction_service.py`

**Purpose:** Measure proportion of variance explained by model

**Mathematical Foundation:**
```
R² = 1 - (SS_res / SS_tot)
```
Where:
- SS_res = Σ (y_i - ŷ_i)² (residual sum of squares)
- SS_tot = Σ (y_i - ȳ)² (total sum of squares)

**Interpretation:**
- R² = 1.0 → Perfect predictions
- R² = 0.0 → Model performs as well as mean baseline
- R² < 0.0 → Model worse than baseline

**Why Used:**
- **Standardized Metric:** Allows comparison across datasets
- **Interpretability:** Percentage of variance explained
- **Model Selection:** Higher R² = better model

---

## 8. Summary

### Algorithms by Category:

**LLMs (5):**
1. Google Gemini Pro (question generation)
2. Sentence Transformer (semantic similarity)
3. RoBERTa (sentiment analysis)
4. DistilBERT (QA)
5. BART (summarization)

**ML Models (6):**
1. XGBoost (quality prediction)
2. LightGBM (quality prediction)
3. Random Forest (quality prediction)
4. Gradient Boosting (quality prediction)
5. Isolation Forest (anomaly detection)
6. K-Means (behavior clustering)

**Statistical Tests (5):**
1. T-test (mean comparison)
2. Mann-Whitney U (non-parametric comparison)
3. Cohen's d (effect size)
4. Demographic Parity (fairness)
5. Equal Opportunity (fairness)

**Mathematical Operations:**
- Cosine similarity
- Jaccard similarity
- StandardScaler normalization
- Variance calculations
- Coefficient of variation

### Why This Combination?

1. **Comprehensive Coverage:** LLMs for generation, ML for prediction, statistics for fairness
2. **Robustness:** Multiple models and tests provide redundancy
3. **Interpretability:** Statistical tests and feature importance provide explanations
4. **Fairness:** Bias detection ensures ethical AI deployment
5. **Performance:** Ensemble methods and state-of-the-art algorithms maximize accuracy

---

## References

- XGBoost: Chen & Guestrin (2016). "XGBoost: A Scalable Tree Boosting System"
- LightGBM: Ke et al. (2017). "LightGBM: A Highly Efficient Gradient Boosting Decision Tree"
- Isolation Forest: Liu et al. (2008). "Isolation Forest"
- K-Means: MacQueen (1967). "Some Methods for Classification and Analysis of Multivariate Observations"
- Cohen's d: Cohen (1988). "Statistical Power Analysis for the Behavioral Sciences"
- Demographic Parity: Dwork et al. (2012). "Fairness Through Awareness"
- Equal Opportunity: Hardt et al. (2016). "Equality of Opportunity in Supervised Learning"

