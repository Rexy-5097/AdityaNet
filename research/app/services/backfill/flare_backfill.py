import os
import re
import io
import concurrent.futures
import logging
import ftplib
import pandas as pd
from datetime import date, datetime, timedelta
from sqlalchemy.dialects.postgresql import insert
from app.db.session import async_session_maker
from app.models.flare import FlareEvent
from app.services.backfill.checkpoint_manager import CheckpointManager

logger = logging.getLogger(__name__)


class SWPCEventFetcher:
    def __init__(self) -> None:
        self.ftp = None

    def connect(self) -> None:
        """Ensure FTP client is connected and in the correct directory."""
        if self.ftp is None:
            try:
                logger.info("Opening FTP connection to ftp.swpc.noaa.gov...")
                self.ftp = ftplib.FTP("ftp.swpc.noaa.gov")
                self.ftp.login()
                self.ftp.cwd("pub/indices/events")
            except Exception as e:
                logger.error(f"FTP connection failed: {e}")
                self.ftp = None
                raise e

    def disconnect(self) -> None:
        """Safely close the FTP connection."""
        if self.ftp is not None:
            try:
                self.ftp.quit()
            except Exception:
                pass
            self.ftp = None
            logger.info("FTP connection closed.")

    def fetch_file(self, filename: str) -> str | None:
        """Download text file contents from SWPC FTP server, reusing connection."""
        self.connect()
        buf = io.BytesIO()
        try:
            self.ftp.retrbinary(f"RETR {filename}", buf.write)
            return buf.getvalue().decode("utf-8", errors="ignore")
        except ftplib.error_perm as e:
            # Check for file not found error 550
            if "550" in str(e):
                logger.warning(f"File {filename} not found on FTP server.")
                return None
            raise e
        except Exception as e:
            logger.warning(f"FTP error during fetch of {filename}: {e}. Reconnecting...")
            self.disconnect()
            self.connect()
            buf = io.BytesIO()
            self.ftp.retrbinary(f"RETR {filename}", buf.write)
            return buf.getvalue().decode("utf-8", errors="ignore")


