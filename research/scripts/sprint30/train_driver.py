"""
scripts/sprint30/train_driver.py

Sprint 30 Phase 2 — the Sprint 26 faithful V1 trainer with EXACTLY TWO changes,
per the "minimum extent required" rule of the Sprint 30 brief:
  1. --features-file: feature-column list is a parameter (default: the frozen
     14-column artifacts/feature_columns.json), and
  2. PatchTST is constructed with n_features=len(feature list) so the patch
     embedding width follows the dataset (F1.json: "patch embedding width
     changes; all else frozen protocol").
Output directory moves to artifacts/sprint30/runs/. Every scientific default —
optimizer, learning rate, weight decay, focal loss, sampler, gradient clip,
batch size, steps per epoch, validation steps, max epochs, patience, shuffled
validation loader — is byte-identical to scripts/sprint26/train_driver.py
(the Sprint 25 frozen protocol, artifacts/sprint25/02_retraining_protocol.md).
"""
import argparse, json, os, sys, time, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
import torch
import torch.optim as optim

from app.services.ml.model import PatchTST
from app.services.ml.trainer import FocalLoss           # reused unchanged
from app.services.ml.dataset import SolarFlareWindowDataset, make_train_loader, make_eval_loader
from app.services.ml.metrics import compute_metrics, compute_prob_metrics, find_best_threshold


def set_seed(seed):
    random.seed(seed); np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.backends.mps.is_available():
        torch.mps.manual_seed(seed)


