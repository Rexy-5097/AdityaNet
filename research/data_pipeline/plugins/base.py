from abc import ABC, abstractmethod
from typing import Dict, Any

class BasePayloadPlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the payload plugin (e.g., 'solexs', 'hel1os')."""
        pass

    @abstractmethod
    def match_url(self, url: str) -> bool:
        """Returns True if this plugin handles the given URL/filename."""
        pass

    @abstractmethod
    def verify(self, file_path: str) -> bool:
        """Verifies ZIP and raw scientific data structure integrity."""
        pass

    @abstractmethod
    def check_quality(self, file_path: str) -> Dict[str, Any]:
        """Runs scientific data quality validation checks (NaNs, continuity, duplicates, etc.)."""
        pass

    @abstractmethod
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extracts scientific telemetry metadata from the file."""
        pass
