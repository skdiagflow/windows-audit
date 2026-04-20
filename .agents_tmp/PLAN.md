# 1. OBJECTIVE

Build a comprehensive Windows Manager–level audit suite (similar to Yamicsoft) that runs directly on Windows machines and collects detailed system information across 8 modules: System Information, Installed Software, Local Users, Printers, Network, Startup Programs, Browser Data, and Advanced Features. The tool must export output in CLI/terminal, JSON, HTML report, PDF, and Excel/CSV formats.

## Problem Statement

Users need a unified Windows audit tool to inventory their system configuration, installed software, user accounts, network settings, startup items, and browser data for compliance, troubleshooting, or migration purposes. No single tool currently provides all these capabilities with multi-format export options.

---

# 2. CONTEXT SUMMARY

## Target Environment
- **Platform**: Windows 10/11 (x64/x86)
- **Execution**: Direct local execution (not remote)
- **Privileges**: Standard user (most data) + Administrator elevated (some registry/services data)

## Technology Stack
- **Core Language**: Python 3.10+
- **Windows Integration**: PowerShell subprocess calls + pywin32 for Windows API
- **Data Collection**: PowerShell commands + WMI/CIM queries + registry reads + filesystem access
- **Output Formats**: 
  - CLI/Terminal (rich colored output with tqdm)
  - JSON (structured export)
  - HTML (styled report)
  - PDF (via WeasyPrint or reportlab)
  - Excel/CSV (via openpyxl/xlsxwriter)

## Key Dependencies
- `pywin32` - Windows API access
- `psutil` - System info
- `openpyxl` / `xlsxwriter` - Excel export
- `weasyprint` / `reportlab` - PDF generation
- `jinja2` - HTML templates
- `colorama` - CLI colors
- `requests` - Browser API detection

---

# 3. APPROACH OVERVIEW

## Architecture
A modular Python-based CLI application with:
1. **Core Engine**: Orchestrates data collection via PowerShell/WMI/registry
2. **Collector Modules**: Each module class responsible for specific data collection
3. **Formatter System**: Multiple output handlers (CLI, JSON, HTML, PDF, Excel)
4. **CLI Interface**: Click or argparse-based command-line interface

## Data Collection Strategy
| Module | Primary Method | Fallback |
|--------|---------------|----------|
| System Info | WMI/CIM + PowerShell | Registry |
| Software | Registry + PowerShell | Directory scan |
| Users | WMI/CIM | NetUser* APIs |
| Printers | WMI/CIM + PowerShell | Registry |
| Network | WMI/CIM + PowerShell | ipconfig/netsh |
| Startup | Registry + Filesystem | Startup folder |
| Browser | Filesystem + JSON parsing | Browser APIs |
| Advanced | WMI + PowerShell + Scanners | Various |

## Module Execution Order
1. System Information (Foundation - validates environment)
2. Installed Software (Inventory)
3. Local Users (Security audit)
4. Printers (Hardware)
5. Network (Connectivity)
6. Startup Programs (Performance)
7. Browser Module (Browser-specific)
8. Advanced Features (System-wide)

---

# 4. IMPLEMENTATION STEPS

## Phase 1: Core Infrastructure

### Step 1.1: Project Setup & Configuration
- Create project directory structure
- Set up Python virtual environment
- Configure pyproject.toml / setup.py
- Add all dependencies
- Verify Python + PowerShell connectivity

### Step 1.2: Core Engine Framework
- Create `AuditEngine` main class
- Implement PowerShell subprocess executor
- Implement WMI/CIM query helper
- Implement registry reader
- Add logging system
- Add error handling & recovery

### Step 1.3: Base Collector Classes
- Create abstract `Collector` base class
- Implement common data collection utilities
- Add result caching mechanism
- Implement parallel execution support

---

## Phase 2: Core Modules (MVP)

### Step 2.1: System Information Module
- Windows Edition (win_product)
- Windows Version (win_version)
- Build Number (win_build)
- Architecture (x64/x86)
- CPU Name & Cores
- Total RAM
- GPU Name & Driver
- BIOS Serial
- Motherboard info
- Disk Total/Free space
- DirectX Version
- Generate MSINFO32 export

### Step 2.2: Installed Software Module
- Read registry uninstall keys
- Query PowerShell Get-Package
- Collect: Name, Version, Publisher, Install Location
- Separate Microsoft vs Third-party
- Handle multiple registry hives

### Step 2.3: Local Users Module
- Query WMI Win32_UserAccount
- Get all local users
- Extract: Disabled, Lockout, PasswordRequired flags
- Handle domain users separately

### Step 2.4: Printers Module
- Query WMI Win32_Printer
- Collect: Name, Driver, Port
- Identify Default printer
- Handle printer status

### Step 2.5: Network Module
- Query WMI Win32_NetworkAdapter
- Extract: IPv4, Gateway, DNS, MAC
- Saved WiFi profiles via netsh
- WiFi security type detection

### Step 2.6: Startup Programs Module
- Read HKLM Run registry
- Read HKCU Run registry
- Scan Startup folder
- Collect all startup items

---

## Phase 3: Browser Module

