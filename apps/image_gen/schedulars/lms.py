"""
LMS (Linear Multi-Step) Scheduler
==================================

A linear multi-step method scheduler for diffusion sampling.

Characteristics:
    - VRAM: Medium (stores previous steps in memory)
    - Speed: Medium-Slow (requires more steps)
    - Quality: Good, smooth gradients
    - Deterministic: Consistent outputs

Best For:
    - Smooth color gradients
    - Landscapes and atmospheric scenes
    - When other schedulers produce artifacts

Recommended Steps: 40-60 (needs more steps than DPM++)

Caution for 4GB VRAM:
    LMS stores multiple previous steps in memory, which can 
    increase VRAM usage. Consider using Euler A or DPM++ 2M 
    Karras instead if you're memory-constrained.

Note: Less commonly used now since DPM++ variants achieve 
better quality in fewer steps. Kept for compatibility with 
older workflows and specific use cases.
"""

from diffusers import LMSDiscreteScheduler
from typing import Callable


def load(pipe_config) -> Callable:
    """Load LMS Discrete scheduler."""
    return LMSDiscreteScheduler.from_config(pipe_config)