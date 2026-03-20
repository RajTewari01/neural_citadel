"""
DPM++ 2M Karras Scheduler
=========================

A deterministic multi-step scheduler with Karras noise schedule.

Characteristics:
    - VRAM: Low (~same as base model)
    - Speed: Fast (converges in 20-25 steps)
    - Quality: Excellent detail and sharpness
    - Deterministic: Same seed = same output

Best For:
    - High-quality realistic images
    - Low VRAM setups (4-6GB)
    - When you need consistent, reproducible results

Recommended Steps: 20-25 (max 26 for low VRAM safety)

Note: Uses Karras sigma schedule which provides better noise 
distribution, resulting in sharper images with less artifacts.
"""

from diffusers import DPMSolverMultistepScheduler
from typing import Callable


def load(pipe_config) -> Callable:
    """Load DPM++ 2M Karras scheduler."""
    return DPMSolverMultistepScheduler.from_config(
        pipe_config,
        use_karras_sigmas=True,
        algorithm_type="dpmsolver++"  # 2M variant (deterministic)
    )