### Step 3.1: Browser Detection
- Detect installed browsers (Chrome, Firefox, Edge, Brave, Opera)
- Identify default browser via registry
- Handle portable installations

### Step 3.2: Browser Data Collection
- Chrome/Chromium bookmarks parsing (JSON)
- Firefox places.sqlite parsing
- Browser extensions list
- Browser history extraction
- Cookie extraction (optional, Advanced)

### Step 3.3: Consolidated Browser Report
- Merge all browser bookmarks
- Unified bookmarks output
- Cross-browser deduplication

---

## Phase 4: Advanced Features

### Step 4.1: Installed Drivers
- Query WMI Win32_PnPSignedDriver
- Driver list with version/vendor
- Digital signature status

### Step 4.2: Running Processes
- Query WMI Win32_Process
- Process name, PID, Path
- Memory usage

### Step 4.3: Scheduled Tasks
- Query scheduled tasks via PowerShell
- Task name, status, last run
- Next run time

### Step 4.4: Services
- Query WMI Win32_Service
- Service name, status, startup type
- Account info

### Step 4.5: Firewall Status
- Query Windows Firewall via netsh
- Profile status (Domain/Private/Public)
- Rule count

### Step 4.6: Defender Status
- Query Windows Security Center
- Real-time protection status
- Last scan info

### Step 4.7-4.9: Optional Advanced
- Browser cookies (if requested)
- Browser passwords (if requested, secure)
- EXE conversion (if requested)

---

## Phase 5: Output Formatters

### Step 5.1: CLI/Terminal Output
- Rich colored output with colorama/rich
- Table-formatted display
- Progress indicators
- Module-by-module output

### Step 5.2: JSON Export
- Structured JSON output
- All modules in single file
- Pretty-printed option
- Minified option

### Step 5.3: HTML Report
- Jinja2 template design
- Styled HTML report
- CSS styling inline
- Responsive design
- Module sections with anchors

### Step 5.4: PDF Export
- Convert HTML to PDF
- WeasyPrint or reportlab
- Page numbers
- Header/footer
- Professional formatting

### Step 5.5: Excel/CSV Export
- Separate sheets per module (Excel)
- CSV option for each module
- Cell formatting
- Column auto-sizing
- Headers

---

## Phase 6: Integration & CLI

### Step 6.1: CLI Interface
- Click-based CLI
- Module selection flags
- Output format selection
- Verbose mode
- Export path specification

### Step 6.2: Main Entry Point
- `windows-audit` command
- Interactive mode
- Batch mode
- Help system

### Step 6.3: HTML Report Generation
- Automated HTML report creation
- Customizable templates
- Theme selection

---

## Phase 7: Testing & Validation

### Step 7.1: Unit Tests
- Test each collector module
- Mock PowerShell/WMI responses
- Test error handling

### Step 7.2: Integration Tests
- Run on actual Windows system
- Validate data accuracy
- Cross-validate with system tools

### Step 7.3: Output Validation
- Verify JSON schema
- Verify HTML rendering
- Verify PDF generation
- Verify Excel/CSV content

---

# 5. TESTING AND VALIDATION

## Success Criteria

| Module | Validation Method | Expected Output |
|--------|-----------------|------------------|
| System Info | Compare with MSINFO32 | Match Windows version, CPU, RAM, GPU |
| Software | Compare with Add/Remove Programs | All installed software listed |
| Users | Compare with Local Users UI | All local users with correct flags |
| Printers | Compare with Devices & Printers | All printers with correct drivers |
| Network | Compare with ipconfig / ncpa.cpl | All adapters, IPs, gateways |
| Startup | Compare with Task Manager Startup | All startup items |
| Browser | Manual browser check | All bookmarks, extensions |
| Advanced | Compare with respective tools | Services, processes, tasks match |

## Output Validation

- **CLI**: Formatted tables display correctly, colors work
- **JSON**: Valid JSON, no parsing errors
- **HTML**: Renders in browser, styles applied
- **PDF**: Opens in PDF reader, pages intact
- **Excel**: Opens in Excel, all data present
- **CSV**: Opens in spreadsheet, parses correctly

## Test Environment
- Windows 10/11 (virtual machine or test system)
- Python 3.10+
- Administrator privileges for full data access

---

## File Structure

```
windows-audit/
├── windows_audit/
│   ├── __init__.py
│   ├── __main__.py
│   ├── engine.py              # Core engine
│   ├── collectors/            # Collector modules
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── system_info.py
│   │   ├── software.py
│   │   ├── users.py
│   │   ├── printers.py
│   │   ├── network.py
│   │   ├── startup.py
│   │   ├── browser.py
│   │   └── advanced.py
│   ├── formatters/           # Output formatters
│   │   ├── __init__.py
│   │   ├── cli.py
│   │   ├── json.py
│   │   ├── html.py
│   │   ├── pdf.py
│   │   └── excel.py
│   ├── cli.py                # CLI interface
│   └── utils/                # Utilities
│       ├── __init__.py
│       ├── powershell.py
│       ├── wmi.py
│       └── registry.py
├── templates/                # HTML templates
│   ├── base.html
│   └── report.html
├── tests/                    # Test suite
├── pyproject.toml
├── setup.py
├── requirements.txt
├── requirements-dev.txt
└── README.md
```
