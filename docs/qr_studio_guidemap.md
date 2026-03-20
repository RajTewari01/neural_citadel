# QR Studio - Modular Architecture Guide

A complete blueprint for restructuring your QR code generator into a professional, production-ready application inspired by the `image_gen` pipeline architecture.

---

## Current State Analysis

Your `qrcode_utils.py` is a **monolithic file** (~600 lines) containing:
- Path configuration
- Data input logic (61 options)
- Color handling
- 7+ QR generation methods
- File I/O and logging

This works, but doesn't scale. Let's fix that.

---

## Target Architecture

```
qr_studio/
├── __init__.py
├── engine.py                    # Core QR generation engine
├── configs/
│   ├── __init__.py
│   ├── paths.py                 # All output/asset paths
│   └── defaults.py              # Default colors, sizes, error correction
├── pipeline/
│   ├── __init__.py
│   ├── pipeline_types.py        # QRConfig dataclass (like PipelineConfigs)
│   ├── svg.py                   # SVG QR pipeline
│   ├── gradient.py              # All gradient QRs (radial, square, etc.)
│   ├── logo.py                  # Logo-embedded QRs
│   └── styled.py                # Custom module drawers
├── data/
│   ├── __init__.py
│   ├── data_types.py            # Enum/Literal for 61 QR types
│   ├── handlers.py              # URL, WiFi, vCard, Crypto handlers
│   └── validators.py            # Input validation (URL, phone, email)
├── styles/
│   ├── __init__.py
│   ├── colors.py                # Color conversion, palettes
│   ├── gradients.py             # Gradient mask factories
│   └── drawers.py               # Module drawer presets
├── utils/
│   ├── __init__.py
│   ├── file_ops.py              # Save, open, sequence counter
│   └── logging_config.py        # Centralized logging setup
└── cli/
    ├── __init__.py
    └── main.py                  # CLI entry point (menu system)
```

---

## Component Breakdown

### 1. `configs/paths.py`
**What it does**: Single source of truth for all paths.

```python
# Example structure (don't copy, adapt)
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
ASSETS_DIR = BASE_DIR / "Assets"
OUTPUT_DIR = BASE_DIR / "Generated_Assets" / "QR_Codes"

QR_PATHS = {
    "svg": OUTPUT_DIR / "SVG_QRcodes",
    "gradient": OUTPUT_DIR / "Gradient_QRcodes",
    "logo": OUTPUT_DIR / "LOGO_QRcodes",
}

LOGO_PATH = ASSETS_DIR / "Logos" / "LOGO.png"
```

---

### 2. `pipeline/pipeline_types.py`
**What it does**: Defines a `QRConfig` dataclass that standardizes all generation parameters.

```python
@dataclass
class QRConfig:
    data: str                           # The encoded data
    output_type: Literal["svg", "png"]  # Output format
    output_dir: Path                    # Where to save
    
    # Style Options
    module_drawer: str = "rounded"      # rounded, square, circle, gapped
    error_correction: str = "H"         # L, M, Q, H
    
    # Colors (Optional)
    background_color: tuple = (255, 255, 255)
    foreground_color: tuple = (0, 0, 0)
    
    # Gradient (Optional)
    gradient_type: Optional[str] = None  # radial, vertical, horizontal, square
    gradient_colors: Optional[dict] = None
    
    # Logo (Optional)
    logo_path: Optional[Path] = None
    
    # Metadata
    box_size: int = 10
    border: int = 4
```

---

### 3. `data/handlers.py`
**What it does**: Separates data formatting logic from the UI. Each handler is a pure function.

| Handler | Input | Output |
|---------|-------|--------|
| `format_url(url)` | `"google.com"` | `"https://google.com"` |
| `format_wifi(ssid, password, type)` | `...` | `"WIFI:S:...;;"` |
| `format_vcard(name, phone, ...)` | `...` | `"BEGIN:VCARD\n..."` |
| `format_upi(id, name, amount)` | `...` | `"upi://pay?pa=..."` |
| `format_crypto(type, address)` | `...` | `"bitcoin:..."` |

**Why**: Your `data_taker()` currently mixes UI (input prompts) with logic (string formatting). Separate them.

---

### 4. `engine.py`
**What it does**: The core generator. Takes a `QRConfig`, returns a `Path` to the saved file.

