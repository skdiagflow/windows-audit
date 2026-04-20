"""Windows registry reading utilities."""
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import winreg
    REG_AVAILABLE = True
except ImportError:
    # Fallback for non-Windows
    REG_AVAILABLE = False

from .logging_utils import get_logger

logger = get_logger(__name__)

# Registry hives
HKEY_LOCAL_MACHINE = "HKLM"
HKEY_CURRENT_USER = "HKCU"
HKEY_CLASSES_ROOT = "HKCR"
HKEY_USERS = "HKU"
HKEY_CURRENT_CONFIG = "HKCC"

# Common registry paths
REGISTRY_PATHS = {
    "uninstall_64": r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
    "uninstall_32": r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
    "run_64": r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
    "run_32": r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run",
    "run_current_user": r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
    "startup_folder": r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run",
    # Software paths
    "software_64": r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths",
    "software_32": r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths",
    # Chrome browser paths
    "chrome_extensions": r"SOFTWARE\Google\Chrome\Extensions",
    "chrome_preferences": r"SOFTWARE\Google\Chrome\Preferences",
    # Firefox paths
    "firefox": r"SOFTWARE\Mozilla\Firefox",
    # Edge paths
    "edge": r"SOFTWARE\Microsoft\Edge\Extensions",
}


class RegistryReader:
    """Read Windows registry values."""
    
    def __init__(self):
        """Initialize registry reader."""
        self._hives = {}
    
    def _get_hive(self, hive: str):
        """Get a registry hive handle."""
        if not REG_AVAILABLE:
            raise RuntimeError("Registry not available on this platform")
        
        hive_map = {
            "HKLM": winreg.HKEY_LOCAL_MACHINE,
            "HKCU": winreg.HKEY_CURRENT_USER,
            "HKCR": winreg.HKEY_CLASSES_ROOT,
            "HKU": winreg.HKEY_USERS,
            "HKCC": winreg.HKEY_CURRENT_CONFIG,
        }
        
        if hive in self._hives:
            return self._hives[hive]
        
        if hive not in hive_map:
            raise ValueError(f"Unknown registry hive: {hive}")
        
        try:
            self._hives[hive] = winreg.OpenKey(hive_map[hive], "")
            return self._hives[hive]
        except WindowsError as e:
            logger.error(f"Failed to open registry hive {hive}: {e}")
            raise
    
    def read_value(
        self,
        hive: str,
        path: str,
        value_name: str
    ) -> Optional[Any]:
        """Read a single registry value.
        
        Args:
            hive: Registry hive (e.g., "HKLM")
            path: Registry path
            value_name: Name of the value to read
            
        Returns:
            Registry value or None if not found
        """
        if not REG_AVAILABLE:
            return None
        
        try:
            hive_key = self._get_hive(hive)
            key = winreg.OpenKey(hive_key, path)
            try:
                value, _ = winreg.QueryValueEx(key, value_name)
                return value
            finally:
                winreg.CloseKey(key)
        except WindowsError as e:
            logger.debug(f"Registry value not found: {hive}\\{path}\\{value_name}: {e}")
            return None
    
    def read_values(
        self,
        hive: str,
        path: str
    ) -> Dict[str, Any]:
        """Read all values in a registry key.
        
        Args:
            hive: Registry hive
            path: Registry path
            
        Returns:
            Dictionary of value names to values
        """
        if not REG_AVAILABLE:
            return {}
        
        try:
            hive_key = self._get_hive(hive)
            key = winreg.OpenKey(hive_key, path)
            try:
                values = {}
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        values[name] = value
                        i += 1
                    except OSError:
                        break
                return values
            finally:
                winreg.CloseKey(key)
        except WindowsError as e:
            logger.debug(f"Registry key not found: {hive}\\{path}: {e}")
            return {}
    
    def read_subkeys(
        self,
        hive: str,
        path: str
    ) -> List[str]:
        """List subkeys in a registry key.
        
        Args:
            hive: Registry hive
            path: Registry path
            
        Returns:
            List of subkey names
        """
        if not REG_AVAILABLE:
            return []
        
        try:
            hive_key = self._get_hive(hive)
            key = winreg.OpenKey(hive_key, path)
            try:
                subkeys = []
                i = 0
                while True:
                    try:
                        name = winreg.EnumKey(key, i)
                        subkeys.append(name)
                        i += 1
                    except OSError:
                        break
                return subkeys
            finally:
                winreg.CloseKey(key)
        except WindowsError as e:
            logger.debug(f"Registry key not found: {hive}\\{path}: {e}")
            return []
    
    def close(self) -> None:
        """Close all registry handles."""
        for key in self._hives.values():
            try:
                winreg.CloseKey(key)
            except Exception:
                pass
        self._hives.clear()


def read_registry(
    hive: str,
    path: str,
    value_name: Optional[str] = None
) -> Union[Any, Dict[str, Any], List[str]]:
    """Convenience function to read registry values.
    
    Args:
        hive: Registry hive (e.g., "HKLM")
        path: Registry path
        value_name: Specific value name, or None for all values
        
    Returns:
        Registry value(s)
    """
    reader = RegistryReader()
    try:
        if value_name:
            return reader.read_value(hive, path, value_name)
        else:
            return reader.read_values(hive, path)
    finally:
        reader.close()


def get_installed_software() -> List[Dict[str, Any]]:
    """Get installed software from registry.
    
    Returns:
        List of installed software dictionaries
    """
    reader = RegistryReader()
    software = []
    
    # Registry paths to check
    uninstall_paths = [
        (HKEY_LOCAL_MACHINE, REGISTRY_PATHS["uninstall_64"]),
        (HKEY_LOCAL_MACHINE, REGISTRY_PATHS["uninstall_32"]),
        (HKEY_CURRENT_USER, REGISTRY_PATHS["uninstall_64"]),
    ]
    
    for hive, path in uninstall_paths:
        subkeys = reader.read_subkeys(hive, path)
        
        for subkey in subkeys:
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
                    "source": f"{hive}\\{path}",
                })
    
    reader.close()
    return software