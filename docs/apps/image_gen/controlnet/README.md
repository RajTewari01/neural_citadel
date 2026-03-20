# ControlNet Modules

> `apps/image_gen/controlnet/`

Guidance modules for controlled image generation using ControlNet.

---

## Overview

ControlNet allows you to **guide image generation** using:
- Edge maps (Canny)
- Depth maps
- Pose skeletons (OpenPose)

---

## Available Modules

| File | Control Type | Purpose |
|------|--------------|---------|
| `base.py` | - | Shared utilities |
| `canny.py` | Canny | Edge detection for line art |
| `depth.py` | Depth | 3D-aware composition |
| `openpose.py` | OpenPose | Human pose guidance |

---

## Module Details

### `base.py` - Shared Utilities

```python
from pathlib import Path

def get_project_root() -> Path:
    """Dynamically find project root."""

def load_controlnet(control_type: str):
    """Load ControlNet model by type."""
```

---

### `canny.py` - Edge Detection

Extracts edges from an image for guiding generation.

```python
from apps.image_gen.controlnet.canny import (
    extract_canny,      # Get edge map from image
    load_controlnet,    # Load Canny ControlNet model
    apply_controlnet,   # Apply to pipeline
)

# Extract edges from reference image
edge_map = extract_canny(
    image,
    low_threshold=100,
    high_threshold=200
)

# Load ControlNet
controlnet = load_controlnet()

# Apply to generation
result = apply_controlnet(
    pipe,
    controlnet,
    edge_map,
    prompt="line art of a cat",
    scale=1.0
)
```

**Use cases:**
- Line art conversion
- Architectural drawings
- Edge-guided composition

---

### `depth.py` - Depth Estimation

Uses MiDaS to estimate depth and guide 3D-aware generation.

```python
from apps.image_gen.controlnet.depth import (
    estimate_depth,     # Get depth map from image
    load_controlnet,    # Load Depth ControlNet model
    apply_controlnet,   # Apply to pipeline
)

# Estimate depth from reference image
depth_map = estimate_depth(image)

# Load ControlNet
controlnet = load_controlnet()

# Apply to generation
result = apply_controlnet(
    pipe,
    controlnet,
    depth_map,
    prompt="3D landscape",
    scale=1.0
)
```

**Use cases:**
- 3D-aware compositions
- Depth-based styling
- Maintaining spatial relationships

---

### `openpose.py` - Pose Detection

Detects human poses for pose-guided generation.

```python
from apps.image_gen.controlnet.openpose import (
    detect_pose,        # Get pose skeleton from image
    load_controlnet,    # Load OpenPose ControlNet model
    apply_controlnet,   # Apply to pipeline
)

# Detect pose from reference image
pose_map = detect_pose(image)

# Load ControlNet
controlnet = load_controlnet()

# Apply to generation
result = apply_controlnet(
    pipe,
    controlnet,
    pose_map,
    prompt="dancing woman",
    scale=1.0
)
```

**Use cases:**
- Character pose matching
- Action scenes
- Multi-person compositions

---

## Model Files

ControlNet models should be placed in:
```
assets/models/image_gen/controlnet/
├── control_v11p_sd15_canny.pth
├── control_v11f1p_sd15_depth.pth
└── control_v11p_sd15_openpose.pth
```

Paths are configured in `configs/paths.py`.

---

## Usage in Pipeline

From `pipeline/types.py`:

```python
from apps.image_gen.pipeline.types import PipelineConfigs, ControlNetConfig

config = PipelineConfigs(
    base_model=Path("model.safetensors"),
    output_dir=Path("output/"),
    prompt="a landscape",
    c_net=[
        ControlNetConfig(
            control_type="canny",
            image_path=Path("reference.png"),
            scale=1.0
        )
    ]
)
```

---

## ControlNetConfig

```python
@dataclass
class ControlNetConfig:
    control_type: Literal["canny", "depth", "openpose"]
    image_path: Union[str, Path]  # Reference image
    scale: float = 1.0            # Guidance strength (0-1)
```

---

## Tips

1. **Scale**: Lower scale (0.5-0.7) allows more creative freedom
2. **Canny thresholds**: Adjust for cleaner/noisier edges
3. **Multiple ControlNets**: Can combine (e.g., Canny + Depth)
4. **VRAM**: Each ControlNet adds ~1GB VRAM usage
