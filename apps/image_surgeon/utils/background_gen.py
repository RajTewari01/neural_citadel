"""
Text2Image Background Generator for Image Surgeon
==================================================
Generates fresh backgrounds using txt2img - NO original image context.
This prevents face hallucination that happens with inpainting.
"""

import torch
import gc
import time
from pathlib import Path
from typing import Optional
from PIL import Image
import sys

# Add project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from configs.paths import DIFFUSION_MODELS


class BackgroundGenerator:
    """
    Generate fresh backgrounds using txt2img.
    NO original image context = NO face hallucination.
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
        """Load the txt2img pipeline."""
        if self.pipe is not None:
            return
        
        from diffusers import StableDiffusionPipeline, AutoencoderKL, DPMSolverSDEScheduler
        import warnings
        warnings.filterwarnings("ignore", category=FutureWarning)
        warnings.filterwarnings("ignore", message=".*deprecate.*")
        
        print("📦 Loading Background Generator (dreamshaper_8)...")
        
        # Load custom VAE
        from configs.paths import VAE_MODELS
        vae_path = VAE_MODELS.get("vae_ft_mse")
        if vae_path is None:
            vae_path = Path("D:/neural_citadel/assets/models/image_gen/vae/vae-ft-mse-840000-ema-pruned.safetensors")
        
        print(f"   Loading VAE: vae-ft-mse-840000")
        vae = AutoencoderKL.from_single_file(
            str(vae_path),
            torch_dtype=torch.float32,
        )
        
        self.pipe = StableDiffusionPipeline.from_single_file(
            str(self.model_path),
            torch_dtype=torch.float32,
            use_safetensors=True,
            safety_checker=None,
            requires_safety_checker=False,
            local_files_only=True,
            vae=vae,
        )
        
        # VRAM optimizations for 4GB GPUs
        self.pipe.enable_sequential_cpu_offload()
        self.pipe.enable_vae_slicing()
        self.pipe.enable_vae_tiling()
        self.pipe.enable_attention_slicing(slice_size="max")
        
        print("✅ Background Generator loaded (CPU offload)")
    
    def generate(
        self,
        prompt: str,
        width: int = 512,
        height: int = 512,
        negative_prompt: str = "person, human, face, portrait, selfie, ugly, blurry, low quality",
        steps: int = 25,
        cfg: float = 7.5,
        seed: int = None
    ) -> Image.Image:
        """
        Generate a fresh background with no original image context.
        
        Args:
            prompt: Background description
            width: Output width
            height: Output height
            negative_prompt: What to avoid
            steps: Diffusion steps
            cfg: Guidance scale
            seed: Random seed
            
        Returns:
            Generated background image
        """
        if self.pipe is None:
            self.load()
        
        import random
        actual_seed = seed if seed else random.randint(0, 2**32-1)
        generator = torch.Generator(device='cpu').manual_seed(actual_seed)
        
        print(f"🎨 Generating fresh background: {prompt[:50]}...")
        print(f"   Size: {width}x{height}, Seed: {actual_seed}")
        
        start = time.time()
        result = self.pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_inference_steps=steps,
            guidance_scale=cfg,
            generator=generator,
        ).images[0]
        
        print(f"✅ Background generated ({time.time()-start:.1f}s)")
        return result
    
    def unload(self):
        """Free VRAM."""
        if self.pipe is not None:
            del self.pipe
            self.pipe = None
        self._flush()
        print("🔓 Background Generator unloaded")


if __name__ == "__main__":
    print("Background Generator - generates fresh backgrounds with txt2img")
    print("Usage:")
    print("  from apps.image_surgeon.utils.background_gen import BackgroundGenerator")
    print("  gen = BackgroundGenerator()")
    print("  bg = gen.generate('tropical beach sunset')")
