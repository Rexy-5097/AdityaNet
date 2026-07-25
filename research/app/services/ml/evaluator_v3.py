"""
app/services/ml/evaluator_v3.py

Evaluation and calibration modules for Version 3 Multi-Instrument forecasting system.
"""

import logging
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.isotonic import IsotonicRegression

from app.services.ml.metrics import compute_full_suite, compute_ece

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# 1. Temperature Scaler for Logits Calibration
# ──────────────────────────────────────────────────────────────────────────────
class TemperatureScaler(nn.Module):
    """
    Parametric calibration using Temperature Scaling on raw logits.
    Fits temperature parameter T > 0 on validation set to minimize NLL.
    """

    def __init__(self):
        super().__init__()
        self.temperature = nn.Parameter(torch.ones(1) * 1.5)

    def forward(self, logits: torch.Tensor) -> torch.Tensor:
        # Scale logits
        return logits / self.temperature

    def fit(self, val_logits: torch.Tensor, val_targets: torch.Tensor, max_epochs: int = 100):
        """
        Fit temperature parameter using LBFGS optimizer on validation logits.
        """
        logger.info("Fitting Temperature Scaler on validation logits...")
        val_logits = val_logits.clone().detach().cpu()
        val_targets = val_targets.clone().detach().cpu().float()

        # Optimizer
        optimizer = optim.LBFGS([self.temperature], lr=0.01, max_iter=max_epochs)
        criterion = nn.BCEWithLogitsLoss()

        def eval_val():
            optimizer.zero_grad()
            loss = criterion(self.forward(val_logits).squeeze(-1), val_targets)
            loss.backward()
            return loss

        optimizer.step(eval_val)
        # Ensure T > 0
        with torch.no_grad():
            self.temperature.clamp_(min=1e-4)
            
        logger.info(f"Fitted Temperature: {self.temperature.item():.4f}")
        return self

# ──────────────────────────────────────────────────────────────────────────────
# 2. Complete Evaluator
# ──────────────────────────────────────────────────────────────────────────────
class EvaluatorV3:
    """
    Computes scientific forecasting metrics and fits calibrator targets.
    """

    def __init__(self):
        self.isotonic_calibrator = IsotonicRegression(out_of_bounds='clip')
        self.temp_scaler = TemperatureScaler()

    def fit_calibrators(self, val_logits: np.ndarray, val_targets: np.ndarray):
        val_logits = np.ravel(val_logits)
        val_targets = np.ravel(val_targets)
        # Convert val logits to probabilities for isotonic
        val_probs = 1.0 / (1.0 + np.exp(-val_logits))
        self.isotonic_calibrator.fit(val_probs, val_targets)
        
        # Fit temperature scaling
        val_logits_t = torch.tensor(val_logits)
        val_targets_t = torch.tensor(val_targets)
        self.temp_scaler.fit(val_logits_t, val_targets_t)

    def calibrate_probabilities(self, logits: np.ndarray, method="isotonic") -> np.ndarray:
        logits = np.ravel(logits)
        raw_probs = 1.0 / (1.0 + np.exp(-logits))
        if method == "isotonic":
            return self.isotonic_calibrator.predict(raw_probs)
        elif method == "temperature":
            with torch.no_grad():
                scaled_logits = self.temp_scaler(torch.tensor(logits)).numpy()
            return 1.0 / (1.0 + np.exp(-scaled_logits))
        return raw_probs

    def evaluate(self, logits: np.ndarray, targets: np.ndarray, threshold: float = 0.5) -> dict:
        """
        Calculate complete metric suite using the canonical metrics module.
        """
        logits = np.ravel(logits)
        targets = np.ravel(targets)
        probs = 1.0 / (1.0 + np.exp(-logits))
        return compute_full_suite(targets, probs, threshold=threshold)
