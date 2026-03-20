"""
Inpainting Integration for Image Surgeon
=========================================
Uses existing SD pipeline to inpaint masked regions with new content.
Designed for 4GB VRAM GPUs.
Uses dreamshaper_8 model from configs/paths.py
"""

import torch
import gc
import uuid
import time
from pathlib import Path
from typing import Optional, Union, Tuple
from PIL import Image
import numpy as np

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from configs.paths import DIFFUSION_MODELS, VAE_MODELS, DRESS_MODIFIED_DIR


class InpaintEngine:
    """
    Lightweight inpainting engine using StableDiffusionInpaintPipeline.
    Uses Dreamshaper 8 for high quality background generation.
    Optimized for 4GB VRAM.
    """
    
    def __init__(self):
        """
        Initialize inpainting engine with Dreamshaper 8.
        """
        self.pipe = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Use Dreamshaper 8 for better quality backgrounds
        self.model_path = DIFFUSION_MODELS["dreamshaper"]
        
        print(f"InpaintEngine initialized")
        print(f"   Model: dreamshaper_8")
        print(f"   Device: {self.device}")
    
    def _flush(self):
        """Clean up GPU memory."""
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
    
    def load_model(self):
        """Load the inpainting pipeline."""
        from diffusers import StableDiffusionInpaintPipeline, AutoencoderKL
        
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {self.model_path}")
        
        print(f"Loading inpaint pipeline: {self.model_path.name}")
        
        # Load VAE
        vae_path = VAE_MODELS.get("ft_mse")
        vae = None
        if vae_path and vae_path.exists():
            vae = AutoencoderKL.from_single_file(
                str(vae_path),
                torch_dtype=torch.float32,
                use_safetensors=True,
                local_files_only=True
            )
        
        # Load pipeline
        load_kwargs = {
            "torch_dtype": torch.float32,
            "use_safetensors": self.model_path.suffix == ".safetensors",
            "safety_checker": None,
            "requires_safety_checker": False,
            "local_files_only": True,
        }
        
        if vae:
            load_kwargs["vae"] = vae
        
        self.pipe = StableDiffusionInpaintPipeline.from_single_file(
            str(self.model_path),
            **load_kwargs
        )
        
        # Apply VRAM optimizations (GTX 1650 survival)
        self.pipe.enable_sequential_cpu_offload()
        self.pipe.enable_vae_slicing()
        self.pipe.enable_vae_tiling()
        self.pipe.enable_attention_slicing(slice_size="max")
        
        print(f"Inpaint pipeline loaded")
        
        if torch.cuda.is_available():
            vram_used = torch.cuda.memory_allocated() / 1024**3
            print(f"VRAM used: {vram_used:.2f} GB")
    
    def inpaint(
        self,
        image: Union[str, Path, Image.Image],
        mask: Union[str, Path, Image.Image, np.ndarray],
        prompt: str,
        negative_prompt: str = "ugly, blurry, low quality, distorted",
        strength: float = 0.85,
        steps: int = 25,
        cfg: float = 7.0,
        seed: Optional[int] = None,
        output_path: Optional[Path] = None
    ) -> Image.Image:
        """
        Inpaint a masked region with new content.
        
        Args:
            image: Original image
            mask: Binary mask (white = region to inpaint)
            prompt: What to generate in the masked region
            negative_prompt: What to avoid
            strength: How much to change (0.0-1.0)
            steps: Number of diffusion steps
            cfg: Classifier-free guidance scale
            seed: Random seed for reproducibility
            output_path: Optional path to save result
            
        Returns:
            PIL Image with inpainted content
        """
        if self.pipe is None:
            self.load_model()
        
        # Load image
        if isinstance(image, (str, Path)):
            image = Image.open(image).convert("RGB")
        elif isinstance(image, np.ndarray):
            image = Image.fromarray(image).convert("RGB")
        
        # Load/convert mask
        if isinstance(mask, (str, Path)):
            mask = Image.open(mask).convert("L")
        elif isinstance(mask, np.ndarray):
            mask = Image.fromarray((mask * 255).astype(np.uint8)).convert("L")
        elif isinstance(mask, Image.Image):
            mask = mask.convert("L")
        
        # Ensure same size
        if mask.size != image.size:
            mask = mask.resize(image.size)
        
        # Generate
        seed = seed if seed is not None else torch.randint(0, 2**32 - 1, (1,)).item()
        generator = torch.Generator("cpu").manual_seed(seed)
        
        print(f"Inpainting: {prompt[:50]}...")
        print(f"   Seed: {seed}, Steps: {steps}, CFG: {cfg}")
        
        start = time.time()
        result = self.pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=image,
            mask_image=mask,
            strength=strength,
            num_inference_steps=steps,
            guidance_scale=cfg,
            generator=generator
        )
        
        output = result.images[0]
        print(f"Inpaint time: {time.time() - start:.2f}s")
        
        # Save if path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output.save(output_path)
            print(f"Saved: {output_path}")
        
        return output
    
    def unload(self):
        """Unload model and free VRAM."""
        if self.pipe is not None:
            del self.pipe
            self.pipe = None
        self._flush()
        print("Inpaint pipeline unloaded")


# =============================================================================
# TEST
# =============================================================================
if __name__ == "__main__":
    print("Inpaint Integration Test")
    print("========================")
    print("Usage:")
    print("  from apps.image_surgeon.tools.inpaint import InpaintEngine")
    print("  engine = InpaintEngine()")
    print("  result = engine.inpaint(image, mask, 'prompt')")
