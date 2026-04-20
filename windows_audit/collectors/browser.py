"""Browser Data Collector."""
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

from ..utils import get_logger

logger = get_logger(__name__)


def get_browser_collector() -> "BrowserCollector":
    """Get BrowserCollector instance."""
    return BrowserCollector()


def run_browser_collector(engine) -> Dict[str, Any]:
    """Run browser collector (convenience function)."""
    collector = BrowserCollector()
    return collector.collect(engine)


class BrowserCollector:
    """Collects browser data (bookmarks, history, extensions)."""
    
    def __init__(self):
        self.name = "browser"
        self.description = "Browser data, bookmarks, extensions"
        self.requires_admin = False
    
    def collect(self, engine) -> Dict[str, Any]:
        """Collect browser information.
        
        Args:
            engine: AuditEngine instance
            
        Returns:
            Browser information dictionary
        """
        logger.info("Collecting browser data...")
        
        data = {}
        
        # Detect browsers
        data["detected_browsers"] = self._detect_browsers()
        
        # Get Chrome data
        data["chrome"] = self._get_chrome_data()
        
        # Get Firefox data
        data["firefox"] = self._get_firefox_data()
        
        # Get Edge data
        data["edge"] = self._get_edge_data()
        
        # Get Brave data
        data["brave"] = self._get_brave_data()
        
        # Consolidate bookmarks
        data["all_bookmarks"] = self._consolidate_bookmarks(data)
        
        # Summary
        data["summary"] = self._get_summary(data)
        
        logger.info(f"Browser data collected: {len(data['detected_browsers'])} browsers")
        return data
    
    def _detect_browsers(self) -> List[Dict[str, Any]]:
        """Detect installed browsers."""
        browsers = []
        
        # Map browser names to their registry/app paths
        browser_configs = {
            "Chrome": {
                "path": r"SOFTWARE\Google\Chrome\BLBeacon",
                "key": "version",
                "exe": "chrome.exe",
            },
            "Firefox": {
                "path": r"SOFTWARE\Mozilla\Mozilla Firefox",
                "key": "CurrentVersion",
                "exe": "firefox.exe",
            },
            "Edge": {
                "path": r"SOFTWARE\Microsoft\Edge\BLBeacon",
                "key": "version",
                "exe": "msedge.exe",
            },
            "Brave": {
                "path": r"SOFTWARE\BraveSoftware\Brave-Browser\BLBeacon",
                "key": "version",
                "exe": "brave.exe",
            },
            "Opera": {
                "path": r"SOFTWARE\Opera Software\Opera Stable",
                "key": "Version",
                "exe": "opera.exe",
            },
        }
        
        from ..utils import RegistryReader
        reader = RegistryReader()
        
        for name, config in browser_configs.items():
            try:
                # Check HKLM and HKCU
                for hive in ["HKLM", "HKCU"]:
                    version = reader.read_value(
                        hive, 
                        config["path"], 
                        config["key"]
                    )
                    if version:
                        browsers.append({
                            "name": name,
                            "version": str(version),
                            "exe": config["exe"],
                        })
                        break
            except Exception as e:
                logger.debug(f"Browser {name} detection failed: {e}")
        
        reader.close()
        return browsers
    
    def _get_chrome_data(self) -> Dict[str, Any]:
        """Get Chrome browser data."""
        data = {"bookmarks": [], "extensions": [], "history": []}
        
        # Chrome paths
        base_path = os.path.join(
            os.environ.get("LOCALAPPDATA", ""),
            "Google\\Chrome\\User Data\\Default"
        )
        
        if not os.path.exists(base_path):
            return data
        
        # Parse bookmarks
        bookmark_path = os.path.join(base_path, "Bookmarks")
        if os.path.exists(bookmark_path):
            try:
                with open(bookmark_path, "r", encoding="utf-8") as f:
                    bookmarks = json.load(f)
                    data["bookmarks"] = self._parse_chrome_bookmarks(
                        bookmarks.get("roots", {})
                    )
            except Exception as e:
                logger.debug(f"Chrome bookmarks parse failed: {e}")
        
        # Get extensions
        extension_path = os.path.join(base_path, "Extensions")
        if os.path.exists(extension_path):
            try:
                for ext in os.listdir(extension_path):
                    ext_path = os.path.join(extension_path, ext)
                    if os.path.isdir(ext_path):
                        # Get latest version folder
                        versions = os.listdir(ext_path)
                        if versions:
                            manifest_path = os.path.join(
                                ext_path, 
                                versions[-1], 
                                "manifest.json"
                            )
                            if os.path.exists(manifest_path):
                                try:
                                    with open(manifest_path, "r") as f:
                                        manifest = json.load(f)
                                        data["extensions"].append({
                                            "id": ext,
                                            "name": manifest.get("name", ""),
                                            "version": manifest.get("version", ""),
                                        })
                                except:
                                    pass
            except Exception as e:
                logger.debug(f"Chrome extensions parse failed: {e}")
        
        return data
    
    def _parse_chrome_bookmarks(self, roots: Dict) -> List[Dict[str, Any]]:
        """Parse Chrome bookmark structure."""
        bookmarks = []
        
        for folder_type in ["bookmark_bar", "other", "synced"]:
            folder = roots.get(folder_type, {})
            if folder:
                bookmarks.extend(self._extract_chrome_bookmark_items(folder))
        
        return bookmarks
    
    def _extract_chrome_bookmark_items(self, folder: Dict) -> List[Dict[str, Any]]:
        """Extract bookmark items recursively."""
        items = []
        
        for child in folder.get("children", []):
            if child.get("type") == "url":
                items.append({
                    "name": child.get("name"),
                    "url": child.get("url"),
                })
            elif child.get("type") == "folder":
                items.extend(self._extract_chrome_bookmark_items(child))
        
        return items
    
    def _get_firefox_data(self) -> Dict[str, Any]:
        """Get Firefox browser data."""
        data = {"bookmarks": [], "extensions": [], "history": []}
        
        # Firefox profile paths
        ff_base = os.path.join(
            os.environ.get("APPDATA", ""),
            "Mozilla\\Firefox\\Profiles"
        )
        
        if not os.path.exists(ff_base):
            return data
        
        # Find default profile
        try:
            profiles = os.listdir(ff_base)
            if not profiles:
                return data
            
            profile_path = os.path.join(ff_base, profiles[0])
            
            # Parse places.sqlite would require sqlite3 - simplified for now
            # Try to get places.sqlite for history
            places_path = os.path.join(profile_path, "places.sqlite")
            if os.path.exists(places_path):
                data["has_places"] = True
                
        except Exception as e:
            logger.debug(f"Firefox data parse failed: {e}")
        
        return data
    
    def _get_edge_data(self) -> Dict[str, Any]:
        """Get Microsoft Edge browser data."""
        data = {"bookmarks": [], "extensions": [], "history": []}
        
        # Edge paths
        base_path = os.path.join(
            os.environ.get("LOCALAPPDATA", ""),
            "Microsoft\\Edge\\User Data\\Default"
        )
        
        if not os.path.exists(base_path):
            return data
        
        # Parse bookmarks (similar to Chrome)
        bookmark_path = os.path.join(base_path, "Bookmarks")
        if os.path.exists(bookmark_path):
            try:
                with open(bookmark_path, "r", encoding="utf-8") as f:
                    bookmarks = json.load(f)
                    data["bookmarks"] = self._parse_chrome_bookmarks(
                        bookmarks.get("roots", {})
                    )
            except Exception as e:
                logger.debug(f"Edge bookmarks parse failed: {e}")
        
        return data
    
    def _get_brave_data(self) -> Dict[str, Any]:
        """Get Brave browser data."""
        data = {"bookmarks": [], "extensions": [], "history": []}
        
        # Brave uses similar structure to Chrome
        base_path = os.path.join(
            os.environ.get("LOCALAPPDATA", ""),
            "BraveSoftware\\Brave-Browser\\User Data\\Default"
        )
        
        if not os.path.exists(base_path):
            return data
        
        bookmark_path = os.path.join(base_path, "Bookmarks")
        if os.path.exists(bookmark_path):
            try:
                with open(bookmark_path, "r", encoding="utf-8") as f:
                    bookmarks = json.load(f)
                    data["bookmarks"] = self._parse_chrome_bookmarks(
                        bookmarks.get("roots", {})
                    )
            except Exception as e:
                logger.debug(f"Brave bookmarks parse failed: {e}")
        
        return data
    
    def _consolidate_bookmarks(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Consolidate bookmarks from all browsers."""
        all_bookmarks = []
        
        # Add from each browser
        browser_bookmarks = {
            "Chrome": data.get("chrome", {}).get("bookmarks", []),
            "Firefox": data.get("firefox", {}).get("bookmarks", []),
            "Edge": data.get("edge", {}).get("bookmarks", []),
            "Brave": data.get("brave", {}).get("bookmarks", []),
        }
        
        for browser, bookmarks_list in browser_bookmarks.items():
            for bookmark in bookmarks_list:
                bookmark["browser"] = browser
                # Deduplicate by URL
                if not any(
                    b.get("url") == bookmark.get("url") 
                    for b in all_bookmarks
                ):
                    all_bookmarks.append(bookmark)
        
        return all_bookmarks
    
    def _get_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get browser summary."""
        return {
            "browsers_detected": len(data.get("detected_browsers", [])),
            "total_bookmarks": len(data.get("all_bookmarks", [])),
            "chrome_extensions": len(data.get("chrome", {}).get("extensions", [])),
        }