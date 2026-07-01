"""
app/services/ml/trainer_v3.py

Training orchestration for SuryaNet Version 3 model using transfer learning.
"""

import os
import time
import logging
import random
import math
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter

from app.services.ml.model_v3 import LateFusionPatchTST
from app.services.ml.metrics import compute_metrics, compute_prob_metrics, find_best_threshold

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Global Seeding Utility for Deterministic Reproducibility
# ──────────────────────────────────────────────────────────────────────────────
def set_seed(seed: int = 42):
    """
    Sets global seeds for Python, NumPy, PyTorch, and accelerator backends.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    elif torch.backends.mps.is_available():
        torch.mps.manual_seed(seed)
    logger.info(f"Deterministic seed set to: {seed}")

# Focal Loss (operating on raw logits)
class FocalLoss(nn.Module):
    def __init__(self, gamma: float = 2.0, alpha: float = 0.25, reduction: str = "mean"):
        super().__init__()
        self.gamma = gamma
        self.alpha = float(torch.clamp(torch.tensor(alpha), 0.25, 0.75))
        self.reduction = reduction

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        logits = logits.squeeze(-1)
        bce = nn.functional.binary_cross_entropy_with_logits(logits, targets, reduction="none")
        probs = torch.sigmoid(logits)
        p_t = probs * targets + (1.0 - probs) * (1.0 - targets)
        alpha_t = self.alpha * targets + (1.0 - self.alpha) * (1.0 - targets)
        focal = alpha_t * ((1.0 - p_t) ** self.gamma) * bce
        if self.reduction == "mean":
            return focal.mean()
        return focal.sum()

def set_encoder_frozen(model: LateFusionPatchTST, name: str, freeze: bool = True):
    """
    Freeze or unfreeze the parameters of a specific instrument branch.
    """
    assert name in ["goes", "solexs", "hel1os"], f"Invalid branch name: {name}"
    
    # Submodules matching the branch name
    submodule_prefixes = {
        "goes": ["patch_embed_goes", "pos_enc_goes", "encoder_goes", "norm_goes", "pool_query_goes", "pool_attn_goes"],
        "solexs": ["patch_embed_solexs", "pos_enc_solexs", "encoder_solexs", "norm_solexs", "pool_query_solexs", "pool_attn_solexs", "missing_token_solexs", "proj_solexs"],
        "hel1os": ["patch_embed_hel1os", "pos_enc_hel1os", "encoder_hel1os", "norm_hel1os", "pool_query_hel1os", "pool_attn_hel1os", "missing_token_hel1os", "proj_hel1os"]
    }
    
    prefixes = submodule_prefixes[name]
    count = 0
    for n, p in model.named_parameters():
        if any(n.startswith(prefix) for prefix in prefixes):
            p.requires_grad = not freeze
            count += 1
            
    action = "Freezing" if freeze else "Unfreezing"
    logger.info(f"{action} {name} branch: affected {count} parameter tensors.")

class TrainerV3:
    """
    Version 3 Training Orchestrator supporting Stage 1 (pretrain) and Stage 2 (fine-tune) unfreezing.
    Includes deterministic seeding, optimizer state mapping, and advanced training diagnostics.
    """

    def __init__(
        self,
        model: LateFusionPatchTST,
        train_loader: DataLoader,
        val_loader: DataLoader,
        pos_rate: float,
        checkpoint_dir: str = "artifacts/models_v3",
        tb_log_dir: str = "artifacts/runs_v3",
        max_epochs: int = 10,
        patience: int = 3,
        lr: float = 1e-4,
        weight_decay: float = 1e-4,
        clip_norm: float = 1.0,
        device: str = "cpu",
        seed: int | None = None
    ):
        self.model = model
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.max_epochs = max_epochs
        self.patience = patience
        self.lr = lr
        self.weight_decay = weight_decay
        self.clip_norm = clip_norm
        self.device = torch.device(device)
        self.checkpoint_dir = checkpoint_dir

        if seed is not None:
            set_seed(seed)
            # Enforce dataloader worker determinism if possible
            if hasattr(self.train_loader, "generator") and self.train_loader.generator is not None:
                self.train_loader.generator.manual_seed(seed)

        self.model.to(self.device)
        self.criterion = FocalLoss(alpha=pos_rate)
        device_type = self.device.type
        self.scaler = torch.amp.GradScaler(device_type, enabled=(device_type in ["cuda", "mps"]))
        
        self.best_val_tss = -1.0
        self.start_epoch = 1
        self.current_epoch = 0

        # Build initial optimizer and scheduler
        self.optimizer = None
        self.scheduler = None
        self.rebuild_optimizer_and_scheduler()

        os.makedirs(checkpoint_dir, exist_ok=True)
        self.writer = SummaryWriter(log_dir=tb_log_dir)

    def set_encoder_frozen(self, name: str, freeze: bool = True):
        """
        Helper method to freeze/unfreeze encoder branches and rebuild the optimizer state mapping.
        """
        set_encoder_frozen(self.model, name, freeze)
        self.rebuild_optimizer_and_scheduler()

    def rebuild_optimizer_and_scheduler(self):
        """
        Rebuilds optimizer and scheduler to match the current set of trainable parameters.
        Preserves optimizer momentum and state history for parameters that remain trainable.
        """
        old_optimizer = self.optimizer
        trainable_params = list(filter(lambda p: p.requires_grad, self.model.parameters()))

        # Instantiate new optimizer
        self.optimizer = optim.AdamW(
            trainable_params,
            lr=self.lr,
            weight_decay=self.weight_decay
        )

        # Copy state history from old optimizer for active parameters
        copied_states = 0
        if old_optimizer is not None:
            for p in trainable_params:
                if p in old_optimizer.state:
                    self.optimizer.state[p] = old_optimizer.state[p]
                    copied_states += 1

        # Prevent scheduler initial_lr KeyError when resuming or rebuilding midway
        for group in self.optimizer.param_groups:
            group.setdefault("initial_lr", self.lr)

        # Cosine learning rate scheduler (aligning last_epoch index)
        scheduler_last_epoch = max(-1, self.current_epoch - 1)
        self.scheduler = optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer,
            T_max=self.max_epochs,
            last_epoch=scheduler_last_epoch
        )

        logger.info(
            f"Optimizer & Scheduler rebuilt | "
            f"trainable_parameters={sum(p.numel() for p in trainable_params):,} | "
            f"preserved_optimizer_states={copied_states} | "
            f"scheduler_last_epoch={scheduler_last_epoch}"
        )

    def get_gradient_norms(self) -> dict[str, float]:
        """
        Computes L2 gradient norms grouped by instrument branches and architectural submodules.
        """
        norms = {"goes": 0.0, "solexs": 0.0, "hel1os": 0.0, "fusion": 0.0, "classifier": 0.0, "total": 0.0}
        squares = {k: 0.0 for k in norms}
        
        for name, param in self.model.named_parameters():
            if param.grad is not None:
                grad_norm = param.grad.data.norm(2).item()
                val = grad_norm ** 2
                squares["total"] += val
                
                # Categorize submodules
                if any(x in name for x in ["goes"]):
                    squares["goes"] += val
                elif any(x in name for x in ["solexs"]):
                    squares["solexs"] += val
                elif any(x in name for x in ["hel1os"]):
                    squares["hel1os"] += val
                elif any(x in name for x in ["fusion_attn"]):
                    squares["fusion"] += val
                elif any(x in name for x in ["head"]):
                    squares["classifier"] += val

        for k in norms:
            norms[k] = math.sqrt(squares[k])
        return norms

    def train_epoch(self, epoch: int) -> tuple[float, float]:
        self.model.train()
        total_loss = 0.0
        n_batches = 0
        
        t_start = time.time()
        total_samples = 0

        for batch_idx, (inputs, targets) in enumerate(self.train_loader):
            # Unpack inputs
            x_g, x_s, x_h, m_s, m_h = [x.to(self.device) for x in inputs]
            targets = targets.to(self.device)
            total_samples += x_g.size(0)

            self.optimizer.zero_grad()

            # Mixed precision training
            device_type = self.device.type
            enabled = device_type in ["cuda", "mps"]
            with torch.amp.autocast(device_type=device_type if enabled else "cpu", enabled=enabled):
                logits = self.model(x_g, x_s, x_h, m_s, m_h)
                loss = self.criterion(logits, targets)

            # NaN check in loss
            if torch.isnan(loss):
                logger.error(f"NaN loss detected at epoch {epoch}, batch {batch_idx}!")
                raise ValueError("Training aborted due to NaN loss.")

            # Backpropagation using GradScaler
            self.scaler.scale(loss).backward()
            
            # Gradient clipping
            self.scaler.unscale_(self.optimizer)
            
            # NaN check in gradients
            has_nan = False
            for p in self.model.parameters():
                if p.grad is not None and torch.isnan(p.grad).any():
                    has_nan = True
                    break
            if has_nan:
                logger.warning(f"NaN gradient detected at epoch {epoch}, batch {batch_idx}! Clipping skipped for batch.")
                # We skip optimizer step for this batch to prevent weight corruption
                self.optimizer.zero_grad()
                continue

            nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=self.clip_norm)
            
            self.scaler.step(self.optimizer)
            self.scaler.update()

            total_loss += loss.item()
            n_batches += 1
            
        epoch_loss = total_loss / n_batches if n_batches > 0 else 0.0
        t_elapsed = time.time() - t_start
        throughput = total_samples / t_elapsed if t_elapsed > 0 else 0.0
        
        return epoch_loss, throughput

    def validate(self) -> tuple[float, float, float]:
        self.model.eval()
        total_loss = 0.0
        n_batches = 0
        
        all_logits = []
        all_targets = []

        with torch.no_grad():
            for inputs, targets in self.val_loader:
                x_g, x_s, x_h, m_s, m_h = [x.to(self.device) for x in inputs]
                targets = targets.to(self.device)

                logits = self.model(x_g, x_s, x_h, m_s, m_h)
                loss = self.criterion(logits, targets)

                total_loss += loss.item()
                n_batches += 1

                all_logits.append(logits.cpu())
                all_targets.append(targets.cpu())

        val_loss = total_loss / n_batches if n_batches > 0 else 0.0
        
        logits_concat = torch.cat(all_logits, dim=0).numpy().squeeze(-1)
        targets_concat = torch.cat(all_targets, dim=0).numpy()
        
        probs = 1.0 / (1.0 + np.exp(-logits_concat))
        preds = np.where(probs >= 0.5, 1, 0)
        
        metrics = compute_metrics(targets_concat, preds)
        best_th, best_tss = find_best_threshold(targets_concat, probs)

        return val_loss, best_tss, best_th

    def fit(self, stage_label="training") -> str:
        logger.info(f"Starting {stage_label} loop from epoch {self.start_epoch} to {self.max_epochs}...")
        
        patience_counter = 0
        best_model_path = ""

        # Query memory allocations if CUDA or MPS available
        def get_memory_allocated():
            if torch.cuda.is_available():
                return torch.cuda.memory_allocated() / (1024 ** 2) # MB
            elif torch.backends.mps.is_available():
                # Query allocated memory if torch supports it
                try:
                    return torch.mps.current_allocated_memory() / (1024 ** 2) # MB
                except AttributeError:
                    return 0.0
            return 0.0

        for epoch in range(self.start_epoch, self.max_epochs + 1):
            self.current_epoch = epoch
            t0 = time.time()
            
            train_loss, throughput = self.train_epoch(epoch)
            
            # Compute gradient norms at the end of epoch backprop
            grad_norms = self.get_gradient_norms()
            
            val_loss, val_tss, val_th = self.validate()
            self.scheduler.step()
            
            elapsed = time.time() - t0
            memory_used = get_memory_allocated()
            
            # Logging to TensorBoard
            self.writer.add_scalar(f"{stage_label}/Loss/train", train_loss, epoch)
            self.writer.add_scalar(f"{stage_label}/Loss/val", val_loss, epoch)
            self.writer.add_scalar(f"{stage_label}/TSS/val", val_tss, epoch)
            self.writer.add_scalar(f"{stage_label}/lr", self.optimizer.param_groups[0]["lr"], epoch)
            self.writer.add_scalar(f"{stage_label}/Throughput", throughput, epoch)
            self.writer.add_scalar(f"{stage_label}/MemoryMB", memory_used, epoch)
            for name, val in grad_norms.items():
                self.writer.add_scalar(f"{stage_label}/GradNorm/{name}", val, epoch)
            
            logger.info(
                f"Epoch {epoch:02d} | Train Loss: {train_loss:.5f} | Val Loss: {val_loss:.5f} | "
                f"Val TSS: {val_tss:.4f} (best_th={val_th:.4f}) | lr: {self.optimizer.param_groups[0]['lr']:.2e} | "
                f"Throughput: {throughput:.1f} samples/s | Mem: {memory_used:.1f} MB | time: {elapsed:.1f}s"
            )

            # Checkpoint saving
            is_best = val_tss > self.best_val_tss
            if is_best:
                self.best_val_tss = val_tss
                patience_counter = 0
                best_model_path = os.path.join(self.checkpoint_dir, f"patchtst_{stage_label}_best.pt")
                self.save_checkpoint(epoch, best_model_path)
                logger.info(f"→ Saved new BEST model checkpoint to {best_model_path}")
            else:
                patience_counter += 1
                
            # Regular checkpoint
            latest_path = os.path.join(self.checkpoint_dir, f"patchtst_{stage_label}_latest.pt")
            self.save_checkpoint(epoch, latest_path)

            if patience_counter >= self.patience:
                logger.warning(f"Early stopping triggered after {patience_counter} epochs without val TSS improvement.")
                break
                
        return best_model_path

    def save_checkpoint(self, epoch: int, filepath: str):
        state = {
            "epoch": epoch,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "scheduler_state_dict": self.scheduler.state_dict(),
            "scaler_state_dict": self.scaler.state_dict(),
            "best_val_tss": self.best_val_tss,
            "current_epoch": self.current_epoch,
        }
        torch.save(state, filepath)

    def load_checkpoint(self, filepath: str):
        logger.info(f"Loading checkpoint state from {filepath}...")
        checkpoint = torch.load(filepath, map_location=self.device)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
        if "scaler_state_dict" in checkpoint:
            self.scaler.load_state_dict(checkpoint["scaler_state_dict"])
        self.start_epoch = checkpoint["epoch"] + 1
        self.current_epoch = checkpoint.get("current_epoch", checkpoint["epoch"])
        self.best_val_tss = checkpoint["best_val_tss"]
        logger.info(f"Checkpoint loaded. Resuming from epoch {self.start_epoch} (best TSS={self.best_val_tss:.4f}).")
