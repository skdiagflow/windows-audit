"""Installed Software Collector."""
import logging
import os
from typing import Any, Dict, List
from pathlib import Path

from ..utils import get_logger, read_registry, get_installed_software

logger = get_logger(__name__)


def get_software_collector() -> "SoftwareCollector":
    """Get SoftwareCollector instance."""
    return SoftwareCollector()


def run_software_collector(engine) -> Dict[str, Any]:
    """Run software collector (convenience function)."""
    collector = SoftwareCollector()
    return collector.collect(engine)


class SoftwareCollector:
    """Collects installed software information."""
    
    def __init__(self):
        self.name = "software"
        self.description = "Installed software from registry and PowerShell"
        self.requires_admin = False
    
    def collect(self, engine) -> Dict[str, Any]:
        """Collect installed software.
        
        Args:
            engine: AuditEngine instance
            
        Returns:
            Software information dictionary
        """
        logger.info("Collecting installed software...")
        
        data = {}
        
        # Get software from registry
        data["registry"] = self._get_from_registry()
        
        # Get software from PowerShell
        data["powershell"] = self._get_from_powershell(engine)
        
        # Combine and deduplicate
        data["all_software"] = self._combine_software(data)
        
        # Separate Microsoft vs third-party
        data["microsoft"] = self._filter_microsoft(data["all_software"])
        data["third_party"] = self._filter_third_party(data["all_software"])
        
        logger.info(f"Software collected: {len(data.get('all_software', []))} programs")
        return data
    
    def _get_from_registry(self) -> List[Dict[str, Any]]:
        """Get installed software from registry."""
        software = []
        
        # Registry paths to check
        uninstall_paths = [
            ("HKLM", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            ("HKLM", r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            ("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]
        
        for hive, path in uninstall_paths:
            try:
                subkeys = read_registry(hive, path)
                if not subkeys:
                    continue
                    
                # Get subkeys (folders) under each path - need to iterate differently
                # Using registry directly
                from ..utils import RegistryReader
                reader = RegistryReader()
                
                subkey_names = reader.read_subkeys(hive, path)
                
                for subkey in subkey_names:
                    full_path = f"{path}\\{subkey}"
                    values = reader.read_values(hive, full_path)
                    
                    if values.get("DisplayName"):
                        software.append({
                            "name": values.get("DisplayName"),
                            "version": values.get("DisplayVersion"),
                            "publisher": values.get("Publisher"),
                            "install_date": values.get("InstallDate"),
                            "install_location": values.get("InstallLocation"),
                            "uninstall_string": values.get("UninstallString"),
                            "display_icon": values.get("DisplayIcon"),
                            "url_info": values.get("URLInfoAbout"),
                            "source": f"{hive}\\{path}",
                        })
                
                reader.close()
                
            except Exception as e:
                logger.debug(f"Registry path {hive}\\{path}: {e}")
        
        return software
    
    def _get_from_powershell(self, engine) -> List[Dict[str, Any]]:
        """Get installed software from PowerShell."""
        software = []
        
        try:
            # Try Get-Package cmdlet
            cmd = "Get-Package | Select-Object Name, Version, Provider, Source | ConvertTo-Json"
            result = engine.ps.run(cmd, json_output=True)
            
            if isinstance(result, list):
                for item in result:
                    software.append({
                        "name": item.get("Name"),
                        "version": item.get("Version"),
                        "provider": item.get("Provider"),
                        "source": item.get("Source"),
                    })
            elif isinstance(result, dict):
                # Single item
                software.append({
                    "name": result.get("Name"),
                    "version": result.get("Version"),
                })
                
        except Exception as e:
            logger.debug(f"PowerShell Get-Package failed: {e}")
        
        return software
    
    def _combine_software(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Combine and deduplicate software lists."""
        combined = {}
        
        # Add registry software
        for item in data.get("registry", []):
            name = item.get("name", "")
            if name and name not in combined:
                combined[name] = item
        
        # Add PowerShell software
        for item in data.get("powershell", []):
            name = item.get("name", "")
            if name and name not in combined:
                combined[name] = item
        
        return list(combined.values())
    
    def _filter_microsoft(self, software: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter Microsoft software."""
        microsoft = []
        
        microsoft_keywords = [
            "microsoft", "msdn", "visual studio", 
            ".net", "windows", "office"
        ]
        
        for item in software:
            name = item.get("name", "").lower()
            publisher = item.get("publisher", "").lower()
            
            if any(kw in name or kw in publisher for kw in microsoft_keywords):
                microsoft.append(item)
        
        return microsoft
    
    def _filter_third_party(self, software: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter third-party (non-Microsoft) software."""
        microsoft_keywords = [
            "microsoft", "msdn", "visual studio",
            ".net", "windows", "office"
        ]
        
        third_party = []
        
        for item in software:
            name = item.get("name", "").lower()
            publisher = item.get("publisher", "").lower()
            
            if not any(kw in name or kw in publisher for kw in microsoft_keywords):
                third_party.append(item)
        
        return third_party