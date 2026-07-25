"""
scripts/sprint33_diag/train_driver_diag.py

Forecast Reliability Diagnostic driver (frozen pre-registration 48cbaad).
Extends the frozen Sprint-25 protocol with the diagnostic instrumentation the
pre-registration requires — nothing about the SCIENTIFIC protocol changes; the
additions are (a) full per-epoch logging and (b) the pre-registered ablation
knobs, one variable per arm:

  --data-fraction F   : train on a random F fraction of WINDOW indices (H1 scaling)
  --match-count N     : train on exactly N random windows (size-matched-V1, H2)
  --base-rate R       : downsample POSITIVE windows to base rate R (H7/H2)
  --dropout D         : PatchTST dropout (H3 regularization; baseline 0.2)
  --weight-decay W    : AdamW weight decay (H3; baseline 1e-4)
  --sampler-mode M    : weighted (baseline) | natural (no 50/50 forcing, H7)
  --steps-per-epoch S : gradient steps/epoch (H4 exposure; baseline 5000)
  --subset-seed K     : seed for the window-index subset (independent of model seed)

Every selected window-index set is hashed and saved to the run dir for exact
reproducibility. max_epochs 15, patience 8 (observe the full curve).

Per-epoch logging (pre-registration "Epoch-level outputs"): train loss, val
loss, train ROC-AUC, val ROC-AUC, train PR-AUC, val PR-AUC, train TSS, val TSS,
Brier, ECE, reliability bins, confusion matrix, positive/negative prediction
rate. Threshold-independent (ROC-AUC/PR-AUC/Brier) are the primary criteria.
"""
import argparse, hashlib, json, os, sys, time, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
import torch
import torch.optim as optim
from torch.utils.data import Subset, DataLoader, WeightedRandomSampler
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss

from app.services.ml.model import PatchTST
from app.services.ml.trainer import FocalLoss
from app.services.ml.dataset import SolarFlareWindowDataset, make_train_loader, make_eval_loader
from app.services.ml.metrics import compute_metrics, find_best_threshold, compute_ece

SEQ = 360


def set_seed(s):
    random.seed(s); np.random.seed(s); torch.manual_seed(s)
    if torch.backends.mps.is_available(): torch.mps.manual_seed(s)


def select_indices(labels, data_fraction, match_count, base_rate, subset_seed):
    """Return the window indices to train on (train-only; windows kept intact)."""
    rng = np.random.default_rng(subset_seed)
    n = len(labels); idx = np.arange(n)
    if base_rate is not None:
        pos = idx[labels == 1]; neg = idx[labels == 0]
        # keep all negatives; downsample positives to achieve base_rate
        target_pos = int(round(base_rate * len(neg) / (1 - base_rate)))
        target_pos = min(target_pos, len(pos))
        keep_pos = rng.choice(pos, size=target_pos, replace=False)
        sel = np.sort(np.concatenate([neg, keep_pos]))
    elif match_count is not None:
        sel = np.sort(rng.choice(idx, size=min(match_count, n), replace=False))
    elif data_fraction is not None and data_fraction < 1.0:
        k = int(round(data_fraction * n)); sel = np.sort(rng.choice(idx, size=k, replace=False))
    else:
        sel = idx
    return sel


def diag_metrics(probs, labels):
    """Full metric suite on (probs, labels). Threshold-independent primary."""
    out = {}
    try: out["roc_auc"] = float(roc_auc_score(labels, probs))
    except Exception: out["roc_auc"] = float("nan")
    try: out["pr_auc"] = float(average_precision_score(labels, probs))
    except Exception: out["pr_auc"] = float("nan")
    out["brier"] = float(brier_score_loss(labels, np.clip(probs, 0, 1))) if len(set(labels.tolist())) > 1 else float("nan")
    try: out["ece"] = float(compute_ece(probs, labels)[0])
    except Exception: out["ece"] = float("nan")
    thr, _ = find_best_threshold(labels, probs, metric="tss")
    pred = (probs >= thr).astype(int)
    m = compute_metrics(labels, pred)
    out["tss"] = float(m["tss"]); out["best_threshold"] = float(thr)
    tp = int(((pred == 1) & (labels == 1)).sum()); fp = int(((pred == 1) & (labels == 0)).sum())
    fn = int(((pred == 0) & (labels == 1)).sum()); tn = int(((pred == 0) & (labels == 0)).sum())
    out["confusion"] = {"tp": tp, "fp": fp, "fn": fn, "tn": tn}
    out["pos_pred_rate"] = float(pred.mean()); out["neg_pred_rate"] = float(1 - pred.mean())
    return out