```python
class QREngine:
    def __init__(self):
        self._ensure_directories()
        self.logger = self._setup_logging()
    
    def generate(self, config: QRConfig) -> Path:
        """Universal generation method."""
        qr = self._create_qr_object(config)
        img = self._apply_styles(qr, config)
        return self._save(img, config)
    
    def _create_qr_object(self, config):
        # Error correction, data, fit
        
    def _apply_styles(self, qr, config):
        # Drawer, gradient, logo
        
    def _save(self, img, config) -> Path:
        # Filename, save, return path
```

---

### 5. `cli/main.py`
**What it does**: User-facing menu. Calls handlers and engine.

```python
def main():
    print_menu()
    choice = get_user_choice()
    
    # Get formatted data from handler
    data = DATA_HANDLERS[choice]()  # e.g., handlers.format_wifi(...)
    
    # Build config
    config = QRConfig(data=data, ...)
    
    # Generate
    engine = QREngine()
    output_path = engine.generate(config)
    
    print(f"Saved: {output_path}")
```

---

## Feature Upgrades to Add

### Tier 1: Essential
| Feature | Location | Description |
|---------|----------|-------------|
| **Input Validation** | `data/validators.py` | Validate URLs, emails, phone numbers before encoding |
| **Preset Themes** | `styles/colors.py` | Named presets: "neon", "pastel", "corporate" |
| **Batch Generation** | `engine.py` | `generate_batch(configs: List[QRConfig])` |
| **CLI Flags** | `cli/main.py` | `--output`, `--style`, `--no-open` |

### Tier 2: Professional
| Feature | Location | Description |
|---------|----------|-------------|
| **REST API** | `api/routes.py` | FastAPI endpoints for web integration |
| **QR Scanning** | `scanner/` | Decode QR from camera/image |
| **Analytics DB** | `db/` | Track generated QRs, most used types |
| **Template System** | `templates/` | Pre-made brand templates (logo + colors) |

### Tier 3: Advanced
| Feature | Location | Description |
|---------|----------|-------------|
| **AI Logo Placement** | `styles/ai_logo.py` | Smart logo positioning based on QR density |
| **Bulk CSV Import** | `data/csv_handler.py` | Generate 1000 QRs from spreadsheet |
| **Custom Finder Patterns** | `styles/finders.py` | Replace corner squares with custom shapes |
| **Animated QR** | `pipeline/animated.py` | GIF QR codes with gradient animation |

---

## Migration Checklist

- [ ] Create folder structure
- [ ] Move path constants to `configs/paths.py`
- [ ] Create `QRConfig` dataclass
- [ ] Extract data formatters to `data/handlers.py`
- [ ] Refactor `engine.py` to use `QRConfig`
- [ ] Move color logic to `styles/colors.py`
- [ ] Move gradient masks to `styles/gradients.py`
- [ ] Create `cli/main.py` as new entry point
- [ ] Add input validation
- [ ] Add preset themes
- [ ] Write tests for each handler

---

## File Mapping: Old → New

| Old (`qrcode_utils.py`) | New Location |
|-------------------------|--------------|
| `BASE_DIR`, `SVG_QR_PATH`, etc. | `configs/paths.py` |
| `data_taker()` | `cli/main.py` (UI) + `data/handlers.py` (logic) |
| `color_converter()` | `styles/colors.py` |
| `random_gradient_picker()` | `styles/gradients.py` |
| `generate_svg_qr_code()` | `pipeline/svg.py` |
| `radial_gradient_qrcode()` | `pipeline/gradient.py` |
| `normal_logo_in_qr()` | `pipeline/logo.py` |
| `_get_next_sequence()` | `utils/file_ops.py` |
| `_open_file()` | `utils/file_ops.py` |
| Logging setup | `utils/logging_config.py` |

---

## Quick Start: First 3 Files to Create

### 1. `configs/paths.py`
Extract all `Path(...)` definitions.

### 2. `pipeline/pipeline_types.py`
Create `QRConfig` dataclass.

### 3. `engine.py`
Create `QREngine.generate(config: QRConfig)` that replaces all 7 methods.

Once these 3 are done, everything else is just refactoring existing code into the correct folders.

---

> **Pro Tip**: Your `image_gen` uses `PipelineConfigs` + `DiffusionEngine.generate()`. 
> Your QR Studio should use `QRConfig` + `QREngine.generate()`. Same pattern.
