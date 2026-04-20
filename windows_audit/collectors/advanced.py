"""Advanced Features Collector."""
import logging
from typing import Any, Dict, List

from ..utils import get_logger

logger = get_logger(__name__)


def get_advanced_collector() -> "AdvancedCollector":
    """Get AdvancedCollector instance."""
    return AdvancedCollector()


def run_advanced_collector(engine) -> Dict[str, Any]:
    """Run advanced collector (convenience function)."""
    collector = AdvancedCollector()
    return collector.collect(engine)


class AdvancedCollector:
    """Collects advanced system information (drivers, processes, services, etc.)."""
    
    def __init__(self):
        self.name = "advanced"
        self.description = "Advanced features - drivers, processes, tasks, services"
        self.requires_admin = True
    
    def collect(self, engine) -> Dict[str, Any]:
        """Collect advanced information.
        
        Args:
            engine: AuditEngine instance
            
        Returns:
            Advanced information dictionary
        """
        logger.info("Collecting advanced features...")
        
        data = {}
        
        # Installed drivers
        data["drivers"] = self._get_drivers(engine)
        
        # Running processes
        data["processes"] = self._get_processes(engine)
        
        # Scheduled tasks
        data["scheduled_tasks"] = self._get_scheduled_tasks(engine)
        
        # Windows services
        data["services"] = self._get_services(engine)
        
        # Firewall status
        data["firewall"] = self._get_firewall(engine)
        
        # Windows Defender
        data["defender"] = self._get_defender(engine)
        
        # Summary
        data["summary"] = self._get_summary(data)
        
        logger.info(f"Advanced features collected")
        return data
    
    def _get_drivers(self, engine) -> List[Dict[str, Any]]:
        """Get installed drivers."""
        drivers = []
        
        try:
            driver_list = engine.wmi.query(
                "SELECT * FROM Win32_PnPSignedDriver WHERE DriverType != 0",
                props=["DeviceID", "DriverName", "DriverVersion", "DriverProvider", 
                       "InfName", "DeviceClass", "Signer"]
            )
            
            # Limit to top 100
            for driver in driver_list[:100]:
                drivers.append({
                    "name": driver.get("DriverName"),
                    "version": driver.get("DriverVersion"),
                    "provider": driver.get("DriverProvider"),
                    "device_class": driver.get("DeviceClass"),
                    "inf_name": driver.get("InfName"),
                    "signer": driver.get("Signer"),
                    "device_id": driver.get("DeviceID"),
                })
                
        except Exception as e:
            logger.warning(f"WMI drivers query failed: {e}")
        
        return drivers
    
    def _get_processes(self, engine) -> List[Dict[str, Any]]:
        """Get running processes."""
        processes = []
        
        try:
            process_list = engine.wmi.get_class("Win32_Process")
            
            for proc in process_list:
                # Get memory usage (WorkingSetSize)
                processes.append({
                    "name": proc.get("Name"),
                    "process_id": proc.get("ProcessId"),
                    "path": proc.get("ExecutablePath"),
                    "command_line": proc.get("CommandLine"),
                    "working_set": proc.get("WorkingSetSize"),
                    "thread_count": proc.get("ThreadCount"),
                    "creation_date": proc.get("CreationDate"),
                    "owner": self._get_process_owner(proc.get("ProcessId"), engine),
                })
                
                # Limit to top 100
                if len(processes) >= 100:
                    break
                    
        except Exception as e:
            logger.warning(f"WMI processes query failed: {e}")
        
        return processes
    
    def _get_process_owner(self, pid: int, engine) -> str:
        """Get process owner."""
        try:
            cmd = f"(Get-Process -Id {pid} -ErrorAction SilentlyContinue).SessionId"
            result = engine.ps.run(cmd)
            return result or ""
        except:
            return ""
    
    def _get_scheduled_tasks(self, engine) -> List[Dict[str, Any]]:
        """Get scheduled tasks."""
        tasks = []
        
        try:
            cmd = """
            Get-ScheduledTask | Where-Object {$_.State -ne 'Disabled'} | 
            Select-Object TaskName, TaskPath, State, Description, Author | 
            ConvertTo-Json -Depth 2
            """
            result = engine.ps.run(cmd, json_output=True)
            
            if isinstance(result, list):
                for task in result:
                    tasks.append({
                        "name": task.get("TaskName"),
                        "path": task.get("TaskPath"),
                        "state": task.get("State"),
                        "description": task.get("Description"),
                        "author": task.get("Author"),
                    })
            elif isinstance(result, dict):
                tasks.append({
                    "name": result.get("TaskName"),
                    "path": result.get("TaskPath"),
                    "state": result.get("State"),
                })
                
        except Exception as e:
            logger.warning(f"Scheduled tasks query failed: {e}")
        
        return tasks
    
    def _get_services(self, engine) -> List[Dict[str, Any]]:
        """Get Windows services."""
        services = []
        
        try:
            service_list = engine.wmi.get_class("Win32_Service")
            
            for svc in service_list:
                services.append({
                    "name": svc.get("Name"),
                    "display_name": svc.get("DisplayName"),
                    "state": svc.get("State"),
                    "start_type": svc.get("StartMode"),
                    "path": svc.get("PathName"),
                    "description": svc.get("Description"),
                    "account": svc.get("StartName"),
                })
                
        except Exception as e:
            logger.warning(f"WMI services query failed: {e}")
        
        return services
    
    def _get_firewall(self, engine) -> Dict[str, Any]:
        """Get Windows Firewall status."""
        firewall = {}
        
        try:
            cmd = """
            Get-NetFirewallProfile | Select-Object Name, Enabled | ConvertTo-Json
            """
            result = engine.ps.run(cmd, json_output=True)
            
            if isinstance(result, list):
                for profile in result:
                    firewall[profile.get("Name", "").lower()] = {
                        "enabled": profile.get("Enabled", False),
                    }
            elif isinstance(result, dict):
                firewall[result.get("Name", "").lower()] = {
                    "enabled": result.get("Enabled", False),
                }
                
        except Exception as e:
            logger.warning(f"Firewall query failed: {e}")
        
        return firewall
    
    def _get_defender(self, engine) -> Dict[str, Any]:
        """Get Windows Defender status."""
        defender = {}
        
        try:
            # Try Windows Security Center
            cmd = """
            Get-MpComputerStatus | Select-Object AntispywareEnabled, RealTimeProtectionEnabled, AntivirusEnabled, LastQuickScanTime, LastFullScanTime | ConvertTo-Json
            """
            result = engine.ps.run(cmd, json_output=True)
            
            if isinstance(result, dict):
                defender = {
                    "antispyware_enabled": result.get("AntispywareEnabled"),
                    "realtime_protection": result.get("RealTimeProtectionEnabled"),
                    "antivirus_enabled": result.get("AntivirusEnabled"),
                    "last_quick_scan": result.get("LastQuickScanTime"),
                    "last_full_scan": result.get("LastFullScanTime"),
                }
                
        except Exception as e:
            logger.debug(f"Windows Defender query failed: {e}")
            defender = {"status": "unavailable"}
        
        return defender
    
    def _get_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get advanced summary."""
        return {
            "drivers": len(data.get("drivers", [])),
            "processes": len(data.get("processes", [])),
            "scheduled_tasks": len(data.get("scheduled_tasks", [])),
            "services": len(data.get("services", [])),
            "firewall_profiles": len(data.get("firewall", {})),
        }