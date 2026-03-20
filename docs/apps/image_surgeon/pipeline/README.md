# Pipeline Types

> `apps/image_surgeon/pipeline/pipeline_types.py`

Configuration dataclasses for the image surgery pipeline.

---

## Overview

This module defines the **configuration structure** for image surgery pipelines using Python dataclasses.

---

## Classes

### `SurgeonConfig`

Main configuration class for image surgery operations.

```python
@dataclass
class SurgeonConfig:
    # REQUIRED
    mode: str                    # "clothes" | "background"
    input_image: Path            # Input image path
    
    # PROMPT-BASED SELECTION
    prompt: Optional[str] = None # Text prompt for asset matching or generation
    
    # BACKGROUND OPTIONS
    solid_color: Optional[Tuple[int, int, int]] = None  # RGB tuple
    background_image: Optional[Path] = None             # Background image
    transparent: bool = False                           # Transparent output
    
    # CLOTHES OPTIONS
    garment_path: Optional[Path] = None  # Specific garment file
    
    # PROCESSING
    upscale: float = 4.0        # Upscale factor
    steps: int = 40             # Inference steps
    
    # OUTPUT
    output_dir: Optional[Path] = None   # Custom output directory
    output_name: Optional[str] = None   # Custom filename
    auto_open: bool = False             # Open after generation
    
    # ADVANCED
    sam_model: str = "large"            # SAM2 model size
    save_raw_extract: bool = False      # Save raw extraction
```

---

## Field Details

### Mode Options

| Mode | Description |
|------|-------------|
| `"background"` | Replace or generate background |
| `"clothes"` | Virtual try-on (change garment) |

### Background Workflow

When `mode="background"`:

1. **Solid Color** - `solid_color=(R,G,B)` applies flat color
2. **Background Image** - `background_image=Path` composites onto image
3. **Generative** - `prompt="sunset beach"` uses SD inpainting
4. **Transparent** - `transparent=True` removes background

### Clothes Workflow

When `mode="clothes"`:

1. **Prompt Match** - `prompt="red dress"` finds best asset
2. **Direct Path** - `garment_path=Path` uses specific garment

---

## Validation

`__post_init__` performs automatic processing:

### Path Conversion
```python
# Strings converted to Path objects
self.input_image = Path(self.input_image)
if self.garment_path:
    self.garment_path = Path(self.garment_path)
```

### Auto-set Raw Extraction
```python
# Background mode auto-saves raw extraction
if self.mode == "background":
    self.save_raw_extract = True
```

---

## Usage Example

```python
from apps.image_surgeon.pipeline.pipeline_types import SurgeonConfig

# Background with solid color
config = SurgeonConfig(
    mode="background",
    input_image=Path("photo.jpg"),
    solid_color=(0, 0, 0),  # Black
)

# Background with AI generation
config = SurgeonConfig(
    mode="background",
    input_image=Path("photo.jpg"),
    prompt="beautiful sunset beach, golden hour",
)

# Clothes change with prompt matching
config = SurgeonConfig(
    mode="clothes",
    input_image=Path("photo.jpg"),
    prompt="red evening dress",
    upscale=4.0,
    steps=40,
)
```

---

# Asset Registry

> `apps/image_surgeon/pipeline/registry.py`

Asset discovery and scoring for garments and backgrounds.

---

## Constants

```python
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

CLOTHES_DIR = PROJECT_ROOT / "assets" / "apps_assets" / "image_surgeon" / "clothes"
BACKGROUNDS_DIR = PROJECT_ROOT / "assets" / "apps_assets" / "image_surgeon" / "backgrounds"
```

---

## Functions

### `discover_assets(asset_type)`

Discover available assets organized by category.

```python
def discover_assets(asset_type: str = "clothes") -> Dict[str, List[Path]]:
    """
    Args:
        asset_type: "clothes" or "backgrounds"
        
    Returns:
        Dict mapping category name to list of asset paths
        
    Example:
        {
            "dresses": [Path(".../dress_red.png"), ...],
            "lingerie": [Path(".../bra_black.png"), ...],
        }
    """
```

### `get_best_match(prompt, asset_type)`

Find best matching asset using keyword scoring.

```python
def get_best_match(prompt: str, asset_type: str = "clothes") -> Optional[Path]:
    """
    Scores assets by keyword overlap with prompt.
    Filename matches worth 2 points, category matches worth 1.
    
    Args:
        prompt: User's text prompt (e.g., "red evening dress")
        asset_type: "clothes" or "backgrounds"
        
    Returns:
        Path to best matching asset, or None if empty
    """
```

### `list_categories(asset_type)`

List available asset categories.

```python
def list_categories(asset_type: str = "clothes") -> List[str]:
    """Returns: ["dresses", "lingerie", "tops", ...]"""
```

---

## Asset Directory Structure

```
assets/apps_assets/image_surgeon/
├── clothes/
│   ├── dresses/
│   │   └── dress_evening_black.png
│   ├── lingerie/
│   │   ├── bra_lace_black.png
│   │   └── panty_lace_white.png
│   ├── tops/
│   │   └── tshirt_white_basic.png
│   └── ...
└── backgrounds/
    ├── nature/
    ├── studio/
    └── ...
```
