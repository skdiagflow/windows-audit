"""CLI Interface for Windows Audit Suite."""
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import click
    CLICK_AVAILABLE = True
except ImportError:
    CLICK_AVAILABLE = False

from .utils import get_logger, setup_logging

logger = get_logger(__name__)


# Available modules
AVAILABLE_MODULES = [
    "system_info",
    "software",
    "users",
    "printers",
    "network",
    "startup",
    "browser",
    "advanced",
]

# Module descriptions
MODULE_DESCRIPTIONS = {
    "system_info": "System Information (OS, CPU, RAM, GPU, etc.)",
    "software": "Installed Software",
    "users": "Local Users",
    "printers": "Installed Printers",
    "network": "Network Adapters and Configuration",
    "startup": "Startup Programs",
    "browser": "Browser Data (bookmarks, extensions)",
    "advanced": "Advanced (drivers, processes, services)",
}

# All modules shortcut
ALL_MODULES = AVAILABLE_MODULES


class WindowsAuditCLI:
    """Windows Audit CLI application."""
    
    def __init__(
        self,
        verbose: bool = False,
        output: str = None,
        format: str = "cli"
    ):
        """Initialize CLI.
        
        Args:
            verbose: Enable verbose logging
            output: Output file path
            format: Output format (cli, json, html, pdf, excel)
        """
        self.verbose = verbose
        self.output = output
        self.format = format
        self.data: Dict[str, Any] = {}
        
        # Set up logging
        setup_logging(level="DEBUG" if verbose else "INFO")
    
    def run(
        self,
        modules: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Run the audit.
        
        Args:
            modules: List of modules to run (None = all)
            
        Returns:
            Audit results
        """
        # Default to all modules
        if not modules:
            modules = ALL_MODULES
        
        logger.info(f"Running modules: {', '.join(modules)}")
        
        # Import and run collectors
        from .collectors import COLLECTORS
        from .engine import AuditEngine
        
        # Create engine
        engine = AuditEngine(verbose=self.verbose)
        
        # Run each module
        results = {}
        for module_name in modules:
            if module_name not in COLLECTORS:
                logger.warning(f"Unknown module: {module_name}")
                continue
            
            try:
                logger.info(f"Running: {module_name}")
                collector_func = COLLECTORS[module_name]
                results[module_name] = collector_func(engine)
                
            except Exception as e:
                logger.error(f"Module {module_name} failed: {e}")
                results[module_name] = {"error": str(e)}
        
        engine.close()
        
        self.data = results
        return results
    
    def format_output(self) -> str:
        """Format output based on selected format."""
        from .formatters import (
            CLIFormatter,
            JSONFormatter,
            HTMLFormatter,
            PDFFormatter,
            ExcelFormatter,
        )
        
        if self.format == "cli":
            formatter = CLIFormatter()
            return formatter.format(self.data)
        
        elif self.format == "json":
            formatter = JSONFormatter(pretty=True)
            return formatter.format(self.data)
        
        elif self.format == "html":
            formatter = HTMLFormatter()
            return formatter.format(self.data)
        
        elif self.format == "pdf":
            formatter = PDFFormatter()
            return formatter.format_from_data(
                self.data, 
                self.output
            )
        
        elif self.format == "excel":
            formatter = ExcelFormatter()
            if self.output:
                formatter.format_to_file(self.data, self.output)
                return f"Excel saved to {self.output}"
            return "Excel output requires --output file"
        
        return str(self.data)
    
    def save_output(self, content: Any) -> None:
        """Save output to file.
        
        Args:
            content: Output content
        """
        if self.output:
            if isinstance(content, bytes):
                with open(self.output, "wb") as f:
                    f.write(content)
            else:
                with open(self.output, "w", encoding="utf-8") as f:
                    f.write(str(content))
            
            logger.info(f"Output saved to {self.output}")


def main():
    """Main entry point - simplified CLI."""
    if not CLICK_AVAILABLE:
        print("Error: click is required for CLI")
        sys.exit(1)
    
    # Create a parentclick group to share options
    @click.group()
    def cli():
        """Windows Audit Suite - Comprehensive Windows system audit tool."""
        pass
    
    # Add options to group
    @cli.command()
    @click.option("--verbose", "-v", is_flag=True, help="Verbose output")
    @click.option("--output", "-o", type=click.Path(), help="Output file path")
    @click.option(
        "--format", 
        "-f", 
        type=click.Choice(["cli", "json", "html", "pdf", "excel"]),
        default="cli",
        help="Output format"
    )
    @click.option(
        "--modules", 
        "-m", 
        help="Modules to run (comma-separated)"
    )
    def run(verbose, output, format, modules):
        """Run the audit (default command)."""
        # Create CLI
        cli_obj = WindowsAuditCLI(
            verbose=verbose,
            output=output,
            format=format
        )
        
        # Run audit
        try:
            results = cli_obj.run(modules)
            
            # Output
            if format != "pdf" and format != "excel":
                content = cli_obj.format_output()
                
                if output:
                    cli_obj.save_output(content)
                else:
                    click.echo(content)
            else:
                cli_obj.format_output()
                click.echo(f"Output saved to {output}")
                
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
    
    # Make 'run' the default command
    cli.commands['run'] = cli.commands.pop('run')
    
    # Add list
    @cli.command(name='list')
    def list_modules():
        """List available modules."""
        click.echo("Available modules:")
        click.echo("")
        
        for module in AVAILABLE_MODULES:
            desc = MODULE_DESCRIPTIONS.get(module, "")
            click.echo(f"  {module:15s} - {desc}")
    
    # Run CLI default
    if len(sys.argv) == 1:
        sys.argv.append("run")
    
    # Run the CLI
    cli(obj={}, standalone_mode=False)


if __name__ == "__main__":
    main()