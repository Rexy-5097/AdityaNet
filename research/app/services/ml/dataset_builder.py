import json
import logging
import os
import pandas as pd
from sqlalchemy import select
from app.db.session import async_session_maker
from app.models.goes import GOESXRS
from app.models.flare import FlareEvent
from app.services.ml.config import FORECAST_HORIZON_MINUTES, TARGET_FLARE_CLASSES
from app.services.ml.features import compute_features

logger = logging.getLogger(__name__)


class DatasetBuilder:
    def __init__(self) -> None:
        self.dataset_dir = "artifacts"
        self.parquet_path = os.path.join(self.dataset_dir, "feature_dataset.parquet")
        self.columns_path = os.path.join(self.dataset_dir, "feature_columns.json")

    async def _fetch_data_from_db(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Fetch all GOESXRS telemetry and FlareEvent logs from TimescaleDB."""
        logger.info("Fetching GOES telemetry and flare events from database...")
        
        async with async_session_maker() as session:
            # Fetch GOES XRS telemetry using column selection (avoids ORM overhead)
            goes_stmt = select(
                GOESXRS.timestamp,
                GOESXRS.short_flux,
                GOESXRS.long_flux,
                GOESXRS.satellite,
                GOESXRS.quality_flag,
                GOESXRS.source
            ).order_by(GOESXRS.timestamp.asc())
            goes_result = await session.execute(goes_stmt)
            goes_rows = goes_result.all()
            
            goes_df = pd.DataFrame(
                goes_rows,
                columns=["timestamp", "short_flux", "long_flux", "satellite", "quality_flag", "source"]
            )

            # Fetch Flare events using column selection
            flare_stmt = select(
                FlareEvent.event_id,
                FlareEvent.start_time,
                FlareEvent.peak_time,
                FlareEvent.end_time,
                FlareEvent.flare_class,
                FlareEvent.region_number,
                FlareEvent.source
            ).order_by(FlareEvent.start_time.asc())
            flare_result = await session.execute(flare_stmt)
            flare_rows = flare_result.all()
            
            flares_df = pd.DataFrame(
                flare_rows,
                columns=["event_id", "start_time", "peak_time", "end_time", "flare_class", "region_number", "source"]
            )

        return goes_df, flares_df

    async def build_and_export_dataset(self) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
        """
        Build the physics-aware feature matrix and targets, export to artifacts,
        and return (X, y_binary, y_class).
        """
        goes_df, flares_df = await self._fetch_data_from_db()

        if goes_df.empty:
            raise ValueError("No telemetry data found in the database. Cannot build dataset.")

        # 1. Convert timestamp to datetime and sort
        goes_df["timestamp"] = pd.to_datetime(goes_df["timestamp"])
        goes_df = goes_df.sort_values(by="timestamp").drop_duplicates(subset=["timestamp"])
        
        # 2. Reindex telemetry to a regular 1-minute grid to ensure rolling operations are correct
        goes_df = goes_df.set_index("timestamp")
        goes_df = goes_df.asfreq("1Min")
        
        # Forward-fill telemetry (cap at 10 minutes to avoid long gap interpolations)
        goes_df["short_flux"] = goes_df["short_flux"].ffill(limit=10)
        goes_df["long_flux"] = goes_df["long_flux"].ffill(limit=10)
        goes_df["satellite"] = goes_df["satellite"].ffill(limit=10)
        goes_df["quality_flag"] = goes_df["quality_flag"].fillna(0).astype(int)
        goes_df["source"] = goes_df["source"].ffill(limit=10)
        
        goes_df = goes_df.reset_index()

        # 3. Target Engineering (Lookahead Window)
        goes_df_stamps = goes_df["timestamp"]

        # A. Target Binary (matches configured positive target classes, e.g. ["C", "M", "X"] or ["M", "X"])
        # Check first character of flare class
        binary_flares = flares_df[flares_df["flare_class"].str[0].isin(TARGET_FLARE_CLASSES)]
        binary_flare_times = pd.to_datetime(binary_flares["start_time"]).dt.floor("Min")
        
        binary_indicator = pd.Series(0, index=goes_df.index)
        binary_indices = goes_df_stamps[goes_df_stamps.isin(binary_flare_times)].index
        binary_indicator.loc[binary_indices] = 1

        target_binary = (
            binary_indicator.shift(-1)
            .iloc[::-1]
            .rolling(window=FORECAST_HORIZON_MINUTES, min_periods=1)
            .max()
            .iloc[::-1]
            .fillna(0)
            .astype(int)
        )

        # B. Target Multiclass (strictly 0 = None, 1 = M-class, 2 = X-class)
        m_flares = flares_df[flares_df["flare_class"].str.startswith("M", na=False)]
        x_flares = flares_df[flares_df["flare_class"].str.startswith("X", na=False)]
        m_flare_times = pd.to_datetime(m_flares["start_time"]).dt.floor("Min")
        x_flare_times = pd.to_datetime(x_flares["start_time"]).dt.floor("Min")

        m_indicator = pd.Series(0, index=goes_df.index)
        x_indicator = pd.Series(0, index=goes_df.index)
        m_indicator.loc[goes_df_stamps[goes_df_stamps.isin(m_flare_times)].index] = 1
        x_indicator.loc[goes_df_stamps[goes_df_stamps.isin(x_flare_times)].index] = 2

        class_indicator = pd.concat([m_indicator, x_indicator], axis=1).max(axis=1)

        target_class = (
            class_indicator.shift(-1)
            .iloc[::-1]
            .rolling(window=FORECAST_HORIZON_MINUTES, min_periods=1)
            .max()
            .iloc[::-1]
            .fillna(0)
            .astype(int)
        )

        goes_df["target_6hr_binary"] = target_binary
        goes_df["target_6hr_class"] = target_class

        # 4. Generate features using the features module
        # Pass the configured target flare timestamps to calculate minutes_since_last_flare
        df_features = compute_features(goes_df, flare_times=list(binary_flare_times))


        # 5. Clean up NaNs created by rolling windows/differencing
        # We must drop rows with NaN values in the feature matrix prior to training.
        # Save columns before drop to isolate feature names
        non_feature_cols = ["timestamp", "satellite", "quality_flag", "source", "target_6hr_binary", "target_6hr_class"]
        feature_cols = [col for col in df_features.columns if col not in non_feature_cols]

        df_cleaned = df_features.dropna(subset=feature_cols).copy()
        
        logger.info(f"Generated dataset contains {len(df_cleaned)} valid rows.")

        # 6. Save Dataset to Parquet and JSON files for future sprints (RF, XGBoost, PatchTST)
        os.makedirs(self.dataset_dir, exist_ok=True)
        
        logger.info(f"Saving dataset parquet to {self.parquet_path}...")
        df_cleaned.to_parquet(self.parquet_path, engine="pyarrow", index=False)
        
        logger.info(f"Saving feature column names to {self.columns_path}...")
        with open(self.columns_path, "w", encoding="utf-8") as f:
            json.dump(feature_cols, f, indent=2)

        # Isolate X and y matrices with timestamp as index
        df_indexed = df_cleaned.set_index("timestamp")
        X = df_indexed[feature_cols]
        y_binary = df_indexed["target_6hr_binary"]
        y_class = df_indexed["target_6hr_class"]

        return X, y_binary, y_class

