"""
Minimal VAE Load Test
"""
import torch
from pathlib import Path
from diffusers import AutoencoderKL

vae_path = Path(r"D:\neural_citadel\assets\models\image_gen\vae\vae-ft-mse-840000-ema-pruned.safetensors")
print(f"VAE exists: {vae_path.exists()}")

print("Loading VAE...")
try:
    vae = AutoencoderKL.from_single_file(
        str(vae_path),
        torch_dtype=torch.float32,
        use_safetensors=True
    )
    print("VAE loaded successfully!")
except Exception as e:
    print(f"VAE load failed: {e}")
    import traceback
    traceback.print_exc()
