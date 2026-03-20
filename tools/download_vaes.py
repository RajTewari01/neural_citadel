"""
Download Working Anime VAEs
"""
import requests
from pathlib import Path
import sys

VAE_DIR = Path("d:/neural_citadel/assets/models/image_gen/vae")

# Hugging Face direct downloads for anime VAEs
VAES_TO_DOWNLOAD = {
    # kl-f8-anime2 VAE - the most common anime VAE
    "anime.vae.safetensors": "https://huggingface.co/hakurei/waifu-diffusion-v1-4/resolve/main/vae/kl-f8-anime2.ckpt",
    
    # OrangeMix VAE from stabilityai
    "orangemix.vae.safetensors": "https://huggingface.co/stabilityai/sd-vae-ft-mse-original/resolve/main/vae-ft-mse-840000-ema-pruned.safetensors"
}

def download_file(url: str, dest: Path):
    print(f"Downloading: {dest.name}")
    print(f"  From: {url}")
    
    response = requests.get(url, stream=True, timeout=300)
    response.raise_for_status()
    
    total = int(response.headers.get('content-length', 0))
    downloaded = 0
    
    with open(dest, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = (downloaded / total) * 100
                print(f"\r  Progress: {pct:.1f}%", end="", flush=True)
    
    print(f"\n  Saved: {dest}")

if __name__ == "__main__":
    for filename, url in VAES_TO_DOWNLOAD.items():
        dest = VAE_DIR / filename
        if dest.exists():
            print(f"Skipping {filename} - already exists")
            continue
        try:
            download_file(url, dest)
        except Exception as e:
            print(f"Failed to download {filename}: {e}")
