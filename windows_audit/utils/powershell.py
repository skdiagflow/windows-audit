"""PowerShell execution utilities."""
import subprocess
import json
import logging
from typing import Any, Dict, List, Optional, Union

from .logging_utils import get_logger

logger = get_logger(__name__)


class PowerShellExecutor:
    """Execute PowerShell commands and scripts on Windows."""
    
    def __init__(
        self,
        timeout: int = 30,
        encoding: str = "utf-8",
        error_action: str = "Continue"
    ):
        """Initialize PowerShell executor.
        
        Args:
            timeout: Command timeout in seconds
            encoding: Output encoding
            error_action: PowerShell error action preference
        """
        self.timeout = timeout
        self.encoding = encoding
        self.error_action = error_action
    
    def run(
        self,
        command: str,
        params: Optional[Dict[str, Any]] = None,
        json_output: bool = False
    ) -> Union[str, List[Dict], Dict, None]:
        """Run a PowerShell command.
        
        Args:
            command: PowerShell command or script
            params: Optional parameters to pass to the command
            json_output: Expect JSON output
            
        Returns:
            Command output as string, list, or dict
            
        Raises:
            subprocess.TimeoutExpired: Command timed out
            subprocess.CalledProcessError: Command failed
        """
        # Build full command with error handling preference
        full_cmd = f"$ErrorActionPreference = '{self.error_action}'; {command}"
        
        # Add parameters if provided
        if params:
            param_str = "; ".join(f"${k} = {self._format_value(v)}" for k, v in params.items())
            full_cmd = f"{param_str}; {full_cmd}"
        
        logger.debug(f"Executing PowerShell: {command[:100]}...")
        
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", full_cmd],
                capture_output=True,
                text=True,
                encoding=self.encoding,
                timeout=self.timeout
            )
            
            # Check for errors
            if result.returncode != 0 and result.stderr:
                logger.warning(f"PowerShell stderr: {result.stderr}")
            
            output = result.stdout.strip()
            
            # Parse JSON if requested
            if json_output and output:
                try:
                    return json.loads(output)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON: {e}")
                    return output
            
            return output
            
        except subprocess.TimeoutExpired:
            logger.error(f"PowerShell command timed out after {self.timeout}s")
            raise
        except subprocess.CalledProcessError as e:
            logger.error(f"PowerShell command failed: {e}")
            raise
    
    def run_script(
        self,
        script: str,
        json_output: bool = False
    ) -> Union[str, List[Dict], Dict, None]:
        """Run a PowerShell script file.
        
        Args:
            script: Path to PowerShell script file
            json_output: Expect JSON output
            
        Returns:
            Script output
        """
        cmd = f"& '{script}'"
        return self.run(cmd, json_output=json_output)
    
    def _format_value(self, value: Any) -> str:
        """Format a Python value for PowerShell."""
        if isinstance(value, str):
            # Escape single quotes by doubling them
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        elif isinstance(value, bool):
            return "$true" if value else "$false"
        elif isinstance(value, (list, tuple)):
            items = ", ".join(self._format_value(v) for v in value)
            return f"@({items})"
        elif isinstance(value, dict):
            pairs = ", ".join(
                f"{self._format_value(k)} = {self._format_value(v)}"
                for k, v in value.items()
            )
            return f"@{{{pairs}}}"
        else:
            return str(value)
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get basic system information using PowerShell.
        
        Returns:
            System info dictionary
        """
        script = """
        @{
            ComputerName = $env:COMPUTERNAME
            UserName = $env:USERNAME
            OSVersion = [System.Environment]::OSVersion.VersionString
            Architecture = $env:PROCESSOR_ARCHITECTURE
            NumberOfProcessors = $env:NUMBER_OF_PROCESSORS
        } | ConvertTo-Json
        """
        result = self.run(script, json_output=True)
        if isinstance(result, dict):
            return result
        return {}


def execute_ps1(
    command: str,
    timeout: int = 30,
    json_output: bool = False
) -> Union[str, List[Dict], Dict, None]:
    """Convenience function to execute a PowerShell command.
    
    Args:
        command: PowerShell command
        timeout: Command timeout
        json_output: Expect JSON output
        
    Returns:
        Command output
    """
    executor = PowerShellExecutor(timeout=timeout)
    return executor.run(command, json_output=json_output)