"""
Full Pipeline Load Test - With file logging
"""
import sys
import torch
from pathlib import Path

# Redirect stderr to file for debugging
log_file = open("d:/neural_citadel/debug_error.txt", "w")
sys.stderr = log_file
sys.stdout = log_file

try:
    from diffusers import StableDiffusionPipeline, AutoencoderKL

    model_path = Path(r"D:\neural_citadel\assets\models\image_gen\diffusion\illustrator\diffusionBrushEverythingSFWNSFWAll_v10.safetensors")
    vae_path = Path(r"D:\neural_citadel\assets\models\image_gen\vae\vae-ft-mse-840000-ema-pruned.safetensors")

    print(f"Model exists: {model_path.exists()}")
    print(f"VAE exists: {vae_path.exists()}")

    print("Loading VAE...")
    vae = AutoencoderKL.from_single_file(str(vae_path), torch_dtype=torch.float32)
    print("VAE OK")

    print("Loading Pipeline...")
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
    
    print("SUCCESS: Pipeline ready!")
    del pipe
except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    traceback.print_exc()
finally:
    log_file.flush()
    log_file.close()
