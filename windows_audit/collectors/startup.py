"""Startup Programs Collector."""
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

from ..utils import get_logger, read_registry

logger = get_logger(__name__)


def get_startup_collector() -> "StartupCollector":
    """Get StartupCollector instance."""
    return StartupCollector()


def run_startup_collector(engine) -> Dict[str, Any]:
    """Run startup collector (convenience function)."""
    collector = StartupCollector()
    return collector.collect(engine)


class StartupCollector:
    """Collects startup programs and services."""
    
    def __init__(self):
        self.name = "startup"
        self.description = "Startup programs from registry and folders"
        self.requires_admin = False
    
    def collect(self, engine) -> Dict[str, Any]:
        """Collect startup information.
        
        Args:
            engine: AuditEngine instance
            
        Returns:
            Startup information dictionary
        """
        logger.info("Collecting startup programs...")
        
        data = {}
        
        # Get registry startup items
        data["registry"] = self._get_registry_startup()
        
        # Get startup folder items
        data["folders"] = self._get_folder_startup()
        
        # Combine
        data["all_items"] = data.get("registry", []) + data.get("folders", [])
        
        # Summary
        data["summary"] = self._get_summary(data["all_items"])
        
        logger.info(f"Startup items collected: {len(data['all_items'])}")
        return data
    
    def _get_registry_startup(self) -> List[Dict[str, Any]]:
        """Get startup items from registry."""
        items = []
        
        # Registry paths for startup
        registry_paths = [
            ("HKLM", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
            ("HKLM", r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"),
            ("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
            ("HKCU", r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"),
            ("HKLM", r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"),
            ("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"),
        ]
        
        for hive, path in registry_paths:
            try:
                from ..utils import RegistryReader
                reader = RegistryReader()
                
                values = reader.read_values(hive, path)
                
                for name, value in values.items():
                    items.append({
                        "name": name,
                        "command": value,
                        "source": f"{hive}\\{path}",
                        "type": "registry",
                    })
                
                reader.close()
                
            except Exception as e:
                logger.debug(f"Registry startup path {hive}\\{path}: {e}")
        
        return items
    
    def _get_folder_startup(self) -> List[Dict[str, Any]]:
        """Get startup items from startup folders."""
        items = []
        
        # Startup folders
        startup_folders = [
            os.path.join(os.environ.get("APPDATA", ""), "Microsoft\\Windows\\Start Menu\\Programs\\Startup"),
            os.path.join(os.environ.get("PROGRAMDATA", ""), "Microsoft\\Windows\\Start Menu\\Programs\\Startup"),
        ]
        
        for folder in startup_folders:
            if not folder or not os.path.exists(folder):
                continue
            
            try:
                for file in os.listdir(folder):
                    file_path = os.path.join(folder, file)
                    
                    if os.path.isfile(file_path):
                        items.append({
                            "name": file,
                            "path": file_path,
                            "source": folder,
                            "type": "folder",
                        })
                        
            except Exception as e:
                logger.debug(f"Startup folder {folder}: {e}")
        
        return items
    
    def _get_summary(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get startup summary."""
        return {
            "total": len(items),
            "registry": sum(1 for i in items if i.get("type") == "registry"),
            "folder": sum(1 for i in items if i.get("type") == "folder"),
        }