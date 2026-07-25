import os
from typing import Dict, Any
from data_pipeline.plugins.base import BasePayloadPlugin

class SdoPayloadPlugin(BasePayloadPlugin):
    @property
    def name(self) -> str:
        return "sdo"

    def match_url(self, url: str) -> bool:
        return "sdo" in url.lower() or "jsoc" in url.lower()

    def verify(self, file_path: str) -> bool:
        return os.path.exists(file_path) and os.path.getsize(file_path) > 0

    def check_quality(self, file_path: str) -> Dict[str, Any]:
        return {"valid": True, "errors": [], "nan_percentage": 0.0}

    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        return {
            "instrument": "sdo_aia",
            "observation_date": "",
            "cadence": 12.0,
            "num_rows": 0,
            "start_time": "",
            "end_time": "",
            "energy_channels": "[]",
            "missing_percentage": 0.0
        }
