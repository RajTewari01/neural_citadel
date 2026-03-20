# Schedulers (Noise Schedulers)

> `apps/image_gen/schedulars/`

Different noise scheduling algorithms for the diffusion denoising process.

---

## Overview

Schedulers control **how noise is removed** during image generation. Different schedulers produce different results.

---

## Available Schedulers

| File | Name | Type | Best For |
|------|------|------|----------|
| `euler.py` | Euler Ancestral | Stochastic | Fast, general purpose |
| `dpmpp_2m_karras.py` | DPM++ 2M Karras | Deterministic | Best quality |
| `dpmpp_sde_karras.py` | DPM++ SDE Karras | Stochastic | Natural variation |
| `dpmpp_2m_sde_karras.py` | DPM++ 2M SDE Karras | Hybrid | Balanced |
| `ddim.py` | DDIM | Deterministic | Img2Img, consistency |
| `lms.py` | LMS Discrete | Smooth | Smooth gradients |
| `dpmpp.py` | DPM++ (Legacy) | Fast | Simple fast generation |

---

## Usage

Each scheduler has a `load()` function that takes a config and returns the scheduler:

```python
from apps.image_gen.schedulars.dpmpp_2m_karras import load

# Apply to pipeline
pipe.scheduler = load(pipe.scheduler.config)
```

---

## Scheduler Details

### `euler.py` - Euler Ancestral

```python
from diffusers import EulerAncestralDiscreteScheduler

def load(config) -> EulerAncestralDiscreteScheduler:
    return EulerAncestralDiscreteScheduler.from_config(config)
```

**Characteristics:**
- Fast generation
- Low VRAM usage
- Good default choice
- Slightly random (stochastic)

---

### `dpmpp_2m_karras.py` - DPM++ 2M Karras

```python
from diffusers import DPMSolverMultistepScheduler

def load(config) -> DPMSolverMultistepScheduler:
    return DPMSolverMultistepScheduler.from_config(
        config,
        use_karras_sigmas=True,
        algorithm_type="dpmsolver++"
    )
```

**Characteristics:**
- Best quality output
- Deterministic (same seed = same image)
- Low VRAM
- Converges well in 20-25 steps
- ⚠️ Unsafe above 26 steps on low VRAM

---

### `dpmpp_sde_karras.py` - DPM++ SDE Karras

```python
from diffusers import DPMSolverSDEScheduler

def load(config) -> DPMSolverSDEScheduler:
    return DPMSolverSDEScheduler.from_config(
        config,
        use_karras_sigmas=True,
        noise_sampler_seed=0
    )
```

**Characteristics:**
- Natural variation
- Stochastic (adds noise during denoising)
- Medium VRAM usage
- Popular on CivitAI

---

### `dpmpp_2m_sde_karras.py` - DPM++ 2M SDE Karras

```python
from diffusers import DPMSolverMultistepScheduler

def load(config) -> DPMSolverMultistepScheduler:
    return DPMSolverMultistepScheduler.from_config(
        config,
        use_karras_sigmas=True,
        algorithm_type="sde-dpmsolver++"
    )
```

**Characteristics:**
- Hybrid: 2M + SDE
- Balanced quality/variation
- Good for most use cases

---

### `ddim.py` - DDIM

```python
from diffusers import DDIMScheduler

def load(config) -> DDIMScheduler:
    return DDIMScheduler.from_config(config)
```

**Characteristics:**
- Fully deterministic
- Good for img2img
- Consistent, reproducible results
- Works well with lower step counts

---

### `lms.py` - LMS Discrete

```python
from diffusers import LMSDiscreteScheduler

def load(config) -> LMSDiscreteScheduler:
    return LMSDiscreteScheduler.from_config(config)
```

**Characteristics:**
- Smooth gradient transitions
- Needs more steps (30+)
- Good for landscapes/smooth subjects

---

## Scheduler Selection Guide

| Use Case | Recommended Scheduler |
|----------|----------------------|
| Fast preview | `euler_a` |
| Best quality | `dpmpp_2m_karras` |
| Natural variation | `dpmpp_sde_karras` |
| Consistent results | `ddim` |
| Smooth gradients | `lms` |
| CivitAI compatibility | `dpmpp_sde_karras` |

---

## VRAM Usage

| Scheduler | VRAM Impact |
|-----------|-------------|
| Euler A | Low |
| DPM++ 2M Karras | Low |
| DPM++ SDE Karras | Medium |
| DDIM | Low |
| LMS | Low |
