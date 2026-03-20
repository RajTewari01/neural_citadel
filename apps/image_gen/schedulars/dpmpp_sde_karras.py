"""
DPM++ SDE Karras Scheduler
==========================

A stochastic (SDE) variant of DPM++ with Karras noise schedule.

Characteristics:
    - VRAM: Medium (slightly higher due to stochastic sampling)
    - Speed: Medium (best at 20-30 steps)
    - Quality: Very sharp, detailed images
    - Stochastic: Adds controlled randomness for more natural results

Best For:
    - Artistic/creative images
    - When you want slight variation between runs
    - Portraits and detailed textures

Recommended Steps: 25-30

Note: The SDE (Stochastic Differential Equation) variant adds 
noise during sampling, which can produce more natural-looking 
results but uses slightly more VRAM than the 2M variant.
"""

from diffusers import DPMSolverMultistepScheduler
from typing import Callable


def load(pipe_config) -> Callable:
    """Load DPM++ SDE Karras scheduler."""
    return DPMSolverMultistepScheduler.from_config(
        pipe_config,
        use_karras_sigmas=True,
        algorithm_type="sde-dpmsolver++"  # SDE variant (stochastic)
    )
