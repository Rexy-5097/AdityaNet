"""
Sprint DA-03C — Network Resilience & Session Recovery Hardening
===============================================================
Builds on Sprint H-01. Authentication, cookie handling, protocol replay,
manifest schema, ZIP/FITS verification, dataset versioning: UNCHANGED.

New in DA-03C (transport layer only):
  1. classify_exception(): BrokenPipe/Timeout/DNS → NetworkInterrupted (never SessionExpired)
  2. SessionHealthStateMachine: Healthy|NetworkInterrupted|TemporarilyUnavailable|Refreshing|Expired
  3. DNS retry: 2→5→10→20→30s backoff, no session invalidation
  4. BrokenPipe: TCP reset + HTTP Range resume from last byte
  5. ReadTimeout: up to 8 retries, always range-resume
  6. Worker isolation: per-worker consecutive-failure counter; only bad worker pauses
  7. network_events.json: per-transport-event structured log
  8. network_resilience_report.md: aggregated statistics at end of run

Pipeline version: 1.5.0-SprintDA03C
"""

import os, sys, json, yaml, re, time, shutil, sqlite3, hashlib, zipfile
import argparse, threading, traceback as _traceback, socket, http.client
from datetime import datetime, timezone
from enum import Enum, auto
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_pipeline.downloader.logger import logger
from data_pipeline.downloader.checksum import calculate_sha256, calculate_crc32, write_checksum_file
from data_pipeline.downloader.verifier import QualityInspector
from data_pipeline.downloader.inventory import InventoryGenerator

try:
    import urllib3.exceptions as _urllib3_exc
    _URLLIB3_AVAILABLE = True
except ImportError:
    _URLLIB3_AVAILABLE = False

try:
    import requests.exceptions as _req_exc
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False

# ─── URL / Script Parsing (unchanged from H-01) ───────────────────────────────

def parse_pradan_script(script_path: str):
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"PRADAN script not found: {script_path}")
    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
    cookie_match = re.search(r'cookies="([^"]+)"', content)
    if not cookie_match:
        raise ValueError(f"No cookies= found in {script_path}")
    cookies_str = cookie_match.group(1).strip()
    url_match = re.search(r'urlPrefix="([^"]+)"', content)
    base_url = url_match.group(1).strip() if url_match else "https://pradan1.issdc.gov.in"
    paths = re.findall(r'"(/al1/protected/downloadData/hel1os/[^"]+)"', content)
    seen, unique_paths = set(), []
    for p in paths:
        if p not in seen:
            seen.add(p); unique_paths.append(p)
    logger.info(f"Parsed {len(unique_paths)} unique HEL1OS URLs from {script_path}")
    logger.info(f"Cookie hash: {hashlib.md5(cookies_str.encode()).hexdigest()}")
    return cookies_str, base_url, unique_paths

def url_to_filename(url_path):
    return url_path.split("/")[-1].split("?")[0]

def url_to_date(url_path):
    m = re.search(r"/(\d{4})/(\d{2})/(\d{2})/", url_path)
    if m: return m.group(1)+m.group(2)+m.group(3)
    fname = url_to_filename(url_path)
    dm = re.search(r"HLS_(\d{8})_", fname)
    return dm.group(1) if dm else ""

# ─── Transport Exception Taxonomy (NEW DA-03C) ────────────────────────────────

_TRANSPORT_BASE_TYPES = (
    BrokenPipeError, ConnectionResetError, ConnectionAbortedError,
    ConnectionRefusedError, TimeoutError, socket.timeout, socket.gaierror,
    socket.herror, OSError, http.client.IncompleteRead, http.client.RemoteDisconnected,
)
_TRANSPORT_TYPE_NAMES = {
    "BrokenPipeError","ConnectionResetError","ConnectionAbortedError",
    "ConnectionRefusedError","TimeoutError","ChunkedEncodingError",
    "IncompleteRead","ReadTimeout","ConnectTimeout","NameResolutionError",
    "ProxyError","RemoteDisconnected","SSLError",
}
_TRANSPORT_STR_KEYWORDS = [
    "BrokenPipe","Broken pipe","Connection reset","ConnectionReset",
    "Connection aborted","Read timed out","timed out","NameResolution",
    "Failed to resolve","nodename nor servname","gaierror","IncompleteRead",
    "ChunkedEncoding","RemoteDisconnected","EOF occurred","Connection refused",
]

def classify_exception(exc: Exception) -> str:
    if type(exc).__name__ in _TRANSPORT_TYPE_NAMES:
        return "NetworkInterrupted"
    if isinstance(exc, _TRANSPORT_BASE_TYPES):
        return "NetworkInterrupted"
    if _REQUESTS_AVAILABLE and isinstance(exc, (
        _req_exc.ReadTimeout, _req_exc.ConnectTimeout,
        _req_exc.ConnectionError, _req_exc.ChunkedEncodingError,
    )):
        return "NetworkInterrupted"
    if _URLLIB3_AVAILABLE and isinstance(exc, (
        _urllib3_exc.NameResolutionError, _urllib3_exc.MaxRetryError,
        _urllib3_exc.TimeoutError, _urllib3_exc.ProtocolError,
    )):
        return "NetworkInterrupted"
    exc_str = str(exc)
    if any(kw.lower() in exc_str.lower() for kw in _TRANSPORT_STR_KEYWORDS):
        return "NetworkInterrupted"
    return "Unknown"

def is_dns_error(exc: Exception) -> bool:
    exc_str = str(exc)
    if isinstance(exc, (socket.gaierror, socket.herror)):
        return True
    if _URLLIB3_AVAILABLE and isinstance(exc, _urllib3_exc.NameResolutionError):
        return True
    return any(kw.lower() in exc_str.lower() for kw in
               ["NameResolution","Failed to resolve","nodename nor servname","gaierror","[Errno 8]"])