class FlareBackfillService:
    def __init__(self) -> None:
        self.fetcher = SWPCEventFetcher()
        self.raw_dir = os.path.join("artifacts", "raw")
        os.makedirs(self.raw_dir, exist_ok=True)

    def parse_time_str(
        self, time_str: str, base_date: date, start_time: datetime | None = None
    ) -> datetime | None:
        """Clean prefixes and convert HHMM time string to datetime, handling cross-day rollover."""
        if not time_str or time_str == "////" or "///" in time_str:
            return None
        
        # Strip letters (like B, U, A, E, etc.)
        cleaned = re.sub(r"[^0-9]", "", time_str)
        if len(cleaned) != 4:
            return None
        
        try:
            hours = int(cleaned[0:2])
            minutes = int(cleaned[2:4])
            if hours >= 24 or minutes >= 60:
                return None
            
            dt = datetime(base_date.year, base_date.month, base_date.day, hours, minutes)
            
            # If peak/end time is numerically earlier than start time, it rolled over to the next day
            if start_time is not None and dt < start_time:
                dt += timedelta(days=1)
            
            return dt
        except Exception:
            return None

    def parse_event_text(self, text_content: str, base_date: date) -> list[dict]:
        """Parse daily SWPC events text and group optical (FLA) & X-ray (XRA) observations."""
        lines = text_content.splitlines()
        parsed_items = []

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith(":"):
                continue

            # Pad to 85 characters to guarantee slicing indices are safe, preserving leading spaces
            padded = line.ljust(85)

            event_id_raw = padded[0:8].strip()
            begin_raw = padded[8:17].strip()
            max_raw = padded[17:27].strip()
            end_raw = padded[27:33].strip()
            obs = padded[33:38].strip()
            q = padded[38:42].strip()
            event_type = padded[42:47].strip()
            loc_frq = padded[47:57].strip()
            particulars = padded[57:75].strip()
            reg_raw = padded[75:].strip()

            # Find base event number
            match_no = re.search(r"\d+", event_id_raw)
            if not match_no:
                continue
            event_no = int(match_no.group(0))

            if event_type not in ["XRA", "FLA"]:
                continue

            # Parse region number
            region = None
            if reg_raw and reg_raw != "////":
                try:
                    region = int(reg_raw)
                except ValueError:
                    pass

            parsed_items.append({
                "event_no": event_no,
                "begin_raw": begin_raw,
                "max_raw": max_raw,
                "end_raw": end_raw,
                "obs": obs,
                "event_type": event_type,
                "loc_frq": loc_frq,
                "particulars": particulars,
                "region": region,
            })

        # Group by event_no to link FLA and XRA
        groups = {}
        for item in parsed_items:
            groups.setdefault(item["event_no"], []).append(item)

        final_flares = []
        class_regex = re.compile(r"^[ABCMX]\d+(\.\d+)?$")

        for event_no, group_items in groups.items():
            # Find XRA (X-ray) lines
            xra_lines = [it for it in group_items if it["event_type"] == "XRA"]
            # Find FLA (optical) lines
            fla_lines = [it for it in group_items if it["event_type"] == "FLA"]

            for xra in xra_lines:
                particulars_tokens = xra["particulars"].split()
                if not particulars_tokens:
                    continue
                flare_class = particulars_tokens[0]
                if not class_regex.match(flare_class):
                    continue

                # Parse start, peak, and end datetimes
                start_dt = self.parse_time_str(xra["begin_raw"], base_date)
                if not start_dt:
                    continue

                peak_dt = self.parse_time_str(xra["max_raw"], base_date, start_time=start_dt)
                end_dt = self.parse_time_str(xra["end_raw"], base_date, start_time=start_dt)

                # Initialize metadata
                location = None
                importance = None
                region_number = xra["region"]

                # Enrich metadata if matching FLA line exists
                if fla_lines:
                    # Use the first available optical flare line
                    fla = fla_lines[0]
                    if fla["loc_frq"] and fla["loc_frq"] != "1-8A":
                        location = fla["loc_frq"]
                    
                    fla_particulars = fla["particulars"].split()
                    if fla_particulars:
                        importance = fla_particulars[0]
                    
                    if region_number is None:
                        region_number = fla["region"]

                # Generate a unique event ID matching previous convention
                begin_iso = start_dt.strftime("%Y-%m-%d %H:%M:%S")
                event_id = f"XRA_{xra['obs']}_{begin_iso}".replace(" ", "_")

                final_flares.append({
                    "event_id": event_id,
                    "start_time": start_dt,
                    "peak_time": peak_dt,
                    "end_time": end_dt,
                    "flare_class": flare_class,
                    "region_number": region_number,
                    "location": location,
                    "importance": importance,
                    "source": xra["obs"],
                })

        return final_flares

    async def upsert_records(self, records: list[dict]) -> int:
        """Bulk upsert FlareEvent records using ON CONFLICT DO UPDATE."""
        if not records:
            return 0

        # Deduplicate records by event_id in memory to prevent CardinalityViolationError
        seen = {}
        for r in records:
            seen[r["event_id"]] = r
        deduped = list(seen.values())

        chunk_size = 2000
        total_inserted = 0

        for i in range(0, len(deduped), chunk_size):
            chunk = deduped[i:i + chunk_size]
            async with async_session_maker() as session:
                insert_stmt = insert(FlareEvent).values(chunk)
                update_cols = {
                    col.name: col
                    for col in insert_stmt.excluded
                    if col.name not in ["event_id", "created_at"]
                }
                upsert_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=["event_id"], set_=update_cols
                )
                await session.execute(upsert_stmt)
                await session.commit()
            total_inserted += len(chunk)

        return total_inserted

    async def export_year_parquet(self, year: int) -> None:
        """Export Flare events for a given year to a Parquet file."""
        logger.info(f"Exporting Flare events for year {year} to Parquet...")
        parquet_path = os.path.join(self.raw_dir, f"flare_{year}.parquet")
        
        start_dt = datetime(year, 1, 1, 0, 0, 0)
        end_dt = datetime(year, 12, 31, 23, 59, 59)

        async with async_session_maker() as session:
            from sqlmodel import select
            stmt = (
                select(FlareEvent)
                .where(FlareEvent.start_time >= start_dt, FlareEvent.start_time <= end_dt)
                .order_by(FlareEvent.start_time.asc())
            )
            result = await session.execute(stmt)
            records = result.scalars().all()

        if not records:
            logger.warning(f"No records found in database for year {year} to export to Parquet.")
            return

        df = pd.DataFrame([r.model_dump() for r in records])
        # Format datetimes
        if "created_at" in df.columns:
            df["created_at"] = df["created_at"].dt.strftime("%Y-%m-%d %H:%M:%S")

        df.to_parquet(parquet_path, index=False)
        logger.info(f"Exported {len(df)} flare events to {parquet_path}")

    async def backfill(self, start_date: date, end_date: date) -> None:
        """Execute daily loop to download daily text files, parse events, and store in DB."""
        logger.info(f"Commencing Flare events backfill from {start_date} to {end_date}...")
        
        # Build chronological list of dates to process
        dates_to_process = []
        curr = start_date
        while curr <= end_date:
            dates_to_process.append(curr)
            curr += timedelta(days=1)

        checkpoint_date = await CheckpointManager.get_checkpoint("FLARE_BACKFILL")
        if checkpoint_date:
            dates_to_process = [d for d in dates_to_process if d > checkpoint_date]

        if not dates_to_process:
            logger.info("No new Flare event dates to backfill.")
            return

        def process_chunk_of_days(days) -> list[tuple[date, list[dict], Exception | None]]:
            fetcher = SWPCEventFetcher()
            results = []
            try:
                for target_date in days:
                    filename = f"{target_date.strftime('%Y%m%d')}events.txt"
                    try:
                        content = fetcher.fetch_file(filename)
                        records = []
                        if content:
                            records = self.parse_event_text(content, target_date)
                        results.append((target_date, records, None))
                    except Exception as e:
                        results.append((target_date, [], e))
            finally:
                fetcher.disconnect()
            return results

        chunk_size = 100
        for idx in range(0, len(dates_to_process), chunk_size):
            chunk = dates_to_process[idx:idx + chunk_size]
            logger.info(f"Processing Flare events batch: {chunk[0]} to {chunk[-1]}")
            
            # Split chunk into 4 sub-chunks for the 4 workers
            sub_chunks = [chunk[i::4] for i in range(4)]
            sub_chunks = [sc for sc in sub_chunks if sc] # Remove empty ones if any
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(sub_chunks)) as executor:
                futures = {executor.submit(process_chunk_of_days, sc): i for i, sc in enumerate(sub_chunks)}
                
                failed = False
                batch_results = []
                for fut in concurrent.futures.as_completed(futures):
                    try:
                        sub_results = fut.result()
                        for target_date, records, err in sub_results:
                            if err is not None:
                                logger.error(f"Error processing day {target_date}: {err}")
                                failed = True
                            else:
                                batch_results.append((target_date, records))
                    except Exception as e:
                        logger.error(f"Future error: {e}")
                        failed = True
                
                # Sort batch_results chronologically to insert and update checkpoints in order
                batch_results.sort(key=lambda x: x[0])
                
                # Insert records and update checkpoints sequentially
                checkpoint_date = await CheckpointManager.get_checkpoint("FLARE_BACKFILL")
                latest_consec = checkpoint_date
                processed_any = False
                for target_date, records in batch_results:
                    if failed and target_date > (latest_consec + timedelta(days=1) if latest_consec else start_date):
                        # Stop checkpoint advancement if a failure occurred
                        break
                    
                    if records:
                        inserted = await self.upsert_records(records)
                        logger.info(f"Successfully backfilled Flares {target_date}: {inserted} records.")
                        processed_any = True
                    
                    await CheckpointManager.update_checkpoint("FLARE_BACKFILL", target_date, "in_progress")
                    latest_consec = target_date
                
                # Check if we transitioned to a new year or finished all to export Parquet
                if processed_any:
                    years_in_batch = {d.year for d in chunk}
                    for y in sorted(years_in_batch):
                        await self.export_year_parquet(y)
                
                if failed:
                    raise RuntimeError("One or more days failed during flare backfill batch.")

        # Disconnect internal class fetcher if any
        self.fetcher.disconnect()

        final_checkpoint = await CheckpointManager.get_checkpoint("FLARE_BACKFILL")
        if final_checkpoint and final_checkpoint >= end_date:
            await CheckpointManager.update_checkpoint("FLARE_BACKFILL", end_date, "completed")
            logger.info("Flare events backfill pipeline completed successfully.")
