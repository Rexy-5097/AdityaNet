# Validation Report — Sprint 18A

## Independent Verification of Root Cause Analysis Statistics

### 1. Structural Validation
- **Sample counts**:
  - Subset A (FP vs TN): 17,606 samples
  - Subset B (FN vs TP): 2,394 samples
  - Total subset: 20,000 samples
- **Duplicated/omitted samples**: None (verified via sample index checks).
- **Bootstrap iteration count**: 10,000 iterations (verified via bootstrap matrix dimensions).
- **Feature counts**: 49 active features (variance_15m and variance_60m omitted due to zero/constant variance std <= 10^-9 in the subset).
- **Matrix dimensions**:
  - Feature correlations: 2,401 elements (49 x 49 matrix).
  - Bootstrap coefficients: 257 parameters total.
    - Model A: 38 (Model 1), 40 (Model 2), 49 (Model 3) parameters.
    - Model B: 39 (Model 1), 41 (Model 2), 50 (Model 3) parameters.
    (Note: variance_60m is included in Model B because its standard deviation exceeds 10^-9 in subset B, but omitted in Model A because it is <= 10^-9 in subset A).
- **Status**: **PASS**

### 2. Logistic Regression
- **Coefficients, odds ratios, standard errors, Wald statistics, confidence intervals, and p-values**:
  - **FP vs TN model (Model A)**:
    - Model 1 (Physical): Verified (all parameters match exactly).
    - Model 2 (Physical + Uncertainty): Verified (all parameters match exactly).
    - Model 3 (All): Verified (all parameters match exactly).
  - **FN vs TP model (Model B)**:
    - Model 1 (Physical): Verified (all parameters match exactly).
    - Model 2 (Physical + Uncertainty): Verified (all parameters match exactly).
    - Model 3 (All): Verified (all parameters match exactly).
- **Status**: **PASS**

### 3. Correlation Matrices
- **Pearson correlation matrix**: Verified (all 2,401 elements match exactly).
- **Spearman correlation matrix**: Verified (all 2,401 elements match exactly).
- **Status**: **PASS**

### 4. Variance Inflation Factors (VIF)
- **VIF values**: Verified (all 49 VIF elements match exactly).
- **Status**: **PASS**

### 5. Mutual Information
- **Feature mutual information values and rankings**: Verified (all values and ranked features for FP and FN match exactly).
- **Status**: **PASS**

### 6. Effect Size Statistics
- **Cohen's d, Cliff's Delta, Rank-biserial correlation, Mann-Whitney U, and p-values**: Verified (all values match exactly).
- **Status**: **PASS**

### 7. Taxonomy Association
- **Contingency tables, Chi-square, Cramer's V, degrees of freedom, and p-values**:
  - Contingency table elements match exactly.
  - Chi-Square: 2309.934718
  - Cramer's V: 0.847900
  - Degrees of freedom: 10
  - p-value: 0.0
- **Status**: **PASS**

### 8. Bootstrap Validation
- **Coefficient means, standard deviations, medians, and confidence intervals**: Verified (all bootstrap parameters across all 6 models match exactly).
- **Status**: **PASS**

## Overall Status: PASS
