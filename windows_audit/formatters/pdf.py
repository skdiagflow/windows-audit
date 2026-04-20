"""PDF Output Formatter using ReportLab."""
import logging
from typing import Any, Dict
from pathlib import Path

# Try reportlab first (no GTK required)
try:
    from reportlab.lib.pagesizes import A4, LETTER
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    _reportlab_error = ""

# Fallback to WeasyPrint if reportlab not available
if not REPORTLAB_AVAILABLE:
    try:
        from weasyprint import HTML, CSS
        WEASYPRINT_AVAILABLE = True
    except (ImportError, OSError):
        WEASYPRINT_AVAILABLE = False

from ..utils import get_logger

logger = get_logger(__name__)


class PDFFormatter:
    """Format audit results as PDF using ReportLab."""
    
    def __init__(self, page_size: str = "A4"):
        """Initialize PDF formatter."""
        self.page_size = A4 if page_size.upper() == "A4" else LETTER
        
        if not REPORTLAB_AVAILABLE and not WEASYPRINT_AVAILABLE:
            logger.warning("PDF libraries not available - install reportlab: pip install reportlab")
    
    def format(
        self, 
        data: Dict[str, Any], 
        output_path: str = None
    ) -> bytes:
        """Convert data to PDF.
        
        Args:
            data: Audit results
            output_path: Optional output file path
            
        Returns:
            PDF bytes
        """
        if REPORTLAB_AVAILABLE:
            return self._format_with_reportlab(data, output_path)
        elif WEASYPRINT_AVAILABLE:
            return self._format_with_weasyprint(data, output_path)
        else:
            raise RuntimeError(
                "PDF generation requires reportlab. Install with: pip install reportlab"
            )
    
    def _format_with_reportlab(
        self, 
        data: Dict[str, Any], 
        output_path: str = None
    ) -> bytes:
        """Format using ReportLab."""
        from io import BytesIO
        from datetime import datetime
        
        buffer = BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.page_size,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=0.75*inch
        )
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#0066cc'),
            spaceAfter=12
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#333333'),
            spaceAfter=10,
            spaceBefore=20
        )
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
        
        # Build content
        story = []
        
        # Title
        story.append(Paragraph("Windows Audit Report", title_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
        story.append(Spacer(1, 0.5*inch))
        
        # System Info
        if 'system_info' in data:
            story.append(Paragraph("System Information", heading_style))
            si = data['system_info']
            
            if 'os' in si:
                os_info = si.get('os', {})
                story.append(Paragraph(f"<b>Operating System:</b> {os_info.get('name', 'N/A')}", normal_style))
                story.append(Paragraph(f"<b>Version:</b> {os_info.get('version', '')}", normal_style))
                story.append(Paragraph(f"<b>Build:</b> {os_info.get('build', '')}", normal_style))
            
            if 'cpu' in si:
                cpu = si.get('cpu', {})
                story.append(Paragraph(f"<b>CPU:</b> {cpu.get('name', 'N/A')}", normal_style))
            
            if 'memory' in si:
                mem = si.get('memory', {})
                story.append(Paragraph(f"<b>RAM:</b> {mem.get('total_physical_gb', 'N/A')} GB", normal_style))
        
        # Software Summary
        if 'software' in data:
            story.append(PageBreak())
            story.append(Paragraph("Installed Software", heading_style))
            sw = data['software']
            summary = sw.get('summary', {})
            
            software_list = sw.get('all_software', [])
            microsoft_list = sw.get('microsoft', [])
            third_party_list = sw.get('third_party', [])
            
            table_data = [
                ['Category', 'Count'],
                ['Total', str(len(software_list))],
                ['Microsoft', str(len(microsoft_list))],
                ['Third-Party', str(len(third_party_list))],
            ]
            
            t = Table(table_data, colWidths=[2*inch, 1.5*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            story.append(t)
        
        # Users Summary
        if 'users' in data:
            story.append(PageBreak())
            story.append(Paragraph("Local Users", heading_style))
            usr = data['users']
            summary = usr.get('summary', {})
            
            table_data = [
                ['Status', 'Count'],
                ['Total Users', str(summary.get('total', 0))],
                ['Enabled', str(summary.get('enabled', 0))],
                ['Disabled', str(summary.get('disabled', 0))],
            ]
            
            t = Table(table_data, colWidths=[2*inch, 1.5*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            story.append(t)
        
        # Network Summary
        if 'network' in data:
            story.append(PageBreak())
            story.append(Paragraph("Network Adapters", heading_style))
            net = data['network']
            summary = net.get('summary', {})
            
            story.append(Paragraph(f"<b>Total Adapters:</b> {summary.get('total', 0)}", normal_style))
            story.append(Paragraph(f"<b>WiFi Adapters:</b> {summary.get('wifi', 0)}", normal_style))
            story.append(Paragraph(f"<b>Ethernet:</b> {summary.get('ethernet', 0)}", normal_style))
        
        # Advanced Summary
        if 'advanced' in data:
            story.append(PageBreak())
            story.append(Paragraph("Advanced Features", heading_style))
            adv = data['advanced']
            summary = adv.get('summary', {})
            
            table_data = [
                ['Category', 'Count'],
                ['Drivers', str(summary.get('drivers', 0))],
                ['Processes', str(summary.get('processes', 0))],
                ['Scheduled Tasks', str(summary.get('scheduled_tasks', 0))],
                ['Services', str(summary.get('services', 0))],
            ]
            
            t = Table(table_data, colWidths=[2*inch, 1.5*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            story.append(t)
        
        # Build PDF
        doc.build(story)
        
        pdf_data = buffer.getvalue()
        
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_data)
            logger.info(f"PDF saved to {output_path}")
        
        return pdf_data
    
    def _format_with_weasyprint(
        self, 
        data: Dict[str, Any], 
        output_path: str = None
    ) -> bytes:
        """Format using WeasyPrint (fallback)."""
        from .html import HTMLFormatter
        html_fmt = HTMLFormatter()
        html_content = html_fmt.format(data)
        
        html = HTML(string=html_content)
        pdf = html.write_pdf()
        
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf)
            logger.info(f"PDF saved to {output_path}")
        
        return pdf
    
    def format_from_data(
        self, 
        data: Dict[str, Any], 
        output_path: str = None
    ) -> bytes:
        """Generate PDF directly from data (compatibility method)."""
        return self.format(data, output_path)
    
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