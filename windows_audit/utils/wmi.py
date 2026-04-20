"""WMI/CIM query utilities."""
import logging
from typing import Any, Dict, List, Optional, Union

try:
    import win32com.client
    import pythoncom
    COM_AVAILABLE = True
except ImportError:
    COM_AVAILABLE = False

from .logging_utils import get_logger

logger = get_logger(__name__)


class WMIQuery:
    """Query WMI/CIM data on Windows."""
    
    _initialized = False
    
    def __init__(self, namespace: str = "root/cimv2"):
        """Initialize WMI query.
        
        Args:
            namespace: WMI namespace (default: root/cimv2)
        """
        self.namespace = namespace
        self._client = None
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize COM client."""
        if not COM_AVAILABLE:
            logger.warning("win32com.client not available - WMI queries will use fallback")
            return
        
        try:
            pythoncom.CoInitialize()
            self._client = win32com.client.Dispatch("WbemScripting.SWbemLocator")
            self._initialized = True
            logger.debug(f"WMI connected to namespace: {self.namespace}")
        except Exception as e:
            logger.error(f"Failed to initialize WMI: {e}")
            self._initialized = False
    
    def query(
        self,
        wql: str,
        props: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Execute a WQL query.
        
        Args:
            wql: WQL query string
            props: Optional list of properties to retrieve
            
        Returns:
            List of result dictionaries
        """
        if not self._initialized or not self._client:
            logger.warning("WMI not initialized - returning empty result")
            return []
        
        try:
            # Connect to WMI
            conn = self._client.ConnectServer(".", self.namespace)
            
            # Execute query
            results = conn.ExecQuery(wql)
            
            # Process results
            items = []
            for item in results:
                obj = {}
                try:
                    if props:
                        # Get specific properties
                        for prop in props:
                            try:
                                obj[prop] = getattr(item, prop, None)
                            except Exception:
                                obj[prop] = None
                    else:
                        # Get all properties
                        for prop in item.Properties_:
                            try:
                                obj[prop.Name] = prop.Value
                            except Exception:
                                pass
                except Exception as e:
                    logger.debug(f"Error processing WMI item: {e}")
                    continue
                
                items.append(obj)
            
            return items
            
        except Exception as e:
            logger.error(f"WMI query failed: {e}")
            return []
    
    def get_class(self, class_name: str) -> List[Dict[str, Any]]:
        """Get all instances of a WMI class.
        
        Args:
            class_name: WMI class name (e.g., Win32_OperatingSystem)
            
        Returns:
            List of instance dictionaries
        """
        return self.query(f"SELECT * FROM {class_name}")
    
    def close(self) -> None:
        """Close WMI connection."""
        if COM_AVAILABLE:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass


def get_wmi_data(
    class_name: str,
    namespace: str = "root/cimv2",
    props: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Convenience function to get WMI data.
    
    Args:
        class_name: WMI class name
        namespace: WMI namespace
        props: Properties to retrieve
        
    Returns:
        List of instance dictionaries
    """
    wmi = WMIQuery(namespace=namespace)
    try:
        return wmi.get_class(class_name, props=props)
    finally:
        wmi.close()