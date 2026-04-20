"""CLI/Terminal Output Formatter."""
import logging
from typing import Any, Dict, List

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.tree import Tree
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from ..utils import get_logger

logger = get_logger(__name__)


class CLIFormatter:
    """Format audit results for CLI/terminal output."""
    
    def __init__(self, use_colors: bool = True):
        """Initialize CLI formatter.
        
        Args:
            use_colors: Use colored output
        """
        self.use_colors = use_colors
        
        if RICH_AVAILABLE:
            self.console = Console()
        else:
            self.console = None
    
    def format(self, data: Dict[str, Any]) -> str:
        """Format all data for CLI output.
        
        Args:
            data: Audit results
            
        Returns:
            Formatted string
        """
        if not self.console:
            # Fallback to simple text
            return self._format_simple(data)
        
        return self._format_rich(data)
    
    def _format_rich(self, data: Dict[str, Any]) -> str:
        """Format using rich library."""
        output = []
        
        # Header
        output.append("\n" + "=" * 60)
        output.append("WINDOWS AUDIT REPORT")
        output.append("=" * 60 + "\n")
        
        # System Information
        if "system_info" in data:
            output.append(self._format_system_info(data["system_info"]))
        
        # Software
        if "software" in data:
            output.append(self._format_software(data["software"]))
        
        # Users
        if "users" in data:
            output.append(self._format_users(data["users"]))
        
        # Printers
        if "printers" in data:
            output.append(self._format_printers(data["printers"]))
        
        # Network
        if "network" in data:
            output.append(self._format_network(data["network"]))
        
        # Startup
        if "startup" in data:
            output.append(self._format_startup(data["startup"]))
        
        # Browser
        if "browser" in data:
            output.append(self._format_browser(data["browser"]))
        
        # Advanced
        if "advanced" in data:
            output.append(self._format_advanced(data["advanced"]))
        
        return "\n".join(output)
    
    def _format_simple(self, data: Dict[str, Any]) -> str:
        """Simple text formatting without rich."""
        output = []
        
        output.append("\n" + "=" * 60)
        output.append("WINDOWS AUDIT REPORT")
        output.append("=" * 60 + "\n")
        
        # System Information
        if "system_info" in data:
            si = data["system_info"]
            output.append("SYSTEM INFORMATION")
            output.append("-" * 40)
            
            if "os" in si:
                os_info = si.get("os", {})
                output.append(f"  OS: {os_info.get('name', 'Unknown')}")
                output.append(f"  Version: {os_info.get('version', '')}")
                output.append(f"  Build: {os_info.get('build', '')}")
            
            if "memory" in si:
                mem = si.get("memory", {})
                output.append(f"  RAM: {mem.get('total_physical_gb', 'N/A')} GB total")
                output.append(f"  Free RAM: {mem.get('free_physical_gb', 'N/A')} GB")
            
            if "cpu" in si:
                cpu = si.get("cpu", {})
                output.append(f"  CPU: {cpu.get('name', 'Unknown')}")
            
            output.append("")
        
        # Software summary
        if "software" in data:
            sw = data["software"]
            output.append("INSTALLED SOFTWARE")
            output.append("-" * 40)
            summary = sw.get("summary", {})
            output.append(f"  Total: {len(sw.get('all_software', []))} programs")
            output.append(f"  Microsoft: {len(sw.get('microsoft', []))}")
            output.append(f"  Third-party: {len(sw.get('third_party', []))}")
            output.append("")
        
        return "\n".join(output)
    
    def _format_system_info(self, data: Dict[str, Any]) -> str:
        """Format system information."""
        output = []
        
        table = Table(title="System Information", show_header=True)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        if "os" in data:
            os_info = data.get("os", {})
            table.add_row("Operating System", os_info.get("name", "Unknown"))
            table.add_row("Version", os_info.get("version", ""))
            table.add_row("Build", os_info.get("build", ""))
        
        if "cpu" in data:
            cpu = data.get("cpu", {})
            table.add_row("CPU", cpu.get("name", "Unknown"))
            table.add_row("Cores", str(cpu.get("cores", "")))
        
        if "memory" in data:
            mem = data.get("memory", {})
            table.add_row("RAM Total", f"{mem.get('total_physical_gb', 'N/A')} GB")
            table.add_row("RAM Free", f"{mem.get('free_physical_gb', 'N/A')} GB")
        
        if "disks" in data:
            for disk in data.get("disks", [])[:3]:
                table.add_row(
                    "Disk", 
                    f"{disk.get('device_id', '')} - {disk.get('free_space_gb', 0)}GB free"
                )
        
        output.append("")
        if self.console:
            self.console.print(table)
            output.append("")
        
        return "\n".join(output)
    
    def _format_software(self, data: Dict[str, Any]) -> str:
        """Format software information."""
        output = []
        
        table = Table(title="Installed Software", show_header=True)
        table.add_column("Name", style="cyan")
        table.add_column("Version", style="white")
        table.add_column("Publisher", style="yellow")
        
        for sw in data.get("all_software", [])[:20]:
            table.add_row(
                sw.get("name", ""),
                sw.get("version", ""),
                sw.get("publisher", "")
            )
        
        output.append("")
        if self.console:
            self.console.print(table)
            output.append(f"\n  Total: {len(data.get('all_software', []))} programs")
            output.append("")
        
        return "\n".join(output)
    
    def _format_users(self, data: Dict[str, Any]) -> str:
        """Format user information."""
        output = []
        
        table = Table(title="Local Users", show_header=True)
        table.add_column("Username", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Password Required", style="yellow")
        
        for user in data.get("local_users", [])[:20]:
            status = "Disabled" if user.get("disabled") else "Enabled"
            table.add_row(
                user.get("name", ""),
                status,
                "Yes" if user.get("password_required") else "No"
            )
        
        output.append("")
        if self.console:
            self.console.print(table)
        
        return "\n".join(output)
    
    def _format_printers(self, data: Dict[str, Any]) -> str:
        """Format printer information."""
        output = []
        
        table = Table(title="Printers", show_header=True)
        table.add_column("Name", style="cyan")
        table.add_column("Driver", style="white")
        table.add_column("Default", style="yellow")
        
        for printer in data.get("printers", [])[:10]:
            default = "Yes" if printer.get("default") else "No"
            table.add_row(
                printer.get("name", ""),
                printer.get("driver_name", ""),
                default
            )
        
        output.append("")
        if self.console:
            self.console.print(table)
        
        return "\n".join(output)
    
    def _format_network(self, data: Dict[str, Any]) -> str:
        """Format network information."""
        output = []
        
        table = Table(title="Network Adapters", show_header=True)
        table.add_column("Adapter", style="cyan")
        table.add_column("MAC Address", style="white")
        table.add_column("Status", style="yellow")
        
        for adapter in data.get("adapters", [])[:10]:
            table.add_row(
                adapter.get("name", ""),
                adapter.get("mac_address", ""),
                str(adapter.get("status", ""))
            )
        
        output.append("")
        if self.console:
            self.console.print(table)
        
        return "\n".join(output)
    
    def _format_startup(self, data: Dict[str, Any]) -> str:
        """Format startup programs."""
        output = []
        
        table = Table(title="Startup Programs", show_header=True)
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="white")
        table.add_column("Source", style="yellow")
        
        for item in data.get("all_items", []):
            table.add_row(
                item.get("name", ""),
                item.get("type", ""),
                item.get("source", "")
            )
        
        output.append("")
        if self.console:
            self.console.print(table)
        
        return "\n".join(output)
    
    def _format_browser(self, data: Dict[str, Any]) -> str:
        """Format browser data."""
        output = []
        
        table = Table(title="Installed Browsers", show_header=True)
        table.add_column("Browser", style="cyan")
        table.add_column("Version", style="white")
        
        for browser in data.get("detected_browsers", []):
            table.add_row(
                browser.get("name", ""),
                browser.get("version", "")
            )
        
        output.append("")
        if self.console:
            self.console.print(table)
        
        return "\n".join(output)
    
    def _format_advanced(self, data: Dict[str, Any]) -> str:
        """Format advanced features."""
        output = []
        
        summary = data.get("summary", {})
        
        table = Table(title="Advanced Features Summary", show_header=True)
        table.add_column("Category", style="cyan")
        table.add_column("Count", style="white")
        
        table.add_row("Drivers", str(summary.get("drivers", 0)))
        table.add_row("Processes", str(summary.get("processes", 0)))
        table.add_row("Scheduled Tasks", str(summary.get("scheduled_tasks", 0)))
        table.add_row("Services", str(summary.get("services", 0)))
        
        output.append("")
        if self.console:
            self.console.print(table)
        
        return "\n".join(output)