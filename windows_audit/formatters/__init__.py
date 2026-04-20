"""Windows Audit Formatters."""

from .cli import CLIFormatter
from .json import JSONFormatter
from .html import HTMLFormatter
from .pdf import PDFFormatter
from .excel import ExcelFormatter, CSVFormatter

__all__ = [
    "CLIFormatter",
    "JSONFormatter",
    "HTMLFormatter",
    "PDFFormatter",
    "ExcelFormatter",
    "CSVFormatter",
]

# Format mapping
FORMATS = {
    "cli": CLIFormatter,
    "json": JSONFormatter,
    "html": HTMLFormatter,
    "pdf": PDFFormatter,
    "excel": ExcelFormatter,
    "csv": CSVFormatter,
}