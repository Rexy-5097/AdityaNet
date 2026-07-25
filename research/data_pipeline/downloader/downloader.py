import os
import time
from typing import Dict, Any, Optional
from rich.progress import Progress, BarColumn, TextColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
from data_pipeline.downloader.logger import logger
from data_pipeline.downloader.session import PradanSession
from data_pipeline.downloader.manifest import DownloadManifest, DownloadRecord

class FileDownloader:
    def __init__(self, session: PradanSession, manifest: DownloadManifest, download_dir: str):
        self.session = session
        self.manifest = manifest
        self.download_dir = download_dir
        self.temp_dir = os.path.join(download_dir, "temp")
        os.makedirs(self.temp_dir, exist_ok=True)

    def download(self, record: DownloadRecord, progress: Optional[Progress] = None, task_id: Optional[Any] = None) -> str:
        """
        Downloads a file from the server. Supports streaming, partial resumption via Range headers,
        and automatic retry on disconnect/timeout.
        """
        url_path = record.source_url
        filename = record.filename
        
        # Local paths
        partial_path = os.path.join(self.temp_dir, f"{filename}.part")
        
        # 1. Fetch headers to get Content-Length and verify Range support
        try:
            head_response = self.session.head(url_path)
            content_length = int(head_response.headers.get("Content-Length", 0))
            accept_ranges = head_response.headers.get("Accept-Ranges", "").lower()
            
            # Save query parameters and headers to record
            record.pradan_query_params = url_path.split('?')[-1] if '?' in url_path else ""
            record.http_headers = str(dict(head_response.headers))
            record.size = content_length
            self.manifest.update(record)
            
        except Exception as e:
            logger.warning(f"HEAD request failed for {filename}, falling back to direct download: {e}")
            content_length = 0
            accept_ranges = "none"

        # 2. Check if we can resume a partial file
        local_size = 0
        headers = {}
        write_mode = "wb"
        
        if os.path.exists(partial_path) and content_length > 0:
            local_size = os.path.getsize(partial_path)
            if local_size < content_length and ("bytes" in accept_ranges or accept_ranges == "yes"):
                headers["Range"] = f"bytes={local_size}-"
                write_mode = "ab"
                logger.info(f"Resuming download for {filename} from byte {local_size}/{content_length}...")
            elif local_size == content_length:
                logger.info(f"Partial file {filename}.part is already complete. Skipping download.")
                return partial_path
            else:
                local_size = 0
                logger.info(f"Starting download of {filename} from scratch.")

        # 3. Setup Rich Progress Task if running sequential or passed from manager
        own_progress = False
        if progress is None:
            own_progress = True
            progress = Progress(
                TextColumn("[bold blue]{task.description}"),
                BarColumn(bar_width=40),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn()
            )
            progress.start()
            task_id = progress.add_task(f"Downloading: {filename}", total=content_length)

        if task_id is not None and local_size > 0:
            progress.update(task_id, completed=local_size)

        # 4. Stream the file content
        start_time = time.time()
        downloaded = local_size
        
        try:
            response = self.session.get(url_path, stream=True, headers=headers)
            
            # Check if server accepted range request
            if response.status_code == 200 and write_mode == "ab":
                # Server ignored Range header, starting from scratch
                write_mode = "wb"
                downloaded = 0
                if task_id is not None:
                    progress.update(task_id, completed=0)
            
            with open(partial_path, write_mode) as f:
                for chunk in response.iter_content(chunk_size=16384):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if task_id is not None:
                            progress.update(task_id, advance=len(chunk))
                            
            elapsed = time.time() - start_time
            record.download_time = elapsed
            record.download_timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            record.status = "Downloaded"
            self.manifest.update(record)
            
            return partial_path
            
        except Exception as e:
            logger.error(f"Download failed for {filename}: {e}")
            raise
        finally:
            if own_progress:
                progress.stop()