# ─── Session Health State Machine (NEW DA-03C) ────────────────────────────────

class SessionState(Enum):
    HEALTHY                = auto()
    NETWORK_INTERRUPTED    = auto()
    TEMPORARILY_UNAVAILABLE = auto()
    REFRESHING             = auto()
    EXPIRED                = auto()

class SessionExpiredException(Exception): pass
class NetworkInterruptedException(Exception): pass

DNS_RETRY_DELAYS = [2, 5, 10, 20, 30]

class Hel1osAuthSessionManager:
    """
    DA-03B authentication preserved exactly (verbatim Cookie injection).
    DA-03C: SessionHealthStateMachine + transport error isolation.
    """
    def __init__(self, cookies_str: str, base_url: str):
        self.cookies_str = cookies_str
        self.base_url    = base_url
        self.cookie_hash = hashlib.md5(cookies_str.encode("utf-8")).hexdigest()
        self.lock        = threading.Lock()
        self._state      = SessionState.HEALTHY
        self._state_lock = threading.RLock()
        self._workers_gate = threading.Event()
        self._workers_gate.set()
        self.network_interruptions  = 0
        self.dns_failures           = 0
        self.session_refreshes      = 0
        self.total_downtime_seconds = 0.0
        self.session = None
        self._init_session()

    def _init_session(self):
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        self.session = requests.Session()
        self.session.cookies.clear()               # DA-03B fix preserved
        adapter = HTTPAdapter(max_retries=Retry(total=0, raise_on_status=False))
        self.session.mount("https://", adapter)
        self.session.mount("http://",  adapter)
        self.session.headers.update({              # DA-03B fix preserved
            "User-Agent":      "Wget/1.21.1",
            "Accept":          "*/*",
            "Accept-Encoding": "identity",
            "Connection":      "Keep-Alive",
            "Cookie":          self.cookies_str,   # verbatim — duplicate JSESSIONID preserved
        })

    def reset_tcp(self):
        """Fresh TCP socket pool only — auth headers UNCHANGED."""
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        adapter = HTTPAdapter(max_retries=Retry(total=0, raise_on_status=False))
        self.session.mount("https://", adapter)
        self.session.mount("http://",  adapter)
        logger.info("TCP pool reset (auth headers preserved).")

    @property
    def state(self):
        with self._state_lock: return self._state
    @state.setter
    def state(self, v):
        with self._state_lock:
            if self._state != v:
                logger.info(f"Session: {self._state.name} → {v.name}")
            self._state = v

    def wait_for_gate(self):
        self._workers_gate.wait()

    def keep_alive(self) -> str:
        """Returns 'Healthy' | 'Expired' | 'TemporarilyUnavailable'."""
        url = f"{self.base_url}/al1/protected/payload.xhtml"
        try:
            resp = self.session.get(url, timeout=20, stream=False, allow_redirects=True)
            final_url = resp.url
            is_login = (
                "login.xhtml" in final_url or
                "idp.issdc.gov.in" in final_url or
                "openid-connect/auth" in final_url
            )
            if not is_login and resp.status_code == 200:
                try:
                    snip = resp.content[:512].decode("utf-8", errors="ignore")
                    is_login = "loginForm" in snip or (
                        "username" in snip.lower() and "password" in snip.lower()
                    )
                except Exception: pass
            if resp.status_code == 200 and not is_login:
                logger.info(f"Keep-alive: Healthy")
                return "Healthy"
            logger.warning(f"Keep-alive: Expired (url={final_url})")
            return "Expired"
        except Exception as exc:
            logger.warning(f"Keep-alive: TemporarilyUnavailable ({type(exc).__name__}: {exc})")
            return "TemporarilyUnavailable"

    def handle_auth_failure(self):
        """Called ONLY when HTTP response confirms login redirect — never on transport errors."""
        with self.lock:
            if self.state == SessionState.REFRESHING:
                logger.info("Refresh in progress — waiting...")
                self._workers_gate.wait(); return
            self.state = SessionState.REFRESHING
            self._workers_gate.clear()
            t0 = time.time()
            try:
                self.session_refreshes += 1
                self._init_session()
                result = self.keep_alive()
                if result == "Healthy":
                    self.state = SessionState.HEALTHY
                    self._workers_gate.set()
                    self.total_downtime_seconds += time.time() - t0
                    logger.info("Session refresh successful.")
                    return
                if result == "TemporarilyUnavailable":
                    for delay in DNS_RETRY_DELAYS:
                        logger.warning(f"Keep-alive unavailable; retry in {delay}s...")
                        time.sleep(delay)
                        result = self.keep_alive()
                        if result == "Healthy":
                            self.state = SessionState.HEALTHY
                            self._workers_gate.set()
                            self.total_downtime_seconds += time.time() - t0
                            logger.info("Session refresh successful after network recovery.")
                            return
                self.state = SessionState.EXPIRED
                self._workers_gate.set()
                self.total_downtime_seconds += time.time() - t0
                raise SessionExpiredException(
                    "Session expired. Provide fresh credentials in legacy/pradan_hel1os_fresh.sh."
                )
            except SessionExpiredException: raise
            except Exception as exc:
                self.state = SessionState.EXPIRED
                self._workers_gate.set()
                raise SessionExpiredException(f"Refresh error: {exc}") from exc

    def handle_network_interruption(self):
        """TCP-level failure — reset socket pool, no session state change."""
        self.network_interruptions += 1
        with self._state_lock:
            if self._state == SessionState.HEALTHY:
                self._state = SessionState.NETWORK_INTERRUPTED
        self.reset_tcp()
        time.sleep(2)
        with self._state_lock:
            if self._state == SessionState.NETWORK_INTERRUPTED:
                self._state = SessionState.HEALTHY

    def handle_dns_failure(self):
        """DNS outage — backoff + retry, no session invalidation."""
        self.dns_failures += 1
        prev = self.state
        self.state = SessionState.TEMPORARILY_UNAVAILABLE
        self._workers_gate.clear()
        resolved = False
        for delay in DNS_RETRY_DELAYS:
            logger.warning(f"DNS failure; retry in {delay}s...")
            time.sleep(delay)
            try:
                socket.getaddrinfo("pradan1.issdc.gov.in", 443)
                resolved = True; break
            except Exception: continue
        self._workers_gate.set()
        self.state = SessionState.HEALTHY if resolved else prev
        logger.info("DNS resolved." if resolved else "DNS still failing; workers retry individually.")

