"""
R-ESRGAN 4x+ Upscaler
=====================

Very efficient standard Real-ESRGAN model for general-purpose upscaling.

Characteristics:
    - VRAM: ~500-800 MB
    - Quality: Excellent for realistic photos
    - Speed: Fast with tile-based processing
    - Best For: General purpose, realistic images

Model File: RealESRGAN_x4plus.pth (~64MB)
"""

from pathlib import Path
from PIL import Image
from typing import Optional

# Dynamically add project root to path
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
import sys
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from configs.paths import UPSCALER_MODELS, UPSCALER_CONFIGS
from .base import create_upscaler, run_upscale, flush_vram

# Cached upscaler instance
_upscaler = None


def load(half: bool = False, tile: int = 256):
    """
    Load the R-ESRGAN 4x+ model.
    
    Args:
        half: Use FP16 for less VRAM (recommended for 4GB cards)
        tile: Tile size (lower = less VRAM, try 128 for low VRAM)
    
    Returns:
        RealESRGANer instance
    """
    global _upscaler
    
    if _upscaler is None:
        model_path = UPSCALER_MODELS["R-ESRGAN 4x+"]
        config = UPSCALER_CONFIGS["R-ESRGAN 4x+"]
        
        _upscaler = create_upscaler(
            model_path=model_path,
            model_name="RealESRGAN_x4plus",
            scale=config["scale"],
            tile=tile,
            half=half,
            num_block=config["num_block"]
        )
    
    return _upscaler


def upscale(
    image: Image.Image,
    scale: float = 4.0,
    half: bool = False,
    tile: int = 256
) -> Image.Image:
    """
    Upscale an image using R-ESRGAN 4x+.
    
    Args:
        image: Input PIL Image
        scale: Output scale factor (default 4.0)
        half: Use FP16 for less VRAM
        tile: Tile size for processing
    
    Returns:
        Upscaled PIL Image
    """
    upscaler = load(half=half, tile=tile)
    result = run_upscale(upscaler, image, outscale=scale)
    return result


def unload():
    """Unload model and free VRAM."""
    global _upscaler
    _upscaler = None
    flush_vram()
