# Configuration

> `configs/`

Centralized configuration for the entire project.

---

## Overview

```
configs/
├── paths.py          # All model paths and directories
└── secrets/          # API keys and credentials (gitignored)
    └── socials.env   # Social media credentials
```

---

## `paths.py` - Centralized Paths

All model paths for the image generation system. **Edit this file if you move models.**

### Base Directories

```python
ROOT_DIR = Path(__file__).resolve().parent.parent  # Project root
ASSETS_DIR = ROOT_DIR / "assets"
MODELS_DIR = ASSETS_DIR / "models" / "image_gen"
```

All paths are **dynamically resolved** from the file location - no hardcoded paths.

---

### Upscaler Models

```python
UPSCALERS_DIR = MODELS_DIR / "upscalers"

UPSCALER_MODELS = {
    "R-ESRGAN 4x+": UPSCALERS_DIR / "RealESRGAN_x4plus.pth",
    "R-ESRGAN 4x+ Anime6B": UPSCALERS_DIR / "RealESRGAN_x4plus_anime_6B.pth",
    "4x-UltraSharp": UPSCALERS_DIR / "4x-UltraSharp.pth",
}

UPSCALER_CONFIGS = {
    "R-ESRGAN 4x+": {"num_block": 23, "scale": 4},
    "R-ESRGAN 4x+ Anime6B": {"num_block": 6, "scale": 4},
    "4x-UltraSharp": {"num_block": 23, "scale": 4},
}
```

---

### ControlNet Models

```python
CONTROLNET_DIR = MODELS_DIR / "controlnet"

CONTROLNET_MODELS = {
    "canny": CONTROLNET_DIR / "control_v11p_sd15_canny.pth",
    "depth": CONTROLNET_DIR / "control_v11f1p_sd15_depth.pth",
    "openpose": CONTROLNET_DIR / "control_v11p_sd15_openpose.pth",
}
```

---

### Diffusion Models

```python
DIFFUSION_DIR = MODELS_DIR / "diffusion"

DIFFUSION_MODELS = {
    # Add your models here:
    # "realistic_vision": DIFFUSION_DIR / "realisticVisionV60.safetensors",
}
```

---

### LoRA Models

```python
LORA_DIR = MODELS_DIR / "lora"

LORA_MODELS = {
    # Add your LoRAs here:
    # "chastity": LORA_DIR / "chastity cage.safetensors",
}
```

---

### Output Directories

```python
OUTPUT_DIR = ASSETS_DIR / "generated"
CANNY_CACHE_DIR = OUTPUT_DIR / "canny_cache"
```

---

### Helper Functions

```python
def get_upscaler_path(name: str) -> Path:
    """Get upscaler model path by name."""
    if name not in UPSCALER_MODELS:
        raise ValueError(f"Unknown: {name}")
    return UPSCALER_MODELS[name]

def get_controlnet_path(name: str) -> Path:
    """Get ControlNet model path by name."""
    if name not in CONTROLNET_MODELS:
        raise ValueError(f"Unknown: {name}")
    return CONTROLNET_MODELS[name]

def validate_paths() -> List[str]:
    """Check if all model paths exist. Returns missing files."""
    missing = []
    for name, path in UPSCALER_MODELS.items():
        if not path.exists():
            missing.append(f"Upscaler '{name}': {path}")
    for name, path in CONTROLNET_MODELS.items():
        if not path.exists():
            missing.append(f"ControlNet '{name}': {path}")
    return missing
```

---

## Usage

```python
from configs.paths import (
    UPSCALER_MODELS,
    CONTROLNET_MODELS,
    get_upscaler_path,
    validate_paths
)

# Get a specific model path
path = get_upscaler_path("4x-UltraSharp")

# Check for missing models
missing = validate_paths()
if missing:
    print("Missing models:")
    for m in missing:
        print(f"  - {m}")
```

---

## Expected Directory Structure

```
assets/models/image_gen/
├── upscalers/
│   ├── RealESRGAN_x4plus.pth
│   ├── RealESRGAN_x4plus_anime_6B.pth
│   └── 4x-UltraSharp.pth
├── controlnet/
│   ├── control_v11p_sd15_canny.pth
│   ├── control_v11f1p_sd15_depth.pth
│   └── control_v11p_sd15_openpose.pth
├── diffusion/
│   └── (your model checkpoints)
└── lora/
    └── (your LoRA files)
```

---

## Adding New Models

1. Download the model file
2. Place in appropriate directory
3. Add entry to the corresponding dictionary in `paths.py`

```python
DIFFUSION_MODELS = {
    "my_new_model": DIFFUSION_DIR / "my_model.safetensors",
}
```
