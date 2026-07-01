"""
app/services/ml/inference.py

SuryaNet Sprint 5.5 — Upgraded Operational Inference Service

Changes vs Sprint 5:
  - Loads thresholds from artifacts/operator_thresholds.json (Sprint 5.5 format)
    with tiered uncertainty suppression keys.
  - RED alert confirmation uses rolling-mean + positive linear slope instead of
    strict monotonic comparison. Per user specification:
        mean(last 3 probs) > red_threshold  AND  linregress slope > 0
  - Three-tier uncertainty suppression:
        unc > 0.10  →  RED  → YELLOW
        unc > 0.15  →  YELLOW → GREEN
        unc > 0.20  →  all alerts → GREEN
  - Confidence levels: HIGH / MEDIUM / LOW based on probability + uncertainty.
  - Integrates explainability layer (CLS attention top-3 patches + physical context).
  - Integrates ISRO mission impact catalog.
"""

import os
import json
import logging
import pickle
import numpy as np
import pandas as pd
import torch
from collections import deque
from threading import Lock
from scipy.stats import linregress

from app.services.ml.model import PatchTST, predict_with_uncertainty
from app.services.ml.features import compute_features

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Calibrator Wrapper Class
# ──────────────────────────────────────────────────────────────────────────────
class CalibratorWrapper:
    """
    Wrapper for probability calibration models.
    Supports Platt Scaling (Logistic Regression on logits) and Isotonic Regression.
    """
    def __init__(self, method: str, model):
        self.method = method
        self.model = model

    def __call__(self, p: float | np.ndarray) -> float | np.ndarray:
        p_arr = np.atleast_1d(p)
        if self.method == "platt":
            eps = 1e-7
            p_clipped = np.clip(p_arr, eps, 1 - eps)
            logits = np.log(p_clipped / (1 - p_clipped)).reshape(-1, 1)
            cal_p = self.model.predict_proba(logits)[:, 1]
        elif self.method == "isotonic":
            cal_p = self.model.predict(p_arr)
        else:
            cal_p = p_arr

        if np.isscalar(p):
            return float(cal_p[0])
        return cal_p


