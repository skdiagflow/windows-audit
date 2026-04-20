"""Excel/CSV Output Formatter."""
import logging
import csv
from typing import Any, Dict, List
from pathlib import Path

try:
    import openpyxl
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

from ..utils import get_logger

logger = get_logger(__name__)


class ExcelFormatter:
    """Format audit results as Excel/CSV."""
    
    def __init__(self, include_csv: bool = False):
        """Initialize Excel formatter.
        
        Args:
            include_csv: Also generate CSV files
        """
        self.include_csv = include_csv
        
        if not OPENPYXL_AVAILABLE:
            logger.warning("openpyxl not available - Excel export disabled")
    
    def format(self, data: Dict[str, Any]) -> bytes:
        """Format data as Excel workbook.
        
        Args:
            data: Audit results
            
        Returns:
            Excel file bytes
        """
        if not OPENPYXL_AVAILABLE:
            raise RuntimeError("openpyxl not available")
        
        wb = Workbook()
        
        # Remove default sheet
        wb.remove(wb.active)
        
        # Add sheets for each module
        self._add_system_info_sheet(wb, data.get("system_info", {}))
        self._add_software_sheet(wb, data.get("software", {}))
        self._add_users_sheet(wb, data.get("users", {}))
        self._add_printers_sheet(wb, data.get("printers", {}))
        self._add_network_sheet(wb, data.get("network", {}))
        self._add_startup_sheet(wb, data.get("startup", {}))
        self._add_browser_sheet(wb, data.get("browser", {}))
        self._add_advanced_sheet(wb, data.get("advanced", {}))
        
        return wb
    
    def format_to_file(
        self, 
        data: Dict[str, Any], 
        file_path: str
    ) -> None:
        """Format and save to file.
        
        Args:
            data: Audit results
            file_path: Output file path
        """
        if not OPENPYXL_AVAILABLE:
            raise RuntimeError("openpyxl not available")
        
        wb = self.format(data)
        
        # Save workbook
        try:
            wb.save(file_path)
            logger.info(f"Excel saved to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save Excel: {e}")
            raise
        
        # Generate CSV files if requested
        if self.include_csv:
            base_path = Path(file_path).with_suffix("")
            self._generate_csv_files(data, str(base_path))
    
    def _generate_csv_files(
        self, 
        data: Dict[str, Any], 
        base_path: str
    ) -> None:
        """Generate CSV files for each module."""
        csv_mappings = {
            "software": data.get("software", {}).get("all_software", []),
            "users": data.get("users", {}).get("local_users", []),
            "printers": data.get("printers", {}).get("printers", []),
            "network": data.get("network", {}).get("adapters", []),
            "startup": data.get("startup", {}).get("all_items", []),
        }
        
        for name, rows in csv_mappings.items():
            if rows:
                csv_path = f"{base_path}_{name}.csv"
                try:
                    with open(csv_path, "w", newline="", encoding="utf-8") as f:
                        if rows:
                            fieldnames = rows[0].keys()
                            writer = csv.DictWriter(f, fieldnames=fieldnames)
                            writer.writeheader()
                            writer.writerows(rows)
                    
                    logger.info(f"CSV saved to {csv_path}")
                    
                except Exception as e:
                    logger.warning(f"CSV save failed: {e}")
    
    def _add_system_info_sheet(self, wb: Workbook, data: Dict[str, Any]) -> None:
        """Add system info sheet."""
        ws = wb.create_sheet("System Info")
        
        # Headers and data
        ws.append(["System Information", ""])
        ws.append(["", ""])
        
        if "os" in data:
            os_info = data.get("os", {})
            ws.append(["Property", "Value"])
            ws.append(["Operating System", os_info.get("name", "")])
            ws.append(["Version", os_info.get("version", "")])
            ws.append(["Build", os_info.get("build", "")])
            ws.append(["Architecture", os_info.get("architecture", "")])
        
        if "cpu" in data:
            cpu = data.get("cpu", {})
            ws.append(["", ""])
            ws.append(["CPU", ""])
            ws.append(["Name", cpu.get("name", "")])
            ws.append(["Cores", cpu.get("cores", "")])
        
        if "memory" in data:
            mem = data.get("memory", {})
            ws.append(["", ""])
            ws.append(["Memory", ""])
            ws.append(["Total (GB)", mem.get("total_physical_gb", "")])
            ws.append(["Free (GB)", mem.get("free_physical_gb", "")])
        
        # Style header
        self._style_sheet(ws)
    
    def _add_software_sheet(self, wb: Workbook, data: Dict[str, Any]) -> None:
        """Add software sheet."""
        ws = wb.create_sheet("Installed Software")
        
        # Headers
        headers = ["Name", "Version", "Publisher", "Install Date"]
        ws.append(headers)
        
        # Data
        for sw in data.get("all_software", []):
            ws.append([
                sw.get("name", ""),
                sw.get("version", ""),
                sw.get("publisher", ""),
                sw.get("install_date", ""),
            ])
        
        self._style_sheet(ws)
    
    def _add_users_sheet(self, wb: Workbook, data: Dict[str, Any]) -> None:
        """Add users sheet."""
        ws = wb.create_sheet("Local Users")
        
        # Headers
        headers = ["Username", "Full Name", "Status", "Password Required", "Lockout"]
        ws.append(headers)
        
        # Data
        for user in data.get("local_users", []):
            ws.append([
                user.get("name", ""),
                user.get("full_name", ""),
                "Disabled" if user.get("disabled") else "Enabled",
                "Yes" if user.get("password_required") else "No",
                "Yes" if user.get("lockout") else "No",
            ])
        
        self._style_sheet(ws)
    
    def _add_printers_sheet(self, wb: Workbook, data: Dict[str, Any]) -> None:
        """Add printers sheet."""
        ws = wb.create_sheet("Printers")
        
        # Headers
        headers = ["Name", "Driver", "Port", "Default", "Network"]
        ws.append(headers)
        
        # Data
        for printer in data.get("printers", []):
            ws.append([
                printer.get("name", ""),
                printer.get("driver_name", ""),
                printer.get("port_name", ""),
                "Yes" if printer.get("default") else "No",
                "Yes" if printer.get("network") else "No",
            ])
        
        self._style_sheet(ws)
    
    def _add_network_sheet(self, wb: Workbook, data: Dict[str, Any]) -> None:
        """Add network sheet."""
        ws = wb.create_sheet("Network")
        
        # Headers
        headers = ["Adapter", "Type", "MAC Address", "Status"]
        ws.append(headers)
        
        # Data
        for adapter in data.get("adapters", []):
            ws.append([
                adapter.get("name", ""),
                adapter.get("adapter_type", ""),
                adapter.get("mac_address", ""),
                str(adapter.get("status", "")),
            ])
        
        self._style_sheet(ws)
    
    def _add_startup_sheet(self, wb: Workbook, data: Dict[str, Any]) -> None:
        """Add startup sheet."""
        ws = wb.create_sheet("Startup Programs")
        
        # Headers
        headers = ["Name", "Command", "Type", "Source"]
        ws.append(headers)
        
        # Data
        for item in data.get("all_items", []):
            ws.append([
                item.get("name", ""),
                item.get("command", ""),
                item.get("type", ""),
                item.get("source", ""),
            ])
        
        self._style_sheet(ws)
    
    def _add_browser_sheet(self, wb: Workbook, data: Dict[str, Any]) -> None:
        """Add browser sheet."""
        ws = wb.create_sheet("Browsers")
        
        # Headers
        headers = ["Browser", "Version"]
        ws.append(headers)
        
        # Data
        for browser in data.get("detected_browsers", []):
            ws.append([
                browser.get("name", ""),
                browser.get("version", ""),
            ])
        
        self._style_sheet(ws)
    
    def _add_advanced_sheet(self, wb: Workbook, data: Dict[str, Any]) -> None:
        """Add advanced sheet."""
        ws = wb.create_sheet("Advanced")
        
        summary = data.get("summary", {})
        
        # Summary
        ws.append(["Advanced Features", ""])
        ws.append(["", ""])
        ws.append(["Category", "Count"])
        ws.append(["Drivers", summary.get("drivers", 0)])
        ws.append(["Processes", summary.get("processes", 0)])
        ws.append(["Scheduled Tasks", summary.get("scheduled_tasks", 0)])
        ws.append(["Services", summary.get("services", 0)])
        
        # Services
        ws.append(["", ""])
        ws.append(["Services", ""])
        headers = ["Name", "Display Name", "State", "Start Type"]
        ws.append(headers)
        
        for svc in data.get("services", [])[:100]:
            ws.append([
                svc.get("name", ""),
                svc.get("display_name", ""),
                svc.get("state", ""),
                svc.get("start_type", ""),
            ])
        
        self._style_sheet(ws)
    
    def _style_sheet(self, ws) -> None:
        """Style an Excel worksheet."""
        # Header style
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="0066CC", end_color="0066CC", fill_type="solid")
        
        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="left")
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width


