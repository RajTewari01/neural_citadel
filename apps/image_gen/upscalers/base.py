"""
Base Upscaler Utilities
=======================

Shared utilities for standard Real-ESRGAN based upscalers.
Handles model loading, inference, and VRAM management.

NOTE: UltraSharp uses base_ultrasharp.py instead (isolated due to special requirements).
"""

import torch
import gc
import cv2
import numpy as np
from PIL import Image
from pathlib import Path
from typing import Optional, Union
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer


def flush_vram():
    """Clear CUDA cache to free VRAM."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def create_upscaler(
    model_path: Union[str, Path],
    model_name: str,
    scale: int = 4,
    tile: int = 256,
    tile_pad: int = 10,
    pre_pad: int = 0,
    half: bool = False,
    num_in_ch: int = 3,
    num_out_ch: int = 3,
    num_feat: int = 64,
    num_block: int = 23,
    num_grow_ch: int = 32,
) -> RealESRGANer:
    """
    Create a RealESRGANer instance with the specified model.
    
    For standard Real-ESRGAN models (RealESRGAN_x4plus, Anime6B).
    UltraSharp should use base_ultrasharp.py instead.
    
    Args:
        model_path: Path to the .pth model file
        model_name: Name identifier for the model
        scale: Upscaling factor (default 4)
        tile: Tile size for processing (default 256)
        tile_pad: Padding between tiles (default 10)
        pre_pad: Pre-padding size (default 0)
        half: Use FP16 for less VRAM (default False)
        num_in_ch: Input channels (default 3)
        num_out_ch: Output channels (default 3)
        num_feat: Feature channels (default 64)
        num_block: Number of RRDB blocks (default 23, use 6 for anime)
        num_grow_ch: Growth channels (default 32)
    
    Returns:
        RealESRGANer instance ready for upscaling
    """
    model_path = Path(model_path)
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")
    
    # Build the network architecture
    model = RRDBNet(
        num_in_ch=num_in_ch,
        num_out_ch=num_out_ch,
        num_feat=num_feat,
        num_block=num_block,
        num_grow_ch=num_grow_ch,
        scale=scale
    )
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    # Load model
    loadnet = torch.load(str(model_path), map_location=torch.device('cpu'))
    
    # Handle params_ema key
    if 'params_ema' in loadnet:
        keyname = 'params_ema'
    else:
        keyname = 'params'
    
    if keyname in loadnet:
        loadnet = loadnet[keyname]
    
    # Load state dict (standard models should work directly)
    model.load_state_dict(loadnet, strict=True)
    model.eval()
    if device == 'cuda':
        model = model.cuda()

    upscaler = RealESRGANer(
        scale=scale,
        model_path=str(model_path),
        model=model,
        tile=tile,
        tile_pad=tile_pad,
        pre_pad=pre_pad,
        half=half,
        device=device
    )
    
    return upscaler


def run_upscale(
    upscaler: RealESRGANer,
    image: Image.Image,
    outscale: float = 4.0
) -> Image.Image:
    """
    Run upscaling on a PIL Image with proper color space handling.
    
    Args:
        upscaler: RealESRGANer instance
        image: Input PIL Image
        outscale: Output scale factor (default 4.0)
    
    Returns:
        Upscaled PIL Image
    """
    # Ensure RGB mode (prevent RGBA, L, P modes from causing issues)
    if image.mode != 'RGB':
        print(f"   [!] Converting {image.mode} to RGB")
        image = image.convert('RGB')
    
    # Convert PIL to numpy array
    img_np = np.array(image)
    
    # Handle grayscale images
    if len(img_np.shape) == 2:
        img_np = np.stack([img_np] * 3, axis=-1)
    
    # Ensure uint8 dtype
    if img_np.dtype != np.uint8:
        print(f"   [!] Converting {img_np.dtype} to uint8")
        img_np = img_np.astype(np.uint8)
    
    # Standard single-pass BGR conversion
    img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    
    # Run upscaling (Real-ESRGAN expects BGR format)
    output_bgr, _ = upscaler.enhance(img_bgr, outscale=outscale)
    
    # Convert BGR back to RGB
    output_rgb = cv2.cvtColor(output_bgr, cv2.COLOR_BGR2RGB)
    
    # Ensure uint8 and valid range
    output_rgb = np.clip(output_rgb, 0, 255).astype(np.uint8)
    
    # Convert back to PIL Image
    result = Image.fromarray(output_rgb)
    
    return result