# ─── Network Event Log (NEW DA-03C) ──────────────────────────────────────────

class NetworkEventLog:
    def __init__(self, log_path: str):
        self.log_path = log_path
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

    def record(self, *, filename, worker_id, failure_type, resume_offset=0,
               downloaded_bytes=0, retry_count=0, elapsed_seconds=0.0, recovered=False, extra=None):
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "filename": filename, "worker_id": worker_id,
            "failure_type": failure_type, "resume_offset": resume_offset,
            "downloaded_bytes": downloaded_bytes, "retry_count": retry_count,
            "elapsed_seconds": round(elapsed_seconds, 3), "recovered": recovered,
        }
        if extra: event.update(extra)
        with self._lock:
            with open(self.log_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(event) + "\n")

# ─── HEL1OS Downloader (DA-03C) ──────────────────────────────────────────────

class Hel1osDownloader:
    VERSION          = "dataset_v3"
    PIPELINE_VERSION = "1.5.0-SprintDA03C"
    MAX_READ_RETRIES = 8
    MAX_WORKER_CONSEC_FAILURES = 5

    def __init__(self, config_path, script_path, force_redownload=False):
        self.config_path      = config_path
        self.script_path      = script_path
        self.force_redownload = force_redownload
        self.config           = self._load_config()

        self.db_path       = self.config["manifest_database"].replace("{version}", self.VERSION)
        self.inventory_dir = self.config["inventory_output"].replace("{version}", self.VERSION)
        self.checksums_dir = self.config["checksums_directory"].replace("{version}", self.VERSION)
        self.reports_dir   = self.config["reports_directory"].replace("{version}", self.VERSION)
        self.metadata_dir  = self.config["metadata_directory"].replace("{version}", self.VERSION)
        self.download_dir  = self.config["download_directory"]
        self.temp_dir      = os.path.join(self.download_dir, "temp_hel1os")

        for d in [self.temp_dir, os.path.dirname(self.db_path), self.inventory_dir,
                  self.checksums_dir, self.reports_dir, self.metadata_dir,
                  os.path.join(self.reports_dir, "protocol_certificates"),
                  os.path.join(self.download_dir, "corrupted")]:
            os.makedirs(d, exist_ok=True)

        self.cookies_str, self.base_url, self.url_paths = parse_pradan_script(script_path)
        self._init_manifest_db()
        self._run_schema_migration()

        self.session_mgr   = Hel1osAuthSessionManager(self.cookies_str, self.base_url)
        self.inspector     = QualityInspector(corrupted_dir=os.path.join(self.download_dir, "corrupted"))
        self.inventory_gen = InventoryGenerator(self.db_path, self.inventory_dir)
        self.net_events    = NetworkEventLog(os.path.join(self.reports_dir, "network_events.json"))

        self.stats = {
            "total_urls":0,"downloaded":0,"skipped":0,"still_failed":0,
            "permanent_failures":0,"zip_failures":0,"fits_failures":0,
            "elapsed_time":0.0,"scientific_coverage":0.0,"total_retries":0,
            "network_interruptions":0,"dns_failures":0,"auth_failures":0,
        }
        self._worker_failures: dict = {}
        self._worker_lock = threading.Lock()

    def _load_config(self):
        with open(self.config_path) as f: return yaml.safe_load(f)

    # ── Manifest DB ────────────────────────────────────────────────────────────

    def _init_manifest_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=30000;")
        conn.execute("""CREATE TABLE IF NOT EXISTS downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT, source_url TEXT UNIQUE,
            filename TEXT, payload TEXT, date TEXT, size INTEGER,
            checksum TEXT, zip_crc TEXT, status TEXT DEFAULT 'Queued',
            download_time REAL, download_timestamp TEXT, pradan_query_params TEXT,
            http_headers TEXT, original_filename TEXT, local_filename TEXT,
            path TEXT, remarks TEXT, download_start TEXT, download_finish TEXT,
            elapsed_time REAL, retry_count INTEGER DEFAULT 0, http_status INTEGER,
            content_type TEXT, content_length INTEGER, response_hash TEXT,
            verification_status TEXT, failure_reason TEXT, etag TEXT,
            last_modified TEXT, cookie_hash TEXT)""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_dl_src ON downloads(source_url)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_dl_st  ON downloads(status)")
        conn.execute("""CREATE TABLE IF NOT EXISTS fits_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT, download_id INTEGER,
            instrument TEXT, observation_date TEXT, cadence REAL, num_rows INTEGER,
            start_time TEXT, end_time TEXT, energy_channels TEXT,
            missing_percentage REAL,
            FOREIGN KEY (download_id) REFERENCES downloads(id) ON DELETE CASCADE)""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_fits_dl ON fits_metadata(download_id)")
        conn.commit(); conn.close()

    def _run_schema_migration(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL;")
        existing = {r[1] for r in conn.execute("PRAGMA table_info(downloads)").fetchall()}
        for col, t in {
            "download_start":"TEXT","download_finish":"TEXT","elapsed_time":"REAL",
            "retry_count":"INTEGER","http_status":"INTEGER","content_type":"TEXT",
            "content_length":"INTEGER","response_hash":"TEXT","verification_status":"TEXT",
            "failure_reason":"TEXT","etag":"TEXT","last_modified":"TEXT","cookie_hash":"TEXT",
        }.items():
            if col not in existing:
                conn.execute(f"ALTER TABLE downloads ADD COLUMN {col} {t}")
        conn.commit(); conn.close()

    _db_lock = threading.Lock()

    def _db_connect(self):
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=30000;")
        conn.row_factory = sqlite3.Row
        return conn

    def _populate_manifest(self):
        logger.info(f"Populating manifest with {len(self.url_paths)} HEL1OS URLs...")
        with self._db_lock:
            conn = self._db_connect()
            ins = skp = 0
            for p in self.url_paths:
                fn = url_to_filename(p); dt = url_to_date(p)
                url = f"{self.base_url}{p}"
                try:
                    conn.execute(
                        "INSERT OR IGNORE INTO downloads "
                        "(source_url,filename,payload,date,status,pradan_query_params) "
                        "VALUES (?,?,'hel1os',?,'Queued',?)",
                        (url, fn, dt, p.split("?")[1] if "?" in p else ""))
                    if conn.execute("SELECT changes()").fetchone()[0] > 0: ins += 1
                    else: skp += 1
                except sqlite3.IntegrityError: skp += 1
            conn.commit(); conn.close()
        logger.info(f"Manifest: {ins} new, {skp} already present.")

    def _load_pending(self):
        conn = self._db_connect()
        if self.force_redownload:
            rows = conn.execute("SELECT * FROM downloads ORDER BY id ASC").fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM downloads WHERE status IN "
                "('Queued','Failed','Interrupted','Corrupted') ORDER BY id ASC"
            ).fetchall()
        result = [dict(r) for r in rows]; conn.close(); return result

    def _load_all(self):
        conn = self._db_connect()
        rows = [dict(r) for r in conn.execute("SELECT * FROM downloads").fetchall()]
        conn.close(); return rows

    # ── HTTP Response Classification ──────────────────────────────────────────

    def _classify_http_response(self, response) -> str:
        status = response.status_code
        ct = response.headers.get("Content-Type","")
        if status == 403: return "Forbidden"
        if status == 404: return "NotFound"
        if status == 401: return "AuthenticationFailed"
        if status >= 500: return "ServerError"
        if status not in (200, 206): return "Interrupted"
        fu = response.url
        hu = " ".join(r.url for r in response.history)
        is_login = (
            "login.xhtml" in fu or "idp.issdc.gov.in" in fu or
            "openid-connect/auth" in fu or "login.xhtml" in hu or
            "idp.issdc.gov.in" in hu
        )
        if is_login: return "LoginRedirect"
        if "text/html" in ct: return "LoginRedirect"
        cl = int(response.headers.get("Content-Length",0))
        if 0 < cl < 10240: return "AuthExpired"
        return "Success"

    # ── Resilient stream ──────────────────────────────────────────────────────

    def _stream_with_resilience(self, full_url, partial_path, filename, worker_id, start_ts):
        http_status = content_type = etag = last_modified = None
        content_length = 0
        read_retries = 0

        while read_retries <= self.MAX_READ_RETRIES:
            self.session_mgr.wait_for_gate()
            if self.session_mgr.state == SessionState.EXPIRED:
                raise SessionExpiredException("Session expired.")

            local_size = os.path.getsize(partial_path) if os.path.exists(partial_path) else 0
            req_headers = {}
            write_mode  = "wb"
            if local_size > 0:
                req_headers["Range"] = f"bytes={local_size}-"
                write_mode = "ab"
                logger.info(f"[W{worker_id}] Resume {filename} from byte {local_size}")

            response = None
            try:
                response = self.session_mgr.session.get(
                    full_url, stream=True, headers=req_headers,
                    timeout=(15, 90), allow_redirects=True,
                )
                classification = self._classify_http_response(response)

                if classification in ("LoginRedirect","AuthExpired","AuthenticationFailed"):
                    logger.warning(f"[W{worker_id}] Auth failure for {filename}: {classification}")
                    self.stats["auth_failures"] += 1
                    self.session_mgr.handle_auth_failure()
                    read_retries += 1; self.stats["total_retries"] += 1; continue

                if classification in ("Forbidden","NotFound"):
                    return (response.status_code, content_type or "", 0, etag or "", last_modified or "", classification)

                if classification == "ServerError":
                    read_retries += 1; time.sleep(min(2**read_retries, 60)); continue

                if classification != "Success":
                    read_retries += 1; time.sleep(2); continue

                http_status    = response.status_code
                content_type   = response.headers.get("Content-Type","")
                content_length = int(response.headers.get("Content-Length",0)) + local_size
                etag           = response.headers.get("ETag","")
                last_modified  = response.headers.get("Last-Modified","")

                with open(partial_path, write_mode) as fh:
                    for chunk in response.iter_content(chunk_size=65536):
                        if chunk: fh.write(chunk)

                return (http_status, content_type, content_length, etag, last_modified, "Success")

            except Exception as exc:
                exc_class = classify_exception(exc)
                if exc_class == "NetworkInterrupted":
                    read_retries += 1; self.stats["total_retries"] += 1
                    elapsed = time.time() - start_ts
                    local_now = os.path.getsize(partial_path) if os.path.exists(partial_path) else 0
                    fname_type = type(exc).__name__
                    is_dns  = is_dns_error(exc)
                    is_pipe = "BrokenPipe" in fname_type or "BrokenPipe" in str(exc)
                    is_tout = "Timeout" in fname_type or "timed out" in str(exc).lower()

                    logger.warning(
                        f"[W{worker_id}] Transport {fname_type} for {filename} "
                        f"at byte {local_now}. Retry {read_retries}/{self.MAX_READ_RETRIES}"
                    )
                    self.net_events.record(
                        filename=filename, worker_id=worker_id, failure_type=fname_type,
                        resume_offset=local_now, downloaded_bytes=local_now,
                        retry_count=read_retries, elapsed_seconds=elapsed, recovered=False,
                    )

                    if is_dns:
                        self.stats["dns_failures"] += 1
                        self.session_mgr.handle_dns_failure(); continue
                    if is_pipe:
                        self.stats["network_interruptions"] += 1
                        self.session_mgr.handle_network_interruption()
                        time.sleep(min(2**read_retries, 30)); continue
                    if is_tout:
                        backoff = min(5*read_retries, 60)
                        logger.warning(f"[W{worker_id}] Timeout; backing off {backoff}s")
                        time.sleep(backoff); continue

                    self.stats["network_interruptions"] += 1
                    self.session_mgr.handle_network_interruption()
                    time.sleep(min(2**read_retries, 30)); continue
                else:
                    raise
            finally:
                if response:
                    try: response.close()
                    except Exception: pass

        raise NetworkInterruptedException(
            f"Exceeded {self.MAX_READ_RETRIES} transport retries for {filename}"
        )

    # ── Full download + verify ────────────────────────────────────────────────

    def _download_and_verify(self, record: dict, worker_id: int = 0) -> str:
        filename     = record["filename"]
        full_url     = record["source_url"]
        url_path     = full_url.replace(self.base_url, "")
        partial_path = os.path.join(self.temp_dir, f"{filename}.part")
        dl_start     = datetime.now(timezone.utc).isoformat()
        start_ts     = time.time()

        self.session_mgr.wait_for_gate()
        if self.session_mgr.state == SessionState.EXPIRED:
            return "AuthenticationFailed"

        try:
            # HEAD for metadata
            content_length = etag = last_modified = 0
            try:
                head = self.session_mgr.session.head(full_url, timeout=(10,15))
                content_length = int(head.headers.get("Content-Length",0))
                etag           = head.headers.get("ETag","")
                last_modified  = head.headers.get("Last-Modified","")
            except Exception as exc:
                if classify_exception(exc) == "NetworkInterrupted":
                    logger.warning(f"[W{worker_id}] HEAD transport err for {filename}: {exc}")

            # Resilient stream
            (http_status, content_type, content_length,
             etag, last_modified, http_class) = self._stream_with_resilience(
                full_url, partial_path, filename, worker_id, start_ts)

            if http_class in ("Forbidden","NotFound"):
                return http_class
            if http_class in ("LoginRedirect","AuthExpired","AuthenticationFailed"):
                return "AuthenticationFailed"
            if http_class != "Success":
                return "Interrupted"

            # Size sanity
            final_size = os.path.getsize(partial_path)
            if content_length > 0 and final_size != content_length:
                logger.error(f"[W{worker_id}] Size mismatch {filename}: disk={final_size} expected={content_length}")
                return "Interrupted"

            # ZIP signature
            try:
                with open(partial_path,"rb") as fh:
                    sig_ok = fh.read(4) == b"PK\x03\x04"
            except Exception: sig_ok = False
            if not sig_ok:
                logger.error(f"[W{worker_id}] ZIP sig fail {filename}")
                self._quarantine(partial_path); self.stats["zip_failures"] += 1
                return "CorruptedZIP"

            # ZIP testzip
            try:
                with zipfile.ZipFile(partial_path) as zf:
                    bad = zf.testzip()
                    if bad:
                        logger.error(f"[W{worker_id}] ZIP testzip fail {filename}: {bad}")
                        self._quarantine(partial_path); self.stats["zip_failures"] += 1
                        return "CorruptedZIP"
            except zipfile.BadZipFile as exc:
                logger.error(f"[W{worker_id}] BadZip {filename}: {exc}")
                self._quarantine(partial_path); self.stats["zip_failures"] += 1
                return "CorruptedZIP"

            # FITS validation
            plugin_ok, plugin_msg = self.inspector.verify_archive(partial_path, url_path)
            if not plugin_ok:
                logger.error(f"[W{worker_id}] FITS fail {filename}: {plugin_msg}")
                self.stats["fits_failures"] += 1
                return "CorruptedFITS"

            # Checksums
            sha256  = calculate_sha256(partial_path)
            zip_crc = calculate_crc32(partial_path)
            write_checksum_file(partial_path, sha256, self.checksums_dir)

            # Archive
            obs_date = record.get("date","")
            year_dir = os.path.join(self.download_dir,"raw","hel1os", obs_date[:4] if obs_date else "unknown")
            os.makedirs(year_dir, exist_ok=True)
            final_path = os.path.join(year_dir, filename)
            logger.info(f"[W{worker_id}] Archiving: {filename} -> {final_path}")
            os.replace(partial_path, final_path)

            dl_finish = datetime.now(timezone.utc).isoformat()
            elapsed   = time.time() - start_ts
            self._write_cert(record, final_path, http_status, content_type, content_length,
                             sha256, zip_crc, True, dl_start, dl_finish)

            quality = self.inspector.run_quality_check(final_path, url_path)
            meta    = self.inspector.extract_metadata(final_path, url_path)

            with self._db_lock:
                conn = self._db_connect()
                conn.execute("""UPDATE downloads SET
                    status='Verified',size=?,checksum=?,zip_crc=?,path=?,
                    download_start=?,download_finish=?,elapsed_time=?,http_status=?,
                    content_type=?,content_length=?,response_hash=?,
                    verification_status='Verified',etag=?,last_modified=?,
                    cookie_hash=?,remarks='Verified via Sprint DA-03C' WHERE id=?""",
                    (final_size,sha256,zip_crc,final_path,dl_start,dl_finish,elapsed,
                     http_status,content_type,content_length,sha256,
                     etag,last_modified,self.session_mgr.cookie_hash,record["id"]))
                conn.execute("""INSERT OR REPLACE INTO fits_metadata
                    (download_id,instrument,observation_date,cadence,num_rows,
                     start_time,end_time,energy_channels,missing_percentage)
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                    (record["id"],meta["instrument"],meta["observation_date"],meta["cadence"],
                     meta["num_rows"],meta["start_time"],meta["end_time"],meta["energy_channels"],
                     quality.get("nan_percentage",0.0)))
                conn.commit(); conn.close()

            logger.info(f"[W{worker_id}] Verified: {filename}")
            return "Verified"

        except SessionExpiredException:
            return "AuthenticationFailed"
        except NetworkInterruptedException as exc:
            logger.error(f"[W{worker_id}] Max transport retries for {filename}: {exc}")
            return "MaxRetriesExceeded"
        except Exception as exc:
            if classify_exception(exc) == "NetworkInterrupted":
                logger.error(f"[W{worker_id}] Unhandled transport err {filename}: {exc}")
                return "Interrupted"
            logger.error(f"[W{worker_id}] Unexpected err {filename}: {exc}\n{_traceback.format_exc()}")
            if os.path.exists(partial_path):
                try: os.remove(partial_path)
                except Exception: pass
            return "Interrupted"

    def _quarantine(self, file_path):
        dest = os.path.join(self.download_dir,"corrupted",os.path.basename(file_path))
        logger.warning(f"Quarantining {os.path.basename(file_path)}")
        try: shutil.move(file_path, dest)
        except Exception as exc:
            logger.error(f"Quarantine failed: {exc}")
            try: os.remove(file_path)
            except Exception: pass

    def _write_cert(self, record, final_path, http_status, content_type, content_length,
                    sha256, zip_crc, fits_valid, dl_start, dl_finish):
        try:
            cert_dir  = os.path.join(self.reports_dir,"protocol_certificates")
            cert_path = os.path.join(cert_dir, f"{record['filename']}.cert.json")
            cert = {
                "manifest_id":record["id"],"filename":record["filename"],
                "source_url":record["source_url"],"payload":"hel1os",
                "download_start":dl_start,"download_finish":dl_finish,
                "cookie_hash":self.session_mgr.cookie_hash,"http_status":http_status,
                "content_type":content_type,"content_length":content_length,
                "sha256":sha256,"zip_crc":zip_crc,"fits_validated":fits_valid,
                "final_path":final_path,"pipeline_version":self.PIPELINE_VERSION,
                "generated_at":datetime.now(timezone.utc).isoformat(),
            }
            with open(cert_path,"w") as fh: json.dump(cert, fh, indent=2)
        except Exception as exc:
            logger.warning(f"Cert write failed: {exc}")

    # ── Worker with isolation ─────────────────────────────────────────────────

    def _process_record(self, record: dict, worker_id: int = 0) -> str:
        filename = record["filename"]
        if record["status"] == "Verified" and not self.force_redownload:
            logger.info(f"[W{worker_id}] Skip {filename} (Verified).")
            return "Skipped"

        with self._worker_lock:
            consec = self._worker_failures.get(worker_id, 0)
        if consec >= self.MAX_WORKER_CONSEC_FAILURES:
            logger.warning(f"[W{worker_id}] Pausing 30s after {consec} consecutive failures")
            time.sleep(30)
            with self._worker_lock: self._worker_failures[worker_id] = 0

        for attempt in range(5):
            try:
                result = self._download_and_verify(record, worker_id)

                if result in ("Forbidden","NotFound"):
                    with self._db_lock:
                        conn = self._db_connect()
                        conn.execute("UPDATE downloads SET status='PermanentFailure',"
                                     "failure_reason=? WHERE id=?",
                                     (f"Permanent: {result}", record["id"]))
                        conn.commit(); conn.close()
                    with self._worker_lock: self._worker_failures[worker_id] = 0
                    return "PermanentFailure"

                if result == "AuthenticationFailed":
                    logger.error(f"[W{worker_id}] AuthFailure for {filename}")
                    with self._db_lock:
                        conn = self._db_connect()
                        conn.execute("UPDATE downloads SET status='Failed',"
                                     "failure_reason='AuthenticationFailed' WHERE id=?",
                                     (record["id"],))
                        conn.commit(); conn.close()
                    with self._worker_lock:
                        self._worker_failures[worker_id] = self._worker_failures.get(worker_id,0) + 1
                    return "AuthenticationFailed"

                if result == "Verified":
                    with self._worker_lock: self._worker_failures[worker_id] = 0
                    return "Verified"

                with self._db_lock:
                    conn = self._db_connect()
                    conn.execute("UPDATE downloads SET status='Failed',failure_reason=? WHERE id=?",
                                 (f"Transient: {result}", record["id"]))
                    conn.commit(); conn.close()
                with self._worker_lock:
                    self._worker_failures[worker_id] = self._worker_failures.get(worker_id,0) + 1
                sleep_t = min(2.0**(attempt+1), 120)
                logger.warning(f"[W{worker_id}] Retry {attempt+1}/5 for {filename} in {sleep_t:.0f}s")
                time.sleep(sleep_t)

            except Exception as exc:
                logger.error(f"[W{worker_id}] Worker exc for {filename}: {exc}")
                with self._worker_lock:
                    self._worker_failures[worker_id] = self._worker_failures.get(worker_id,0) + 1
                time.sleep(min(2.0**(attempt+1), 120))

        with self._db_lock:
            conn = self._db_connect()
            conn.execute("UPDATE downloads SET status='Failed',remarks='Max outer retries exceeded' WHERE id=?",
                         (record["id"],))
            conn.commit(); conn.close()
        return "Failed"

    # ── Main run ──────────────────────────────────────────────────────────────

    def run(self) -> dict:
        logger.info("="*70)
        logger.info("Sprint DA-03C — HEL1OS Network-Resilient Downloader")
        logger.info(f"Dataset: {self.VERSION}  |  Pipeline: {self.PIPELINE_VERSION}")
        logger.info(f"Total URLs: {len(self.url_paths)}")
        logger.info("="*70)
        start_ts = time.time()
        self._populate_manifest()
        pending = self._load_pending()
        skipped = [r for r in self._load_all() if r["status"]=="Verified" and not self.force_redownload]
        self.stats["skipped"] = len(skipped)
        logger.info(f"Pending: {len(pending)} | Already verified (skip): {len(skipped)}")
        workers = self.config.get("workers", 4)
        logger.info(f"Spawning {workers} workers...")

        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {ex.submit(self._process_record, rec, i % workers): rec
                       for i, rec in enumerate(pending)}
            for fut in as_completed(futures):
                rec = futures[fut]
                try:
                    r = fut.result()
                    if r in ("Verified","Recovered"):       self.stats["downloaded"] += 1
                    elif r == "PermanentFailure":           self.stats["permanent_failures"] += 1; self.stats["still_failed"] += 1
                    elif r == "Skipped":                    self.stats["skipped"] += 1
                    elif r == "AuthenticationFailed":       self.stats["auth_failures"] += 1; self.stats["still_failed"] += 1
                    else:                                   self.stats["still_failed"] += 1
                except Exception as exc:
                    logger.error(f"Thread exc: {exc}"); self.stats["still_failed"] += 1

        self.stats["elapsed_time"]          = time.time() - start_ts
        self.stats["network_interruptions"] += self.session_mgr.network_interruptions
        self.stats["dns_failures"]          += self.session_mgr.dns_failures

        self.inventory_gen.generate()
        self._completeness_audit()
        self._generate_trust_certificate()
        self._generate_resilience_report()
        self._generate_summary_report()

        logger.info("="*70)
        logger.info("Sprint DA-03C complete.")
        logger.info(f"  Verified    : {self.stats['downloaded']}")
        logger.info(f"  Skipped     : {self.stats['skipped']}")
        logger.info(f"  Still failed: {self.stats['still_failed']}")
        logger.info(f"  Retries     : {self.stats['total_retries']}")
        logger.info(f"  Net errors  : {self.stats['network_interruptions']}")
        logger.info(f"  DNS failures: {self.stats['dns_failures']}")
        logger.info(f"  Auth fails  : {self.stats['auth_failures']}")
        logger.info(f"  Elapsed     : {self.stats['elapsed_time']:.1f}s")
        logger.info("="*70)
        return self.stats

    def _completeness_audit(self):
        conn = self._db_connect()
        dates = [r[0] for r in conn.execute(
            "SELECT observation_date FROM fits_metadata ORDER BY observation_date ASC"
        ).fetchall() if r[0]]
        conn.close()
        if not dates: self.stats["scientific_coverage"]=0.0; return
        unique = sorted(set(dates))
        try:
            s = datetime.strptime(unique[0],"%Y%m%d")
            e = datetime.strptime(unique[-1],"%Y%m%d")
            expected = (e-s).days+1
        except Exception: expected = len(unique)
        obs = len(unique)
        cov = float(obs/expected)*100 if expected > 0 else 100.0
        self.stats["scientific_coverage"] = cov
        logger.info(f"Coverage: expected={expected} observed={obs} {cov:.2f}%")

    def _generate_trust_certificate(self):
        sha = hashlib.sha256()
        with open(self.db_path,"rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""): sha.update(chunk)
        conn = self._db_connect()
        vc = conn.execute("SELECT COUNT(*) FROM downloads WHERE status='Verified'").fetchone()[0]
        fc = conn.execute("SELECT COUNT(*) FROM downloads WHERE status NOT IN ('Verified','Skipped')").fetchone()[0]
        conn.close()
        cert = {"trust_certificate":{
            "dataset_version":self.VERSION,"instrument":"HEL1OS",
            "pipeline_version":self.PIPELINE_VERSION,
            "total_urls_ingested":self.stats["total_urls"],
            "archives_downloaded":self.stats["downloaded"],
            "archives_verified":vc,"archives_failed":fc,
            "zip_failures":self.stats["zip_failures"],"fits_failures":self.stats["fits_failures"],
            "scientific_coverage_pct":self.stats["scientific_coverage"],
            "manifest_sha256":sha.hexdigest(),"cookie_hash":self.session_mgr.cookie_hash,
            "session_refreshes":self.session_mgr.session_refreshes,
            "network_interruptions":self.session_mgr.network_interruptions,
            "dns_failures":self.session_mgr.dns_failures,"total_retries":self.stats["total_retries"],
            "generated_at":datetime.now(timezone.utc).isoformat(),
        }}
        for p in [os.path.join(self.inventory_dir,"trust_certificate.json"),
                  "hel1os_trust_certificate.json",
                  "/Users/soumyadebtripathy/.gemini/antigravity/brain/c3fa7d09-8249-46c9-98a1-4faacc713a0e/hel1os_trust_certificate.json"]:
            try:
                with open(p,"w") as fh: json.dump(cert, fh, indent=4)
            except Exception: pass
        logger.info(f"Trust cert: {os.path.join(self.inventory_dir,'trust_certificate.json')}")

    def _generate_resilience_report(self):
        events_path = os.path.join(self.reports_dir, "network_events.json")
        events = []
        if os.path.exists(events_path):
            with open(events_path) as fh:
                for line in fh:
                    line=line.strip()
                    if line:
                        try: events.append(json.loads(line))
                        except Exception: pass
        te = len(events)
        rec = sum(1 for e in events if e.get("recovered"))
        bp  = sum(1 for e in events if "BrokenPipe" in e.get("failure_type",""))
        dns = sum(1 for e in events if any(k in e.get("failure_type","") for k in ["gaierror","NameResolution"]))
        tout= sum(1 for e in events if "Timeout" in e.get("failure_type",""))
        tr  = self.stats["total_retries"]
        sr  = self.session_mgr.session_refreshes
        ad  = self.session_mgr.total_downtime_seconds
        rp  = (rec/te*100) if te > 0 else 100.0
        ar  = tr / max(self.stats["downloaded"]+self.stats["still_failed"],1)
        md = [
            "# Network Resilience Report — Sprint DA-03C\n\n",
            f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')}\n",
            f"**Pipeline:** `{self.PIPELINE_VERSION}`\n\n",
            "## Transport Event Summary\n\n",
            "| Metric | Value |\n|---|---|\n",
            f"| Total transport events | {te} |\n",
            f"| Recovered automatically | {rec} |\n",
            f"| Recovery success rate | {rp:.1f}% |\n",
            f"| BrokenPipe events | {bp} |\n",
            f"| DNS failure events | {dns} |\n",
            f"| ReadTimeout events | {tout} |\n",
            f"| Total download retries | {tr} |\n",
            f"| Average retries per file | {ar:.2f} |\n\n",
            "## Session Health\n\n",
            "| Metric | Value |\n|---|---|\n",
            f"| Session refreshes | {sr} |\n",
            f"| Auth downtime (s) | {ad:.1f} |\n",
            f"| Network interruptions | {self.session_mgr.network_interruptions} |\n",
            f"| DNS failures | {self.session_mgr.dns_failures} |\n\n",
            "## Acquisition Summary\n\n",
            "| Metric | Value |\n|---|---|\n",
            f"| Downloaded & verified | {self.stats['downloaded']} |\n",
            f"| Skipped (pre-verified) | {self.stats['skipped']} |\n",
            f"| Still failed | {self.stats['still_failed']} |\n",
            f"| Scientific coverage | {self.stats['scientific_coverage']:.2f}% |\n",
            f"| Total elapsed | {self.stats['elapsed_time']:.1f}s |\n\n",
            "## DA-03C Hardening Applied\n\n",
            "- BrokenPipe → TCP reset + HTTP Range resume (no session invalidation)\n",
            "- ReadTimeout → Range resume, up to 8 retries\n",
            "- DNS failure → 2/5/10/20/30s backoff, no session invalidation\n",
            "- State machine: Healthy|NetworkInterrupted|TemporarilyUnavailable|Refreshing|Expired\n",
            "- Auth failures ONLY on confirmed HTTP login redirects\n",
            "- Worker isolation: per-worker consecutive failure counter\n",
        ]
        for p in [os.path.join(self.reports_dir,"network_resilience_report.md"),
                  "/Users/soumyadebtripathy/.gemini/antigravity/brain/c3fa7d09-8249-46c9-98a1-4faacc713a0e/network_resilience_report.md"]:
            try:
                with open(p,"w") as fh: fh.writelines(md)
            except Exception: pass
        logger.info(f"Resilience report: {os.path.join(self.reports_dir,'network_resilience_report.md')}")

    def _generate_summary_report(self):
        s = {
            "sprint":"DA-03C","dataset_version":self.VERSION,"instrument":"HEL1OS",
            "pipeline_version":self.PIPELINE_VERSION,"total_urls":self.stats["total_urls"],
            "downloaded":self.stats["downloaded"],"skipped":self.stats["skipped"],
            "still_failed":self.stats["still_failed"],"permanent_failures":self.stats["permanent_failures"],
            "zip_failures":self.stats["zip_failures"],"fits_failures":self.stats["fits_failures"],
            "elapsed_seconds":self.stats["elapsed_time"],
            "scientific_coverage_pct":self.stats["scientific_coverage"],
            "total_retries":self.stats["total_retries"],
            "network_interruptions":self.stats["network_interruptions"],
            "dns_failures":self.stats["dns_failures"],"auth_failures":self.stats["auth_failures"],
            "session_refreshes":self.session_mgr.session_refreshes,
            "generated_at":datetime.now(timezone.utc).isoformat(),
        }
        out = os.path.join(self.reports_dir,"hel1os_ingestion_summary.json")
        with open(out,"w") as fh: json.dump(s, fh, indent=4)

# ─── Final Assertions ─────────────────────────────────────────────────────────

def verify_and_assert(db_path):
    logger.info("Running final integrity assertions...")
    conn = sqlite3.connect(db_path)
    verified = conn.execute("SELECT path,filename FROM downloads WHERE status='Verified'").fetchall()
    zip_errors = []; html_errors = []
    for path, fn in verified:
        if not path or not os.path.exists(path): continue
        try:
            with zipfile.ZipFile(path) as zf:
                if zf.testzip() is not None: zip_errors.append(fn)
        except Exception: zip_errors.append(fn)
        try:
            with open(path,"rb") as fh:
                h = fh.read(512)
                if b"<!DOCTYPE html" in h or b"<html" in h: html_errors.append(fn)
        except Exception: pass
    dup_hashes = conn.execute(
        "SELECT checksum,COUNT(*) FROM downloads WHERE status='Verified' "
        "AND checksum IS NOT NULL AND checksum!='' "
        "GROUP BY checksum HAVING COUNT(*)>1"
    ).fetchall()
    conn.close()
    assert len(zip_errors)==0,  f"ZIP errors in verified: {zip_errors}"
    assert len(html_errors)==0, f"HTML in verified: {html_errors}"
    if dup_hashes: logger.warning(f"Duplicate checksums (multi-version files): {len(dup_hashes)} groups")
    logger.info("ALL INTEGRITY ASSERTIONS PASSED.")
    print("PASS")

# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Sprint DA-03C — HEL1OS Network-Resilient Downloader")
    p.add_argument("--config", default="data_pipeline/config.yaml")
    p.add_argument("--script", default="legacy/pradan_hel1os_fresh.sh")
    p.add_argument("--force",  action="store_true")
    args = p.parse_args()
    try:
        dl = Hel1osDownloader(args.config, args.script, args.force)
        dl.run()
        verify_and_assert(dl.db_path)
    except Exception as exc:
        logger.critical(f"Fatal: {exc}")
        logger.error("".join(_traceback.format_exception(*sys.exc_info())))
        print("FAIL"); sys.exit(1)
