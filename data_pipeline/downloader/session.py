import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from data_pipeline.downloader.logger import logger

class PradanSession:
    def __init__(self, cookie_str: str, base_url: str, retry_count: int = 5, timeout: int = 30):
        self.cookie_str = cookie_str
        self.base_url = base_url
        self.timeout = timeout
        self.retry_count = retry_count
        self.session = None
        self._last_refresh = 0.0
        self._refresh_interval = 600.0  # Refresh session every 10 minutes
        self._init_session()

    def _init_session(self):
        self.session = requests.Session()
        
        # Parse cookies from raw cookie string
        cookies = {}
        for part in self.cookie_str.split(';'):
            if '=' in part:
                name, val = part.strip().split('=', 1)
                cookies[name] = val
        self.session.cookies.update(cookies)
        
        # Configure robust retry strategy with backoff
        retry_strategy = Retry(
            total=self.retry_count,
            backoff_factor=1.5,  # exponential backoff: 1.5, 3.0, 4.5, ...
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            raise_on_status=False
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        # Set standard headers to look like a browser session
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": f"{self.base_url}/al1/protected/payload.xhtml",
            "Connection": "keep-alive"
        })
        self._keep_alive()

    def _keep_alive(self):
        """Pings the payload page to refresh the session and keep it alive."""
        url = f"{self.base_url}/al1/protected/payload.xhtml"
        try:
            logger.info("Sending session keep-alive/refresh ping...")
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code == 200:
                logger.info("Session keep-alive successful.")
                self._last_refresh = time.time()
            else:
                logger.warning(f"Session keep-alive returned status code {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to refresh session: {e}")

    def get(self, path: str, stream: bool = True, headers: dict = None) -> requests.Response:
        """Sends a GET request. Handles keep-alive check and automatic session reset on timeout."""
        # Check if session needs keep-alive refresh
        if time.time() - self._last_refresh > self._refresh_interval:
            self._keep_alive()
            
        url = f"{self.base_url}{path}" if path.startswith('/') else path
        
        for attempt in range(self.retry_count):
            try:
                response = self.session.get(url, stream=stream, timeout=self.timeout, headers=headers)
                return response
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                logger.warning(f"Connection error on attempt {attempt+1}/{self.retry_count}: {e}")
                if attempt == self.retry_count - 1:
                    raise
                # Re-initialize session on connection loss
                logger.info("Re-initializing session for reconnection...")
                self._init_session()
                time.sleep(2 ** attempt)

    def head(self, path: str) -> requests.Response:
        """Sends a HEAD request with connection recovery."""
        url = f"{self.base_url}{path}" if path.startswith('/') else path
        
        for attempt in range(self.retry_count):
            try:
                response = self.session.head(url, timeout=self.timeout)
                return response
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                logger.warning(f"Connection error on head attempt {attempt+1}/{self.retry_count}: {e}")
                if attempt == self.retry_count - 1:
                    raise
                self._init_session()
                time.sleep(2 ** attempt)