class CSVFormatter:
    """Format audit results as CSV."""
    
    def __init__(self, delimiter: str = ","):
        """Initialize CSV formatter.
        
        Args:
            delimiter: CSV delimiter
        """
        self.delimiter = delimiter
    
    def format(
        self, 
        data: Dict[str, Any], 
        module: str
    ) -> str:
        """Format specific module as CSV.
        
        Args:
            data: Audit results
            module: Module name
            
        Returns:
            CSV string
        """
        output = []
        
        # Get data for module
        module_data = self._get_module_data(data, module)
        
        if not module_data:
            return ""
        
        # Get fieldnames from first row
        if module_data:
            fieldnames = list(module_data[0].keys())
            output.append(self.delimiter.join(fieldnames))
            
            # Add rows
            for row in module_data:
                values = [str(row.get(f, "")) for f in fieldnames]
                output.append(self.delimiter.join(values))
        
        return "\n".join(output)
    
    def _get_module_data(
        self, 
        data: Dict[str, Any], 
        module: str
    ) -> List[Dict[str, Any]]:
        """Get data for specific module."""
        mappings = {
            "software": data.get("software", {}).get("all_software", []),
            "users": data.get("users", {}).get("local_users", []),
            "printers": data.get("printers", {}).get("printers", []),
            "network": data.get("network", {}).get("adapters", []),
            "startup": data.get("startup", {}).get("all_items", []),
        }
        
        return mappings.get(module, [])