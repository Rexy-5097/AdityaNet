"""
app/services/ml/metrics.py

Space-weather classification metrics for SuryaNet.

Supports hard binary predictions, raw/calibrated probabilities,
calibration error metrics (ECE, MCE), and statistical significance testing.
"""

import math
import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score

def compute_mcc(tp: int, fp: int, fn: int, tn: int) -> float:
    """Matthews Correlation Coefficient."""
    num = float((tp * tn) - (fp * fn))
    den = math.sqrt(float((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)))
    if den == 0.0:
        return 0.0
    return num / den

def compute_hss(tp: int, fp: int, fn: int, tn: int) -> float:
    """Heidke Skill Score."""
    total = float(tp + tn + fp + fn)
    if total == 0.0:
        return 0.0
    expected_correct = float((tp + fn) * (tp + fp) + (tn + fn) * (tn + fp)) / total
    den = total - expected_correct
    if den == 0.0:
        return 0.0
    return (float(tp + tn) - expected_correct) / den

def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """
    Compute space-weather classification metrics from hard binary predictions.

    Args:
        y_true: Ground truth binary labels [N].
        y_pred: Predicted binary labels [N].

    Returns:
        dict with keys: confusion_matrix, pod, pofd, tss, far,
                        precision, recall, f1, hss, mcc.
    """
    y_true = np.ravel(np.array(y_true))
    y_pred = np.ravel(np.array(y_pred))

    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))

    pod       = float(tp) / (tp + fn) if (tp + fn) > 0 else 0.0
    pofd      = float(fp) / (fp + tn) if (fp + tn) > 0 else 0.0
    tss       = pod - pofd
    far       = float(fp) / (tp + fp) if (tp + fp) > 0 else 0.0
    precision = float(tp) / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = pod   # identical by definition
    f1        = (2 * precision * recall / (precision + recall)
                 if (precision + recall) > 0 else 0.0)
    
    hss = compute_hss(tp, fp, fn, tn)
    mcc = compute_mcc(tp, fp, fn, tn)

    return {
        "confusion_matrix": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "pod":       pod,
        "pofd":      pofd,
        "tss":       tss,
        "far":       far,
        "precision": precision,
        "recall":    recall,
        "f1":        f1,
        "hss":       hss,
        "mcc":       mcc,
    }

def compute_prob_metrics(y_true: np.ndarray, y_prob: np.ndarray) -> dict:
    """
    Compute probability-based metrics.

    Args:
        y_true: Ground truth binary labels [N].
        y_prob: Predicted probabilities [N]  (sigmoid output, range [0, 1]).

    Returns:
        dict with keys: roc_auc, pr_auc, brier_score.
    """
    y_true = np.ravel(np.array(y_true, dtype=np.float32))
    y_prob = np.ravel(np.array(y_prob, dtype=np.float32))

    n_pos = int(y_true.sum())
    n_neg = int((1 - y_true).sum())

    # ROC-AUC: needs at least one positive and one negative
    if n_pos > 0 and n_neg > 0:
        try:
            roc_auc = float(roc_auc_score(y_true, y_prob))
        except Exception:
            roc_auc = 0.5
        
        try:
            # PR-AUC via average precision score
            pr_auc  = float(average_precision_score(y_true, y_prob))
        except Exception:
            pr_auc  = 0.0
    else:
        roc_auc = float("nan")
        pr_auc  = float("nan")

    brier = float(np.mean((y_prob - y_true) ** 2))

    return {
        "roc_auc":     roc_auc,
        "pr_auc":      pr_auc,
        "brier_score": brier,
    }

def find_best_threshold(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    metric: str = "tss",
    n_thresholds: int = 100,
) -> tuple[float, float]:
    """
    Find the probability threshold that maximises a given metric on the validation set.

    Args:
        y_true:       Ground truth binary labels [N].
        y_prob:       Predicted probabilities [N].
        metric:       Metric to optimise — "tss" or "f1" (default "tss").
        n_thresholds: Number of candidate thresholds to evaluate (default 100).

    Returns:
        (best_threshold, best_metric_value)
    """
    y_true = np.ravel(np.array(y_true))
    y_prob = np.ravel(np.array(y_prob))

    thresholds  = np.linspace(0.01, 0.99, n_thresholds)
    best_thresh = 0.5
    best_val    = -float("inf")

    for t in thresholds:
        y_pred  = (y_prob >= t).astype(int)
        m       = compute_metrics(y_true, y_pred)
        val     = m[metric]
        if val > best_val:
            best_val    = val
            best_thresh = float(t)

    return best_thresh, best_val

