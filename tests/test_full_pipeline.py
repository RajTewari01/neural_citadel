"""
Full Pipeline Load Test
"""
import torch
from pathlib import Path
from diffusers import StableDiffusionPipeline, AutoencoderKL

model_path = Path(r"D:\neural_citadel\assets\models\image_gen\diffusion\illustrator\diffusionBrushEverythingSFWNSFWAll_v10.safetensors")
vae_path = Path(r"D:\neural_citadel\assets\models\image_gen\vae\vae-ft-mse-840000-ema-pruned.safetensors")

print(f"Model exists: {model_path.exists()}")
print(f"VAE exists: {vae_path.exists()}")

print("Loading VAE...")
vae = AutoencoderKL.from_single_file(str(vae_path), torch_dtype=torch.float32)
print("VAE OK")

print("Loading Pipeline...")
try:
    pipe = StableDiffusionPipeline.from_single_file(
        str(model_path),
        vae=vae,
        torch_dtype=torch.float32,
        use_safetensors=True,
        safety_checker=None,
        requires_safety_checker=False
    )
    print("Pipeline loaded!")
    
    print("Enabling optimizations...")
    pipe.enable_sequential_cpu_offload()
    pipe.enable_vae_slicing()
    print("Optimizations OK")
    
    print("SUCCESS: Pipeline ready for generation")
    del pipe
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
