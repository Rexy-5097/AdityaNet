import os
import re
import asyncio
import logging
import tempfile
import httpx
import pandas as pd
import numpy as np
import netCDF4
from datetime import date, datetime, timedelta
from sqlalchemy.dialects.postgresql import insert
from app.db.session import async_session_maker
from app.models.goes import GOESXRS
from app.services.backfill.checkpoint_manager import CheckpointManager

logger = logging.getLogger(__name__)


class GOESBackfillService:
    def __init__(self) -> None:
        self.raw_dir = os.path.join("artifacts", "raw")
        os.makedirs(self.raw_dir, exist_ok=True)

    def _get_ncei_url(self, satellite: str, year: int, month: int) -> str:
        """Construct the NCEI directory URL for a given satellite, year, and month."""
        if satellite in ["goes16", "goes18"]:
            return f"https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/{satellite}/l2/data/xrsf-l2-avg1m_science/{year}/{month:02d}/"
        else:
            return f"https://www.ncei.noaa.gov/data/goes-space-environment-monitor/access/science/xrs/{satellite}/xrsf-l2-avg1m_science/{year}/{month:02d}/"

    async def discover_nc_files(self, year: int, month: int) -> list[dict]:
        """Scrape NCEI directory listings to find available NetCDF files, combining data across satellites preferring higher priority ones."""
        # Preferred satellites order for years
        # 2023+ -> goes18, goes16, goes15, goes14, goes13
        # 2017-2022 -> goes16, goes15, goes14, goes13
        # 2010-2016 -> goes15, goes14, goes13
        if year >= 2023:
            satellites = ["goes18", "goes16", "goes15", "goes14", "goes13"]
        elif year >= 2017:
            satellites = ["goes16", "goes15", "goes14", "goes13"]
        else:
            satellites = ["goes15", "goes14", "goes13"]

        discovered_by_date = {}

        async with httpx.AsyncClient(timeout=15.0) as client:
            # Loop from lowest priority to highest priority so that higher priority satellite overrides lower priority
            for sat in reversed(satellites):
                url = self._get_ncei_url(sat, year, month)
                logger.info(f"Attempting file discovery at NCEI: {url}")
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        # Find all netcdf links in the directory listing
                        filenames = re.findall(r'href="([^"]+\.nc)"', response.text)
                        if filenames:
                            count = 0
                            for fname in filenames:
                                # Match date pattern dYYYYMMDD
                                match = re.search(r"_d(\d{8})_", fname)
                                if match:
                                    file_date = datetime.strptime(match.group(1), "%Y%m%d").date()
                                    discovered_by_date[file_date] = {
                                        "date": file_date,
                                        "filename": fname,
                                        "url": url + fname,
                                        "satellite": sat
                                    }
                                    count += 1
                            logger.info(f"Discovered {count} files for {sat} in {year}-{month:02d}")
                except Exception as e:
                    logger.warning(f"Failed discovering files for {sat} in {year}-{month:02d}: {e}")

        discovered = list(discovered_by_date.values())
        if discovered:
            logger.info(f"Combined total of {len(discovered)} files discovered for {year}-{month:02d} across satellites.")
        else:
            logger.warning(f"No NCEI files discovered for {year}-{month:02d}")
        return discovered

    async def fetch_operational_fallback(self, target_date: date) -> list[dict]:
        """Fallback to SWPC operational JSON feed if within the last 7 days."""
        today = date.today()
        if today - target_date > timedelta(days=7):
            logger.warning(f"Operational fallback unavailable: target date {target_date} is older than 7 days.")
            return []

        url = "https://services.swpc.noaa.gov/json/goes/primary/xrays-7-day.json"
        logger.info(f"Fetching operational fallback data from SWPC: {url} for date {target_date}")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                if response.status_code != 200:
                    return []
                raw_data = response.json()

            if not raw_data:
                return []

            # Pivot and filter for target date
            df_raw = pd.DataFrame(raw_data)
            df_raw["time_tag"] = pd.to_datetime(df_raw["time_tag"]).dt.tz_localize(None)
            df_raw = df_raw[df_raw["time_tag"].dt.date == target_date]

            if df_raw.empty:
                return []

            df_pivoted = df_raw.pivot_table(
                index=["time_tag", "satellite"],
                columns="energy",
                values="flux",
                aggfunc="first",
            ).reset_index()

            df_pivoted.rename(
                columns={
                    "time_tag": "timestamp",
                    "0.05-0.4nm": "short_flux",
                    "0.1-0.8nm": "long_flux",
                },
                inplace=True,
            )

            # Enforce columns
            if "short_flux" not in df_pivoted.columns:
                df_pivoted["short_flux"] = None
            if "long_flux" not in df_pivoted.columns:
                df_pivoted["long_flux"] = None

            records = []
            for _, row in df_pivoted.iterrows():
                # Convert np/pd types to native python types
                sh_flux = float(row["short_flux"]) if pd.notna(row["short_flux"]) else None
                ln_flux = float(row["long_flux"]) if pd.notna(row["long_flux"]) else None
                records.append({
                    "timestamp": row["timestamp"].to_pydatetime(),
                    "satellite": int(row["satellite"]),
                    "short_flux": sh_flux,
                    "long_flux": ln_flux,
                    "quality_flag": 0,
                    "source": "NOAA_GOES_OPERATIONAL",
                    "source_file": "operational_fallback",
                    "processing_version": "N/A",
                })
            return records
        except Exception as e:
            logger.error(f"Failed to fetch operational fallback for {target_date}: {e}")
            return []

    async def download_and_parse_nc(self, url: str, client: httpx.AsyncClient | None = None) -> list[dict]:
        """Download a NetCDF file and parse variables into list of records."""
        logger.info(f"Downloading file: {url}")
        
        max_retries = 3
        content = None
        for attempt in range(max_retries):
            try:
                if client is not None:
                    response = await client.get(url)
                else:
                    async with httpx.AsyncClient(timeout=60.0) as local_client:
                        response = await local_client.get(url)
                response.raise_for_status()
                content = response.content
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to download {url} after {max_retries} attempts: {e}")
                    raise e
                sleep_time = 2 * (attempt + 1)
                logger.warning(f"Failed to download {url} (attempt {attempt+1}/{max_retries}): {e}. Retrying in {sleep_time}s...")
                await asyncio.sleep(sleep_time)

        # Create temporary file to read NetCDF structure
        with tempfile.NamedTemporaryFile(delete=False, suffix=".nc") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            ds = netCDF4.Dataset(tmp_path)
            
            # Determine satellite number from global attribute or URL filename
            filename = os.path.basename(url)
            match_sat = re.search(r"_g(\d+)_", filename)
            satellite_num = int(match_sat.group(1)) if match_sat else 16

            time_var = ds.variables["time"]
            times = netCDF4.num2date(
                time_var[:],
                units=time_var.units,
                calendar=getattr(time_var, "calendar", "standard"),
            )

            xrsa_flux = ds.variables["xrsa_flux"][:]
            xrsb_flux = ds.variables["xrsb_flux"][:]
            
            # Use xrsb_flag or default to xrsa_flag/0
            if "xrsb_flag" in ds.variables:
                quality_flags = ds.variables["xrsb_flag"][:]
            elif "xrsa_flag" in ds.variables:
                quality_flags = ds.variables["xrsa_flag"][:]
            else:
                quality_flags = np.zeros(len(times), dtype=int)

            records = []
            source_name = f"NOAA_GOES_{satellite_num}_L2"

            for idx in range(len(times)):
                t = times[idx]
                ts = datetime(t.year, t.month, t.day, t.hour, t.minute, t.second)
                
                # Check for masked array or nan values
                sa_flux = xrsa_flux[idx]
                sb_flux = xrsb_flux[idx]
                q_flag = int(quality_flags[idx])

                def clean_val(v):
                    if v is None or isinstance(v, np.ma.core.MaskedConstant) or np.isnan(v):
                        return None
                    return float(v)

                records.append({
                    "timestamp": ts,
                    "satellite": satellite_num,
                    "short_flux": clean_val(sa_flux),
                    "long_flux": clean_val(sb_flux),
                    "quality_flag": q_flag,
                    "source": source_name,
                })
            ds.close()
            return records
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    async def upsert_records(self, records: list[dict]) -> int:
        """Bulk upsert GOES records using ON CONFLICT DO UPDATE."""
        if not records:
            return 0
        
        # Deduplicate records by timestamp in memory to prevent CardinalityViolationError
        seen = {}
        for r in records:
            seen[r["timestamp"]] = r
        deduped = list(seen.values())

        chunk_size = 2000
        total_inserted = 0

        for i in range(0, len(deduped), chunk_size):
            chunk = deduped[i:i + chunk_size]
            async with async_session_maker() as session:
                insert_stmt = insert(GOESXRS).values(chunk)
                update_cols = {
                    col.name: col
                    for col in insert_stmt.excluded
                    if col.name not in ["timestamp", "created_at"]
                }
                upsert_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=["timestamp"], set_=update_cols
                )
                result = await session.execute(upsert_stmt)
                await session.commit()
            total_inserted += len(chunk)

        return total_inserted

    async def export_year_parquet(self, year: int) -> None:
        """Export GOES telemetry for a given year to a Parquet file."""
        logger.info(f"Exporting GOES telemetry for year {year} to Parquet...")
        parquet_path = os.path.join(self.raw_dir, f"goes_{year}.parquet")
        
        start_dt = datetime(year, 1, 1, 0, 0, 0)
        end_dt = datetime(year, 12, 31, 23, 59, 59)

        async with async_session_maker() as session:
            # We select columns to keep Parquet files compact
            from sqlmodel import select
            stmt = (
                select(GOESXRS)
                .where(GOESXRS.timestamp >= start_dt, GOESXRS.timestamp <= end_dt)
                .order_by(GOESXRS.timestamp.asc())
            )
            result = await session.execute(stmt)
            records = result.scalars().all()

        if not records:
            logger.warning(f"No records found in database for year {year} to export to Parquet.")
            return

        df = pd.DataFrame([r.model_dump() for r in records])
        # Convert created_at to string or drop it to avoid tz issue if necessary
        if "created_at" in df.columns:
            df["created_at"] = df["created_at"].dt.strftime("%Y-%m-%d %H:%M:%S")

        df.to_parquet(parquet_path, index=False)
        logger.info(f"Exported {len(df)} records to {parquet_path}")

    async def get_completed_dates(self, start_date: date, end_date: date) -> set[date]:
        """Fetch all dates within the range that already have at least 1400 records in the database."""
        logger.info(f"Checking database for already completed dates between {start_date} and {end_date}...")
        async with async_session_maker() as session:
            from sqlalchemy import text
            stmt = text(
                "SELECT timestamp::date as d, count(*) as count "
                "FROM goesxrs "
                "WHERE timestamp >= :start AND timestamp <= :end "
                "GROUP BY d "
                "HAVING count(*) >= 1400;"
            )
            start_dt = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
            end_dt = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
            result = await session.execute(stmt, {"start": start_dt, "end": end_dt})
            rows = result.fetchall()
            completed = {row[0] for row in rows}
            logger.info(f"Found {len(completed)} dates already completed in the database.")
            return completed

    async def backfill(self, start_date: date, end_date: date) -> None:
        """Execute the backfill pipeline in multi-month parallel batches, respecting checkpoints."""
        logger.info(f"Commencing GOES telemetry backfill from {start_date} to {end_date}...")
        
        # Concurrency limit semaphore
        sem = asyncio.Semaphore(15)

        async with httpx.AsyncClient(timeout=60.0) as client:
            async def process_single_file(f) -> tuple[date, bool]:
                async with sem:
                    f_date = f["date"]
                    try:
                        records = await self.download_and_parse_nc(f["url"], client=client)
                        if records:
                            filename = os.path.basename(f["url"])
                            match_ver = re.search(r"_v(\d+-\d+-\d+)\.nc", filename)
                            processing_version = match_ver.group(1) if match_ver else None
                            for r in records:
                                r["source_file"] = filename
                                r["processing_version"] = processing_version

                            inserted = await self.upsert_records(records)
                            logger.info(f"Successfully backfilled GOES {f_date}: {inserted} records.")
                        return f_date, True
                    except Exception as e:
                        logger.error(f"Error backfilling GOES for date {f_date}: {e}")
                        # Attempt operational fallback if within last 7 days
                        try:
                            fallback_records = await self.fetch_operational_fallback(f_date)
                            if fallback_records:
                                inserted = await self.upsert_records(fallback_records)
                                logger.info(f"Fallback successful for GOES {f_date}: {inserted} records.")
                                return f_date, True
                        except Exception as fe:
                            logger.error(f"Operational fallback also failed for {f_date}: {fe}")
                        return f_date, False

            current_date = start_date
            while current_date <= end_date:
                # We want to process a batch of months (e.g. 6 months)
                batch_months = []
                temp_date = current_date
                # Collect up to 6 months
                while temp_date <= end_date and len(batch_months) < 6:
                    y, m = temp_date.year, temp_date.month
                    m_start = date(y, m, 1)
                    next_m = m_start + timedelta(days=32)
                    m_end = date(next_m.year, next_m.month, 1) - timedelta(days=1)
                    if m_end > end_date:
                        m_end = end_date
                    batch_months.append((y, m, m_start, m_end))
                    temp_date = m_end + timedelta(days=1)

                # Get checkpoint
                checkpoint_date = await CheckpointManager.get_checkpoint("GOES_BACKFILL")
                
                # Check checkpoints and discover files for all months in the batch in parallel
                discover_tasks = []
                valid_months = []
                for y, m, m_start, m_end in batch_months:
                    if checkpoint_date and checkpoint_date >= m_end:
                        logger.info(f"Month {y}-{m:02d} already processed up to checkpoint {checkpoint_date}. Skipping.")
                        continue
                    valid_months.append((y, m, m_start, m_end))
                    discover_tasks.append(self.discover_nc_files(y, m))
                
                if not valid_months:
                    current_date = temp_date
                    continue
                
                discovered_lists = await asyncio.gather(*discover_tasks)
                
                # Get already completed dates in this batch to avoid redownloading
                completed_dates = await self.get_completed_dates(current_date, temp_date)

                # Merge all files to process
                files_to_process = []
                for (y, m, m_start, m_end), files in zip(valid_months, discovered_lists):
                    for f in files:
                        f_date = f["date"]
                        if f_date < current_date or f_date > m_end:
                            continue
                        # Skip if already completed in database
                        if f_date in completed_dates:
                            continue
                        if checkpoint_date and f_date <= checkpoint_date:
                            continue
                        files_to_process.append(f)

                # Sort files chronologically
                files_to_process.sort(key=lambda x: x["date"])

                processed_any = False
                results = []
                if files_to_process:
                    tasks = [process_single_file(f) for f in files_to_process]
                    results = await asyncio.gather(*tasks)
                    
                    success_dates = {d for d, success in results if success}
                    failed_dates = {d for d, success in results if not success}
                    
                    if failed_dates:
                        earliest_fail = min(failed_dates)
                        latest_consec = checkpoint_date
                        for f in files_to_process:
                            f_date = f["date"]
                            if f_date < earliest_fail:
                                if f_date in success_dates:
                                    latest_consec = f_date
                                    processed_any = True
                            else:
                                break
                        if latest_consec and (checkpoint_date is None or latest_consec > checkpoint_date):
                            await CheckpointManager.update_checkpoint("GOES_BACKFILL", latest_consec, "in_progress")
                        raise RuntimeError(f"Failed to process files for dates: {sorted(failed_dates)}")
                    else:
                        latest_consec = temp_date - timedelta(days=1)
                        processed_any = True
                        if latest_consec and (checkpoint_date is None or latest_consec > checkpoint_date):
                            await CheckpointManager.update_checkpoint("GOES_BACKFILL", latest_consec, "in_progress")
                else:
                    # All files in this batch were already completed!
                    latest_consec = temp_date - timedelta(days=1)
                    processed_any = True
                    if latest_consec and (checkpoint_date is None or latest_consec > checkpoint_date):
                        await CheckpointManager.update_checkpoint("GOES_BACKFILL", latest_consec, "in_progress")

                # If no files found on NCEI, check if they are recent and we can use operational fallback
                if not files_to_process and not completed_dates:
                    for y, m, m_start, m_end in valid_months:
                        chk_date = checkpoint_date if checkpoint_date and checkpoint_date >= m_start else m_start - timedelta(days=1)
                        day_to_check = chk_date + timedelta(days=1)
                        while day_to_check <= m_end:
                            try:
                                fallback_records = await self.fetch_operational_fallback(day_to_check)
                                if fallback_records:
                                    inserted = await self.upsert_records(fallback_records)
                                    logger.info(f"Operational fallback backfilled GOES {day_to_check}: {inserted} records.")
                                    await CheckpointManager.update_checkpoint("GOES_BACKFILL", day_to_check, "in_progress")
                                    processed_any = True
                                day_to_check += timedelta(days=1)
                            except Exception as e:
                                logger.error(f"Failed fallback backfill for {day_to_check}: {e}")
                                break

                # Export parquets for any years in this batch
                if processed_any:
                    years_to_export = set()
                    if results:
                        years_to_export.update({d.year for d, success in results if success})
                    for y, m, m_start, m_end in valid_months:
                        years_to_export.add(y)
                    for y in sorted(years_to_export):
                        await self.export_year_parquet(y)

                # Advance current_date to first day of next month after this batch
                current_date = temp_date

            # Final checkpoint update
            final_checkpoint = await CheckpointManager.get_checkpoint("GOES_BACKFILL")
            if final_checkpoint and final_checkpoint >= end_date:
                await CheckpointManager.update_checkpoint("GOES_BACKFILL", end_date, "completed")
                # Make sure the last year is exported
                await self.export_year_parquet(end_date.year)
                logger.info("GOES backfill pipeline completed successfully.")
