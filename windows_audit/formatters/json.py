"""JSON Output Formatter."""
import json
import logging
from datetime import datetime
from typing import Any, Dict

from ..utils import get_logger

logger = get_logger(__name__)


class JSONFormatter:
    """Format audit results as JSON."""
    
    def __init__(
        self,
        pretty: bool = True,
        minified: bool = False,
        indent: int = 2
    ):
        """Initialize JSON formatter.
        
        Args:
            pretty: Pretty print output
            minified: Minified output (overrides pretty)
            indent: Indentation spaces
        """
        self.pretty = pretty and not minified
        self.minified = minified
        self.indent = indent if pretty else None
    
    def format(self, data: Dict[str, Any]) -> str:
        """Format data as JSON string.
        
        Args:
            data: Audit results
            
        Returns:
            JSON string
        """
        # Add metadata
        output = {
            "generated": datetime.now().isoformat(),
            "audit": data,
        }
        
        if self.minified:
            return json.dumps(output, separators=(",", ":"))
        
        return json.dumps(
            output, 
            indent=self.indent, 
            ensure_ascii=False,
            default=str
        )
    
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
            
            logger.info(f"JSON saved to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save JSON: {e}")
            raise