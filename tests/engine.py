"""
Optimized Engine (Float32 + Sequential Offload)
===============================================

The ONLY reliable configuration for GTX 1650 (4GB) to avoid black images:
    1. Full Float32 Pipeline (Prevents NaNs/Black images)
    2. Sequential CPU Offload (Fits Float32 model into 4GB VRAM)
    3. Aggressive Slicing (Minimizes peak memory usage)

Speed: ~10-15s per step (Slower than fp16, but WORKS)
"""

import torch,os
import gc
import uuid
import time
from pathlib import Path
from PIL import Image
from typing import Optional

from diffusers import (
    StableDiffusionPipeline,
    DPMSolverMultistepScheduler,
    AutoencoderKL
)
from diffusers.utils.logging import set_verbosity_error
import warnings

set_verbosity_error()
warnings.filterwarnings("ignore")

_ROOT = Path(__file__).resolve().parent.parent
import sys
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from configs.paths import MODELS_DIR


class DiffusionEngine:
    def __init__(self):
        self.pipe = None
        self.current_model = None
        self.default_model = Path(r"D:\neural_citadel\assets\models\image_gen\diffusion\ghostmix\ghostmix_v20Bakedvae.safetensors")
        self.output_dir = _ROOT / "assets" / "generated"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def _flush(self):
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    def load_model(self, model_path: Optional[Path] = None):
        model_path = model_path or self.default_model
        
        if self.current_model == model_path and self.pipe is not None:
            return
        
        print(f"\nLoading Model (Float32 + Sequential Offload): {model_path.name}")
        start = time.time()
        self._flush()
        
        # --- FIX: Load External VAE ---
        # We use the standard stabilityai VAE which fixes eyes and colors
        print("   -> Loading VAE (stabilityai/sd-vae-ft-mse)...")
        vae = AutoencoderKL.from_single_file(
            r"D:\neural_citadel\assets\models\image_gen\vae\vae-ft-mse-840000-ema-pruned.safetensors",
            torch_dtype=torch.float32
        )
        
        # 1. Load the Checkpoint with the external VAE
        self.pipe = StableDiffusionPipeline.from_single_file(
            str(model_path),
            vae=vae,  # <--- Crucial: Inject the VAE here
            torch_dtype=torch.float32,
            use_safetensors=True,
            safety_checker=None,
            requires_safety_checker=False,
        )
        
        # 2. Sequential Offload (Fits Float32 in 4GB VRAM)
        self.pipe.enable_sequential_cpu_offload()
        print("   -> Sequential CPU offload enabled")
        
        # 3. Maximum split/slicing to save VRAM
        self.pipe.enable_vae_slicing()
        self.pipe.enable_vae_tiling()
        self.pipe.enable_attention_slicing(slice_size="max") 
        print("   -> Aggressive VRAM optimization enabled")
        
        # 4. Use simple scheduler
        self.pipe.scheduler = DPMSolverMultistepScheduler.from_config(
            self.pipe.scheduler.config,
            use_karras_sigmas=True,
            algorithm_type="dpmsolver++"
        )
        
        self.current_model = model_path
        print(f"-> Ready in {time.time() - start:.2f}s")

    def generate(
        self,
        prompt: str = "",
        negative_prompt: str = "",
        width: int = 512,
        height: int = 512,
        steps: int = 30,
        cfg: float = 7.0,
        seed: Optional[int] = None,
        save: bool = True
    ) -> Image.Image:
        if self.pipe is None:
            self.load_model()
        
        width = (width // 8) * 8
        height = (height // 8) * 8
        
        if seed is None:
            seed = torch.randint(0, 2**32 - 1, (1,)).item()
        generator = torch.Generator("cpu").manual_seed(seed) # CPU gen for offload
        
        print(f"\nGenerating: {prompt[:50]}...")
        print(f"   Settings: {width}x{height}, {steps} steps, Float32")
        
        start = time.time()
        
        result = self.pipe(
    prompt = (
   """A sinister hooded figure in black robes kneeling before a stone altar, inside an ancient gothic cathedral crypt, surrounded by hundreds of burning red candles, mysterious occult ritual, statues in stone niches, thick volumetric red fog, dramatic cast shadows, cinematic atmosphere, dark fantasy, hyperrealistic, 8k, detailed stone texture."""
),
negative_prompt = (
    " simple, boring, plain, daytime, flat lighting, low resolution, ugly texture, "
    "cartoon, painting, oversaturated"
),
# Recommended Settings: Steps: 30-40, CFG: 7-8, Sampler: DPM++ 2M Karras,
    width=512,
    height=768,  # Vertical aspect ratio helps full body generation
    num_inference_steps=steps,
    guidance_scale=cfg,
    generator=generator,
)
        
        image = result.images[0]
        duration = time.time() - start
        print(f"Done in {duration:.2f}s ({duration/steps:.2f}s/step)")
        
        if save:
            filename = f"gen_{uuid.uuid4().hex[:8]}.png"
            save_path = self.output_dir / filename
            image.save(save_path)
            print(f"Saved: {save_path}")
            
        return (image, save_path)
    
    def unload(self):
        if self.pipe is not None:
            del self.pipe
            self.pipe = None
            self.current_model = None
        self._flush()

if __name__ == "__main__":
    eng = DiffusionEngine()
    image, path = eng.generate()
    os.startfile(path)
    eng.unload()
