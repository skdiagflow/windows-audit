"""Core Audit Engine for Windows Audit Suite."""
import logging
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .utils import get_logger, PowerShellExecutor, WMIQuery, RegistryReader

logger = get_logger(__name__)


class AuditEngine:
    """Core audit engine that orchestrates data collection."""
    
    def __init__(
        self,
        verbose: bool = False,
        cache_enabled: bool = True,
        parallel_execution: bool = True,
        max_workers: int = 4
    ):
        """Initialize the audit engine.
        
        Args:
            verbose: Enable verbose logging
            cache_enabled: Enable result caching
            parallel_execution: Enable parallel module execution
            max_workers: Maximum parallel workers
        """
        self.verbose = verbose
        self.cache_enabled = cache_enabled
        self.parallel_execution = parallel_execution
        self.max_workers = max_workers
        
        # Core components
        self.ps = PowerShellExecutor()
        self.wmi = WMIQuery()
        self.registry = RegistryReader()
        
        # Cache for results
        self._cache: Dict[str, Any] = {}
        
        # Collected data
        self.data: Dict[str, Any] = {}
        
        logger.info("AuditEngine initialized")
    
    def run_collector(
        self,
        collector: "Collector",
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Run a single collector module.
        
        Args:
            collector: Collector module instance
            use_cache: Use cached results if available
            
        Returns:
            Collected data dictionary
        """
        collector_name = collector.name
        logger.info(f"Running collector: {collector_name}")
        
        # Check cache
        if use_cache and self.cache_enabled and collector_name in self._cache:
            logger.debug(f"Using cached data for {collector_name}")
            return self._cache[collector_name]
        
        # Execute collector
        try:
            result = collector.collect(self)
            
            # Cache result
            if self.cache_enabled:
                self._cache[collector_name] = result
            
            # Store in data
            self.data[collector_name] = result
            
            logger.info(f"Collector {collector_name} completed: {len(result)} items")
            return result
            
        except Exception as e:
            logger.error(f"Collector {collector_name} failed: {e}")
            raise
    
    def run_collectors(
        self,
        collectors: List["Collector"],
        use_cache: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """Run multiple collector modules.
        
        Args:
            collectors: List of collector module instances
            use_cache: Use cached results if available
            
        Returns:
            Dictionary mapping collector names to their data
        """
        results = {}
        
        if self.parallel_execution and len(collectors) > 1:
            # Parallel execution
            logger.info(f"Running {len(collectors)} collectors in parallel")
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_collector = {
                    executor.submit(self.run_collector, c, use_cache): c
                    for c in collectors
                }
                
                for future in as_completed(future_to_collector):
                    collector = future_to_collector[future]
                    try:
                        results[collector.name] = future.result()
                    except Exception as e:
                        logger.error(f"Collector {collector.name} failed: {e}")
                        results[collector.name] = {"error": str(e)}
        else:
            # Sequential execution
            logger.info(f"Running {len(collectors)} collectors sequentially")
            
            for collector in collectors:
                try:
                    results[collector.name] = self.run_collector(collector, use_cache)
                except Exception as e:
                    logger.error(f"Collector {collector.name} failed: {e}")
                    results[collector.name] = {"error": str(e)}
        
        return results
    
    def run_all(
        self,
        collectors: List["Collector"],
        use_cache: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """Run all collector modules and compile results.
        
        Args:
            collectors: List of collector modules to run
            use_cache: Use cached results
            
        Returns:
            Complete audit results
        """
        logger.info("=" * 50)
        logger.info("Starting full audit run")
        logger.info("=" * 50)
        
        results = self.run_collectors(collectors, use_cache)
        
        logger.info("=" * 50)
        logger.info("Audit run completed")
        logger.info("=" * 50)
        
        return results
    
    def get_cached(self, collector_name: str) -> Optional[Dict[str, Any]]:
        """Get cached results for a collector.
        
        Args:
            collector_name: Name of the collector
            
        Returns:
            Cached data or None
        """
        return self._cache.get(collector_name)
    
    def clear_cache(self) -> None:
        """Clear the result cache."""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def close(self) -> None:
        """Clean up resources."""
        try:
            self.registry.close()
            self.wmi.close()
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")
        
        logger.info("AuditEngine closed")


# Import Collector for type hints
from .collectors.base import Collector