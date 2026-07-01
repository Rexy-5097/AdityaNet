import os
import shutil
import zipfile
import importlib
import inspect
from typing import Dict, Any, Tuple, Optional
from data_pipeline.downloader.logger import logger
from data_pipeline.plugins.base import BasePayloadPlugin

class QualityInspector:
    def __init__(self, corrupted_dir: str):
        self.corrupted_dir = corrupted_dir
        self.plugins = self._discover_plugins()
        os.makedirs(corrupted_dir, exist_ok=True)
        logger.info(f"Discovered {len(self.plugins)} payload plugins: {[p.name for p in self.plugins]}")

    def _discover_plugins(self) -> list:
        plugins = []
        # Construct absolute path to the plugins directory
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        plugins_dir = os.path.join(current_dir, "plugins")
        
        if not os.path.exists(plugins_dir):
            return plugins
            
        for filename in os.listdir(plugins_dir):
            if filename.endswith(".py") and filename not in ("__init__.py", "base.py"):
                module_name = f"data_pipeline.plugins.{filename[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and issubclass(obj, BasePayloadPlugin) and obj is not BasePayloadPlugin:
                            plugins.append(obj())
                except Exception as e:
                    logger.error(f"Failed to load plugin from {filename}: {e}")
        return plugins

    def get_plugin(self, identifier: str) -> Optional[BasePayloadPlugin]:
        """Finds a plugin matching the URL path or filename."""
        for plugin in self.plugins:
            if plugin.match_url(identifier):
                return plugin
        return None

    def verify_archive(self, file_path: str, url_identifier: str) -> Tuple[bool, str]:
        """
        Verifies ZIP integrity and delegates scientific structure check to the matched payload plugin.
        Quarantines bad files to downloads/corrupted/.
        """
        if not os.path.exists(file_path):
            return False, f"File does not exist: {file_path}"
            
        filename = os.path.basename(file_path)
        
        # Step 1: Check if ZIP is corrupt or empty
        if os.path.getsize(file_path) == 0:
            self._quarantine(file_path)
            return False, "Empty archive file."
            
        try:
            with zipfile.ZipFile(file_path) as zf:
                if zf.testzip() is not None:
                    self._quarantine(file_path)
                    return False, "Corrupted ZIP archive (failed testzip)."
        except zipfile.BadZipFile as e:
            self._quarantine(file_path)
            return False, f"Invalid ZIP file structure: {e}"

        # Step 2: Match plugin and verify scientific HDU structure
        plugin = self.get_plugin(url_identifier or filename)
        if not plugin:
            # Fallback to simple ZIP check if no matching plugin is found
            logger.warning(f"No specific payload plugin found for {filename}. Defaulting to ZIP-only check.")
            return True, "Verified (ZIP only, no plugin matched)."

        if not plugin.verify(file_path):
            self._quarantine(file_path)
            return False, f"Failed scientific HDU structure validation via plugin '{plugin.name}'."

        return True, "Success"

    def run_quality_check(self, file_path: str, url_identifier: str) -> Dict[str, Any]:
        """Delegates detailed scientific data quality validation checks to the payload plugin."""
        filename = os.path.basename(file_path)
        plugin = self.get_plugin(url_identifier or filename)
        
        if not plugin:
            return {"valid": True, "errors": ["No plugin matched. Skipping scientific quality checks."], "nan_percentage": 0.0}
            
        logger.info(f"Running data quality check for {filename} using plugin '{plugin.name}'...")
        return plugin.check_quality(file_path)

    def extract_metadata(self, file_path: str, url_identifier: str) -> Dict[str, Any]:
        """Extracts scientific telemetry metadata using the payload plugin."""
        filename = os.path.basename(file_path)
        plugin = self.get_plugin(url_identifier or filename)
        
        if not plugin:
            return {
                "instrument": "unknown",
                "observation_date": "",
                "cadence": 0.0,
                "num_rows": 0,
                "start_time": "",
                "end_time": "",
                "energy_channels": "[]",
                "missing_percentage": 0.0
            }
            
        return plugin.extract_metadata(file_path)

    def _quarantine(self, file_path: str):
        """Moves a corrupted file into the quarantined directory."""
        filename = os.path.basename(file_path)
        dest_path = os.path.join(self.corrupted_dir, filename)
        logger.warning(f"Quarantining corrupted file {filename} -> {self.corrupted_dir}")
        try:
            shutil.move(file_path, dest_path)
        except Exception as e:
            logger.error(f"Failed to quarantine corrupted file {file_path} to {dest_path}: {e}")
            try:
                os.remove(file_path)
            except Exception:
                pass
