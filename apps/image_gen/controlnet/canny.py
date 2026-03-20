"""
Canny ControlNet
================

Edge detection ControlNet for line art and edge-based guidance.

Characteristics:
    - VRAM: ~1.5GB (on top of base model)
    - Best For: Line art, architectural drawings, sharp edges
    - Preprocessing: Canny edge detection

Model: control_v11p_sd15_canny.pth

Usage:
    from controlnet import canny
    
    # 1. Detect edges in reference image
    edge_map = canny.detect(reference_image)
    
    # 2. Load ControlNet model
    cnet = canny.load_model()
    
    # 3. Use with pipeline (conditioning)
"""

import torch
from pathlib import Path
from PIL import Image
from typing import Optional, Tuple
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


def detect(
    image: Image.Image,
    low_threshold: int = 100,
    high_threshold: int = 200,
    blur_ksize: int = 5
) -> Image.Image:
    """
    Detect edges using Canny edge detection.
    
    Args:
        image: Input PIL Image
        low_threshold: Lower threshold for edge detection
        high_threshold: Upper threshold for edge detection
        blur_ksize: Gaussian blur kernel size (odd number)
    
    Returns:
        Edge map as PIL Image
    """
    global _detector
    
    # Lazy load detector
    if _detector is None:
        try:
            from controlnet_aux import CannyDetector
            _detector = CannyDetector()
        except ImportError:
            # Fallback to OpenCV
            import cv2
            
            img_np = np.array(image.convert("RGB"))
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            blurred = cv2.GaussianBlur(gray, (blur_ksize, blur_ksize), 0)
            edges = cv2.Canny(blurred, low_threshold, high_threshold)
            return Image.fromarray(edges)
    
    # Use controlnet_aux detector
    return _detector(image, low_threshold, high_threshold)


def load_model(torch_dtype: torch.dtype = torch.float16):
    """
    Load the Canny ControlNet model.
    
    Args:
        torch_dtype: Data type (float16 for less VRAM)
    
    Returns:
        ControlNetModel instance
    """
    global _controlnet
    
    if _controlnet is None:
        model_path = CONTROLNET_MODELS["canny"]
        _controlnet = load_controlnet(model_path, torch_dtype)
    
    return _controlnet


def unload():
    """Unload model and free VRAM."""
    global _controlnet, _detector
    _controlnet = None
    _detector = None
    flush_vram()
