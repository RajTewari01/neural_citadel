"""
Depth ControlNet
================

Depth estimation ControlNet for 3D-aware composition.

Characteristics:
    - VRAM: ~1.5GB (on top of base model)
    - Best For: 3D scenes, perspective control, spatial composition
    - Preprocessing: MiDaS depth estimation

Model: control_v11f1p_sd15_depth.pth

Usage:
    from controlnet import depth
    
    # 1. Estimate depth from reference image
    depth_map = depth.detect(reference_image)
    
    # 2. Load ControlNet model
    cnet = depth.load_model()
    
    # 3. Use with pipeline (conditioning)
"""

import torch
from pathlib import Path
from PIL import Image
from typing import Optional
import numpy as np

# Dynamically add project root to path
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
import sys
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from configs.paths import CONTROLNET_MODELS
from .base import load_controlnet, unload_controlnet, flush_vram

# Cached model
_controlnet = None
_detector = None


def detect(image: Image.Image) -> Image.Image:
    """
    Estimate depth map using MiDaS.
    
    Args:
        image: Input PIL Image
    
    Returns:
        Depth map as PIL Image (grayscale)
    """
    global _detector
    
    # Lazy load detector
    if _detector is None:
        try:
            from controlnet_aux import MidasDetector
            _detector = MidasDetector.from_pretrained("lllyasviel/Annotators")
        except ImportError:
            raise ImportError(
                "controlnet_aux is required for depth detection. "
                "Install with: pip install controlnet_aux"
            )
    
    return _detector(image)


def load_model(torch_dtype: torch.dtype = torch.float16):
    """
    Load the Depth ControlNet model.
    
    Args:
        torch_dtype: Data type (float16 for less VRAM)
    
    Returns:
        ControlNetModel instance
    """
    global _controlnet
    
    if _controlnet is None:
        model_path = CONTROLNET_MODELS["depth"]
        _controlnet = load_controlnet(model_path, torch_dtype)
    
    return _controlnet


def unload():
    """Unload model and free VRAM."""
    global _controlnet, _detector
    _controlnet = None
    _detector = None
    flush_vram()
