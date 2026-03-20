
import requests
import os
from pathlib import Path
from tqdm import tqdm

API_KEY = "62097c4aab513bd7cb7ec4969b394012"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

# Target Directory
LORA_DIR = Path(r"d:\neural_citadel\assets\models\image_gen\lora\style")
LORA_DIR.mkdir(parents=True, exist_ok=True)

TARGET_FILE = LORA_DIR / "polaroid.safetensors"
DOWNLOAD_URL = "https://civitai.com/api/download/models/102533"

def download_file():
    if TARGET_FILE.exists():
        print(f"Skipping {TARGET_FILE.name}, already exists ({TARGET_FILE.stat().st_size / 1024 / 1024:.2f} MB)")
        return

    print(f"Downloading {TARGET_FILE.name} from {DOWNLOAD_URL}...")
    try:
        with requests.get(DOWNLOAD_URL, headers=HEADERS, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            with open(TARGET_FILE, 'wb') as f, tqdm(total=total_size, unit='B', unit_scale=True) as bar:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    bar.update(len(chunk))
        print("Done.")
    except Exception as e:
        print(f"Failed to download: {e}")
        if TARGET_FILE.exists(): TARGET_FILE.unlink()

if __name__ == "__main__":
    download_file()
