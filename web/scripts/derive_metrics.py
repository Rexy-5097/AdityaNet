"""Stage 2b derivation: prediction arrays -> curve geometry the site can render.

WHY THIS EXISTS
---------------
`artifacts/v2/ml/benchmark_predictions.json` holds 192,541 held-out test labels and the
matching per-sample scores for each detector. That is exactly what an ROC curve, a PR
curve, a reliability diagram and a per-day error analysis are computed FROM — but it is
21 MB, which must never reach a browser.

So the curves are computed here, at build time, and emitted as a few hundred points each.
The published figures are therefore derived from the committed artifact by a code path,
in the same way every other number on the site is: nothing is drawn by hand, and nothing
is estimated.

READ-ONLY. This script never writes to artifacts/. It reads the frozen predictions and
emits web/src/generated/data/findings/metrics.json.

Determinism: no sampling, no randomness. Thresholds are the sorted unique score quantiles,
so the same artifact always produces the same curve.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PREDICTIONS = REPO_ROOT / "artifacts/v2/ml/benchmark_predictions.json"
BENCHMARK = REPO_ROOT / "artifacts/v2/ml/benchmark_results.json"
OUT = REPO_ROOT / "web/src/generated/data/findings/metrics.json"

# Curve resolution. 240 points renders smoothly at any width and keeps the payload small;
# the underlying computation still uses every one of the 192,541 samples.
CURVE_POINTS = 240
CALIBRATION_BINS = 12


def load_json(path: Path):
    """Parse artifacts that legitimately contain NaN (a metric can be undefined)."""
    return json.loads(path.read_text(), parse_constant=lambda c: None)


def roc_and_pr(y_true: list[int], scores: list[float]) -> dict:
    """Sweep every distinct score as a threshold; return ROC and PR geometry.

    Single pass over score-sorted samples, so this is O(n log n) rather than O(n * t).
    Positives are counted as the threshold descends, which is the standard construction.
    """
    pairs = sorted(zip(scores, y_true), key=lambda p: -p[0])
    total_pos = sum(y_true)
    total_neg = len(y_true) - total_pos
    if total_pos == 0 or total_neg == 0:
        return {"roc": [], "pr": [], "roc_auc": None, "pr_auc": None}

    roc: list[tuple[float, float]] = [(0.0, 0.0)]
    pr: list[tuple[float, float]] = []
    tp = fp = 0
    prev_score = None

    for score, label in pairs:
        if prev_score is not None and score != prev_score:
            roc.append((fp / total_neg, tp / total_pos))
            if tp + fp > 0:
                pr.append((tp / total_pos, tp / (tp + fp)))
        if label == 1:
            tp += 1
        else:
            fp += 1
        prev_score = score

    roc.append((fp / total_neg, tp / total_pos))
    if tp + fp > 0:
        pr.append((tp / total_pos, tp / (tp + fp)))

    # Trapezoidal AUC over the full-resolution curves, before downsampling for transport.
    roc_auc = sum(
        (roc[i][0] - roc[i - 1][0]) * (roc[i][1] + roc[i - 1][1]) / 2 for i in range(1, len(roc))
    )
    pr_sorted = sorted(pr)
    pr_auc = sum(
        (pr_sorted[i][0] - pr_sorted[i - 1][0]) * (pr_sorted[i][1] + pr_sorted[i - 1][1]) / 2
        for i in range(1, len(pr_sorted))
    )

    return {
        "roc": downsample(roc, CURVE_POINTS),
        "pr": downsample(pr_sorted, CURVE_POINTS),
        "roc_auc": round(roc_auc, 6),
        "pr_auc": round(pr_auc, 6),
    }


def downsample(points: list[tuple[float, float]], n: int) -> list[list[float]]:
    """Keep endpoints exactly; take evenly spaced interior points. Shape is preserved
    because the curves are monotone in x."""
    if len(points) <= n:
        return [[round(x, 5), round(y, 5)] for x, y in points]
    step = (len(points) - 1) / (n - 1)
    idx = sorted({0, len(points) - 1} | {int(round(i * step)) for i in range(n)})
    return [[round(points[i][0], 5), round(points[i][1], 5)] for i in idx]


def calibration(y_true: list[int], probs: list[float], bins: int) -> dict:
    """Reliability diagram: mean predicted probability vs observed frequency per bin.

    Only meaningful for a model that emits calibrated probabilities, so this is computed
    for the learned model and not for the raw count-rate detector, whose score is a
    physical rate rather than a probability.
    """
    edges = [i / bins for i in range(bins + 1)]
    out = []
    for i in range(bins):
        lo, hi = edges[i], edges[i + 1]
        sel = [(p, y) for p, y in zip(probs, y_true) if (p >= lo and (p < hi or i == bins - 1))]
        if not sel:
            continue
        out.append(
            {
                "bin": [round(lo, 4), round(hi, 4)],
                "n": len(sel),
                "mean_predicted": round(sum(p for p, _ in sel) / len(sel), 5),
                "observed": round(sum(y for _, y in sel) / len(sel), 5),
            }
        )
    brier = sum((p - y) ** 2 for p, y in zip(probs, y_true)) / len(y_true)
    return {"bins": out, "brier": round(brier, 6)}


def error_by_day(y_true: list[int], scores: list[float], dates: list[str], thr: float) -> list[dict]:
    """Per-day confusion at the operating threshold — the basis of the error analysis.

    Aggregated by day because that is the unit an operator reasons about, and because the
    day-block bootstrap used for the confidence intervals treats a day as the exchangeable
    unit too.
    """
    acc: dict[str, dict[str, int]] = {}
    for y, s, d in zip(y_true, scores, dates):
        a = acc.setdefault(d, {"tp": 0, "fp": 0, "tn": 0, "fn": 0, "n": 0})
        pred = 1 if s >= thr else 0
        if pred == 1 and y == 1:
            a["tp"] += 1
        elif pred == 1 and y == 0:
            a["fp"] += 1
        elif pred == 0 and y == 1:
            a["fn"] += 1
        else:
            a["tn"] += 1
        a["n"] += 1
    return [{"date": d, **v} for d, v in sorted(acc.items())]


def threshold_sweep(y_true: list[int], scores: list[float], dates: list[str], operating: float) -> list[dict]:
    """Precision / recall / F1 and false-alarm RUNS across candidate thresholds.

    Run count matters more than false-positive count for an operator: 200 isolated false
    minutes scattered through a year is a different burden from 200 contiguous minutes in
    one afternoon. A run is a maximal block of consecutive predicted-positive minutes
    within a day, which is how the published benchmark counts them too.
    """
    lo, hi = min(scores), max(scores)
    # Sweep in the log domain: the count rate spans orders of magnitude.
    import math as _m
    a, b = _m.log10(max(lo, 1e-6)), _m.log10(max(hi, 1e-5))
    candidates = [10 ** (a + (b - a) * i / 59) for i in range(60)]
    if operating not in candidates:
        candidates.append(operating)
    candidates.sort()

    total_pos = sum(y_true)
    out = []
    for thr in candidates:
        tp = fp = fn = 0
        runs = 0
        prev_day = None
        prev_pred = 0
        for y, sc, d in zip(y_true, scores, dates):
            pred = 1 if sc >= thr else 0
            if pred and y:
                tp += 1
            elif pred and not y:
                fp += 1
            elif not pred and y:
                fn += 1
            if pred and (prev_pred == 0 or d != prev_day):
                runs += 1
            prev_pred, prev_day = pred, d
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / total_pos if total_pos else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        out.append({
            "threshold": round(thr, 5),
            "precision": round(prec, 5),
            "recall": round(rec, 5),
            "f1": round(f1, 5),
            "alarm_runs": runs,
            "is_operating": abs(thr - operating) < 1e-9,
        })
    return out


def main() -> None:
    preds = load_json(PREDICTIONS)
    bench = load_json(BENCHMARK)
    out: dict = {"tasks": {}, "source": "artifacts/v2/ml/benchmark_predictions.json"}

    for task_name, task in preds.items():
        y = task["y_test"]
        dates = task["test_dates"]
        thr = task["thr_rate"]

        curves = {}
        for model_key in ("threshold_rate", "lightgbm"):
            if model_key in task:
                curves[model_key] = roc_and_pr(y, task[model_key])

        cal = calibration(y, task["lightgbm"], CALIBRATION_BINS) if "lightgbm" in task else None
        days = error_by_day(y, task["threshold_rate"], dates, thr)

        # Worst days by false negatives, then false positives — where the detector hurts.
        worst = sorted(days, key=lambda d: (-d["fn"], -d["fp"]))[:10]

        sweep = threshold_sweep(y, task["threshold_rate"], dates, thr)

        out["tasks"][task_name] = {
            "threshold_sweep": sweep,
            "n_test": len(y),
            "n_positive": sum(y),
            "operating_threshold": thr,
            "curves": curves,
            "calibration": cal,
            "error_analysis": {
                "n_days": len(days),
                "days_with_any_error": sum(1 for d in days if d["fp"] or d["fn"]),
                "worst_days": worst,
                "daily": [
                    {"date": d["date"], "fp": d["fp"], "fn": d["fn"], "tp": d["tp"]} for d in days
                ],
            },
        }

    # Confusion matrices come straight from the benchmark artifact rather than being
    # recomputed, so the site cannot disagree with the published tables.
    for task_name, task in bench.items():
        if task_name == "meta" or task_name not in out["tasks"]:
            continue
        out["tasks"][task_name]["confusion"] = {
            m: r["minute"]["confusion"] for m, r in task["results"].items()
        }
        out["tasks"][task_name]["minute_metrics"] = {
            m: {
                k: r["minute"][k]
                for k in ("precision", "recall", "f1", "mcc", "balanced_acc", "brier", "pr_auc", "roc_auc")
            }
            for m, r in task["results"].items()
        }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, separators=(",", ":")) + "\n")
    size_kb = OUT.stat().st_size / 1024
    print(f"derive_metrics: wrote {OUT.relative_to(REPO_ROOT)} ({size_kb:.1f} KB)")
    for t, v in out["tasks"].items():
        print(f"  {t}: {v['n_test']} samples, {v['n_positive']} positive, {v['error_analysis']['n_days']} days")


if __name__ == "__main__":
    main()
