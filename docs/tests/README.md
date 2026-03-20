# Tests

> `tests/`

Test files and engine testing.

---

## Overview

```
tests/
└── engine.py    # Main diffusion engine (optimized for GTX 1650)
```

---

## `engine.py` - Diffusion Engine

The **main image generation engine** optimized for GTX 1650 (4GB VRAM).

### Key Configuration

This engine uses a specific configuration to avoid black images on low VRAM:

| Setting | Value | Reason |
|---------|-------|--------|
| Precision | `float32` | Prevents NaN/black images |
| Memory | Sequential CPU Offload | Fits model in 4GB VRAM |
| VAE | External (stabilityai) | Better colors/eyes |
| Slicing | Aggressive | Reduces peak VRAM |

---

### Class: `DiffusionEngine`

```python
class DiffusionEngine:
    def __init__(self):
        self.pipe = None
        self.current_model = None
        self.default_model = Path("...diffusionBrush...safetensors")
        self.output_dir = ROOT / "assets" / "generated"
    
    def load_model(self, model_path: Path = None):
        """Load a model with optimized settings."""
    
    def generate(self, prompt, negative_prompt, width, height, steps, cfg, seed):
        """Generate an image."""
    
    def unload(self):
        """Unload model and free VRAM."""
```

---

### Usage

```python
from tests.engine import DiffusionEngine

# Create engine
engine = DiffusionEngine()

# Generate image
image = engine.generate(
    prompt="a mystical forest at night",
    negative_prompt="ugly, blurry",
    width=512,
    height=768,
    steps=30,
    cfg=7.0,
    seed=42
)

# Clean up
engine.unload()
```

---

### Key Methods

#### `load_model(model_path)`

Loads a Stable Diffusion checkpoint with optimizations:

1. **Load external VAE** - `stabilityai/sd-vae-ft-mse`
2. **Create pipeline** - Float32 precision
3. **Enable sequential offload** - Swaps layers to CPU
4. **Enable slicing** - VAE slicing, tiling, attention slicing
5. **Set scheduler** - DPM++ 2M Karras

```python
self.pipe = StableDiffusionPipeline.from_single_file(
    str(model_path),
    vae=vae,
    torch_dtype=torch.float32,
    safety_checker=None,
    requires_safety_checker=False,
)

self.pipe.enable_sequential_cpu_offload()
self.pipe.enable_vae_slicing()
self.pipe.enable_vae_tiling()
self.pipe.enable_attention_slicing(slice_size="max")
```

#### `generate(...)`

Generates an image with the loaded model:

```python
result = self.pipe(
    prompt=prompt,
    negative_prompt=negative_prompt,
    width=width,
    height=height,
    num_inference_steps=steps,
    guidance_scale=cfg,
    generator=generator,
)
return result.images[0]
```

#### `unload()`

Frees VRAM:

```python
del self.pipe
self.pipe = None
gc.collect()
torch.cuda.empty_cache()
```

---

### Performance

| Metric | Value |
|--------|-------|
| Speed | ~3-5 seconds/step |
| VRAM | ~3-4GB peak |
| Stability | No black images |

---

### Why Float32?

The GTX 1650 has issues with `float16` precision:
- NaN values appear in UNet output
- Results in completely black images
- Float32 is stable but slower

---

### CLI Usage

```bash
python tests/engine.py
```

This runs the engine with default settings and saves to `assets/generated/`.

---

### Customization

To change default model, edit line 44:

```python
self.default_model = Path(r"D:\path\to\your\model.safetensors")
```

To change output directory:

```python
self.output_dir = Path("your/custom/output/dir")
```
