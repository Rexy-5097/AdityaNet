import os
import sys
import asyncio
import logging
import pandas as pd
from sqlalchemy import text

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import engine
from app.services.ml.dataset_builder import DatasetBuilder

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def dump_raw_tables(research_dir: str):
    logger.info("Exporting full raw database telemetry (goesxrs) to Parquet...")
    async with engine.connect() as conn:
        goes_result = await conn.execute(text(
            "SELECT timestamp, satellite, short_flux, long_flux, source, quality_flag, source_file, processing_version, created_at "
            "FROM goesxrs ORDER BY timestamp ASC;"
        ))
        goes_rows = goes_result.fetchall()
        goes_df = pd.DataFrame(goes_rows, columns=goes_result.keys())
        
        # Convert created_at to string to avoid timezone/parquet issues
        if "created_at" in goes_df.columns:
            goes_df["created_at"] = goes_df["created_at"].dt.strftime("%Y-%m-%d %H:%M:%S")
        
        os.makedirs(research_dir, exist_ok=True)
        goes_parquet_path = os.path.join(research_dir, "goes_full.parquet")
        goes_df.to_parquet(goes_parquet_path, engine="pyarrow", index=False)
        logger.info(f"Exported {len(goes_df)} raw goesxrs records to {goes_parquet_path}")

    logger.info("Exporting full raw database flare events (flareevent) to Parquet...")
    async with engine.connect() as conn:
        flare_result = await conn.execute(text(
            "SELECT event_id, start_time, peak_time, end_time, flare_class, region_number, location, importance, source, created_at "
            "FROM flareevent ORDER BY start_time ASC;"
        ))
        flare_rows = flare_result.fetchall()
        flare_df = pd.DataFrame(flare_rows, columns=flare_result.keys())
        
        if "created_at" in flare_df.columns:
            flare_df["created_at"] = flare_df["created_at"].dt.strftime("%Y-%m-%d %H:%M:%S")
            
        flares_parquet_path = os.path.join(research_dir, "flares_full.parquet")
        flare_df.to_parquet(flares_parquet_path, engine="pyarrow", index=False)
        logger.info(f"Exported {len(flare_df)} raw flareevent records to {flares_parquet_path}")


async def build_and_partition_dataset(research_dir: str):
    logger.info("Building the canonical feature dataset...")
    builder = DatasetBuilder()
    
    # This automatically computes features, targets, and saves feature_dataset.parquet and feature_columns.json
    X, y_binary, y_class = await builder.build_and_export_dataset()
    
    # Read the generated feature dataset to partition it
    feature_dataset_path = builder.parquet_path
    logger.info(f"Reading generated feature dataset from {feature_dataset_path}...")
    df = pd.read_parquet(feature_dataset_path)
    
    # Ensure timestamp is datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    logger.info("Partitioning dataset by time splits...")
    # Train: 2010-01-01 to 2019-12-31 (Solar Cycle 24)
    # Validation: 2020-01-01 to 2022-12-31 (Solar Cycle 25 start)
    # Test: 2023-01-01 to Present (Solar Cycle 25 peak)
    
    train_df = df[(df["timestamp"] >= "2010-01-01") & (df["timestamp"] <= "2019-12-31 23:59:59")]
    val_df = df[(df["timestamp"] >= "2020-01-01") & (df["timestamp"] <= "2022-12-31 23:59:59")]
    test_df = df[(df["timestamp"] >= "2023-01-01")]
    
    # Export splits to artifacts/research/
    train_path = os.path.join(research_dir, "train.parquet")
    val_path = os.path.join(research_dir, "validation.parquet")
    test_path = os.path.join(research_dir, "test.parquet")
    
    train_df.to_parquet(train_path, index=False)
    val_df.to_parquet(val_path, index=False)
    test_df.to_parquet(test_path, index=False)
    
    logger.info(f"Successfully exported splits:")
    logger.info(f"  Train:      {len(train_df)} records ({train_path})")
    logger.info(f"  Validation: {len(val_df)} records ({val_path})")
    logger.info(f"  Test:       {len(test_df)} records ({test_path})")


async def main():
    print("==================================================")
    print("SuryaNet: Research-Grade Dataset Builder")
    print("==================================================")
    
    research_dir = os.path.join("artifacts", "research")
    os.makedirs(research_dir, exist_ok=True)
    
    try:
        # 1. Export goes_full.parquet and flares_full.parquet
        await dump_raw_tables(research_dir)
        
        # 2. Build and partition feature dataset
        await build_and_partition_dataset(research_dir)
        
        print("\nDataset Construction and Partitioning Successful!")
    except Exception as e:
        logger.exception(f"Dataset building failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
