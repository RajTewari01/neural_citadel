# Image Generation System

> `apps/image_gen/`

The core image generation system built on Stable Diffusion.

---

## 📁 Structure

```
image_gen/
├── tools/              # Prompt enhancement
│   ├── __init__.py     # Package exports
│   └── prompts.py      # Prompt enhancer (learns from CivitAI)
├── schedulars/         # Noise schedulers
│   ├── ddim.py         # DDIM scheduler
│   ├── euler.py        # Euler Ancestral
│   ├── dpmpp.py        # DPM++ legacy
│   ├── dpmpp_2m_karras.py
│   ├── dpmpp_sde_karras.py
│   └── dpmpp_2m_sde_karras.py
├── upscalers/          # Image upscaling
│   ├── base.py         # Shared utilities
│   ├── lanczos.py      # CPU-based Lanczos
│   ├── realesrgan_4x.py
│   ├── realesrgan_anime.py
│   ├── ultrasharp.py
│   └── diffusion_upscale.py
├── controlnet/         # Guidance modules
│   ├── base.py         # Shared utilities
│   ├── canny.py        # Edge detection
│   ├── depth.py        # Depth estimation
│   └── openpose.py     # Pose detection
└── pipeline/           # Configuration types
    └── types.py        # PipelineConfigs dataclass
```

---

## 🔧 Components

### 1. Prompt Enhancement (`tools/prompts.py`)

Automatically enhances prompts by learning from scraped CivitAI data.

```python
from apps.image_gen.tools import enhance_prompt

result = enhance_prompt("a girl in forest", model_id=46294)
print(result.prompt)         # Enhanced prompt
print(result.negative_prompt) # Learned negative
print(result.steps)          # Optimal steps (24)
print(result.cfg_scale)      # Optimal CFG (3.5)
```

**How it works:**
1. Loads `assets/prompts/model_<ID>_prompts.json`
2. Analyzes prompt patterns (quality boosters, LoRAs, triggers)
3. Extracts optimal settings (steps, CFG, sampler)
4. Applies learned patterns to your prompt

---

### 2. Schedulers (`schedulars/`)

Different noise scheduling algorithms for diffusion:

| Scheduler | File | Best For |
|-----------|------|----------|
| **Euler Ancestral** | `euler.py` | Fast, general purpose |
| **DPM++ 2M Karras** | `dpmpp_2m_karras.py` | Best quality, deterministic |
| **DPM++ SDE Karras** | `dpmpp_sde_karras.py` | Natural variation |
| **DDIM** | `ddim.py` | Img2Img, consistent results |
| **LMS** | `lms.py` | Smooth gradients |

**Usage:**
```python
from apps.image_gen.schedulars.dpmpp_2m_karras import load

scheduler = load(pipe.scheduler.config)
pipe.scheduler = scheduler
```

---

### 3. Upscalers (`upscalers/`)

4x image upscaling options:

| Upscaler | File | VRAM | Quality | Speed |
|----------|------|------|---------|-------|
| **Lanczos** | `lanczos.py` | 0 (CPU) | Good | Fast |
| **R-ESRGAN 4x+** | `realesrgan_4x.py` | ~1GB | Excellent | Medium |
| **Anime6B** | `realesrgan_anime.py` | ~0.5GB | Anime | Fast |
| **4x-UltraSharp** | `ultrasharp.py` | ~1GB | Best | Medium |
| **Diffusion** | `diffusion_upscale.py` | ~2GB | Detailed | Slow |

**Usage:**
```python
from apps.image_gen.upscalers.ultrasharp import upscale

upscaled = upscale(image)  # Returns 4x resolution PIL Image
```

---

### 4. ControlNet (`controlnet/`)

Guidance modules for controlled generation:

| Control Type | File | Purpose |
|--------------|------|---------|
| **Canny** | `canny.py` | Edge detection for line art |
| **Depth** | `depth.py` | 3D-aware composition |
| **OpenPose** | `openpose.py` | Human pose guidance |

---

### 5. Pipeline Types (`pipeline/types.py`)

Configuration dataclasses for the generation pipeline:

```python
from apps.image_gen.pipeline.types import PipelineConfigs, LoraConfig

config = PipelineConfigs(
    base_model=Path("model.safetensors"),
    output_dir=Path("output/"),
    prompt="a beautiful landscape",
    steps=25,
    cfg=7.0,
    scheduler_name="dpm++_2m_karras",
)
```

**Key Classes:**
- `PipelineConfigs` - Main configuration
- `LoraConfig` - LoRA settings
- `ControlNetConfig` - ControlNet settings

---

## 🔄 Adding New Models

1. **Scrape prompts:**
   ```bash
   python tools/api_scraper.py https://civitai.com/models/<ID>
   ```

2. **Add model path to `configs/paths.py`:**
   ```python
   DIFFUSION_MODELS = {
       "my_model": DIFFUSION_DIR / "my_model.safetensors",
   }
   ```

3. **Use in code:**
   ```python
   result = enhance_prompt("prompt", model_id=<ID>)
   ```

---

*See individual module docs for detailed API reference.*
