"""
Euler Ancestral (Euler A) Scheduler
====================================

The classic ancestral sampling scheduler - fast and reliable.

Characteristics:
    - VRAM: Very Low (~minimal overhead)
    - Speed: Very Fast (efficient at 25-35 steps)
    - Quality: Good, slightly softer than DPM++
    - Stochastic: Ancestral sampling adds natural variation

Best For:
    - 4GB VRAM setups (most VRAM-friendly)
    - Quick iterations and testing
    - When speed matters more than maximum detail
    - Default fallback scheduler

Recommended Steps: 25-35

Note: The "ancestral" variant adds noise at each step, making 
outputs slightly different each time. Very forgiving scheduler 
that works well with most models and prompts.
"""

from diffusers import EulerAncestralDiscreteScheduler
from typing import Callable


def load(pipe_config) -> Callable:
    """Load Euler Ancestral scheduler."""
    return EulerAncestralDiscreteScheduler.from_config(pipe_config)