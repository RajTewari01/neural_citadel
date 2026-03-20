"""
Upscalers Package
=================

This package provides image upscaling functionality using various methods.

Available Upscalers:
    - lanczos: CPU-based, zero VRAM, safe fallback
    - realesrgan_4x: R-ESRGAN 4x+, excellent for realistic photos
    - realesrgan_anime: R-ESRGAN 4x+ Anime6B, lightweight for anime
    - diffusion_upscale: Img2Img, hallucinates details (requires SD pipe)

Usage:
    from upscalers import realesrgan_4x
    
    upscaled_image = realesrgan_4x.upscale(image, scale=4)

All model paths are configured in: configs/paths.py
"""

from pathlib import Path

# Dynamically add project root to path
_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # upscalers -> image_gen -> apps -> neural_citadel
import sys
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from configs.paths import UPSCALER_MODELS, UPSCALER_CONFIGS, get_upscaler_path
