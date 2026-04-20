"""System Information Collector."""
import logging
import platform
import os
from typing import Any, Dict, List

from ..utils import get_logger, PowerShellExecutor, WMIQuery, get_wmi_data

logger = get_logger(__name__)


def get_system_info_collector() -> SystemInfoCollector:
    """Get SystemInfoCollector instance."""
    return SystemInfoCollector()


def run_system_info_collector(engine) -> Dict[str, Any]:
    """Run system info collector (convenience function).
    
    Args:
        engine: AuditEngine instance
        
    Returns:
        System information dictionary
    """
    collector = SystemInfoCollector()
    return collector.collect(engine)


class SystemInfoCollector:
    """Collects detailed Windows system information."""
    
    def __init__(self):
        self.name = "system_info"
        self.description = "Windows system information (OS, CPU, RAM, GPU, etc.)"
        self.requires_admin = False
    
    def collect(self, engine) -> Dict[str, Any]:
        """Collect system information.
        
        Args:
            engine: AuditEngine instance
            
        Returns:
            System information dictionary
        """
        logger.info("Collecting system information...")
        
        data = {}
        
        # Get OS information
        data["os"] = self._get_os_info(engine)
        
        # Get CPU information
        data["cpu"] = self._get_cpu_info(engine)
        
        # Get memory information
        data["memory"] = self._get_memory_info(engine)
        
        # Get GPU information
        data["gpu"] = self._get_gpu_info(engine)
        
        # Get disk information
        data["disks"] = self._get_disk_info(engine)
        
        # Get BIOS information
        data["bios"] = self._get_bios_info(engine)
        
        # Get motherboard info
        data["motherboard"] = self._get_motherboard_info(engine)
        
        # Get DirectX version
        data["directx"] = self._get_directx_version(engine)
        
        logger.info(f"System information collected: {len(data)} categories")
        return data
    
    def _get_os_info(self, engine) -> Dict[str, Any]:
        """Get operating system information."""
        try:
            # Try WMI first
            os_list = engine.wmi.get_class("Win32_OperatingSystem")
            if os_list:
                os_data = os_list[0]
                return {
                    "name": os_data.get("Caption", "Windows"),
                    "version": os_data.get("Version", ""),
                    "build": os_data.get("BuildNumber", ""),
                    "architecture": os_data.get("OSArchitecture", ""),
                    "install_date": os_data.get("InstallDate", ""),
                    "last_boot": os_data.get("LastBootUpTime", ""),
                    "free_physical_memory": os_data.get("FreePhysicalMemory", ""),
                    "free_virtual_memory": os_data.get("FreeVirtualMemory", ""),
                }
        except Exception as e:
            logger.warning(f"WMI OS info failed: {e}")
        
        # Fallback to platform module
        return {
            "name": "Windows",
            "version": platform.version(),
            "build": platform.version_build(),
            "architecture": platform.machine(),
        }
    
    def _get_cpu_info(self, engine) -> Dict[str, Any]:
        """Get CPU information."""
        try:
            cpu_list = engine.wmi.get_class("Win32_Processor")
            if cpu_list:
                cpu = cpu_list[0]
                return {
                    "name": cpu.get("Name", "").strip(),
                    "manufacturer": cpu.get("Manufacturer", ""),
                    "cores": cpu.get("NumberOfCores"),
                    "logical_processors": cpu.get("NumberOfLogicalProcessors"),
                    "max_clock_speed": cpu.get("MaxClockSpeed"),
                    "current_clock_speed": cpu.get("CurrentClockSpeed"),
                    "architecture": cpu.get("Architecture"),
                    "processor_id": cpu.get("ProcessorId"),
                    "serial_number": cpu.get("SerialNumber"),
                }
        except Exception as e:
            logger.warning(f"WMI CPU info failed: {e}")
        
        # Fallback to platform
        return {
            "name": platform.processor(),
            "cores": os.cpu_count(),
        }
    
    def _get_memory_info(self, engine) -> Dict[str, Any]:
        """Get memory information."""
        try:
            os_list = engine.wmi.get_class("Win32_OperatingSystem")
            if os_list:
                mem = os_list[0]
                total = int(mem.get("TotalVisibleMemorySize", 0))
                free = int(mem.get("FreePhysicalMemory", 0))
                return {
                    "total_physical_gb": round(total / 1024, 2),
                    "free_physical_gb": round(free / 1024, 2),
                    "used_physical_gb": round((total - free) / 1024, 2),
                    "percent_used": round((total - free) / total * 100, 1) if total else 0,
                }
        except Exception as e:
            logger.warning(f"WMI memory info failed: {e}")
        
        # Fallback - return empty
        return {}
    
    def _get_gpu_info(self, engine) -> List[Dict[str, Any]]:
        """Get GPU information."""
        gpus = []
        try:
            video_list = engine.wmi.get_class("Win32_VideoController")
            for gpu in video_list:
                gpus.append({
                    "name": gpu.get("Name", ""),
                    "driver_version": gpu.get("DriverVersion", ""),
                    "driver_date": gpu.get("DriverDate", ""),
                    "adapter_ram": gpu.get("AdapterRAM"),
                    "adapter_dac_type": gpu.get("AdapterDACType", ""),
                    "video_processor": gpu.get("VideoProcessor", ""),
                    "status": gpu.get("Status", ""),
                })
        except Exception as e:
            logger.warning(f"WMI GPU info failed: {e}")
        
        return gpus
    
    def _get_disk_info(self, engine) -> List[Dict[str, Any]]:
        """Get disk information."""
        disks = []
        try:
            drive_list = engine.wmi.get_class("Win32_LogicalDisk")
            for drive in drive_list:
                if drive.get("DriveType") == 3:  # Fixed disks
                    disks.append({
                        "device_id": drive.get("DeviceID"),
                        "volume_name": drive.get("VolumeName", ""),
                        "file_system": drive.get("FileSystem", ""),
                        "size_gb": round(int(drive.get("Size", 0)) / (1024**3), 2),
                        "free_space_gb": round(int(drive.get("FreeSpace", 0)) / (1024**3), 2),
                        "used_space_gb": round(
                            (int(drive.get("Size", 0)) - int(drive.get("FreeSpace", 0))) / (1024**3), 2
                        ),
                        "percent_free": round(
                            int(drive.get("FreeSpace", 0)) / int(drive.get("Size", 1)) * 100, 1
                        ) if drive.get("Size") else 0,
                    })
        except Exception as e:
            logger.warning(f"WMI disk info failed: {e}")
        
        return disks
    
    def _get_bios_info(self, engine) -> Dict[str, Any]:
        """Get BIOS information."""
        try:
            bios_list = engine.wmi.get_class("Win32_BIOS")
            if bios_list:
                bios = bios_list[0]
                return {
                    "manufacturer": bios.get("Manufacturer", ""),
                    "name": bios.get("Name", ""),
                    "version": bios.get("Version", ""),
                    "serial_number": bios.get("SerialNumber", ""),
                    "release_date": bios.get("ReleaseDate", ""),
                    "smbios_version": bios.get("SMBIOSBIOSVersion", ""),
                }
        except Exception as e:
            logger.warning(f"WMI BIOS info failed: {e}")
        
        return {}
    
    def _get_motherboard_info(self, engine) -> Dict[str, Any]:
        """Get motherboard information."""
        try:
            board_list = engine.wmi.get_class("Win32_BaseBoard")
            if board_list:
                board = board_list[0]
                return {
                    "manufacturer": board.get("Manufacturer", ""),
                    "product": board.get("Product", ""),
                    "version": board.get("Version", ""),
                    "serial_number": board.get("SerialNumber", ""),
                }
        except Exception as e:
            logger.warning(f"WMI motherboard info failed: {e}")
        
        return {}
    
    def _get_directx_version(self, engine) -> str:
        """Get DirectX version."""
        try:
            # Try PowerShell to get DirectX version
            cmd = "(Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\DirectX\\Version').DirectX"
            result = engine.ps.run(cmd)
            if result:
                return result
        except Exception as e:
            logger.debug(f"DirectX version not found: {e}")
        
        return "Unknown"