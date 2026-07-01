import gzip
import json
import logging
import os
import re
from datetime import datetime
import httpx
import pandas as pd
import pandera as pa

logger = logging.getLogger(__name__)

# Pandera schema for FlareEvent models validation
flare_schema = pa.DataFrameSchema(
    {
        "event_id": pa.Column(pa.String, nullable=False),
        "start_time": pa.Column(pa.DateTime, nullable=False),
        "peak_time": pa.Column(pa.DateTime, nullable=True),
        "end_time": pa.Column(pa.DateTime, nullable=True),
        "flare_class": pa.Column(
            pa.String,
            pa.Check.str_matches(r"^[ABCMX]\d+(\.\d+)?$"),
            nullable=False,
        ),
        "region_number": pa.Column(pa.Object, nullable=True),  # mixed type, clean to int/None
        "source": pa.Column(pa.String, nullable=False),
    }
)


class FlareClient:
    def __init__(self) -> None:
        self.url = "https://services.swpc.noaa.gov/json/edited_events.json"
        self.archive_dir = os.path.join("raw-data", "flares")

    async def fetch_and_validate(self) -> pd.DataFrame:
        """Fetch edited events, archive raw payload, extract X-ray flares, and validate with Pandera."""
        logger.info(f"Fetching solar events from {self.url}...")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.url)
            response.raise_for_status()
            raw_data = response.json()

        # Archive raw JSON payload before any processing
        self._archive_raw_payload(raw_data)

        if not raw_data:
            logger.warning("No solar events found in response.")
            return pd.DataFrame(
                columns=[
                    "event_id",
                    "start_time",
                    "peak_time",
                    "end_time",
                    "flare_class",
                    "region_number",
                    "source",
                ]
            )

        # Filter for X-ray flares (XRA)
        xra_events = [
            event for event in raw_data if event.get("type") == "XRA"
        ]

        if not xra_events:
            logger.info("No X-ray flare (XRA) events found in current feed.")
            return pd.DataFrame(
                columns=[
                    "event_id",
                    "start_time",
                    "peak_time",
                    "end_time",
                    "flare_class",
                    "region_number",
                    "source",
                ]
            )

        # Create dataframe
        df = pd.DataFrame(xra_events)

        # Map times
        df["start_time"] = pd.to_datetime(df["begin_datetime"]).dt.tz_localize(None)
        df["peak_time"] = pd.to_datetime(df["max_datetime"]).dt.tz_localize(None)
        df["end_time"] = pd.to_datetime(df["end_datetime"]).dt.tz_localize(None)

        # Map fields
        df.rename(
            columns={
                "particulars1": "flare_class",
                "region": "region_number",
                "observatory": "source",
            },
            inplace=True,
        )

        # Clean region_number (convert to numeric, replace NaN/None with None)
        df["region_number"] = pd.to_numeric(
            df["region_number"], errors="coerce"
        )
        df["region_number"] = df["region_number"].astype(object)
        df.loc[df["region_number"].isna(), "region_number"] = None

        # Build clean event ID
        df["event_id"] = df.apply(
            lambda row: f"XRA_{row['source']}_{row['begin_datetime']}".replace(
                " ", "_"
            ),
            axis=1,
        )

        # Retain only required columns
        columns_order = [
            "event_id",
            "start_time",
            "peak_time",
            "end_time",
            "flare_class",
            "region_number",
            "source",
        ]
        df_mapped = df[columns_order].copy()

        # Clean flare class: ignore non-conforming entries (like SF/optical flare classes that slipped into XRA)
        class_regex = re.compile(r"^[ABCMX]\d+(\.\d+)?$")
        matched_mask = df_mapped["flare_class"].apply(
            lambda val: bool(class_regex.match(str(val)))
            if pd.notna(val)
            else False
        )

        ignored_count = len(df_mapped) - matched_mask.sum()
        if ignored_count > 0:
            logger.info(
                f"Filtering out {ignored_count} events with non-standard flare classes."
            )
            df_mapped = df_mapped[matched_mask].copy()

        if df_mapped.empty:
            logger.warning("No valid X-ray flares remaining after filtering.")
            return df_mapped

        # Deduplicate by event_id to prevent ON CONFLICT DO UPDATE command error.
        # Sort by event_id and flare_class alphabetically ascending, so that the higher magnitude
        # flare class (A < B < C < M < X) comes last and is kept.
        df_mapped = df_mapped.sort_values(by=["event_id", "flare_class"], ascending=[True, True])
        df_mapped = df_mapped.drop_duplicates(subset=["event_id"], keep="last")

        # Validate structured dataset
        logger.info("Validating FlareEvents with Pandera...")
        validated_df = flare_schema.validate(df_mapped)
        return validated_df


    def _archive_raw_payload(self, data: list) -> None:
        """Compress raw JSON response and store it under raw-data/flares/."""
        os.makedirs(self.archive_dir, exist_ok=True)
        timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"flares_raw_{timestamp_str}.json.gz"
        filepath = os.path.join(self.archive_dir, filename)

        logger.info(f"Archiving raw Flares payload to {filepath}...")
        try:
            with gzip.open(filepath, "wt", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"Failed to archive raw Flares payload: {e}")
