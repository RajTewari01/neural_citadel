"""
DDIM (Denoising Diffusion Implicit Models) Scheduler
=====================================================

The original deterministic scheduler for diffusion models.

Characteristics:
    - VRAM: Very Low
    - Speed: Fast (can skip steps efficiently)
    - Quality: Good, consistent results
    - Deterministic: Same seed = exact same output

Best For:
    - Reproducible results (scientific/testing)
    - Image-to-image transformations
    - When you need exact consistency between runs
    - Inpainting workflows

Recommended Steps: 30-50 (benefits from more steps)

Note: DDIM was one of the first schedulers to enable faster 
sampling by skipping steps. Less popular now due to DPM++ 
producing better quality at fewer steps, but still useful 
for reproducibility and img2img.
"""

from diffusers import DDIMScheduler
from typing import Callable


def load(pipe_config) -> Callable:
    """Load DDIM scheduler."""
    return DDIMScheduler.from_config(pipe_config)