def evaluate_val(model, loader, device, val_steps):
    model.eval()
    probs, labels = [], []
    with torch.no_grad():
        for i, (X, y) in enumerate(loader):
            if i >= val_steps: break
            p = torch.sigmoid(model(X.to(device))).squeeze(-1)
            probs.append(p.cpu().numpy()); labels.append(y.numpy())
    probs = np.concatenate(probs); labels = np.concatenate(labels).astype(int)
    thr, _ = find_best_threshold(labels, probs, metric="tss")
    m = compute_metrics(labels, (probs >= thr).astype(int))
    pm = compute_prob_metrics(labels, probs)
    return thr, m, pm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--seed", type=int, required=True)
    # protocol baseline defaults (02_retraining_protocol.md) — DO NOT CHANGE
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--weight-decay", type=float, default=1e-4)
    ap.add_argument("--alpha", type=float, default=0.25)
    ap.add_argument("--gamma", type=float, default=2.0)
    ap.add_argument("--clip-norm", type=float, default=1.0)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--steps-per-epoch", type=int, default=5000)
    ap.add_argument("--val-steps", type=int, default=2000)
    ap.add_argument("--max-epochs", type=int, default=20)
    ap.add_argument("--patience", type=int, default=3)
    ap.add_argument("--t-max", type=int, default=-1, help="CosineAnnealingLR T_max; -1 = max_epochs (baseline)")
    ap.add_argument("--num-workers", type=int, default=2)
    ap.add_argument("--train-parquet", default="artifacts/research/train.parquet")
    ap.add_argument("--val-parquet", default="artifacts/research/validation.parquet")
    # Sprint 30 change 1: configurable feature list
    ap.add_argument("--features-file", default=os.path.join("artifacts", "feature_columns.json"))
    ap.add_argument("--steps-cap", type=int, default=-1,
                    help="smoke-test only: hard cap on train steps per epoch; -1 = off")
    args = ap.parse_args()

    feature_cols = json.load(open(args.features_file))
    t0 = time.time()
    set_seed(args.seed)
    out = os.path.join("artifacts", "sprint30", "runs", args.run_id)
    os.makedirs(out, exist_ok=True)

    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    train_ds = SolarFlareWindowDataset(args.train_parquet, feature_cols=feature_cols, split_name=f"{args.run_id}_train")
    val_ds = SolarFlareWindowDataset(args.val_parquet, feature_cols=feature_cols, split_name=f"{args.run_id}_val")
    # Match the frozen trainer: WeightedRandomSampler train loader, SHUFFLED val
    # loader (dataset.py:166-169). num_workers=2 as in scripts/train_patchtst.py.
    train_loader = make_train_loader(train_ds, batch_size=args.batch_size, num_workers=args.num_workers)
    val_loader = make_eval_loader(val_ds, batch_size=args.batch_size, num_workers=args.num_workers, shuffle=True)
    pos_rate = float(train_ds.get_labels().mean())

    # Sprint 30 change 2: model width follows the feature list
    model = PatchTST(n_features=len(feature_cols)).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    criterion = FocalLoss(gamma=args.gamma, alpha=args.alpha)
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    t_max = args.max_epochs if args.t_max < 0 else args.t_max
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=t_max)

    steps = args.steps_per_epoch if args.steps_cap < 0 else min(args.steps_per_epoch, args.steps_cap)
    history, best_tss, best_epoch, patience_ctr = [], -2.0, -1, 0
    peak_mem = 0.0
    for epoch in range(1, args.max_epochs + 1):
        ep0 = time.time()
        model.train()
        running = torch.zeros((), device=device); nb = 0
        for i, (X, y) in enumerate(train_loader):
            if i >= steps: break
            X, y = X.to(device, non_blocking=True), y.to(device, non_blocking=True)
            optimizer.zero_grad()
            loss = criterion(model(X), y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), args.clip_norm)
            optimizer.step()
            running += loss.detach(); nb += 1   # accumulate on-device; one sync at epoch end
        cur_lr = scheduler.get_last_lr()[0]
        scheduler.step()
        thr, m, pm = evaluate_val(model, val_loader, device, args.val_steps)
        if torch.backends.mps.is_available():
            peak_mem = max(peak_mem, torch.mps.current_allocated_memory() / 1e9)
        rec = {"epoch": epoch, "train_loss": round(float(running) / max(nb, 1), 6),
               "val_tss": round(m["tss"], 4), "val_pod": round(m.get("recall", m.get("pod", 0)), 4),
               "val_roc_auc": round(pm["roc_auc"], 4), "val_pr_auc": round(pm["pr_auc"], 4),
               "val_brier": round(pm.get("brier", pm.get("brier_score", 0)), 4),
               "best_threshold": round(float(thr), 4), "lr": cur_lr,
               "elapsed_sec": round(time.time() - ep0, 1)}
        history.append(rec)
        print(f"[{args.run_id}] ep{epoch} tss={rec['val_tss']} thr={rec['best_threshold']} loss={rec['train_loss']} {rec['elapsed_sec']}s", flush=True)
        if m["tss"] > best_tss:
            best_tss, best_epoch, patience_ctr = m["tss"], epoch, 0
            torch.save({"epoch": epoch, "val_tss": best_tss, "best_threshold": float(thr),
                        "model": model.state_dict(), "seed": args.seed,
                        "n_features": len(feature_cols)}, os.path.join(out, "best.pt"))
        else:
            patience_ctr += 1
            if patience_ctr >= args.patience:
                print(f"[{args.run_id}] early stop at epoch {epoch} (best {best_epoch}, tss {best_tss:.4f})", flush=True)
                break

    meta = {"run_id": args.run_id, "seed": args.seed, "device": str(device),
            "n_features": len(feature_cols), "n_params": n_params,
            "features_file": args.features_file,
            "best_val_tss": round(best_tss, 4), "best_epoch": best_epoch,
            "pos_rate": round(pos_rate, 6), "peak_mem_gb": round(peak_mem, 3),
            "wall_seconds": round(time.time() - t0, 1),
            "params": {"lr": args.lr, "weight_decay": args.weight_decay, "alpha": args.alpha,
                       "gamma": args.gamma, "clip_norm": args.clip_norm, "batch_size": args.batch_size,
                       "steps_per_epoch": args.steps_per_epoch, "max_epochs": args.max_epochs,
                       "patience": args.patience, "t_max": t_max,
                       "train_parquet": args.train_parquet, "val_parquet": args.val_parquet},
            "torch": torch.__version__}
    json.dump(history, open(os.path.join(out, "history.json"), "w"), indent=1)
    json.dump(meta, open(os.path.join(out, "run_meta.json"), "w"), indent=1)
    print(f"[{args.run_id}] DONE best_val_tss={best_tss:.4f}@ep{best_epoch} {meta['wall_seconds']}s peak_mem={peak_mem:.2f}GB", flush=True)


if __name__ == "__main__":
    main()