@torch.no_grad()
def infer(model, loader, device, cap):
    model.eval(); probs, labels, losses = [], [], []
    crit = torch.nn.BCEWithLogitsLoss()
    for i, (X, y) in enumerate(loader):
        if i >= cap: break
        logit = model(X.to(device)).squeeze(-1)
        losses.append(float(crit(logit, y.to(device).float())))
        probs.append(torch.sigmoid(logit).cpu().numpy()); labels.append(y.numpy())
    return (np.concatenate(probs), np.concatenate(labels).astype(int), float(np.mean(losses)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True); ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--features-file", required=True)
    ap.add_argument("--train-parquet", required=True); ap.add_argument("--val-parquet", required=True)
    ap.add_argument("--lr", type=float, default=1e-4); ap.add_argument("--weight-decay", type=float, default=1e-4)
    ap.add_argument("--alpha", type=float, default=0.25); ap.add_argument("--gamma", type=float, default=2.0)
    ap.add_argument("--clip-norm", type=float, default=1.0); ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--steps-per-epoch", type=int, default=5000); ap.add_argument("--val-steps", type=int, default=2000)
    ap.add_argument("--max-epochs", type=int, default=15); ap.add_argument("--patience", type=int, default=8)
    ap.add_argument("--num-workers", type=int, default=2); ap.add_argument("--dropout", type=float, default=0.2)
    ap.add_argument("--sampler-mode", default="weighted", choices=["weighted", "natural"])
    ap.add_argument("--data-fraction", type=float, default=None); ap.add_argument("--match-count", type=int, default=None)
    ap.add_argument("--base-rate", type=float, default=None); ap.add_argument("--subset-seed", type=int, default=0)
    ap.add_argument("--train-eval-cap", type=int, default=100); ap.add_argument("--steps-cap", type=int, default=-1)
    args = ap.parse_args()

    feats = json.load(open(args.features_file)); t0 = time.time(); set_seed(args.seed)
    out = os.path.join("artifacts", "sprint_diagnostic", "runs", args.run_id); os.makedirs(out, exist_ok=True)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

    full_train = SolarFlareWindowDataset(args.train_parquet, feature_cols=feats, split_name=f"{args.run_id}_tr")
    labels_all = full_train.get_labels()
    sel = select_indices(labels_all, args.data_fraction, args.match_count, args.base_rate, args.subset_seed)
    train_ds = Subset(full_train, sel.tolist()) if len(sel) < len(labels_all) else full_train
    sel_labels = labels_all[sel]
    # provenance: hash + save the selected index set
    idx_hash = hashlib.sha256(sel.tobytes()).hexdigest()
    np.save(os.path.join(out, "train_indices.npy"), sel)
    val_ds = SolarFlareWindowDataset(args.val_parquet, feature_cols=feats, split_name=f"{args.run_id}_val")

    # train loader: weighted (baseline) or natural (no 50/50 forcing, H7)
    if args.sampler_mode == "weighted":
        npos = int(sel_labels.sum()); nneg = len(sel_labels) - npos
        w = np.where(sel_labels == 1, 1.0 / max(npos, 1), 1.0 / max(nneg, 1)).astype(np.float64)
        sampler = WeightedRandomSampler(torch.from_numpy(w), num_samples=len(train_ds), replacement=True)
        train_loader = DataLoader(train_ds, batch_size=args.batch_size, sampler=sampler,
                                  num_workers=args.num_workers, persistent_workers=args.num_workers > 0)
    else:
        train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,
                                  num_workers=args.num_workers, persistent_workers=args.num_workers > 0)
    val_loader = make_eval_loader(val_ds, batch_size=args.batch_size, num_workers=args.num_workers, shuffle=True)
    # ordered train-eval subset for train-side metrics (first cap*batch windows, no sampler)
    train_eval_loader = make_eval_loader(Subset(full_train, sel[:args.train_eval_cap * 512].tolist()),
                                         batch_size=512, num_workers=1, shuffle=False)

    model = PatchTST(n_features=len(feats), dropout=args.dropout).to(device)
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    criterion = FocalLoss(gamma=args.gamma, alpha=args.alpha)
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.max_epochs)

    steps = args.steps_per_epoch if args.steps_cap < 0 else min(args.steps_per_epoch, args.steps_cap)
    history, best_roc, best_epoch, patience_ctr = [], -1.0, -1, 0
    for epoch in range(1, args.max_epochs + 1):
        ep0 = time.time(); model.train()
        running = torch.zeros((), device=device); nb = 0
        for i, (X, y) in enumerate(train_loader):
            if i >= steps: break
            X, y = X.to(device, non_blocking=True), y.to(device, non_blocking=True)
            optimizer.zero_grad(); loss = criterion(model(X), y); loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), args.clip_norm); optimizer.step()
            running += loss.detach(); nb += 1
        scheduler.step()
        vp, vl, vloss = infer(model, val_loader, device, args.val_steps)
        tp_, tl_, tloss = infer(model, train_eval_loader, device, 10_000)
        vm = diag_metrics(vp, vl); tm = diag_metrics(tp_, tl_)
        rec = {"epoch": epoch, "train_loss": round(float(running) / max(nb, 1), 6), "val_loss": round(vloss, 6),
               "train_roc_auc": round(tm["roc_auc"], 4), "val_roc_auc": round(vm["roc_auc"], 4),
               "train_pr_auc": round(tm["pr_auc"], 4), "val_pr_auc": round(vm["pr_auc"], 4),
               "train_tss": round(tm["tss"], 4), "val_tss": round(vm["tss"], 4),
               "val_brier": round(vm["brier"], 4), "val_ece": round(vm["ece"], 4),
               "val_confusion": vm["confusion"], "val_pos_pred_rate": round(vm["pos_pred_rate"], 5),
               "val_neg_pred_rate": round(vm["neg_pred_rate"], 5), "best_threshold": round(vm["best_threshold"], 4),
               "lr": scheduler.get_last_lr()[0], "elapsed_sec": round(time.time() - ep0, 1)}
        history.append(rec)
        print(f"[{args.run_id}] ep{epoch} tr_roc={rec['train_roc_auc']} val_roc={rec['val_roc_auc']} "
              f"val_tss={rec['val_tss']} tr_loss={rec['train_loss']} {rec['elapsed_sec']}s", flush=True)
        # PRIMARY selection criterion: validation ROC-AUC (threshold-independent)
        if vm["roc_auc"] > best_roc:
            best_roc, best_epoch, patience_ctr = vm["roc_auc"], epoch, 0
            torch.save({"epoch": epoch, "val_roc_auc": best_roc, "val_tss": vm["tss"],
                        "best_threshold": vm["best_threshold"], "model": model.state_dict(),
                        "seed": args.seed, "n_features": len(feats)}, os.path.join(out, "best.pt"))
        else:
            patience_ctr += 1
            if patience_ctr >= args.patience:
                print(f"[{args.run_id}] early stop ep{epoch} (best ep{best_epoch} roc {best_roc:.4f})", flush=True); break

    meta = {"run_id": args.run_id, "seed": args.seed, "subset_seed": args.subset_seed,
            "n_train_windows": int(len(sel)), "n_train_pos": int(sel_labels.sum()),
            "train_pos_rate": round(float(sel_labels.mean()), 6), "train_indices_sha256": idx_hash,
            "n_params": n_params, "best_val_roc_auc": round(best_roc, 4), "best_epoch": best_epoch,
            "peak_val_roc_auc": round(max(r["val_roc_auc"] for r in history), 4),
            "config": {"dropout": args.dropout, "weight_decay": args.weight_decay,
                       "sampler_mode": args.sampler_mode, "steps_per_epoch": args.steps_per_epoch,
                       "data_fraction": args.data_fraction, "match_count": args.match_count,
                       "base_rate": args.base_rate, "train_parquet": args.train_parquet},
            "wall_seconds": round(time.time() - t0, 1)}
    json.dump(history, open(os.path.join(out, "history.json"), "w"), indent=1)
    json.dump(meta, open(os.path.join(out, "run_meta.json"), "w"), indent=1)
    print(f"[{args.run_id}] DONE peak_val_roc={meta['peak_val_roc_auc']} best_ep{best_epoch} {meta['wall_seconds']}s", flush=True)


if __name__ == "__main__":
    main()
