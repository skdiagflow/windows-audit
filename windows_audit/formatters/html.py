"""HTML Output Formatter."""
import logging
from datetime import datetime
from typing import Any, Dict
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False

from ..utils import get_logger

logger = get_logger(__name__)


class HTMLFormatter:
    """Format audit results as HTML report."""
    
    def __init__(
        self,
        template_dir: str = None,
        theme: str = "default"
    ):
        """Initialize HTML formatter.
        
        Args:
            template_dir: Custom template directory
            theme: Report theme
        """
        self.theme = theme
        self.template_dir = template_dir
        self.env = None
        
        if JINJA2_AVAILABLE:
            self._init_env()
    
    def _init_env(self) -> None:
        """Initialize Jinja2 environment."""
        try:
            if self.template_dir:
                self.env = Environment(
                    loader=FileSystemLoader(self.template_dir),
                    autoescape=select_autoescape(['html', 'xml'])
                )
            else:
                # Use built-in template
                self.env = Environment(
                    autoescape=select_autoescape(['html', 'xml'])
                )
        except Exception as e:
            logger.warning(f"Jinja2 init failed: {e}")
    
    def format(self, data: Dict[str, Any]) -> str:
        """Format data as HTML.
        
        Args:
            data: Audit results
            
        Returns:
            HTML string
        """
        if not JINJA2_AVAILABLE:
            return self._format_simple(data)
        
        try:
            template = self.env.get_template("report.html")
            return template.render(
                data=data,
                generated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                theme=self.theme
            )
        except Exception:
            # Fallback to simple HTML
            return self._format_simple(data)
    
    def _format_simple(self, data: Dict[str, Any]) -> str:
        """Generate simple HTML without Jinja2."""
        html = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<meta charset='utf-8'>",
            "<title>Windows Audit Report</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }",
            ".container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; }",
            "h1 { color: #333; border-bottom: 2px solid #0066cc; }",
            "h2 { color: #0066cc; margin-top: 30px; }",
            "table { width: 100%; border-collapse: collapse; margin: 10px 0; }",
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "th { background: #0066cc; color: white; }",
            "tr:nth-child(even) { background: #f9f9f9; }",
            ".summary { background: #e6f3ff; padding: 15px; border-radius: 5px; }",
            "</style>",
            "</head>",
            "<body>",
            "<div class='container'>",
            "<h1>Windows Audit Report</h1>",
            f"<p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>",
        ]
        
        # System Information
        if "system_info" in data:
            si = data["system_info"]
            html.append("<h2>System Information</h2>")
            html.append("<div class='summary'>")
            
            if "os" in si:
                os_info = si.get("os", {})
                html.append(f"<p><strong>OS:</strong> {os_info.get('name', 'Unknown')}</p>")
                html.append(f"<p><strong>Version:</strong> {os_info.get('version', '')}</p>")
                html.append(f"<p><strong>Build:</strong> {os_info.get('build', '')}</p>")
            
            if "memory" in si:
                mem = si.get("memory", {})
                html.append(f"<p><strong>RAM:</strong> {mem.get('total_physical_gb', 'N/A')} GB total</p>")
            
            html.append("</div>")
        
        # Software
        if "software" in data:
            sw = data["software"]
            html.append("<h2>Installed Software</h2>")
            html.append(f"<p>Total: {len(sw.get('all_software', []))} programs</p>")
            
            if sw.get("all_software"):
                html.append("<table>")
                html.append("<tr><th>Name</th><th>Version</th><th>Publisher</th></tr>")
                
                for item in sw.get("all_software", [])[:50]:
                    name = self._escape(item.get("name", ""))
                    version = self._escape(item.get("version", ""))
                    publisher = self._escape(item.get("publisher", ""))
                    html.append(f"<tr><td>{name}</td><td>{version}</td><td>{publisher}</td></tr>")
                
                html.append("</table>")
        
        # Users
        if "users" in data:
            users = data["users"]
            html.append("<h2>Local Users</h2>")
            html.append(f"<p>Total: {len(users.get('local_users', []))} users</p>")
            
            if users.get("local_users"):
                html.append("<table>")
                html.append("<tr><th>Username</th><th>Status</th></tr>")
                
                for user in users.get("local_users", []):
                    name = self._escape(user.get("name", ""))
                    status = "Disabled" if user.get("disabled") else "Enabled"
                    html.append(f"<tr><td>{name}</td><td>{status}</td></tr>")
                
                html.append("</table>")
        
        # Network
        if "network" in data:
            net = data["network"]
            html.append("<h2>Network Adapters</h2>")
            
            if net.get("adapters"):
                html.append("<table>")
                html.append("<tr><th>Adapter</th><th>MAC Address</th><th>Status</th></tr>")
                
                for adapter in net.get("adapters", [])[:20]:
                    name = self._escape(adapter.get("name", ""))
                    mac = self._escape(adapter.get("mac_address", ""))
                    status = str(adapter.get("status", ""))
                    html.append(f"<tr><td>{name}</td><td>{mac}</td><td>{status}</td></tr>")
                
                html.append("</table>")
        
        # Summary
        if "advanced" in data:
            adv = data["advanced"]
            summary = adv.get("summary", {})
            html.append("<h2>Advanced Summary</h2>")
            html.append("<div class='summary'>")
            html.append(f"<p>Drivers: {summary.get('drivers', 0)}</p>")
            html.append(f"<p>Services: {summary.get('services', 0)}</p>")
            html.append(f"<p>Scheduled Tasks: {summary.get('scheduled_tasks', 0)}</p>")
            html.append("</div>")
        
        html.extend([
            "</div>",
            "</body>",
            "</html>"
        ])
        
        return "\n".join(html)
    
    def _escape(self, text: str) -> str:
        """Escape HTML special characters."""
        if not text:
            return ""
        return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))
    
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
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.format(data))
            
            logger.info(f"HTML saved to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save HTML: {e}")
            raise