# ──────────────────────────────────────────────────────────────────────────────
# SuryaNet Operational Inference Service
# ──────────────────────────────────────────────────────────────────────────────
class SuryaNetInferenceService:
    """
    Production-ready inference service for SuryaNet PatchTST solar flare forecasting.

    Sprint 5.5 upgrades:
      - Tiered uncertainty suppression (0.10/0.15/0.20).
      - RED confirmation via rolling mean + positive linear slope.
      - Confidence levels: HIGH / MEDIUM / LOW.
      - Integrated explainability (attention patch mapping).
      - Integrated ISRO mission impact assessment.
    """

    def __init__(
        self,
        model_path:        str = os.path.join("artifacts", "models", "patchtst_best.pt"),
        calibrator_path:   str = os.path.join("artifacts", "calibrator.pkl"),
        thresholds_path:   str = os.path.join("artifacts", "operator_thresholds.json"),
        feature_cols_path: str = os.path.join("artifacts", "feature_columns.json"),
        n_dropout_samples: int = 50,
    ):
        self.device            = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
        self.n_dropout_samples = n_dropout_samples
        self.lock              = Lock()

        # Rolling history for consecutive-alert confirmation (prob, unc per step)
        # Stores tuples of (calibrated_prob, uncertainty_std)
        self._history: deque = deque(maxlen=3)

        # 1. Load feature columns
        if not os.path.exists(feature_cols_path):
            raise FileNotFoundError(f"Feature columns JSON not found: {feature_cols_path}")
        with open(feature_cols_path, "r") as f:
            self.feature_cols = json.load(f)

        # 2. Initialize and load model
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model checkpoint not found: {model_path}")
        checkpoint = torch.load(model_path, map_location="cpu", weights_only=True)
        self.model = PatchTST()
        self.model.load_state_dict(checkpoint["model"])
        self.model.to(self.device)
        self.model.eval()
        logger.info(f"Loaded PatchTST model from {model_path} onto {self.device}")

        # 3. Load calibrator
        if not os.path.exists(calibrator_path):
            raise FileNotFoundError(f"Calibrator pickle not found: {calibrator_path}")
        with open(calibrator_path, "rb") as f:
            self.calibrator = pickle.load(f)
        logger.info(f"Loaded calibrator ({self.calibrator.method}) from {calibrator_path}")

        # 4. Load Sprint 5.5 thresholds (extended format)
        if not os.path.exists(thresholds_path):
            raise FileNotFoundError(f"Thresholds JSON not found: {thresholds_path}")
        with open(thresholds_path, "r") as f:
            td = json.load(f)

        self.yellow_threshold = td["yellow_threshold"]
        self.red_threshold    = td["red_threshold"]

        # Tiered uncertainty suppression thresholds
        self.unc_red_to_yellow     = td.get("uncertainty_suppress_red_to_yellow",   0.10)
        self.unc_yellow_to_green   = td.get("uncertainty_suppress_yellow_to_green", 0.15)
        self.unc_all_to_green      = td.get("uncertainty_suppress_all_to_green",    0.20)

        # Confidence level thresholds
        self.conf_high_prob_min   = td.get("confidence_high_prob_min",   self.red_threshold)
        self.conf_high_unc_max    = td.get("confidence_high_unc_max",    0.05)
        self.conf_medium_prob_min = td.get("confidence_medium_prob_min", self.yellow_threshold)
        self.conf_medium_unc_max  = td.get("confidence_medium_unc_max",  0.10)

        logger.info(
            f"Thresholds: yellow={self.yellow_threshold:.4f}, red={self.red_threshold:.4f} | "
            f"Uncertainty tiers: {self.unc_red_to_yellow}/{self.unc_yellow_to_green}/{self.unc_all_to_green}"
        )

    # ── Alert Level Logic ──────────────────────────────────────────────────────

    def _determine_raw_alert(self, prob: float) -> str:
        if prob < self.yellow_threshold:
            return "GREEN"
        elif prob < self.red_threshold:
            return "YELLOW"
        else:
            return "RED"

    def _apply_tiered_uncertainty_suppression(self, raw_alert: str, uncertainty: float) -> str:
        """
        Sprint 5.5 three-tier suppression:
          unc > 0.20  →  all alerts → GREEN
          unc > 0.15  →  YELLOW → GREEN
          unc > 0.10  →  RED → YELLOW
        """
        if uncertainty > self.unc_all_to_green:
            return "GREEN"
        if uncertainty > self.unc_yellow_to_green:
            if raw_alert in ("YELLOW", "RED"):
                return "GREEN"
        if uncertainty > self.unc_red_to_yellow:
            if raw_alert == "RED":
                return "YELLOW"
        return raw_alert

    def _determine_confidence_level(self, prob: float, uncertainty: float) -> str:
        """
        Sprint 5.5 confidence levels:
          HIGH   : prob >= red_threshold   AND  unc < 0.05
          MEDIUM : prob >= yellow_threshold AND  unc < 0.10
          LOW    : otherwise
        """
        if prob >= self.conf_high_prob_min and uncertainty < self.conf_high_unc_max:
            return "HIGH"
        if prob >= self.conf_medium_prob_min and uncertainty < self.conf_medium_unc_max:
            return "MEDIUM"
        return "LOW"

    def _check_red_confirmation(
        self,
        alert: str,
        cal_probs_window: np.ndarray,
        std_probs_window: np.ndarray,
    ) -> tuple[str, str]:
        """
        Sprint 5.5 RED alert confirmation using rolling mean + linear slope.

        Confirmation requires:
          1. mean(last 3 calibrated probs) > red_threshold
          2. Linear regression slope over last 3 probs > 0  (rising trend)

        If not confirmed: RED → YELLOW, status = "UNCONFIRMED"

        Returns (alert_level, confirmation_status)
        """
        if alert != "RED":
            return alert, "CONFIRMED"

        # If we have 3 windows in this batch, use them statelessly
        if len(cal_probs_window) >= 3:
            last3_probs = cal_probs_window[-3:]
            mean_p      = float(np.mean(last3_probs))
            x_coords    = np.arange(3, dtype=float)
            slope, _, _, _, _ = linregress(x_coords, last3_probs)

            confirmed = (mean_p > self.red_threshold) and (slope > 0.0)
            if not confirmed:
                return "YELLOW", "UNCONFIRMED"
            return "RED", "CONFIRMED"

        # Stateful path: check rolling history buffer
        with self.lock:
            hist_probs = [p for p, _ in self._history]
            all_probs  = hist_probs + [float(cal_probs_window[-1])]

            if len(all_probs) >= 3:
                last3 = all_probs[-3:]
                mean_p = float(np.mean(last3))
                x_coords = np.arange(len(last3), dtype=float)
                slope, _, _, _, _ = linregress(x_coords, last3)
                confirmed = (mean_p > self.red_threshold) and (slope > 0.0)
            else:
                confirmed = False

        if not confirmed:
            return "YELLOW", "UNCONFIRMED"
        return "RED", "CONFIRMED"

    # ── Prediction Pipeline ────────────────────────────────────────────────────

    def predict(
        self,
        df: pd.DataFrame,
        flare_times: list | None = None,
        include_explainability: bool = True,
    ) -> dict:
        """
        Execute the full Sprint 5.5 prediction pipeline:

          1. Feature engineering
          2. Batched model inference with MC Dropout (50 samples)
          3. Probability calibration
          4. Tiered uncertainty suppression
          5. RED alert confirmation (rolling mean + slope)
          6. Confidence level assignment (HIGH/MEDIUM/LOW)
          7. Explainability: top-3 CLS attention patches with physical context
          8. ISRO mission impact assessment

        Args:
            df:                    DataFrame with ≥ 360 rows of timestamp/short_flux/long_flux.
            flare_times:           Recent M/X flare timestamps for physics feature computation.
            include_explainability: If False, skip attention extraction (faster for batch use).

        Returns:
            dict with all prediction outputs including explainability and impact.
        """
        if len(df) < 360:
            raise ValueError(
                f"Input DataFrame must contain at least 360 minutes of history. Got {len(df)}"
            )

        # 1. Feature engineering
        df = df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)

        df_feats      = compute_features(df, flare_times=flare_times)
        features_arr  = df_feats[self.feature_cols].values.astype(np.float32)
        features_arr  = np.nan_to_num(features_arr, nan=0.0, posinf=0.0, neginf=0.0)

        # 2. Build batch of up to 3 consecutive windows for rolling confirmation
        N = len(df)
        windows = []
        if N >= 362:
            windows.append(features_arr[N - 362 : N - 2])   # t-2
            windows.append(features_arr[N - 361 : N - 1])   # t-1
            windows.append(features_arr[N - 360 : N])        # t (current)
            stateless = True
        else:
            windows.append(features_arr[N - 360 : N])
            stateless = False

        X_batch = torch.from_numpy(np.stack(windows)).to(self.device)

        # 3. MC Dropout inference
        res       = predict_with_uncertainty(self.model, X_batch, n_samples=self.n_dropout_samples)
        mean_probs = res["mean_prob"].cpu().numpy()   # [batch]
        std_probs  = res["std_prob"].cpu().numpy()    # [batch]

        # 4. Calibrate
        cal_probs = self.calibrator(mean_probs)

        # 5. Apply tiered uncertainty suppression to each window
        suppressed_alerts = []
        for i in range(len(cal_probs)):
            raw   = self._determine_raw_alert(float(cal_probs[i]))
            supp  = self._apply_tiered_uncertainty_suppression(raw, float(std_probs[i]))
            suppressed_alerts.append(supp)

        # Extract current-window values
        curr_cal_prob  = float(cal_probs[-1])
        curr_raw_prob  = float(mean_probs[-1])
        curr_unc_std   = float(std_probs[-1])
        curr_alert     = suppressed_alerts[-1]

        # 6. RED confirmation: rolling mean + positive slope
        curr_alert, confirmation = self._check_red_confirmation(
            curr_alert, cal_probs, std_probs
        )

        # 6.5. Hard X-Ray Coincidence Layer
        suppression_reason = None
        if curr_alert == "RED":
            # Retrieve short_flux column history
            short_flux_series = df["short_flux"]
            
            # Missing data handling: Log NaNs and fill using forward-fill then backward-fill
            num_nans = int(short_flux_series.isna().sum())
            if num_nans > 0:
                logger.warning(f"Found {num_nans} NaN values in short_flux window. Interpolating...")
            short_flux_filled = short_flux_series.ffill().bfill()
            
            # Timestamps and cadence check / time step calculation
            ts_series = df["timestamp"]
            t_curr = ts_series.iloc[-1]
            t_5m = ts_series.iloc[-6]
            t_10m = ts_series.iloc[-11]
            
            dt = (t_curr - t_5m).total_seconds() / 60.0
            dt_prev = (t_5m - t_10m).total_seconds() / 60.0
            
            # Guard for non-positive dt values (cadence guard)
            if dt <= 0.0 or dt_prev <= 0.0:
                logger.warning(f"Invalid time delta detected (dt={dt:.2f}, dt_prev={dt_prev:.2f}). Falling back to 5.0 minutes cadence.")
                dt = 5.0
                dt_prev = 5.0
            
            val_t = float(short_flux_filled.iloc[-1])
            val_t5 = float(short_flux_filled.iloc[-6])
            val_t10 = float(short_flux_filled.iloc[-11])
            
            grad = (val_t - val_t5) / dt
            grad_prev = (val_t5 - val_t10) / dt_prev
            acc = (grad - grad_prev) / ((dt + dt_prev) / 2.0)
            
            rules_passed = 0
            if grad > 0.0:
                rules_passed += 1
            if acc > 0.0:
                rules_passed += 1
                
            if rules_passed < 2:
                curr_alert = "YELLOW"
                suppression_reason = f"coincidence_suppressed: rules_passed={rules_passed}"

        # 7. Confidence level
        confidence_level = self._determine_confidence_level(curr_cal_prob, curr_unc_std)

        # 8. Update stateful history (for subsequent single-window calls)
        with self.lock:
            self._history.append((curr_cal_prob, curr_unc_std))

        # 9. Explainability: top-3 CLS attention patches
        top_attention_patches = []
        if include_explainability:
            try:
                from app.services.ml.explainability import get_top_attention_patches
                x_single = X_batch[-1:, :, :]   # [1, 360, 14] – current window
                df_input  = df.iloc[N - 360 :].reset_index(drop=True)
                top_attention_patches = get_top_attention_patches(
                    self.model, x_single, df_input, top_k=3
                )
            except Exception as exc:
                logger.warning(f"Explainability extraction failed (non-fatal): {exc}")

        # 10. ISRO mission impact assessment
        impact_assessment = {}
        try:
            from app.services.operations.impact import get_mission_impact_assessment
            impact_assessment = get_mission_impact_assessment(
                alert_level=curr_alert,
                probability=curr_cal_prob,
                uncertainty=curr_unc_std,
            )
        except Exception as exc:
            logger.warning(f"Mission impact assessment failed (non-fatal): {exc}")

        return {
            "raw_probability":         curr_raw_prob,
            "calibrated_probability":  curr_cal_prob,
            "uncertainty_std":         curr_unc_std,
            "alert_level":             curr_alert,
            "confirmation":            confirmation,
            "confidence_level":        confidence_level,
            "top_attention_patches":   top_attention_patches,
            "mission_impact":          impact_assessment,
            "suppression_reason":      suppression_reason,
        }
