"""
scripts/sprint24/eval_framework.py

Sprint 24 — Unified evaluation framework.

ONE class evaluates every method (persistence, climatology, V1+policy,
V1+validation-swept threshold) through IDENTICAL: dataset, window construction,
episode construction, metric formulas, block-bootstrap procedure, and
confidence-interval computation. Methods differ ONLY in the probability/alert
arrays they hand in. No method gets a special pipeline.

Definitions (documented in artifacts/sprint24/01_evaluation_framework.md):
  Window i           : label = target_6hr_binary at parquet row i+360; the
                       decision timestamp is that row's timestamp.
  Label episode      : maximal run of positive-label windows; runs separated by
                       a gap <= GAP_MIN minutes are merged.
  First flare onset  : label-episode start time + 360 minutes (the label leads
                       the first flare by exactly the forecast horizon).
  Detected           : any alert window inside [episode start, episode end].
  Pre-onset detected : any alert window inside [episode start, onset).
  Lead time          : onset - start of the earliest alert episode overlapping
                       the label episode (can exceed 360 min via carry-in
                       alerts; negative if alerting begins only after onset).
  False alert episode: alert episode overlapping no label episode.

Block bootstrap (never IID — labels have 360-minute mechanical overlap and
flares cluster on multi-hour scales):
  Window metrics  : moving-block bootstrap over contiguous blocks of
                    BLOCK_LEN windows; per-block confusion sums are resampled.
  Episode metrics : block bootstrap over blocks of EP_BLOCK consecutive label
                    episodes (episode outcomes cluster too).
  Paired deltas   : identical resample indices across methods (same RNG seed).
"""

import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score

BLOCK_LEN = 2880      # windows per block = 2 days (see 01_evaluation_framework.md)
EP_BLOCK = 10         # label episodes per episode-bootstrap block
N_BOOT = 1000         # confusion/episode bootstrap replicates
N_BOOT_AUC = 200      # AUC/PR-AUC replicates (each requires full re-ranking)
GAP_MIN = 60          # minutes; label/alert runs closer than this merge
HORIZON_MIN = 360     # forecast horizon
SEED = 20260704


def _runs(mask: np.ndarray):
    """Start/end indices (inclusive) of maximal True runs."""
    if not mask.any():
        return np.empty((0, 2), dtype=np.int64)
    d = np.diff(mask.astype(np.int8))
    starts = np.where(d == 1)[0] + 1
    ends = np.where(d == -1)[0]
    if mask[0]:
        starts = np.r_[0, starts]
    if mask[-1]:
        ends = np.r_[ends, len(mask) - 1]
    return np.stack([starts, ends], axis=1)


def _merge_runs(runs, ts, gap_min):
    """Merge runs whose inter-run time gap <= gap_min minutes."""
    if len(runs) == 0:
        return runs
    merged = [runs[0].tolist()]
    for s, e in runs[1:]:
        gap = (ts[s] - ts[merged[-1][1]]) / np.timedelta64(1, "m")
        if gap <= gap_min:
            merged[-1][1] = e
        else:
            merged.append([s, e])
    return np.array(merged, dtype=np.int64)


def _confusion(labels, alerts):
    tp = int(np.sum((alerts == 1) & (labels == 1)))
    fp = int(np.sum((alerts == 1) & (labels == 0)))
    fn = int(np.sum((alerts == 0) & (labels == 1)))
    tn = int(np.sum((alerts == 0) & (labels == 0)))
    return tp, fp, fn, tn


def _metrics_from_confusion(tp, fp, fn, tn):
    tp, fp, fn, tn = float(tp), float(fp), float(fn), float(tn)
    pod = tp / (tp + fn) if tp + fn else 0.0
    pofd = fp / (fp + tn) if fp + tn else 0.0
    prec = tp / (tp + fp) if tp + fp else 0.0
    far = fp / (tp + fp) if tp + fp else 0.0
    f1 = 2 * prec * pod / (prec + pod) if prec + pod else 0.0
    tss = pod - pofd
    denom_h = (tp + fn) * (fn + tn) + (tp + fp) * (fp + tn)
    hss = 2 * (tp * tn - fp * fn) / denom_h if denom_h else 0.0
    denom_m = np.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    mcc = (tp * tn - fp * fn) / denom_m if denom_m else 0.0
    return {"TSS": tss, "HSS": hss, "MCC": mcc, "Precision": prec, "Recall": pod,
            "F1": f1, "FAR": far, "POD": pod, "POFD": pofd}

