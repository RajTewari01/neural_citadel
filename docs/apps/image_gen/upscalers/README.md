# Upscalers

> `apps/image_gen/upscalers/`

Image upscaling modules for 4x resolution enhancement.

---

## Overview

All upscalers provide 4x resolution increase. Choose based on:
- VRAM availability
- Image type (photo/anime)
- Speed requirements

---

## Available Upscalers

| File | Name | VRAM | Quality | Speed | Best For |
|------|------|------|---------|-------|----------|
| `lanczos.py` | Lanczos | 0 (CPU) | Good | Fast | Fallback |
| `realesrgan_4x.py` | R-ESRGAN 4x+ | ~1GB | Excellent | Medium | Photos |
| `realesrgan_anime.py` | Anime6B | ~0.5GB | Good | Fast | Anime |
| `ultrasharp.py` | 4x-UltraSharp | ~1GB | Best | Medium | All |
| `diffusion_upscale.py` | Diffusion | ~2GB | Details | Slow | Details |

---

## Common API

All upscalers share the same interface:

```python
from apps.image_gen.upscalers.<module> import upscale

# Upscale a PIL Image
upscaled_image = upscale(image)  # Returns 4x resolution PIL.Image
```

---

## Module Details

### `base.py` - Shared Utilities

Common functions used by Real-ESRGAN upscalers:

```python
def flush_vram():
    """Clear CUDA memory."""

def create_upsampler(model_path, num_block=23, scale=4):
    """Create RealESRGANer instance."""

def run_upscale(upsampler, image):
    """Run upscaling and return PIL Image."""
```

---

### `lanczos.py` - CPU Lanczos

**Zero VRAM usage** - runs entirely on CPU.

```python
from apps.image_gen.upscalers.lanczos import upscale

upscaled = upscale(
    image,
    scale=4,           # Scale factor
    sharpening=True,   # Apply sharpening
    sharpening_strength=1.0,
    cinematic=False    # Cinematic color grading
)
```

**Features:**
- Two-pass sharpening
- Contrast enhancement
- Optional cinematic color grading
- UnsharpMask + DETAIL enhancement

---

### `realesrgan_4x.py` - R-ESRGAN 4x+

General-purpose Real-ESRGAN model.

```python
from apps.image_gen.upscalers.realesrgan_4x import upscale

upscaled = upscale(image)
```

**Model:** `RealESRGAN_x4plus.pth`
**Architecture:** RRDB with 23 blocks
**Best for:** Realistic photos

---

### `realesrgan_anime.py` - R-ESRGAN Anime6B

Lightweight model optimized for anime/illustrations.

```python
from apps.image_gen.upscalers.realesrgan_anime import upscale

upscaled = upscale(image)
```

**Model:** `RealESRGAN_x4plus_anime_6B.pth`
**Architecture:** RRDB with 6 blocks (smaller)
**Best for:** Anime, illustrations, line art

---

### `ultrasharp.py` - 4x-UltraSharp

Best balance of quality and performance.

```python
from apps.image_gen.upscalers.ultrasharp import upscale

upscaled = upscale(image)
```

**Model:** `4x-UltraSharp.pth`
**Architecture:** RRDB with 23 blocks
**Best for:** All image types, default choice

---

### `diffusion_upscale.py` - Diffusion Upscale

Uses Stable Diffusion img2img for upscaling. Adds detail hallucination.

```python
from apps.image_gen.upscalers.diffusion_upscale import upscale

upscaled = upscale(
    image,
    prompt="detailed, sharp",  # Guide the upscaling
    strength=0.3,              # Lower = closer to original
    steps=20
)
```

**Features:**
- Adds realistic details
- GPU-intensive (~2GB+ VRAM)
- Automatic CPU Lanczos fallback on OOM
- Uses tiling for large images

---

## Model Files

Models should be placed in:
```
assets/models/image_gen/upscalers/
├── RealESRGAN_x4plus.pth
├── RealESRGAN_x4plus_anime_6B.pth
└── 4x-UltraSharp.pth
```

Paths are configured in `configs/paths.py`.

---

## Usage in Pipeline

From `pipeline/types.py`:

```python
config = PipelineConfigs(
    base_model=Path("model.safetensors"),
    output_dir=Path("output/"),
    prompt="a landscape",
    upscale_method="4x-UltraSharp",  # Choose upscaler
)
```

Available options:
- `"None"` - No upscaling
- `"Lanczos"` - CPU Lanczos
- `"R-ESRGAN 4x+"` - General purpose
- `"R-ESRGAN 4x+ Anime6B"` - Anime
- `"4x-UltraSharp"` - Best quality
- `"Diffusion"` - Detail hallucination

---

## Error Handling

All GPU upscalers have OOM protection:

```python
try:
    upscaled = upscale(image)
except torch.cuda.OutOfMemoryError:
    # Automatic fallback to Lanczos
    from .lanczos import upscale as lanczos_upscale
    upscaled = lanczos_upscale(image)
```
