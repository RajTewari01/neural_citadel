"""
DPM++ 2M SDE Karras Scheduler
=============================

A hybrid scheduler combining 2M multi-step with SDE stochastic sampling.

Characteristics:
    - VRAM: Medium
    - Speed: Medium (20-30 steps optimal)
    - Quality: Excellent balance of detail and natural variation
    - Hybrid: Combines deterministic multi-step with stochastic elements

Best For:
    - Best of both worlds: consistency + natural variation
    - Complex scenes with fine details
    - When 2M is too "perfect" and SDE is too random

Recommended Steps: 25-30

Note: This variant uses the multi-step (2M) algorithm base with 
SDE stochastic noise injection, providing a middle ground between 
pure deterministic and pure stochastic sampling.
"""

from diffusers import DPMSolverMultistepScheduler
from typing import Callable


def load(pipe_config) -> Callable:
    """Load DPM++ 2M SDE Karras scheduler."""
    return DPMSolverMultistepScheduler.from_config(
        pipe_config,
        use_karras_sigmas=True,
        algorithm_type="sde-dpmsolver++",
        solver_order=2  # 2M = second-order multi-step
    )