def compute_ece(probs: np.ndarray, targets: np.ndarray, n_bins: int = 10) -> tuple[float, np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute Expected Calibration Error (ECE) and reliability bin statistics.
    """
    probs = np.ravel(probs)
    targets = np.ravel(targets)
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    
    bin_accs = []
    bin_confs = []
    bin_sizes = []

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        
        in_bin = (probs >= bin_lower) & (probs < bin_upper)
        prop_in_bin = np.mean(in_bin)
        
        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(targets[in_bin])
            avg_confidence_in_bin = np.mean(probs[in_bin])
            
            ece += prop_in_bin * np.abs(avg_confidence_in_bin - accuracy_in_bin)
            
            bin_accs.append(accuracy_in_bin)
            bin_confs.append(avg_confidence_in_bin)
            bin_sizes.append(np.sum(in_bin))
        else:
            bin_accs.append(0.0)
            bin_confs.append(0.0)
            bin_sizes.append(0)

    return float(ece), np.array(bin_accs), np.array(bin_confs), np.array(bin_sizes)

def compute_mce(probs: np.ndarray, targets: np.ndarray, n_bins: int = 10) -> float:
    """
    Compute Maximum Calibration Error (MCE).
    """
    probs = np.ravel(probs)
    targets = np.ravel(targets)
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    max_error = 0.0

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        
        in_bin = (probs >= bin_lower) & (probs < bin_upper)
        if np.sum(in_bin) > 0:
            accuracy_in_bin = np.mean(targets[in_bin])
            avg_confidence_in_bin = np.mean(probs[in_bin])
            error = np.abs(avg_confidence_in_bin - accuracy_in_bin)
            if error > max_error:
                max_error = float(error)
                
    return max_error

def compute_full_suite(y_true: np.ndarray, y_prob: np.ndarray, threshold: float = 0.5) -> dict:
    """
    Complete metric suite: combines hard + probabilistic + calibration.
    Returns all metrics in one call. This is the ONLY function
    that downstream code should call for evaluation.
    """
    y_true = np.ravel(np.array(y_true))
    y_prob = np.ravel(np.array(y_prob))
    
    preds = np.where(y_prob >= threshold, 1, 0)
    
    # 1. Hard classification metrics
    hard_metrics = compute_metrics(y_true, preds)
    
    # 2. Probabilistic metrics
    prob_metrics = compute_prob_metrics(y_true, y_prob)
    
    # 3. Calibration metrics
    ece, bin_accs, bin_confs, bin_sizes = compute_ece(y_prob, y_true)
    mce = compute_mce(y_prob, y_true)
    
    return {
        "roc_auc": prob_metrics["roc_auc"],
        "pr_auc": prob_metrics["pr_auc"],
        "tss": hard_metrics["tss"],
        "hss": hard_metrics["hss"],
        "mcc": hard_metrics["mcc"],
        "precision": hard_metrics["precision"],
        "recall": hard_metrics["recall"],
        "f1": hard_metrics["f1"],
        "false_alarm_ratio": hard_metrics["far"],
        "brier_score": prob_metrics["brier_score"],
        "ece": ece,
        "mce": mce,
        "confusion_matrix": hard_metrics["confusion_matrix"],
        "reliability_diagram": {
            "bin_confs": bin_confs.tolist(),
            "bin_accs": bin_accs.tolist(),
            "bin_sizes": bin_sizes.tolist()
        }
    }

def paired_bootstrap_test(y_true: np.ndarray, probs_a: np.ndarray, probs_b: np.ndarray,
                          threshold_a: float = 0.5, threshold_b: float = 0.5,
                          n_bootstraps: int = 1000, seed: int = 42) -> dict:
    """Paired bootstrap significance testing between two models."""
    np.random.seed(seed)
    y_true = np.ravel(np.array(y_true))
    probs_a = np.ravel(np.array(probs_a))
    probs_b = np.ravel(np.array(probs_b))
    n = len(y_true)
    
    tss_diffs = []
    f1_diffs = []
    auc_diffs = []
    
    for _ in range(n_bootstraps):
        indices = np.random.choice(n, size=n, replace=True)
        y_b = y_true[indices]
        if len(np.unique(y_b)) < 2:
            continue
            
        p_a = probs_a[indices]
        p_b = probs_b[indices]
        
        pred_a = np.where(p_a >= threshold_a, 1, 0)
        pred_b = np.where(p_b >= threshold_b, 1, 0)
        
        m_a = compute_metrics(y_b, pred_a)
        m_b = compute_metrics(y_b, pred_b)
        
        try:
            auc_a = float(roc_auc_score(y_b, p_a))
            auc_b = float(roc_auc_score(y_b, p_b))
        except Exception:
            auc_a = 0.5
            auc_b = 0.5
            
        tss_diffs.append(m_b["tss"] - m_a["tss"])
        f1_diffs.append(m_b["f1"] - m_a["f1"])
        auc_diffs.append(auc_b - auc_a)
        
    tss_diffs = np.array(tss_diffs)
    f1_diffs = np.array(f1_diffs)
    auc_diffs = np.array(auc_diffs)
    
    p_tss = float(np.mean(tss_diffs <= 0))
    p_f1 = float(np.mean(f1_diffs <= 0))
    p_auc = float(np.mean(auc_diffs <= 0))
    
    tss_ci = (float(np.percentile(tss_diffs, 2.5)), float(np.percentile(tss_diffs, 97.5)))
    f1_ci = (float(np.percentile(f1_diffs, 2.5)), float(np.percentile(f1_diffs, 97.5)))
    auc_ci = (float(np.percentile(auc_diffs, 2.5)), float(np.percentile(auc_diffs, 97.5)))
    
    return {
        "p_tss": p_tss,
        "p_f1": p_f1,
        "p_auc": p_auc,
        "tss_ci": tss_ci,
        "f1_ci": f1_ci,
        "auc_ci": auc_ci
    }

def run_mcnemar_test(y_true: np.ndarray, preds_a: np.ndarray, preds_b: np.ndarray) -> tuple[float, list]:
    """McNemar's test for classification difference."""
    y_true = np.ravel(np.array(y_true))
    preds_a = np.ravel(np.array(preds_a))
    preds_b = np.ravel(np.array(preds_b))
    
    correct_a = (preds_a == y_true)
    correct_b = (preds_b == y_true)
    
    b_val = int(np.sum(correct_a & ~correct_b))
    c_val = int(np.sum(~correct_a & correct_b))
    
    table = [
        [int(np.sum(correct_a & correct_b)), b_val],
        [c_val, int(np.sum(~correct_a & ~correct_b))]
    ]
    
    from scipy.stats.contingency import mcnemar
    res = mcnemar(table, exact=True)
    return float(res.pvalue), table
