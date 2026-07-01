import gzip
import json
import logging
import os
from datetime import datetime
import httpx
import pandas as pd
import pandera as pa

logger = logging.getLogger(__name__)

# Pandera schema for wide GOES flux telemetry validation
goes_schema = pa.DataFrameSchema(
    {
        "timestamp": pa.Column(pa.DateTime, nullable=False),
        "satellite": pa.Column(pa.Int, nullable=False),
        "short_flux": pa.Column(pa.Float, nullable=True),  # 0.05-0.4nm
        "long_flux": pa.Column(pa.Float, nullable=True),  # 0.1-0.8nm
        "quality_flag": pa.Column(pa.Int, nullable=False),
        "source": pa.Column(pa.String, nullable=False),
    }
)


class GOESClient:
    def __init__(self) -> None:
        self.url = (
            "https://services.swpc.noaa.gov/json/goes/primary/xrays-7-day.json"
        )
        self.archive_dir = os.path.join("raw-data", "goes")

    async def fetch_and_validate(self) -> pd.DataFrame:
        """Fetch primary 7-day GOES XRS data, archive raw payload, pivot to wide format, and validate."""
        logger.info(f"Fetching GOES telemetry from {self.url}...")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.url)
            response.raise_for_status()
            raw_data = response.json()

        # Archive raw JSON payload before any processing
        self._archive_raw_payload(raw_data)

        if not raw_data:
            logger.warning("No GOES telemetry data found in response.")
            return pd.DataFrame(
                columns=[
                    "timestamp",
                    "satellite",
                    "short_flux",
                    "long_flux",
                    "quality_flag",
                    "source",
                ]
            )

        # Reconstruct structured dataframe from long format
        df_raw = pd.DataFrame(raw_data)
        df_raw["time_tag"] = pd.to_datetime(df_raw["time_tag"]).dt.tz_localize(None)

        # Pivot to separate short/long channels onto columns per timestamp & satellite
        df_pivoted = df_raw.pivot_table(
            index=["time_tag", "satellite"],
            columns="energy",
            values="flux",
            aggfunc="first",
        ).reset_index()

        # Map column names
        df_pivoted.rename(
            columns={
                "time_tag": "timestamp",
                "0.05-0.4nm": "short_flux",
                "0.1-0.8nm": "long_flux",
            },
            inplace=True,
        )

        # Handle edge cases where one passband might be completely missing
        if "short_flux" not in df_pivoted.columns:
            df_pivoted["short_flux"] = None
        if "long_flux" not in df_pivoted.columns:
            df_pivoted["long_flux"] = None

        # Add default metadata columns
        df_pivoted["source"] = "NOAA_GOES_PRIMARY"
        df_pivoted["quality_flag"] = 0

        # Enforce columns order
        columns_order = [
            "timestamp",
            "satellite",
            "short_flux",
            "long_flux",
            "quality_flag",
            "source",
        ]
        df_pivoted = df_pivoted[columns_order]

        # Deduplicate by timestamp to prevent primary key conflict errors
        df_pivoted = df_pivoted.sort_values(by=["timestamp", "satellite"], ascending=[True, True])
        df_pivoted = df_pivoted.drop_duplicates(subset=["timestamp"], keep="last")

        # Validate structured dataset
        logger.info("Validating pivoted GOES telemetry with Pandera...")
        validated_df = goes_schema.validate(df_pivoted)
        return validated_df


    def _archive_raw_payload(self, data: list) -> None:
        """Compress raw JSON response and store it under raw-data/goes/."""
        os.makedirs(self.archive_dir, exist_ok=True)
        timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"goes_raw_{timestamp_str}.json.gz"
        filepath = os.path.join(self.archive_dir, filename)

        logger.info(f"Archiving raw GOES payload to {filepath}...")
        try:
            with gzip.open(filepath, "wt", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"Failed to archive raw GOES payload: {e}")
