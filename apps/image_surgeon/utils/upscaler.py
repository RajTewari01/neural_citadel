"""
RealESRGAN Upscaler for Image Surgeon
=====================================
Standalone ESRGAN upscaler - completely independent from image_gen app.
Uses model from configs/paths.py: RealESRGAN_x4plus_fixed.pth
"""

import torch
import gc
import cv2
import numpy as np
from PIL import Image
from pathlib import Path
import sys

# Add project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from configs.paths import UPSCALER_MODELS, UPSCALER_CONFIGS

# Model path - use standard 4x+ model
ESRGAN_MODEL = UPSCALER_MODELS["R-ESRGAN 4x+"]

# Cached upscaler instance
_upscaler = None


def load_esrgan(half: bool = False, tile: int = 256):
    """
    Load RealESRGAN 4x+ model.
    
    Args:
        half: Use FP16 for less VRAM
        tile: Tile size (lower = less VRAM)
        
    Returns:
        RealESRGANer instance
    """
    global _upscaler
    
    if _upscaler is not None:
        return _upscaler
        
    from basicsr.archs.rrdbnet_arch import RRDBNet
    from realesrgan import RealESRGANer
    
    if not ESRGAN_MODEL.exists():
        raise FileNotFoundError(f"ESRGAN model not found: {ESRGAN_MODEL}")
    
    print("📦 Loading RealESRGAN 4x+...")
    
    # Build network architecture
    model = RRDBNet(
        num_in_ch=3,
        num_out_ch=3,
        num_feat=64,
        num_block=23,
        num_grow_ch=32,
        scale=4
    )
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    # Load weights
    loadnet = torch.load(str(ESRGAN_MODEL), map_location=torch.device('cpu'))
    
    # Handle different model formats
    if 'params_ema' in loadnet:
        loadnet = loadnet['params_ema']
    elif 'params' in loadnet:
        loadnet = loadnet['params']
    # else: loadnet is already the raw state_dict (fixed model format)
    
    model.load_state_dict(loadnet, strict=True)
    model.eval()
    if device == 'cuda':
        model = model.cuda()
    
    _upscaler = RealESRGANer(
        scale=4,
        model_path=str(ESRGAN_MODEL),
        model=model,
        tile=tile,
        tile_pad=10,
        pre_pad=0,
        half=half,
        device=device
    )
    
    print(f"✅ ESRGAN loaded on {device}")
    return _upscaler


def upscale_image(
    image: Image.Image,
    scale: float = 4.0,
    half: bool = False,
    tile: int = 256
) -> Image.Image:
    """
    Upscale an image using RealESRGAN 4x+.
    
    Args:
        image: Input PIL Image
        scale: Output scale factor (default 4.0)
        half: Use FP16 for less VRAM
        tile: Tile size for processing
        
    Returns:
        Upscaled PIL Image
    """
    upscaler = load_esrgan(half=half, tile=tile)
    
    # Ensure RGB
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # PIL to numpy
    img_np = np.array(image)
    
    # RGB to BGR (ESRGAN expects BGR)
    img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    
    # Run upscaling
    print(f"🔍 Upscaling {image.size[0]}x{image.size[1]} → {int(image.size[0]*scale)}x{int(image.size[1]*scale)}...")
    output_bgr, _ = upscaler.enhance(img_bgr, outscale=scale)
    
    # BGR to RGB
    output_rgb = cv2.cvtColor(output_bgr, cv2.COLOR_BGR2RGB)
    output_rgb = np.clip(output_rgb, 0, 255).astype(np.uint8)
    
    result = Image.fromarray(output_rgb)
    print(f"✅ Upscaled to {result.size[0]}x{result.size[1]}")
    
    return result


def unload_esrgan():
    """Free ESRGAN from VRAM."""
    global _upscaler
    _upscaler = None
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    print("🔓 ESRGAN unloaded")


def lanczos_upscale(image: Image.Image, scale: float = 1.0) -> Image.Image:
    """
    Final polish upscale using Lanczos resampling.
    CPU-based, no VRAM needed.
    
    Args:
        image: Input PIL Image
        scale: Scale factor (1.0 = no resize, just polish)
        
    Returns:
        Polished PIL Image
    """
    if scale <= 0:
        scale = 1.0
    
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    new_size = (int(image.width * scale), int(image.height * scale))
    result = image.resize(new_size, Image.LANCZOS)
    
    print(f"✅ Lanczos polish: {image.size} → {result.size}")
    return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        img = Image.open(sys.argv[1])
        result = upscale_image(img)
        out_path = Path(sys.argv[1]).stem + "_upscaled.png"
        result.save(out_path)
        print(f"💾 Saved: {out_path}")
    else:
        print("Usage: python upscaler.py <image_path>")
