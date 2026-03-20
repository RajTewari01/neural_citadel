"""
Diffusion Upscaler for Image Surgeon
=====================================
Uses SD img2img to hallucinate additional details.
STANDALONE - does NOT import from image_gen to avoid dependency conflicts.
"""

import torch
import gc
import time
from pathlib import Path
from typing import Optional
from PIL import Image
import numpy as np
import sys

# Add project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from configs.paths import DIFFUSION_MODELS


class DiffusionUpscaler:
    """
    Hallucinate details using SD img2img.
    Uses dreamshaper_8 for high quality results.
    """
    
    def __init__(self):
        self.pipe = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_path = DIFFUSION_MODELS["dreamshaper"]
    
    def _flush(self):
        """Clean up GPU memory."""
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    def load(self):
        """Load the img2img pipeline."""
        if self.pipe is not None:
            return
        
        from diffusers import StableDiffusionImg2ImgPipeline, AutoencoderKL
        import warnings
        warnings.filterwarnings("ignore", category=FutureWarning)
        warnings.filterwarnings("ignore", message=".*deprecate.*")
        
        print("📦 Loading Diffusion Upscaler (dreamshaper_8)...")
        
        self.pipe = StableDiffusionImg2ImgPipeline.from_single_file(
            str(self.model_path),
            torch_dtype=torch.float32,
            use_safetensors=True,
            safety_checker=None,
            requires_safety_checker=False,
            local_files_only=True,
        )
        
        # VRAM optimizations for 4GB GPUs - CPU offload is key
        self.pipe.enable_sequential_cpu_offload()  # Moves to CPU between layers
        self.pipe.enable_vae_slicing()
        self.pipe.enable_vae_tiling()
        self.pipe.enable_attention_slicing(slice_size="max")
        
        print("✅ Diffusion Upscaler loaded (CPU offload enabled)")
    
    def upscale(
        self,
        image: Image.Image,
        prompt: str = "highly detailed, sharp focus, 8k, masterpiece",
        negative_prompt: str = "blurry, low quality, distorted, ugly",
        strength: float = 0.4,
        steps: int = 15,
        cfg: float = 7.0,
        scale: float = 1.5
    ) -> Image.Image:
        """
        Upscale image with hallucinated details.
        
        Args:
            image: Input image
            prompt: Quality prompt for enhancement
            negative_prompt: What to avoid
            strength: How much to change (0.0-1.0, lower = more faithful)
            steps: Diffusion steps
            cfg: Guidance scale
            scale: Scale factor before processing
            
        Returns:
            Enhanced image
        """
        if self.pipe is None:
            self.load()
        
        # Scale up first
        if scale > 1.0:
            new_size = (int(image.width * scale), int(image.height * scale))
            image = image.resize(new_size, Image.LANCZOS)
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        print(f"🔮 Diffusion upscale: {image.size}, strength={strength}")
        
        start = time.time()
        result = self.pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=image,
            strength=strength,
            num_inference_steps=steps,
            guidance_scale=cfg,
        ).images[0]
        
        print(f"✅ Diffusion upscale complete: {result.size} ({time.time()-start:.1f}s)")
        return result
    
    def unload(self):
        """Free VRAM."""
        if self.pipe is not None:
            del self.pipe
            self.pipe = None
        self._flush()
        print("🔓 Diffusion Upscaler unloaded")


# Standalone function for easy use
def diffusion_upscale(
    image: Image.Image,
    prompt: str = "highly detailed, sharp focus, 8k, masterpiece",
    strength: float = 0.4,
    scale: float = 1.5
) -> Image.Image:
    """
    Quick function to do diffusion upscale.
    Loads and unloads automatically.
    """
    upscaler = DiffusionUpscaler()
    try:
        result = upscaler.upscale(image, prompt=prompt, strength=strength, scale=scale)
        return result
    finally:
        upscaler.unload()


if __name__ == "__main__":
    print("Diffusion Upscaler for Image Surgeon")
    print("Usage:")
    print("  from apps.image_surgeon.utils.diffusion_upscale import diffusion_upscale")
    print("  result = diffusion_upscale(image)")
