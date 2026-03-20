# Utility Tools

> `apps/movie_downloader/tools/`

Security and utility tools for downloaded content.

---

## 📁 Structure

```
tools/
├── __init__.py        # Package exports
└── virus_scanner.py   # Downloaded file security scan
```

---

## 1. Virus Scanner (`virus_scanner.py`)

Security scanning for downloaded files.

```python
class VirusScanner:
    """
    Scan downloaded files for malware.
    Supports multiple backends.
    """
    
    def __init__(self, backend: str = "auto"):
        """
        Args:
            backend: "clamav", "virustotal", or "auto"
        """
    
    def scan_file(self, file_path: Path) -> ScanResult:
        """
        Scan a single file.
        
        Returns:
            ScanResult with:
            - is_clean: bool
            - threats: List[str]
            - scan_time: float
        """
    
    def scan_directory(self, dir_path: Path) -> List[ScanResult]:
        """Scan all files in directory"""
    
    def quarantine(self, file_path: Path) -> Path:
        """Move suspicious file to quarantine"""
```

**Scan Backends:**

| Backend | Description | Requirements |
|---------|-------------|--------------|
| `clamav` | Local ClamAV scan | ClamAV installed |
| `virustotal` | VirusTotal API | API key in config |
| `hash` | Hash-based lookup | None |

**ScanResult Dataclass:**

```python
@dataclass
class ScanResult:
    file_path: Path       # Scanned file
    is_clean: bool        # True if no threats
    threats: List[str]    # Detected threat names
    scan_time: float      # Seconds to scan
    backend: str          # Scanner used
```

---

## CLI Usage

**Scan downloaded files:**
```bash
python runner.py scan
```

**Scan specific path:**
```bash
python runner.py scan --path /path/to/file.exe
python runner.py scan --path /path/to/directory/
```

---

## Configuration

In `configs/paths.py`:

```python
QUARANTINE_DIR = Path("assets/quarantine/")
VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY", "")
```

---

## Usage Example

```python
from apps.movie_downloader.tools.virus_scanner import VirusScanner

scanner = VirusScanner()

# Scan single file
result = scanner.scan_file(Path("download.exe"))
if not result.is_clean:
    print(f"Threats found: {result.threats}")
    scanner.quarantine(result.file_path)

# Scan directory
results = scanner.scan_directory(Path("downloads/"))
clean_files = [r for r in results if r.is_clean]
```
