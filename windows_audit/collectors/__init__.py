"""Windows Audit Collectors."""

from .system_info import SystemInfoCollector, get_system_info_collector, run_system_info_collector
from .software import SoftwareCollector, get_software_collector, run_software_collector
from .users import UsersCollector, get_users_collector, run_users_collector
from .printers import PrintersCollector, get_printers_collector, run_printers_collector
from .network import NetworkCollector, get_network_collector, run_network_collector
from .startup import StartupCollector, get_startup_collector, run_startup_collector
from .browser import BrowserCollector, get_browser_collector, run_browser_collector
from .advanced import AdvancedCollector, get_advanced_collector, run_advanced_collector
from .base import Collector

__all__ = [
    "Collector",
    # System Info
    "SystemInfoCollector",
    "get_system_info_collector",
    "run_system_info_collector",
    # Software
    "SoftwareCollector",
    "get_software_collector",
    "run_software_collector",
    # Users
    "UsersCollector",
    "get_users_collector",
    "run_users_collector",
    # Printers
    "PrintersCollector",
    "get_printers_collector",
    "run_printers_collector",
    # Network
    "NetworkCollector",
    "get_network_collector",
    "run_network_collector",
    # Startup
    "StartupCollector",
    "get_startup_collector",
    "run_startup_collector",
    # Browser
    "BrowserCollector",
    "get_browser_collector",
    "run_browser_collector",
    # Advanced
    "AdvancedCollector",
    "get_advanced_collector",
    "run_advanced_collector",
]

# Map module names to collector functions
COLLECTORS = {
    "system_info": run_system_info_collector,
    "software": run_software_collector,
    "users": run_users_collector,
    "printers": run_printers_collector,
    "network": run_network_collector,
    "startup": run_startup_collector,
    "browser": run_browser_collector,
    "advanced": run_advanced_collector,
}