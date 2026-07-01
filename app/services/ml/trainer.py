"""
app/services/ml/trainer.py

Training orchestration for SuryaNet PatchTST.

Key design decisions:
  - Model outputs raw LOGITS; sigmoid applied only at inference.
  - Focal Loss alpha CLAMPED to [0.25, 0.75] regardless of pos_rate.
    Reason: WeightedRandomSampler already balances batches ~50/50,
    so alpha=0.9938 (computed from raw pos_rate=0.0062) causes all-positive
    prediction collapse. Clamped alpha prevents this.
  - Optimal classification threshold found via TSS maximisation on validation
    probabilities (not fixed at 0.5).
  - MPS device auto-selected; float32 throughout (MPS autocast unreliable <2.5).
  - Early stopping on validation TSS (patience=3).
  - steps_per_epoch cap for M4 Air feasibility (default 5000 train, 2000 val).
"""

import json
import logging
import os
import time
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter

from app.services.ml.model import PatchTST
from app.services.ml.metrics import compute_metrics, compute_prob_metrics, find_best_threshold

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Focal Loss (operates on raw logits)
# ──────────────────────────────────────────────────────────────────────────────
class FocalLoss(nn.Module):
    """
    Binary Focal Loss operating on raw logits.

    FL(p_t) = -alpha_t * (1 - p_t)^gamma * log(p_t)

    Args:
        gamma:    Focusing parameter (default 2.0).
        alpha:    Weight for the positive class. CLAMPED to [0.25, 0.75].
                  With WeightedRandomSampler, batches are ~50/50, so extreme
                  alpha values (e.g., 0.9938) cause all-positive collapse.
        reduction: 'mean' or 'sum'.
    """

    def __init__(self, gamma: float = 2.0, alpha: float = 0.25, reduction: str = "mean"):
        super().__init__()
        self.gamma     = gamma
        self.alpha     = float(np.clip(alpha, 0.25, 0.75))
        self.reduction = reduction
        logger.info(f"FocalLoss | gamma={gamma:.1f} | alpha={self.alpha:.4f} (clamped to [0.25, 0.75])")

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        # logits:  [B, 1] or [B]  — raw logits (no sigmoid applied beforehand)
        # targets: [B]
        logits  = logits.squeeze(-1)
        bce     = nn.functional.binary_cross_entropy_with_logits(
            logits, targets, reduction="none"
        )
        probs   = torch.sigmoid(logits)
        p_t     = probs * targets + (1.0 - probs) * (1.0 - targets)
        alpha_t = self.alpha * targets + (1.0 - self.alpha) * (1.0 - targets)
        focal   = alpha_t * ((1.0 - p_t) ** self.gamma) * bce

        if self.reduction == "mean":
            return focal.mean()
        return focal.sum()


