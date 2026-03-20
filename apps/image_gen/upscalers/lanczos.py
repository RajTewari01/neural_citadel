"""
Lanczos CPU Upscaler
====================

High-quality CPU-based upscaling with no VRAM usage.

Characteristics:
    - VRAM: Zero (100% CPU)
    - Quality: Clean, non-hallucinated results
    - Speed: Fast
    - Best For: Fallback, VRAM-constrained situations

Uses multi-stage processing:
    1. Lanczos resampling (best interpolation)
    2. Two-pass unsharp mask (natural sharpness)
    3. Adaptive contrast boost
    4. Optional color grading
"""

from PIL import Image, ImageEnhance, ImageFilter
from typing import Optional, Tuple


def upscale(
    image: Image.Image,
    scale: float = 2.0,
    target_size: Optional[Tuple[int, int]] = None,
    sharpen: bool = True,
    cinematic: bool = False
) -> Image.Image:
    """
    High-quality Lanczos upscale with smart post-processing.
    
    Args:
        image: Input PIL Image
        scale: Scale factor (default 2.0x)
        target_size: Optional (width, height) tuple to override scale
        sharpen: Apply smart sharpening (default True)
        cinematic: Apply cinematic color grading (default False)
    
    Returns:
        Upscaled PIL Image
    """
    print(f"[Upscale] CPU: Lanczos {scale}x")
    
    # 1. Calculate Target Size
    if target_size:
        target_width, target_height = target_size
    else:
        target_width = int(image.size[0] * scale)
        target_height = int(image.size[1] * scale)
    
    # Ensure dimensions are multiples of 8 (prevents artifacts)
    target_width = (target_width // 8) * 8
    target_height = (target_height // 8) * 8
    
    print(f"   -> Target: {target_width}x{target_height}")
    
    # 2. High-Quality Lanczos Resize
    img_resized = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
    
    if not sharpen:
        return img_resized
    
    # 3. Two-Pass Smart Sharpening (more natural than single aggressive pass)
    print("   -> Applying two-pass sharpening...")
    
    # Pass 1: Gentle overall sharpening
    img_sharp = img_resized.filter(
        ImageFilter.UnsharpMask(radius=1.0, percent=80, threshold=2)
    )
    
    # Pass 2: Edge enhancement (subtle)
    img_sharp = img_sharp.filter(
        ImageFilter.UnsharpMask(radius=2.0, percent=40, threshold=4)
    )
    
    # 4. Subtle Contrast Boost (adaptive)
    enhancer = ImageEnhance.Contrast(img_sharp)
    img_processed = enhancer.enhance(1.08)
    
    # 5. Optional Cinematic Color Grading
    if cinematic:
        print("   -> Applying cinematic grade...")
        # Slight desaturation
        color_enhancer = ImageEnhance.Color(img_processed)
        img_processed = color_enhancer.enhance(0.90)
        
        # Subtle brightness lift in shadows
        brightness_enhancer = ImageEnhance.Brightness(img_processed)
        img_processed = brightness_enhancer.enhance(1.02)
    
    return img_processed


def upscale_fast(image: Image.Image, scale: float = 2.0) -> Image.Image:
    """
    Minimal Lanczos upscale with no post-processing.
    Fastest option when you just need a bigger image.
    """
    target_width = int(image.size[0] * scale)
    target_height = int(image.size[1] * scale)
    return image.resize((target_width, target_height), Image.Resampling.LANCZOS)


def upscale_to_2k(image: Image.Image, sharpen: bool = True) -> Image.Image:
    """
    Convenience function to upscale to ~2K resolution.
    Maintains aspect ratio, targets 2560px width.
    """
    target_width = 2560
    aspect_ratio = image.size[1] / image.size[0]
    target_height = int(target_width * aspect_ratio)
    
    return upscale(
        image,
        target_size=(target_width, target_height),
        sharpen=sharpen
    )