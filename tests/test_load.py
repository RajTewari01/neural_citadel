import torch
import diffusers
import transformers
import accelerate
import safetensors
from diffusers import StableDiffusionPipeline, AutoencoderKL
import os

print(f"Diffusers version: {diffusers.__version__}")
print(f"Transformers version: {transformers.__version__}")
print(f"Accelerate version: {accelerate.__version__}")
print(f"Safetensors version: {safetensors.__version__}")

model_path = r"D:\neural_citadel\assets\models\image_gen\checkpoints\diffusionBrushEverythingSFWNSFWAll_v10.safetensors"
vae_path = r"D:\neural_citadel\assets\models\image_gen\vae\vae-ft-mse-840000-ema-pruned.safetensors"

print(f"Model exists: {os.path.exists(model_path)}")
print(f"VAE exists: {os.path.exists(vae_path)}")

print("Attempting to load VAE...")
try:
    vae = AutoencoderKL.from_single_file(vae_path)
    print("VAE loaded successfully.")
except Exception as e:
    print(f"VAE Load Failed: {e}")

print("Attempting to load Pipeline...")
try:
    pipe = StableDiffusionPipeline.from_single_file(model_path, vae=vae if 'vae' in locals() else None)
    print("Pipeline loaded successfully.")
except Exception as e:
    print(f"Pipeline Load Failed: {e}")
