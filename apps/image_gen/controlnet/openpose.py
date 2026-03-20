"""
OpenPose ControlNet
===================

Human pose estimation ControlNet for body and face guidance.

Characteristics:
    - VRAM: ~1.5GB (on top of base model)
    - Best For: Human poses, body positioning, dance moves
    - Preprocessing: OpenPose skeleton detection

Model: control_v11p_sd15_openpose.pth

Usage:
    from controlnet import openpose
    
    # 1. Detect pose from reference image
    pose_map = openpose.detect(reference_image)
    
    # 2. Load ControlNet model
    cnet = openpose.load_model()
    
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


def detect(
    image: Image.Image,
    include_hand: bool = True,
    include_face: bool = True
) -> Image.Image:
    """
    Detect human pose using OpenPose.
    
    Args:
        image: Input PIL Image
        include_hand: Include hand keypoints
        include_face: Include face keypoints
    
    Returns:
        Pose skeleton map as PIL Image
    """
    global _detector
    
    # Lazy load detector
    if _detector is None:
        try:
            from controlnet_aux import OpenposeDetector
            _detector = OpenposeDetector.from_pretrained("lllyasviel/Annotators")
        except ImportError:
            raise ImportError(
                "controlnet_aux is required for pose detection. "
                "Install with: pip install controlnet_aux"
            )
    
    return _detector(image, include_hand=include_hand, include_face=include_face)


def load_model(torch_dtype: torch.dtype = torch.float16):
    """
    Load the OpenPose ControlNet model.
    
    Args:
        torch_dtype: Data type (float16 for less VRAM)
    
    Returns:
        ControlNetModel instance
    """
    global _controlnet
    
    if _controlnet is None:
        model_path = CONTROLNET_MODELS["openpose"]
        _controlnet = load_controlnet(model_path, torch_dtype)
    
    return _controlnet


def unload():
    """Unload model and free VRAM."""
    global _controlnet, _detector
    _controlnet = None
    _detector = None
    flush_vram()
