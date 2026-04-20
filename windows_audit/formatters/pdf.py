"""PDF Output Formatter."""
import logging
from typing import Any, Dict
from pathlib import Path

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

from ..utils import get_logger

logger = get_logger(__name__)


class PDFFormatter:
    """Format audit results as PDF."""
    
    def __init__(self, page_size: str = "A4"):
        """Initialize PDF formatter.
        
        Args:
            page_size: Page size (A4, Letter)
        """
        self.page_size = page_size
        
        if not WEASYPRINT_AVAILABLE:
            logger.warning("WeasyPrint not available - PDF export disabled")
    
    def format(
        self, 
        html_content: str, 
        output_path: str = None
    ) -> bytes:
        """Convert HTML to PDF.
        
        Args:
            html_content: HTML content
            output_path: Optional output file path
            
        Returns:
            PDF bytes
        """
        if not WEASYPRINT_AVAILABLE:
            raise RuntimeError("WeasyPrint not available")
        
        try:
            html = HTML(string=html_content)
            
            # Generate PDF
            pdf = html.write_pdf(
                stylesheets=[CSS(string=self._get_styles())]
            )
            
            # Save to file if path provided
            if output_path:
                with open(output_path, "wb") as f:
                    f.write(pdf)
                
                logger.info(f"PDF saved to {output_path}")
            
            return pdf
            
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            raise
    
    def format_from_data(
        self, 
        data: Dict[str, Any], 
        output_path: str = None
    ) -> bytes:
        """Generate PDF directly from data.
        
        Args:
            data: Audit results
            output_path: Optional output file path
            
        Returns:
            PDF bytes
        """
        # First convert to HTML
        from .html import HTMLFormatter
        
        html_fmt = HTMLFormatter()
        html_content = html_fmt.format(data)
        
        # Then convert to PDF
        return self.format(html_content, output_path)
    
    def _get_styles(self) -> str:
        """Get CSS styles for PDF."""
        return f"""
        @page {{
            size: {self.page_size};
            margin: 2cm;
        }}
        
        body {{
            font-family: Arial, sans-serif;
            font-size: 10pt;
            line-height: 1.5;
        }}
        
        h1 {{
            color: #333;
            border-bottom: 2px solid #0066cc;
            padding-bottom: 10px;
        }}
        
        h2 {{
            color: #0066cc;
            margin-top: 20px;
            page-break-before: always;
        }}
        
        h3 {{
            color: #333;
            margin-top: 15px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }}
        
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        
        th {{
            background: #0066cc;
            color: white;
            font-weight: bold;
        }}
        
        tr:nth-child(even) {{
            background: #f9f9f9;
        }}
        
        .summary {{
            background: #e6f3ff;
            padding: 15px;
            margin: 10px 0;
        }}
        
        .footer {{
            text-align: center;
            color: #666;
            margin-top: 20px;
            font-size: 8pt;
        }}
        
        @page :first {{
            margin-top: 0;
        }}
        """