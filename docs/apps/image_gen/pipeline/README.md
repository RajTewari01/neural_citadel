# Pipeline Types

> `apps/image_gen/pipeline/types.py`

Configuration dataclasses for the image generation pipeline.

---

## Overview

This module defines the **configuration structure** for image generation pipelines using Python dataclasses with validation.

---

## Classes

### `PipelineConfigs`

Main configuration class for image generation.

```python
@dataclass
class PipelineConfigs:
    # MANDATORY
    base_model: Union[str, Path]   # Model checkpoint path
    output_dir: Union[str, Path]   # Output directory
    prompt: str                    # Generation prompt
    
    # PROMPTS
    neg_prompt: str = ''           # Negative prompt
    triggers: Optional[str] = None # Trigger words (auto-injected)
    
    # UPSCALING
    upscale_method: Optional[Literal[...]] = "4x-UltraSharp"
    
    # SCHEDULER
    scheduler_name: Literal[...] = "euler_a"
    
    # DIMENSIONS
    height: int = 512
    width: int = 768
    
    # GENERATION
    steps: int = 25
    cfg: float = 7.0
    clip_skip: Optional[int] = None
    seed: Optional[int] = None
    
    # LORA
    lora: List[LoraConfig] = field(default_factory=list)
    
    # CONTROLNET
    c_net: List[ControlNetConfig] = field(default_factory=list)
    
    # CONFIG FILES
    model_config: Optional[str] = None
```

---

### `LoraConfig`

LoRA model configuration.

```python
@dataclass
class LoraConfig:
    lora_path: Union[str, Path]           # Path to LoRA file
    scale: float = 1.0                    # LoRA strength (0-1)
    lora_trigger_word: Optional[str] = None  # Trigger word
```

---

### `ControlNetConfig`

ControlNet guidance configuration.

```python
@dataclass
class ControlNetConfig:
    control_type: Literal["canny", "depth", "openpose"]
    image_path: Union[str, Path]  # Reference/control image
    scale: float = 1.0            # Guidance strength
```

---

## Field Details

### Upscale Methods

```python
upscale_method: Optional[Literal[
    "None",                  # No upscaling
    "Lanczos",               # CPU-based, zero VRAM
    "R-ESRGAN 4x+",          # General purpose GPU
    "R-ESRGAN 4x+ Anime6B",  # Anime optimized
    "4x-UltraSharp",         # Best quality (default)
    "Diffusion",             # Img2Img upscale
]] = "4x-UltraSharp"
```

### Scheduler Names

```python
scheduler_name: Literal[
    "euler_a",              # Fast, low VRAM
    "dpm++_2m_karras",      # Best quality
    "dpm++_sde_karras",     # Natural variation
    "dpm++_2m_sde_karras",  # Hybrid
    "ddim",                 # Deterministic
    "lms"                   # Smooth gradients
] = "euler_a"
```

---

## Validation

`__post_init__` performs automatic validation:

### Path Conversion
```python
# Strings are converted to Path objects
if isinstance(self.base_model, str):
    self.base_model = Path(self.base_model)
```

### Dimension Alignment
```python
# Dimensions must be multiples of 8
if self.height % 8 != 0:
    self.height = ((self.height // 8) * 8)
```

### Trigger Word Injection
```python
# Triggers are auto-injected into prompt
if self.triggers:
    if self.triggers.lower() not in self.prompt.lower():
        self.prompt = f'{self.triggers} {self.prompt}'
```

### Value Ranges
```python
# Steps: 1-44
if self.steps <= 0: raise ValueError("Steps needs to be more than 0.")
if self.steps >= 45: raise ValueError("Steps needs to be less than 45.")

# CFG: 0-14
if self.cfg <= 0: raise ValueError("CFG needed to be more than 0")
if self.cfg >= 15: raise ValueError("CFG needed to be less than 15")
```

### Scheduler Limits
```python
# DPM++ 2M Karras is unsafe above 26 steps on low VRAM
if self.scheduler_name == "dpm++_2m_karras" and self.steps > 26:
    raise ValueError("dpm++_2m_karras is unsafe above 26 steps on low VRAM")
```

---

## Usage Example

```python
from pathlib import Path
from apps.image_gen.pipeline.types import PipelineConfigs, LoraConfig, ControlNetConfig

config = PipelineConfigs(
    base_model=Path("models/dreamshaper.safetensors"),
    output_dir=Path("output/"),
    prompt="a beautiful sunset over mountains",
    neg_prompt="ugly, blurry, low quality",
    
    upscale_method="4x-UltraSharp",
    scheduler_name="dpm++_2m_karras",
    
    width=768,
    height=512,
    steps=25,
    cfg=7.0,
    seed=42,
    
    lora=[
        LoraConfig(
            lora_path=Path("loras/detail.safetensors"),
            scale=0.5
        )
    ],
    
    c_net=[
        ControlNetConfig(
            control_type="depth",
            image_path=Path("reference.png"),
            scale=0.7
        )
    ]
)
```

---

## CFG Scale Guide

| CFG Value | Effect |
|-----------|--------|
| 1-3 | Very creative, may ignore prompt |
| 4-6 | Natural, balanced |
| **7** | **Default, good balance** |
| 8-10 | Follows prompt strictly |
| 11-14 | Very strict, may look "burnt" |
