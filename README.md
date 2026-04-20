# Windows Audit Suite

A comprehensive Windows Manager–level audit tool that runs directly on Windows machines and collects detailed system information across 8 modules.

## Features

- **8 Audit Modules**: System Information, Installed Software, Local Users, Printers, Network, Startup Programs, Browser Data, Advanced Features
- **Multi-Format Export**: CLI/Terminal, JSON, HTML, PDF, Excel/CSV
- **Windows Integration**: PowerShell, WMI/CIM, Registry access
- **Rich CLI Output**: Colored tables, progress indicators

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Run full audit with CLI output
windows-audit

# Export to JSON
windows-audit --format json --output report.json

# Export to HTML
windows-audit --format html --output report.html

# Export to PDF
windows-audit --format pdf --output report.pdf

# Export to Excel
windows-audit --format excel --output report.xlsx

# Run specific modules
windows-audit --modules system_info,software,users

# Verbose mode
windows-audit --verbose
```

## Module Details

| Module | Description |
|--------|-------------|
| System Information | Windows Edition, Version, Build, CPU, RAM, GPU, BIOS |
| Installed Software | All installed programs from registry |
| Local Users | Local user accounts with status flags |
| Printers | Installed printers and drivers |
| Network | Network adapters, IP config, WiFi profiles |
| Startup Programs | Registry and folder startup items |
| Browser Data | Bookmarks, history, extensions |
| Advanced | Drivers, processes, scheduled tasks, services |

## License

MIT