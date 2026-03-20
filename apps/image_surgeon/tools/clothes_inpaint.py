"""
Clothes Inpainting for Image Surgeon
=====================================
Uses ZenityX Clothes Inpainting model (trigger word: CLOTHES)
For prompt-based clothing changes without a garment image.
"""

import torch
import gc
import time
from pathlib import Path
from typing import Optional, Union
from PIL import Image
import numpy as np
import sys

# Add project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from configs.paths import DIFFUSION_MODELS, VAE_MODELS


class ClothesInpaintEngine:
    """
    Clothes inpainting using ZenityX model (trigger: CLOTHES).
    For changing clothes via prompt without needing a garment image.
    """
    
    def __init__(self):
        self.pipe = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_path = DIFFUSION_MODELS["clothes_inpainting"]
        
        print("ClothesInpaintEngine initialized")
        print(f"   Model: ZenityX Clothes Inpainting")
        print(f"   Device: {self.device}")
    
    def _flush(self):
        """Clean GPU memory."""
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    def load(self):
        """Load the inpainting pipeline."""
        if self.pipe is not None:
            return
        
        from diffusers import StableDiffusionInpaintPipeline
        import warnings
        warnings.filterwarnings("ignore", category=FutureWarning)
        warnings.filterwarnings("ignore", message=".*deprecate.*")
        
        print("📦 Loading Clothes Inpainting (ZenityX)...")
        
        self.pipe = StableDiffusionInpaintPipeline.from_single_file(
            str(self.model_path),
            torch_dtype=torch.float32,
            use_safetensors=True,
            safety_checker=None,
            requires_safety_checker=False,
            local_files_only=True,
        )
        
        # VRAM optimizations for 4GB GPUs
        self.pipe.enable_sequential_cpu_offload()
        self.pipe.enable_vae_slicing()
        self.pipe.enable_vae_tiling()
        self.pipe.enable_attention_slicing(slice_size="max")
        
        print("✅ Clothes Inpainting loaded (CPU offload)")
    
    def inpaint(
        self,
        image: Image.Image,
        mask: Image.Image,
        prompt: str,
        negative_prompt: str = "ugly, blurry, low quality, distorted, deformed",
        strength: float = 0.95,
        steps: int = 36,
        cfg: float = 15.0
    ) -> Image.Image:
        """
        Inpaint clothes on a person.
        
        Args:
            image: Original person image
            mask: Mask of clothes area (white = inpaint)
            prompt: Clothes description (will add CLOTHES trigger)
            negative_prompt: What to avoid
            strength: Inpainting strength
            steps: Diffusion steps
            cfg: Guidance scale
            
        Returns:
            Image with new clothes
        """
        if self.pipe is None:
            self.load()
        
        # Ensure correct modes
        if image.mode != 'RGB':
            image = image.convert('RGB')
        if mask.mode != 'L':
            mask = mask.convert('L')
        
        # Add trigger word and realistic boost
        full_prompt = f"Clothes, (realistic:1.4), {prompt}"
        
        import random
        seed = random.randint(0, 2**32-1)
        generator = torch.Generator(device='cpu').manual_seed(seed)
        
        print(f"👔 Changing clothes: {prompt[:50]}...")
        print(f"   Full prompt: {full_prompt[:60]}...")
        print(f"   Seed: {seed}, Steps: {steps}, CFG: {cfg}")
        
        start = time.time()
        result = self.pipe(
            prompt=full_prompt,
            negative_prompt=negative_prompt,
            image=image,
            mask_image=mask,
            strength=strength,
            num_inference_steps=steps,
            guidance_scale=cfg,
            generator=generator,
        ).images[0]
        
        print(f"✅ Clothes changed ({time.time()-start:.1f}s)")
        return result
    
    def unload(self):
        """Free GPU memory."""
        if self.pipe is not None:
            del self.pipe
            self.pipe = None
        self._flush()
        print("🔓 Clothes Inpainting unloaded")


if __name__ == "__main__":
    print("Clothes Inpainting for Image Surgeon")
    print("Usage:")
    print("  from apps.image_surgeon.tools.clothes_inpaint import ClothesInpaintEngine")
    print("  engine = ClothesInpaintEngine()")
    print("  result = engine.inpaint(image, mask, 'red evening dress')")
