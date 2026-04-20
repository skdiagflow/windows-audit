"""Base collector class for audit modules."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import logging

from ..utils import get_logger

logger = get_logger(__name__)


class Collector(ABC):
    """Abstract base class for all collector modules."""
    
    def __init__(
        self,
        name: str,
        description: str = "",
        enabled: bool = True,
        requires_admin: bool = False,
        dependencies: Optional[List[str]] = None
    ):
        """Initialize collector.
        
        Args:
            name: Unique name for the collector
            description: Description of what this collector gathers
            enabled: Whether the collector is enabled by default
            requires_admin: Whether admin privileges are required
            dependencies: List of other collectors that must run first
        """
        self.name = name
        self.description = description
        self.enabled = enabled
        self.requires_admin = requires_admin
        self.dependencies = dependencies or []
        
        # Collection results
        self._data: Dict[str, Any] = {}
        self._errors: List[str] = []
    
    @abstractmethod
    def collect(self, engine: "AuditEngine") -> Dict[str, Any]:
        """Collect data using the provided engine.
        
        Args:
            engine: AuditEngine instance
            
        Returns:
            Collected data as a dictionary
        """
        pass
    
    def validate(self) -> bool:
        """Validate that the collector can run.
        
        Returns:
            True if validation passes
        """
        # Base implementation - always valid
        return True
    
    def get_data(self) -> Dict[str, Any]:
        """Get collected data.
        
        Returns:
            Collected data dictionary
        """
        return self._data
    
    def get_errors(self) -> List[str]:
        """Get list of errors encountered during collection.
        
        Returns:
            List of error messages
        """
        return self._errors
    
    def add_error(self, error: str) -> None:
        """Add an error message.
        
        Args:
            error: Error message to add
        """
        self._errors.append(error)
        logger.warning(f"{self.name}: {error}")
    
    def add_data(self, key: str, value: Any) -> None:
        """Add data to the collection.
        
        Args:
            key: Data key
            value: Data value
        """
        self._data[key] = value
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<Collector: {self.name}>"


class SystemInfoCollector(Collector):
    """Specialized collector for system information."""
    
    def collect(self, engine: "AuditEngine") -> Dict[str, Any]:
        """Collect system information.
        
        Args:
            engine: AuditEngine instance
            
        Returns:
            System information dictionary
        """
        # Default implementation - should be overridden
        return {"name": self.name, "data": {}}