# vectorized version over an (R,4) array of resampled confusion sums
def _metrics_vec(cs):
    tp, fp, fn, tn = cs[:, 0], cs[:, 1], cs[:, 2], cs[:, 3]
    with np.errstate(divide="ignore", invalid="ignore"):
        pod = np.where(tp + fn > 0, tp / (tp + fn), 0.0)
        pofd = np.where(fp + tn > 0, fp / (fp + tn), 0.0)
        prec = np.where(tp + fp > 0, tp / (tp + fp), 0.0)
        far = np.where(tp + fp > 0, fp / (tp + fp), 0.0)
        f1 = np.where(prec + pod > 0, 2 * prec * pod / (prec + pod), 0.0)
        dh = (tp + fn) * (fn + tn) + (tp + fp) * (fp + tn)
        hss = np.where(dh > 0, 2 * (tp * tn - fp * fn) / dh, 0.0)
        dm = np.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
        mcc = np.where(dm > 0, (tp * tn - fp * fn) / dm, 0.0)
    return {"TSS": pod - pofd, "HSS": hss, "MCC": mcc, "Precision": prec,
            "Recall": pod, "F1": f1, "FAR": far, "POD": pod, "POFD": pofd}


class UnifiedEvaluator:
    """Identical evaluation for every forecasting method."""

    def __init__(self, timestamps, labels):
        assert len(timestamps) == len(labels)
        self.ts = np.asarray(timestamps, dtype="datetime64[s]")
        self.labels = np.asarray(labels).astype(np.int8)
        self.n = len(labels)
        span_days = (self.ts[-1] - self.ts[0]) / np.timedelta64(1, "D")
        self.months = float(span_days) / 30.44
        # fixed block partition shared by all methods
        self.block_ids = np.arange(self.n) // BLOCK_LEN
        self.n_blocks = int(self.block_ids[-1]) + 1
        # label episodes (identical for all methods)
        self.label_eps = _merge_runs(_runs(self.labels == 1), self.ts, GAP_MIN)
        self.onsets = self.ts[self.label_eps[:, 0]] + np.timedelta64(HORIZON_MIN, "m")
        # shared RNG draws so paired comparisons use identical resamples
        rng = np.random.default_rng(SEED)
        self.win_idx = rng.integers(0, self.n_blocks, size=(N_BOOT, self.n_blocks))
        n_ep_blocks = max(1, int(np.ceil(len(self.label_eps) / EP_BLOCK)))
        self.ep_idx = rng.integers(0, n_ep_blocks, size=(N_BOOT, n_ep_blocks))
        self.n_ep_blocks = n_ep_blocks
        self.auc_idx = rng.integers(0, self.n_blocks, size=(N_BOOT_AUC, self.n_blocks))
        # precompute per-block slices for AUC resampling
        self._block_slices = [np.arange(b * BLOCK_LEN, min((b + 1) * BLOCK_LEN, self.n))
                              for b in range(self.n_blocks)]

    # ── window level ──────────────────────────────────────────────────────────
    def _block_confusion(self, alerts):
        lab, al = self.labels, alerts.astype(np.int8)
        tp = np.bincount(self.block_ids, weights=(al & lab), minlength=self.n_blocks)
        fp = np.bincount(self.block_ids, weights=(al & (1 - lab)), minlength=self.n_blocks)
        fn = np.bincount(self.block_ids, weights=((1 - al) & lab), minlength=self.n_blocks)
        tn = np.bincount(self.block_ids, weights=((1 - al) & (1 - lab)), minlength=self.n_blocks)
        return np.stack([tp, fp, fn, tn], axis=1)  # (n_blocks, 4)

    def window_level(self, probs, alerts, auc_ci=True):
        out = {}
        constant = np.allclose(probs, probs[0])
        out["ROC_AUC"] = 0.5 if constant else float(roc_auc_score(self.labels, probs))
        out["PR_AUC"] = float(self.labels.mean()) if constant else float(
            average_precision_score(self.labels, probs))
        tp, fp, fn, tn = _confusion(self.labels, alerts)
        out.update(_metrics_from_confusion(tp, fp, fn, tn))
        out["confusion"] = {"tp": tp, "fp": fp, "fn": fn, "tn": tn}
        # block-bootstrap CIs for confusion metrics
        bc = self._block_confusion(alerts)
        sums = bc[self.win_idx].sum(axis=1)              # (N_BOOT, 4)
        vec = _metrics_vec(sums)
        out["ci"] = {k: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]
                     for k, v in vec.items()}
        out["_boot"] = {k: v for k, v in vec.items()}    # kept for paired tests
        if auc_ci and not constant:
            aucs, prs = [], []
            for rep in self.auc_idx:
                idx = np.concatenate([self._block_slices[b] for b in rep])
                aucs.append(roc_auc_score(self.labels[idx], probs[idx]))
                prs.append(average_precision_score(self.labels[idx], probs[idx]))
            out["ci"]["ROC_AUC"] = [float(np.percentile(aucs, 2.5)), float(np.percentile(aucs, 97.5))]
            out["ci"]["PR_AUC"] = [float(np.percentile(prs, 2.5)), float(np.percentile(prs, 97.5))]
        return out

    # ── episode level ─────────────────────────────────────────────────────────
    def episode_level(self, alerts):
        al_eps = _merge_runs(_runs(alerts.astype(bool)), self.ts, GAP_MIN)
        out = {"n_label_episodes": int(len(self.label_eps)),
               "n_alert_episodes": int(len(al_eps))}
        det = np.zeros(len(self.label_eps), bool)
        pre = np.zeros(len(self.label_eps), bool)
        lead = np.full(len(self.label_eps), np.nan)
        al_start_ts = self.ts[al_eps[:, 0]] if len(al_eps) else np.array([], dtype="datetime64[s]")
        al_end_ts = self.ts[al_eps[:, 1]] if len(al_eps) else np.array([], dtype="datetime64[s]")
        alert_hit = np.zeros(len(al_eps), bool)
        for i, (s, e) in enumerate(self.label_eps):
            ls, le, onset = self.ts[s], self.ts[e], self.onsets[i]
            ov = np.where((al_start_ts <= le) & (al_end_ts >= ls))[0]
            if len(ov):
                det[i] = True
                alert_hit[ov] = True
                first = al_start_ts[ov].min()
                lead[i] = (onset - first) / np.timedelta64(1, "m")
                in_pre = (al_start_ts[ov] < onset) | (al_start_ts[ov] <= ls)
                # pre-onset means alerting began before the first flare onset
                pre[i] = bool((al_start_ts[ov] < onset).any())
        false_eps = int((~alert_hit).sum())
        durations = ((al_end_ts - al_start_ts) / np.timedelta64(1, "m") + 1.0) if len(al_eps) else np.array([])
        out.update({
            "episodes_detected": int(det.sum()),
            "episodes_missed": int((~det).sum()),
            "episode_recall": float(det.mean()) if len(det) else 0.0,
            "episode_precision": float(alert_hit.mean()) if len(al_eps) else 0.0,
            "episodes_detected_pre_onset": int(pre.sum()),
            "pre_onset_recall": float(pre.mean()) if len(pre) else 0.0,
            "false_alert_episodes": false_eps,
            "false_episodes_per_month": false_eps / self.months,
            "lead_time_min_mean": float(np.nanmean(lead)) if det.any() else None,
            "lead_time_min_median": float(np.nanmedian(lead)) if det.any() else None,
            "lead_time_positive_fraction": float(np.nanmean((lead > 0)[det])) if det.any() else 0.0,
            "alert_minutes_total": float(durations.sum()) if len(al_eps) else 0.0,
            "alert_duration_min_mean": float(durations.mean()) if len(al_eps) else 0.0,
            "alert_duration_min_median": float(np.median(durations)) if len(al_eps) else 0.0,
            "alert_episodes_per_month": len(al_eps) / self.months,
        })
        # episode-block bootstrap for recall / pre-onset recall
        blocks = [np.arange(b * EP_BLOCK, min((b + 1) * EP_BLOCK, len(self.label_eps)))
                  for b in range(self.n_ep_blocks)]
        rec, prer = [], []
        for rep in self.ep_idx:
            sel = np.concatenate([blocks[b] for b in rep]) if len(self.label_eps) else np.array([], int)
            if len(sel):
                rec.append(det[sel].mean()); prer.append(pre[sel].mean())
        out["ci"] = {
            "episode_recall": [float(np.percentile(rec, 2.5)), float(np.percentile(rec, 97.5))],
            "pre_onset_recall": [float(np.percentile(prer, 2.5)), float(np.percentile(prer, 97.5))],
        }
        out["_det"] = det; out["_pre"] = pre  # for paired episode tests
        return out

    # ── one call per method ───────────────────────────────────────────────────
    def evaluate(self, name, probs, alerts_yellow, alerts_red=None, auc_ci=True):
        probs = np.asarray(probs, dtype=np.float64)
        ay = np.asarray(alerts_yellow).astype(np.int8)
        res = {"method": name,
               "window": self.window_level(probs, ay, auc_ci=auc_ci),
               "episode": self.episode_level(ay)}
        res["alert_stats"] = {
            "yellow_windows": int(ay.sum()),
            "yellow_fraction_of_time": float(ay.mean()),
            "alert_minutes_per_day": float(ay.sum()) / (self.months * 30.44),
        }
        if alerts_red is not None:
            ar = np.asarray(alerts_red).astype(np.int8)
            red_eps = _merge_runs(_runs(ar.astype(bool)), self.ts, GAP_MIN)
            res["alert_stats"].update({
                "red_windows": int(ar.sum()),
                "red_fraction_of_time": float(ar.mean()),
                "red_episodes": int(len(red_eps)),
            })
        return res

    # ── paired comparison (identical resamples) ───────────────────────────────
    def paired_window(self, res_a, res_b, metrics=("TSS", "HSS", "MCC", "Recall", "Precision", "F1")):
        out = {}
        for m in metrics:
            da = np.asarray(res_a["window"]["_boot"][m])
            db = np.asarray(res_b["window"]["_boot"][m])
            delta = da - db
            lo, hi = float(np.percentile(delta, 2.5)), float(np.percentile(delta, 97.5))
            p = 2 * min(float((delta <= 0).mean()), float((delta >= 0).mean()))
            out[m] = {"delta_point": float(res_a["window"][m] - res_b["window"][m]),
                      "delta_ci95": [lo, hi], "p_boot": min(1.0, max(p, 1.0 / N_BOOT)),
                      "significant": (lo > 0) or (hi < 0)}
        return out

    def paired_episode(self, res_a, res_b):
        da, db = res_a["episode"]["_det"], res_b["episode"]["_det"]
        pa, pb = res_a["episode"]["_pre"], res_b["episode"]["_pre"]
        blocks = [np.arange(b * EP_BLOCK, min((b + 1) * EP_BLOCK, len(da)))
                  for b in range(self.n_ep_blocks)]
        d_rec, d_pre = [], []
        for rep in self.ep_idx:
            sel = np.concatenate([blocks[b] for b in rep])
            d_rec.append(da[sel].mean() - db[sel].mean())
            d_pre.append(pa[sel].mean() - pb[sel].mean())
        def pack(d, point):
            lo, hi = float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))
            p = 2 * min(float((np.asarray(d) <= 0).mean()), float((np.asarray(d) >= 0).mean()))
            return {"delta_point": point, "delta_ci95": [lo, hi],
                    "p_boot": min(1.0, max(p, 1.0 / N_BOOT)), "significant": (lo > 0) or (hi < 0)}
        return {"episode_recall": pack(d_rec, float(da.mean() - db.mean())),
                "pre_onset_recall": pack(d_pre, float(pa.mean() - pb.mean()))}