# ──────────────────────────────────────────────────────────────────────────────
# Trainer
# ──────────────────────────────────────────────────────────────────────────────
class Trainer:
    """
    Orchestrates PatchTST training with early stopping and checkpointing.

    Args:
        model:             PatchTST instance.
        train_loader:      Training DataLoader (WeightedRandomSampler).
        val_loader:        Validation DataLoader.
        pos_rate:          Fraction of positive samples in raw training set.
                           Used to compute Focal Loss alpha (then clamped).
        max_epochs:        Maximum training epochs (default 20).
        patience:          Early stopping patience on val TSS (default 3).
        lr:                Initial learning rate (default 1e-4).
        weight_decay:      AdamW weight decay (default 1e-4).
        clip_norm:         Gradient clip max norm (default 1.0).
        checkpoint_dir:    Directory to save model checkpoints.
        tb_log_dir:        TensorBoard log directory.
        steps_per_epoch:   Max training batches per epoch (default 5000).
        val_steps:         Max validation batches per epoch (default 2000).
    """

    BEST_CKPT = "patchtst_best.pt"
    LAST_CKPT = "patchtst_last.pt"

    def __init__(
        self,
        model: PatchTST,
        train_loader: DataLoader,
        val_loader: DataLoader,
        pos_rate: float,
        max_epochs: int      = 20,
        patience: int        = 3,
        lr: float            = 1e-4,
        weight_decay: float  = 1e-4,
        clip_norm: float     = 1.0,
        checkpoint_dir: str  = "artifacts/models",
        tb_log_dir: str      = "artifacts/runs",
        steps_per_epoch: int = 5000,
        val_steps: int       = 2000,
    ):
        self.model           = model
        self.train_loader    = train_loader
        self.val_loader      = val_loader
        self.max_epochs      = max_epochs
        self.patience        = patience
        self.clip_norm       = clip_norm
        self.checkpoint_dir  = checkpoint_dir
        self.steps_per_epoch = steps_per_epoch
        self.val_steps       = val_steps

        # Best threshold found on validation (updated each epoch)
        self.best_threshold = 0.5

        os.makedirs(checkpoint_dir, exist_ok=True)
        os.makedirs(tb_log_dir, exist_ok=True)

        # Device: MPS → CPU
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
            logger.info("Device: Apple Silicon MPS")
        else:
            self.device = torch.device("cpu")
            logger.info("Device: CPU")

        self.model.to(self.device)

        # Focal Loss alpha strategy:
        # WeightedRandomSampler produces ~50/50 balanced batches.
        # In this regime, alpha=0.25 (low positive weight) forces the model to
        # be selective — predicting positive only when confident.
        # This avoids both all-positive (alpha too high) and all-negative
        # (alpha too low) collapse modes.
        # The raw pos_rate is preserved for logging only.
        logger.info(f"Training set pos_rate: {pos_rate:.4f} (sampler balances to ~0.50)")
        focal_alpha = 0.25
        self.criterion = FocalLoss(gamma=2.0, alpha=focal_alpha)

        self.optimizer = optim.AdamW(
            model.parameters(), lr=lr, weight_decay=weight_decay
        )
        self.scheduler = optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer, T_max=max_epochs
        )

        self.writer  = SummaryWriter(log_dir=tb_log_dir)
        self.history: list[dict[str, Any]] = []

    # ── Training epoch ────────────────────────────────────────────────────────
    def _train_epoch(self) -> float:
        self.model.train()
        total_loss = 0.0
        n_batches  = 0

        for X, y in self.train_loader:
            X = X.to(self.device)   # [B, 360, 14]
            y = y.to(self.device)   # [B]

            self.optimizer.zero_grad(set_to_none=True)
            logits = self.model(X)  # [B, 1]  raw logits
            loss   = self.criterion(logits, y)
            loss.backward()

            torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.clip_norm)
            self.optimizer.step()

            total_loss += loss.item()
            n_batches  += 1

            if n_batches >= self.steps_per_epoch:
                break

        return total_loss / max(n_batches, 1)

    # ── Validation epoch ──────────────────────────────────────────────────────
    @torch.no_grad()
    def _eval_epoch(
        self, loader: DataLoader
    ) -> tuple[float, dict, dict, float, np.ndarray, np.ndarray]:
        """
        Evaluate on a DataLoader.

        Returns:
            avg_loss:   Scalar loss.
            metrics:    Hard-prediction metrics (using best_threshold).
            prob_metrics: ROC-AUC, PR-AUC, Brier Score.
            best_thresh: Optimal TSS threshold found this epoch.
            all_probs:  [N] raw probabilities.
            all_labels: [N] true labels.
        """
        self.model.eval()
        total_loss = 0.0
        n_batches  = 0
        all_probs  = []
        all_labels = []

        for X, y in loader:
            X = X.to(self.device)
            y = y.to(self.device)

            logits = self.model(X)              # raw logits
            loss   = self.criterion(logits, y)
            total_loss += loss.item()
            n_batches  += 1

            probs = torch.sigmoid(logits).squeeze(-1)
            all_probs.append(probs.cpu().numpy())
            all_labels.append(y.cpu().numpy())

            if n_batches >= self.val_steps:
                break

        avg_loss   = total_loss / max(n_batches, 1)
        all_probs  = np.concatenate(all_probs)
        all_labels = np.concatenate(all_labels)

        # Find optimal threshold on this validation sample
        best_thresh, _ = find_best_threshold(all_labels, all_probs, metric="tss")
        y_pred = (all_probs >= best_thresh).astype(int)

        metrics      = compute_metrics(all_labels, y_pred)
        prob_metrics = compute_prob_metrics(all_labels, all_probs)

        return avg_loss, metrics, prob_metrics, best_thresh, all_probs, all_labels

    # ── Save checkpoint ───────────────────────────────────────────────────────
    def _save_checkpoint(self, filename: str, epoch: int, val_tss: float) -> None:
        path = os.path.join(self.checkpoint_dir, filename)
        torch.save(
            {
                "epoch":          epoch,
                "val_tss":        val_tss,
                "best_threshold": self.best_threshold,
                "model":          self.model.state_dict(),
                "optimizer":      self.optimizer.state_dict(),
                "scheduler":      self.scheduler.state_dict(),
            },
            path,
        )
        logger.info(f"Saved checkpoint: {path}")

    # ── Main training loop ────────────────────────────────────────────────────
    def fit(self) -> list[dict[str, Any]]:
        """
        Train the model for up to max_epochs with early stopping on val TSS.

        Returns:
            history: list of per-epoch metric dicts.
        """
        best_tss     = -float("inf")
        patience_ctr = 0

        logger.info(
            f"Starting training | max_epochs={self.max_epochs} | "
            f"steps_per_epoch={self.steps_per_epoch} | val_steps={self.val_steps} | "
            f"patience={self.patience} | device={self.device}"
        )

        for epoch in range(1, self.max_epochs + 1):
            t0 = time.time()

            train_loss = self._train_epoch()
            val_loss, val_metrics, val_prob_metrics, best_thresh, _, _ = \
                self._eval_epoch(self.val_loader)

            self.best_threshold = best_thresh
            val_tss             = val_metrics["tss"]
            current_lr          = self.scheduler.get_last_lr()[0]
            self.scheduler.step()
            elapsed = time.time() - t0

            # TensorBoard
            self.writer.add_scalar("Loss/train",          train_loss,                        epoch)
            self.writer.add_scalar("Loss/val",            val_loss,                          epoch)
            self.writer.add_scalar("Metrics/val_tss",     val_tss,                           epoch)
            self.writer.add_scalar("Metrics/val_pod",     val_metrics["pod"],                epoch)
            self.writer.add_scalar("Metrics/val_pofd",    val_metrics["pofd"],               epoch)
            self.writer.add_scalar("Metrics/val_roc_auc", val_prob_metrics.get("roc_auc", 0), epoch)
            self.writer.add_scalar("Metrics/val_pr_auc",  val_prob_metrics.get("pr_auc", 0), epoch)
            self.writer.add_scalar("LR",                  current_lr,                        epoch)
            self.writer.add_scalar("Threshold/val_best",  best_thresh,                       epoch)

            record = {
                "epoch":        epoch,
                "train_loss":   round(train_loss, 6),
                "val_loss":     round(val_loss, 6),
                "val_tss":      round(val_tss, 4),
                "val_pod":      round(val_metrics["pod"], 4),
                "val_pofd":     round(val_metrics["pofd"], 4),
                "val_far":      round(val_metrics["far"], 4),
                "val_f1":       round(val_metrics["f1"], 4),
                "val_roc_auc":  round(val_prob_metrics.get("roc_auc", 0.0), 4),
                "val_pr_auc":   round(val_prob_metrics.get("pr_auc", 0.0), 4),
                "val_brier":    round(val_prob_metrics.get("brier_score", 1.0), 4),
                "best_threshold": round(best_thresh, 4),
                "lr":           current_lr,
                "elapsed_sec":  round(elapsed, 1),
            }
            self.history.append(record)

            logger.info(
                f"Epoch {epoch:02d}/{self.max_epochs} | "
                f"train_loss={train_loss:.4f} | val_loss={val_loss:.4f} | "
                f"val_TSS={val_tss:.4f} | val_POD={val_metrics['pod']:.4f} | "
                f"val_POFD={val_metrics['pofd']:.4f} | "
                f"val_ROC={val_prob_metrics.get('roc_auc', 0):.4f} | "
                f"thresh={best_thresh:.3f} | lr={current_lr:.2e} | {elapsed:.1f}s"
            )

            self._save_checkpoint(self.LAST_CKPT, epoch, val_tss)

            if val_tss > best_tss:
                best_tss     = val_tss
                patience_ctr = 0
                self._save_checkpoint(self.BEST_CKPT, epoch, val_tss)
                logger.info(f"  ↑ New best val TSS: {best_tss:.4f} (threshold={best_thresh:.3f})")
            else:
                patience_ctr += 1
                logger.info(f"  No improvement. Patience: {patience_ctr}/{self.patience}")
                if patience_ctr >= self.patience:
                    logger.info(
                        f"Early stopping at epoch {epoch}. Best val TSS: {best_tss:.4f}"
                    )
                    break

        self.writer.close()
        logger.info(f"Training complete. Best val TSS: {best_tss:.4f}")
        return self.history

    # ── Test evaluation (loads best checkpoint) ───────────────────────────────
    def evaluate_test(
        self, test_loader: DataLoader
    ) -> tuple[dict, dict, np.ndarray, np.ndarray]:
        """
        Load best checkpoint and run full test set evaluation.

        Returns:
            hard_metrics:  TSS, POD, POFD, FAR, Precision, Recall, F1.
            prob_metrics:  ROC-AUC, PR-AUC, Brier Score.
            all_probs:     [N] sigmoid probabilities.
            all_labels:    [N] true binary labels.
        """
        best_path  = os.path.join(self.checkpoint_dir, self.BEST_CKPT)
        checkpoint = torch.load(best_path, map_location=self.device, weights_only=True)
        self.model.load_state_dict(checkpoint["model"])
        self.best_threshold = checkpoint.get("best_threshold", 0.5)

        logger.info(
            f"Loaded best checkpoint from epoch {checkpoint['epoch']} "
            f"(val TSS={checkpoint['val_tss']:.4f}, threshold={self.best_threshold:.3f})"
        )

        self.model.eval()
        all_probs  = []
        all_labels = []

        with torch.no_grad():
            for X, y in test_loader:
                X      = X.to(self.device)
                logits = self.model(X)
                probs  = torch.sigmoid(logits).squeeze(-1)
                all_probs.append(probs.cpu().numpy())
                all_labels.append(y.numpy())

        all_probs  = np.concatenate(all_probs)
        all_labels = np.concatenate(all_labels)

        # Use threshold from best val checkpoint
        y_pred       = (all_probs >= self.best_threshold).astype(int)
        hard_metrics = compute_metrics(all_labels, y_pred)
        prob_metrics = compute_prob_metrics(all_labels, all_probs)

        return hard_metrics, prob_metrics, all_probs, all_labels
