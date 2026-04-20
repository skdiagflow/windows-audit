"""Printers Collector."""
import logging
from typing import Any, Dict, List

from ..utils import get_logger

logger = get_logger(__name__)


def get_printers_collector() -> "PrintersCollector":
    """Get PrintersCollector instance."""
    return PrintersCollector()


def run_printers_collector(engine) -> Dict[str, Any]:
    """Run printers collector (convenience function)."""
    collector = PrintersCollector()
    return collector.collect(engine)


class PrintersCollector:
    """Collects installed printer information."""
    
    def __init__(self):
        self.name = "printers"
        self.description = "Installed printers and drivers"
        self.requires_admin = False
    
    def collect(self, engine) -> Dict[str, Any]:
        """Collect printer information.
        
        Args:
            engine: AuditEngine instance
            
        Returns:
            Printer information dictionary
        """
        logger.info("Collecting printers...")
        
        data = {}
        
        # Get printers from WMI
        data["printers"] = self._get_printers(engine)
        
        # Get printer ports
        data["ports"] = self._get_ports(engine)
        
        # Get default printer
        data["default"] = self._get_default_printer(data["printers"])
        
        # Summary
        data["summary"] = self._get_summary(data["printers"])
        
        logger.info(f"Printers collected: {len(data['printers'])}")
        return data
    
    def _get_printers(self, engine) -> List[Dict[str, Any]]:
        """Get installed printers."""
        printers = []
        
        try:
            printer_list = engine.wmi.get_class("Win32_Printer")
            
            for printer in printer_list:
                printers.append({
                    "name": printer.get("Name"),
                    "driver_name": printer.get("DriverName"),
                    "port_name": printer.get("PortName"),
                    "default": printer.get("Default", False),
                    "network": printer.get("Network", False),
                    "shared": printer.get("Shared", False),
                    "status": printer.get("Status"),
                    "status_code": printer.get("StatusCode"),
                    "print_processor": printer.get("PrintProcessor"),
                    "attributes": printer.get("Attributes"),
                    "job_count": printer.get("JobCount"),
                    "spool_enabled": printer.get("SpoolEnabled"),
                    "location": printer.get("Location"),
                    "comment": printer.get("Comment"),
                })
                
        except Exception as e:
            logger.warning(f"WMI printers query failed: {e}")
        
        return printers
    
    def _get_ports(self, engine) -> List[Dict[str, Any]]:
        """Get printer ports."""
        ports = []
        
        try:
            port_list = engine.wmi.get_class("Win32_TCPIPPrinterPort")
            
            for port in port_list:
                ports.append({
                    "name": port.get("Name"),
                    "host_address": port.get("HostAddress"),
                    "port_number": port.get("PortNumber"),
                    "protocol": port.get("Protocol"),
                    "enabled": port.get("Enabled"),
                })
                
        except Exception as e:
            logger.debug(f"WMI printer ports query failed: {e}")
        
        return ports
    
    def _get_default_printer(
        self, 
        printers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get default printer."""
        for printer in printers:
            if printer.get("default"):
                return printer
        
        return {}
    
    def _get_summary(self, printers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get printer summary."""
        total = len(printers)
        default = sum(1 for p in printers if p.get("default"))
        network = sum(1 for p in printers if p.get("network"))
        shared = sum(1 for p in printers if p.get("shared"))
        
        return {
            "total": total,
            "default": default,
            "network": network,
            "shared": shared,
        }