# Prompt Enhancement Module

> `apps/image_gen/tools/prompts.py`

Automatically enhances user prompts by learning from model-specific CivitAI data.

---

## Overview

Instead of using hardcoded presets, this module **analyzes scraped prompts** and learns:

- ✅ Quality boosters (e.g., `hyper realistic, 8k, cinematic`)
- ✅ Common LoRAs used with the model
- ✅ Optimal settings (steps, CFG, sampler)
- ✅ Effective negative prompts
- ✅ Common image sizes

---

## Quick Start

```python
from apps.image_gen.tools import enhance_prompt

# Enhance with model-specific patterns
result = enhance_prompt("a girl in forest", model_id=46294)

print(result.prompt)           # Enhanced prompt
print(result.negative_prompt)  # Learned negative
print(result.steps)            # 24 (from model data)
print(result.cfg_scale)        # 3.5 (from model data)
print(result.sampler)          # DPM++ SDE
print(result.loras)            # ['more_details', ...]
```

---

## Classes

### `EnhancedPrompt`

Dataclass containing enhanced prompt and settings.

| Field | Type | Description |
|-------|------|-------------|
| `prompt` | `str` | Enhanced prompt with quality boosters |
| `negative_prompt` | `str` | Learned negative prompt |
| `steps` | `int` | Optimal inference steps |
| `cfg_scale` | `float` | Optimal CFG scale |
| `sampler` | `str` | Best sampler for model |
| `width` | `int` | Recommended width |
| `height` | `int` | Recommended height |
| `loras` | `List[str]` | LoRAs included in prompt |
| `model_id` | `Optional[int]` | Source model ID |

---

### `PromptEnhancer`

Main class for prompt enhancement.

```python
from apps.image_gen.tools import PromptEnhancer

enhancer = PromptEnhancer()

# See available models
models = enhancer.get_available_models()
# [{'model_id': 46294, 'file': 'model_46294_prompts.json', 'prompt_count': 100}]

# Get style summary
print(enhancer.get_style_summary(46294))
# Model 46294 Style:
#   Quality: hyper realistic, atmospheric, 8k, epic composition
#   LoRAs: more_details, zhongfenghuaxiyou-000018
#   Settings: 24 steps, CFG 3.5, DPM++ SDE
```

---

## Functions

### `enhance_prompt(prompt, model_id=None, **kwargs)`

Quick function to enhance a prompt.

**Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `prompt` | `str` | required | Your simple prompt |
| `model_id` | `int` | `None` | CivitAI model ID |
| `include_loras` | `bool` | `True` | Include common LoRAs |
| `width` | `int` | `512` | Target width |
| `height` | `int` | `768` | Target height |

**Returns:** `EnhancedPrompt`

---

### `enhance_for_model(prompt, model_path, **kwargs)`

Enhance using model file path (auto-detects ID from filename).

```python
from pathlib import Path
from apps.image_gen.tools import enhance_for_model

result = enhance_for_model(
    "ocean sunset",
    model_path=Path("model_46294_v1.safetensors")
)
```

---

### `list_available_models()`

Get list of models with scraped prompts.

```python
from apps.image_gen.tools import list_available_models

models = list_available_models()
# [{'model_id': 46294, 'file': 'model_46294_prompts.json', 'prompt_count': 100}]
```

---

## How It Works

### 1. Load Prompts
Reads `assets/prompts/model_<ID>_prompts.json`

### 2. Analyze Patterns
Extracts:
- Quality boosters (regex matches for common patterns)
- LoRAs (`<lora:name:weight>` extraction)
- Negative prompt words (frequency analysis)
- Settings (mode of steps, CFG, sampler)

### 3. Build Enhanced Prompt
```
[quality boosters] + [user prompt] + [LoRAs]
```

### 4. Return Complete Settings
All learned settings in `EnhancedPrompt` dataclass.

---

## Adding New Models

1. **Scrape from CivitAI:**
   ```bash
   python tools/api_scraper.py https://civitai.com/models/12345
   ```

2. **Use immediately:**
   ```python
   result = enhance_prompt("your prompt", model_id=12345)
   ```

The enhancer automatically detects new prompt files in `assets/prompts/`.

---

## Example Output

**Input:**
```python
enhance_prompt("ocean waves at sunset", model_id=46294)
```

**Output:**
```
EnhancedPrompt(
    prompt="hyper realistic, atmospheric, 8k, epic composition, cinematic, 
            ocean waves at sunset, <lora:more_details:0.5>",
    negative_prompt="hand, easynegative, greyscale, monochrome, water mark...",
    steps=24,
    cfg_scale=3.5,
    sampler="DPM++ SDE",
    width=1024,
    height=1536,
    loras=['more_details'],
    model_id=46294
)
```
