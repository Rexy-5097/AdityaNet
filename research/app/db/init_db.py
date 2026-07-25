import logging
from sqlalchemy import text
from sqlmodel import SQLModel
from app.db.session import engine

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """Initialize database schemas, ensure tables exist, and convert goesxrs to a hypertable."""
    logger.info("Initializing database schemas...")

    # 1. Ensure SQLModel tables exist (safe if already created via Alembic)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("Core database tables verified/created.")

    # Dynamically add location and importance columns to flareevent table if not present
    async with engine.connect() as conn:
        await conn.execute(
            text("ALTER TABLE flareevent ADD COLUMN IF NOT EXISTS location VARCHAR;")
        )
        await conn.execute(
            text("ALTER TABLE flareevent ADD COLUMN IF NOT EXISTS importance VARCHAR;")
        )
        await conn.execute(
            text("ALTER TABLE goesxrs ADD COLUMN IF NOT EXISTS source_file VARCHAR;")
        )
        await conn.execute(
            text("ALTER TABLE goesxrs ADD COLUMN IF NOT EXISTS processing_version VARCHAR;")
        )
        await conn.commit()
        logger.info("Checked/updated table columns.")

    # 2. Check and convert goesxrs to TimescaleDB hypertable
    logger.info("Checking TimescaleDB hypertable configuration for 'goesxrs'...")
    async with engine.connect() as conn:
        # Check if goesxrs is already registered as a hypertable
        check_query = text(
            "SELECT 1 FROM timescaledb_information.hypertables WHERE hypertable_name = 'goesxrs';"
        )
        result = await conn.execute(check_query)
        is_hypertable = result.scalar() is not None

        if not is_hypertable:
            logger.info("Converting 'goesxrs' table to a TimescaleDB hypertable...")
            # We must partition by the 'timestamp' column
            await conn.execute(
                text(
                    "SELECT create_hypertable('goesxrs', 'timestamp', if_not_exists => TRUE);"
                )
            )
            await conn.commit()
            logger.info("'goesxrs' successfully converted to TimescaleDB hypertable.")
        else:
            logger.info("'goesxrs' table is already configured as a hypertable.")

        # 3. Verify hypertable and log chunk/partitioning statistics
        verify_query = text(
            "SELECT num_chunks FROM timescaledb_information.hypertables WHERE hypertable_name = 'goesxrs';"
        )
        verify_result = await conn.execute(verify_query)
        row = verify_result.fetchone()
        if row is not None:
            logger.info(
                f"TimescaleDB hypertable verified successfully. Current chunks allocated: {row[0]}"
            )
        else:
            logger.error(
                "VERIFICATION FAILURE: 'goesxrs' is NOT listed as a TimescaleDB hypertable!"
            )

        # =====================================================================
        # CONTINUOUS AGGREGATES DESIGN (For Sprint 3 - Feature Engineering)
        # =====================================================================
        # To roll up GOES XRS telemetry data into regular intervals, we will define
        # TimescaleDB continuous aggregates. These will serve as clean down-sampled
        # time-series signals for ML training:
        #
        # 1. 5-Minute Rollups:
        #    CREATE MATERIALIZED VIEW goesxrs_rollups_5m
        #    WITH (timescaledb.continuous) AS
        #    SELECT
        #       time_bucket('5 minutes', timestamp) AS bucket,
        #       satellite,
        #       source,
        #       avg(short_flux) AS avg_short_flux,
        #       avg(long_flux) AS avg_long_flux,
        #       variance(long_flux) AS var_long_flux
        #    FROM goesxrs
        #    GROUP BY bucket, satellite, source;
        #
        # 2. 15-Minute / 1-Hour Rollups can be constructed similarly.
        # 3. Refresh Policies will be registered:
        #    SELECT add_continuous_aggregate_policy('goesxrs_rollups_5m',
        #       start_offset => INTERVAL '3 hours',
        #       end_offset => INTERVAL '5 minutes',
        #       schedule_interval => INTERVAL '5 minutes');
        # =====================================================================

if __name__ == "__main__":
    import asyncio
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    asyncio.run(init_db())
