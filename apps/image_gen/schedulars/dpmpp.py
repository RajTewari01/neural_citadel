"""
DPM++ (Legacy) Scheduler
========================

Legacy DPM++ scheduler - kept for backward compatibility.

NOTE: Consider using the specific variants instead:
    - dpmpp_2m_karras.py     -> Deterministic, sharp results
    - dpmpp_sde_karras.py    -> Stochastic, natural variation
    - dpmpp_2m_sde_karras.py -> Hybrid approach

This file uses SDE variant by default for historical reasons.

Characteristics:
    - VRAM: Medium
    - Speed: Medium (20-30 steps)
    - Quality: Excellent
    - Stochastic: SDE adds controlled randomness

Recommended Steps: 25-30
"""

from diffusers import DPMSolverMultistepScheduler
from typing import Callable


def load(pipe_config) -> Callable:
    """Load legacy DPM++ SDE Karras scheduler."""
    return DPMSolverMultistepScheduler.from_config(
        pipe_config,
        use_karras_sigmas=True,
        algorithm_type="sde-dpmsolver++"
    )