import logging
import numpy as np
import pandas as pd
from app.services.ml.config import (
    ROLLING_WINDOWS,
    PEAK_WINDOWS,
    GRADIENT_WINDOWS,
    ACCELERATION_WINDOWS,
    MAX_FLARE_DISTANCE_MINUTES,
)

logger = logging.getLogger(__name__)


def compute_features(df: pd.DataFrame, flare_times: list[pd.Timestamp] | None = None) -> pd.DataFrame:
    """
    Generate physics-aware features from GOES telemetry.
    
    Inputs:
        df: pd.DataFrame with sorted ['timestamp', 'short_flux', 'long_flux'] columns.
        flare_times: list of sorted pd.Timestamp representing flare start times.
        
    Returns:
        pd.DataFrame containing the generated feature columns.
    """
    logger.info("Computing physics-aware features...")
    df = df.copy()
    
    # 1. Raw features (assumes short_flux and long_flux are present)
    # 2. Log flux features (epsilon is added to prevent log(0) / negative infinity)
    df["log_long_flux"] = np.log(df["long_flux"] + 1e-9)

    # 3. Rolling Mean & Variance Features
    for window in ROLLING_WINDOWS:
        df[f"mean_{window}m"] = df["long_flux"].rolling(window=window, min_periods=1).mean()
        df[f"variance_{window}m"] = df["long_flux"].rolling(window=window, min_periods=1).var().fillna(0)

    # 4. Peak Features
    for window in PEAK_WINDOWS:
        df[f"peak_{window}m"] = df["long_flux"].rolling(window=window, min_periods=1).max()

    # 5. Gradient Features (First Derivative)
    for window in GRADIENT_WINDOWS:
        # Rate of change per minute over the window
        df[f"flux_gradient_{window}m"] = df["long_flux"].diff(window) / float(window)

    # 6. Second Derivative Features (Acceleration)
    for window in ACCELERATION_WINDOWS:
        gradient_col = f"flux_gradient_{window}m"
        # Rate of change of gradient per minute
        df[f"flux_acceleration_{window}m"] = df[gradient_col].diff(window) / float(window)

    # 7. Event Distance Feature (minutes_since_last_flare)
    if flare_times:
        # Create a sorted reference dataframe for merge_asof
        flares_df = pd.DataFrame({
            "last_flare_time": sorted(flare_times)
        })
        flares_df["last_flare_time_match"] = flares_df["last_flare_time"]
        
        # Merge telemetry and flares using backward direction (closest past flare)
        merged = pd.merge_asof(
            df,
            flares_df,
            left_on="timestamp",
            right_on="last_flare_time",
            direction="backward"
        )
        
        # Calculate distance in minutes
        delta_minutes = (merged["timestamp"] - merged["last_flare_time_match"]).dt.total_seconds() / 60.0
        
        # Fill missing values (no previous flare) and clip to maximum cap
        df["minutes_since_last_flare"] = delta_minutes.fillna(float(MAX_FLARE_DISTANCE_MINUTES)).clip(
            upper=float(MAX_FLARE_DISTANCE_MINUTES)
        )
    else:
        # Default if no historical flares are provided
        df["minutes_since_last_flare"] = float(MAX_FLARE_DISTANCE_MINUTES)

    return df
