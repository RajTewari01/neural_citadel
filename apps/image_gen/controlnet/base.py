"""
ControlNet Base Utilities
=========================

Shared utilities for all ControlNet models.
Handles model loading and VRAM management.
"""

import torch
import gc
from pathlib import Path
from typing import Optional, Union
from diffusers import ControlNetModel


def flush_vram():
    """Clear CUDA cache to free VRAM."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def load_controlnet(
    model_path: Union[str, Path],
    torch_dtype: torch.dtype = torch.float16,
) -> ControlNetModel:
    """
    Load a ControlNet model from a single file.
    
    Args:
        model_path: Path to the .pth or .safetensors model file
        torch_dtype: Data type for model weights (float16 saves VRAM)
    
    Returns:
        ControlNetModel instance
    """
    model_path = Path(model_path)
    if not model_path.exists():
        raise FileNotFoundError(f"ControlNet model not found: {model_path}")
    
    print(f"[+] Loading ControlNet: {model_path.stem}")
    
    controlnet = ControlNetModel.from_single_file(
        str(model_path),
        torch_dtype=torch_dtype
    )
    
    print(f"   [+] Loaded: {model_path.name}")
    return controlnet


def unload_controlnet(controlnet: Optional[ControlNetModel]):
    """Unload a ControlNet model and free VRAM."""
    if controlnet is not None:
        del controlnet
    flush_vram()
