# Scientific Failure Taxonomy Report — Sprint 17A: Failure Taxonomy of SuryaNet V3

**Author:** Antigravity AI Coding Assistant  
**Date:** June 23, 2026  
**Subject:** Rigorous Data-Driven Analysis of SuryaNet V3 Predictive Failures on the Test Set

---

## 1. Executive Summary

This report presents a complete failure analysis of the frozen **SuryaNet Version 3** model on the `s2_test` dataset, examining the subset of $3,213$ failure cases (False Positives and False Negatives) within the representative $20,000$ sample test subset. 

Instead of hardcoding a taxonomy *a priori*, we allowed the taxonomy to emerge dynamically from the co-occurrence frequencies of 10 boolean physical and model-state flags.

The emergent failure taxonomy consists of three dominant failure modes covering **$77.56\%$** of all failures:
1.  **Quiet Sun False Alarms ($28.20\%$)**: Driven by a heavy temporal bias where the model predicts a flare based on a short elapsed time since the last flare, despite physically quiet background X-ray fluxes.
2.  **Weak Flare Misses ($25.58\%$)**: Missed M-class flares that occur after long quiet periods (median 65.8 hours of quiet sun), where the model's autoregressive history lacks active signatures.
3.  **Missing Sensor Information ($23.78\%$)**: Failures caused by the loss of local instrument telemetry (SoLEXS or HEL1OS), where the model defaults to false alarms due to the absence of clarifying physical signals.

---

## 2. Emergent Failure Taxonomy Breakdown

Based on the co-occurrence of boolean flags, the following categories emerged directly from the data:

| Emergent Category | Sample Count | Percentage | Primary Failure Type |
| :--- | :---: | :---: | :---: |
| **Quiet Sun False Alarm** | 906 | $28.20\%$ | False Positive (FP) |
| **Weak Flare Miss** | 822 | $25.58\%$ | False Negative (FN) |
| **Missing Sensor Information** | 764 | $23.78\%$ | False Positive (FP) |
| **Temporal Drift Failure** | 318 | $9.90\%$ | False Negative (FN) |
| **Unknown** | 165 | $5.14\%$ | Mixed |
| **Background Flux Drift** | 158 | $4.92\%$ | False Positive (FP) |
| **Transition Phase Failure** | 43 | $1.34\%$ | False Positive (FP) |
| **Weak Flare Transition Miss** | 19 | $0.59\%$ | False Negative (FN) |
| **Borderline Label Ambiguity** | 9 | $0.28\%$ | False Positive (FP) |
| **Instrument Disagreement** | 6 | $0.19\%$ | False Positive (FP) |
| **High Confidence Quiet Sun False Alarm** | 3 | $0.09\%$ | False Positive (FP) |

*Audit Note:* The `Unknown` category covers only **$5.14\%$** of failures, verifying that our flag set is highly complete and describes $94.86\%$ of all failures.

---

## 3. Deep-Dive Analysis of Dominant Failure Modes

### 1. Quiet Sun False Alarms ($28.20\%$)
*   **Empirical Profile:** 
    *   Calibrated probability median: $0.3553$ (borderline FP, above threshold $0.316869$).
    *   Median GOES long flux: $9.03 \times 10^{-7}$ W/m² (B-class background, nearly identical to True Negative median of $8.30 \times 10^{-7}$ W/m²).
    *   Median minutes since last flare: **$376.5$ minutes** ($\approx 6.3$ hours), compared to successful True Negative (TN) median of **$4720.0$ minutes** ($\approx 78.7$ hours).
*   **Scientific Explanation:** 
    These false alarms are not caused by sensor anomalies or high background flux. Instead, they represent a **temporal persistence bias**. When a flare has occurred recently (within 6.3 hours), the model's history window is dominated by the decaying active region signatures. The model predicts a high probability of a subsequent flare based on history, even though the current physical state has returned to a completely quiet, non-flaring B-class background.

### 2. Weak Flare Misses ($25.58\%$)
*   **Empirical Profile:**
    *   Calibrated probability median: $0.0810$ (extreme under-confidence).
    *   Median GOES long flux: $1.11 \times 10^{-6}$ W/m² (significantly lower than successful True Positive median of $2.63 \times 10^{-6}$ W/m²).
    *   Median minutes since last flare: **$3949.0$ minutes** ($\approx 65.8$ hours), compared to successful True Positive (TP) median of **$135$ minutes** ($\approx 2.25$ hours).
    *   Target Class: $100\%$ Class 1 (M-class flares, which are weaker than X-class flares).
*   **Scientific Explanation:**
    These represent "surprise" weak flares. Because these flares occur after a long solar quiet period (median 65.8 hours of quiet sun), the model's 6-hour input history contains zero active flare indicators. Since the current background is quiet and no recent activity exists, the autoregressive sequence encoder predicts a very low probability. The model lacks the physics-based precursor sensitivity to predict weak M-class flares that ignite out of long quiet periods.

### 3. Missing Sensor Information ($23.78\%$)
*   **Empirical Profile:**
    *   Median SoLEXS rate: $0.0$ (due to active masking during telemetry drops).
    *   Calibrated probability median: $0.3553$ (borderline FP).
    *   Uncertainty median: $0.0026$ (extremely low, meaning high model confidence).
*   **Scientific Explanation:**
    When local sensors (SoLEXS or HEL1OS) experience telemetry drops, they are replaced by the model's learnable missing tokens. In these states, the model is blind to local X-ray signatures and relies entirely on GOES. In borderline GOES configurations, the absence of local active indicators (which would normally suppress false alarms by showing quiet local conditions) causes the model to default to a False Positive alert.

---

## 4. Comparison with Successful Predictions (TP/TN)

Comparing the failure profiles directly against successful counterparts reveals key differentiators:

1.  **Quiet Sun FPs vs. True Quiet TNs:**
    *   *Uncertainty:* Quiet Sun FPs have a median uncertainty of $0.0026$, whereas True Quiet TNs have a median uncertainty of $0.0034$. The model is **much more confident** on its false alarms than on its true negatives!
    *   *Temporal Offset:* Quiet Sun FPs occur $376.5$ minutes after a flare, while True Quiet TNs occur $4,720$ minutes after a flare. This confirms that the model's failure is driven by the temporal features.
    
2.  **Weak Flare Misses (FN) vs. Detected Flares (TP):**
    *   *GOES Flux:* Missed flares (FN) have a median flux of $1.11 \times 10^{-6}$ W/m², while detected flares (TP) have a median flux of $2.63 \times 10^{-6}$ W/m².
    *   *Temporal Offset:* Missed flares occur $3,949$ minutes after a flare, while detected flares occur $135$ minutes after a flare. This shows that detected flares are almost always parts of active flare "clusters" (recent activity), whereas missed flares are isolated events.

---

## 5. Actionable Feature Engineering Recommendations for Sprint 17B

1.  **Flux Derivative Features:** Since Quiet Sun FPs have similar absolute flux levels to TNs but different temporal histories, we should introduce short-term flux derivatives (e.g., 5-minute and 15-minute gradients) to help the model distinguish active decay from quiet sun.
2.  **Solar Background Normalization:** Normalize the current flux by its running 24-hour minimum to make the model sensitive to weak flare precursors (M-class) when they occur on top of a low background.
3.  **Missing-Aware Fusion:** Train the late fusion encoder to output higher uncertainty when SoLEXS/HEL1OS inputs are masked, preventing high-confidence false alarms during sensor outages.
