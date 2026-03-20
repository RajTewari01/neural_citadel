"""
Diffusion Img2Img Upscaler
==========================

GPU-based upscaling using Stable Diffusion Img2Img pipeline.
Hallucinates new details by running additional inference steps.

Characteristics:
    - VRAM: Reuses base SD pipe (~4-6GB total)
    - Speed: Slow (15-30 seconds for 20 steps)
    - Quality: Can add creative details
    - Risk: May change faces/features at higher strengths

Best For:
    - Adding texture and fine details
    - When you want AI-enhanced upscaling
    - Creative/artistic enhancement

Strength Guide:
    - 0.20-0.35: Safe, preserves original well
    - 0.35-0.50: Moderate changes, adds detail
    - 0.50-0.70: Major changes, may alter faces

Note: This upscaler REQUIRES an active Stable Diffusion pipeline.
It cannot work standalone like Real-ESRGAN upscalers.
"""

import torch
from PIL import Image
from typing import Optional, TYPE_CHECKING
from diffusers import AutoPipelineForImage2Image
from diffusers.utils.logging import set_verbosity_error

if TYPE_CHECKING:
    from diffusers import StableDiffusionPipeline

set_verbosity_error()

def upscale(
    base_pipe: "StableDiffusionPipeline",
    image: Image.Image,
    prompt: str,
    negative_prompt: str = "",
    scale_factor: float = 1.5,
    strength: float = 0.6,
    guidance_scale: float = 6.5,
    num_inference_steps: int = 20,
) -> Image.Image:
    """
    Upscale an image using Img2Img diffusion.
    
    Args:
        base_pipe: The loaded StableDiffusionPipeline (reused to save VRAM)
        image: The low-res generated image
        prompt: The generation prompt (for consistent style)
        negative_prompt: Negative prompt
        scale_factor: 1.5x is safe for 6GB VRAM. 2.0x might crash.
        strength: 0.35 = preserve original, 0.70 = major changes
        guidance_scale: CFG scale (default 6.5)
        num_inference_steps: Steps for upscale pass (20 is usually enough)
    
    Returns:
        Upscaled PIL Image
    """
    print(f"[Upscale] Diffusion: {scale_factor}x (strength={strength})")
    
    # 1. Prepare Target Resolution
    target_width = int(image.size[0] * scale_factor)
    target_height = int(image.size[1] * scale_factor)
    
    # Ensure dimensions are multiples of 8
    target_width = (target_width // 8) * 8
    target_height = (target_height // 8) * 8
    
    # Pre-resize gives the AI a "sketch" to work on
    input_image = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
    
    # 2. Convert text-to-image pipe to img2img (no extra VRAM!)
    # Note: this usually shares components, preventing duplicate VRAM usage
    img2img = AutoPipelineForImage2Image.from_pipe(base_pipe)
    
    # 3. Enable Tiling (CRITICAL for 6GB VRAM)
    if hasattr(img2img, "enable_vae_tiling"):
        img2img.enable_vae_tiling()
    
    try:
        # 4. Generate
        upscaled = img2img(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=input_image,
            strength=strength,
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
            output_type="pil"
        ).images[0]
        
        print(f"[DONE] Diffusion upscale complete: {upscaled.size}")
        return upscaled
        
    except torch.cuda.OutOfMemoryError:
        print("[!] GPU Out Of Memory! Returning Lanczos fallback...")
        torch.cuda.empty_cache()
        # Return the lanczos-upscaled version as fallback
        return input_image


def upscale_with_fallback(
    base_pipe: "StableDiffusionPipeline",
    image: Image.Image,
    prompt: str,
    negative_prompt: str = "",
    scale_factor: float = 1.5,
    **kwargs
) -> Image.Image:
    """
    Upscale with automatic fallback to CPU Lanczos on OOM.
    
    Same args as upscale(), plus:
        **kwargs: Additional arguments passed to upscale()
    """
    try:
        return upscale(
            base_pipe=base_pipe,
            image=image,
            prompt=prompt,
            negative_prompt=negative_prompt,
            scale_factor=scale_factor,
            **kwargs
        )
    except Exception as e:
        print(f"[!] Diffusion upscale failed: {e}")
        print("   Falling back to Lanczos...")
        
        target_width = int(image.size[0] * scale_factor)
        target_height = int(image.size[1] * scale_factor)
        return image.resize((target_width, target_height), Image.Resampling.LANCZOS)
