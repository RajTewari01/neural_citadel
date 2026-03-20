import requests
import os
from pathlib import Path
from tqdm import tqdm

API_KEY = "62097c4aab513bd7cb7ec4969b394012"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

DIFFUSION_DIR = Path(r"d:\neural_citadel\assets\models\image_gen\diffusion\nsfw")
LORA_DIR = Path(r"d:\neural_citadel\assets\models\image_gen\lora\nsfw")

DIFFUSION_DIR.mkdir(parents=True, exist_ok=True)
LORA_DIR.mkdir(parents=True, exist_ok=True)

MODELS = [
    # Checkpoints
    {"id": 418386, "type": "checkpoint", "name": "Realistic Lazy Mix"},
    {"id": 2661, "type": "checkpoint", "name": "URPM"},
    {"id": 1031314, "type": "checkpoint", "name": "PornMaster Pro"},
    
    # LoRAs
    {"id": 1706987, "type": "lora", "name": "Porn/Amateur"},
    {"id": 1686108, "type": "lora", "name": "Uniform Slut"},
    {"id": 142273, "type": "lora", "name": "Transexual Woman"},
]

def download_file(url, path):
    if path.exists():
        print(f"Skipping {path.name}, already exists ({path.stat().st_size / 1024 / 1024:.2f} MB)")
        return

    print(f"Downloading {path.name}...")
    try:
        with requests.get(url, headers=HEADERS, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            with open(path, 'wb') as f, tqdm(total=total_size, unit='B', unit_scale=True) as bar:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    bar.update(len(chunk))
        print("Done.")
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        if path.exists(): path.unlink() # Delete partial

def process_model(model_info):
    mid = model_info['id']
    name = model_info['name']
    mtype = model_info['type']
    
    print(f"\nProcessing {name} ({mid})...")
    
    try:
        # Get Model Details
        r = requests.get(f"https://civitai.com/api/v1/models/{mid}", headers=HEADERS)
        r.raise_for_status()
        data = r.json()
        
        versions = data.get('modelVersions', [])
        if not versions:
            print("No versions found!")
            return

        latest = versions[0]
        dl_url = latest['downloadUrl']
        files = latest.get('files', [])
        
        # Determine filename
        filename = f"{name.replace(' ', '_').replace('/', '_')}.safetensors"
        
        primary_file = None
        for f in files:
            if f.get('primary', False):
                primary_file = f
                break
        
        if not primary_file:
            # Fallback to first model file
            for f in files:
                if f['name'].endswith('.safetensors') or f['name'].endswith('.ckpt'):
                    primary_file = f
                    break
                    
        if primary_file:
            filename = primary_file['name']
            dl_url = primary_file['downloadUrl'] # Update URL to file specific if needed, but usually version URL redirects
            # Actually API usually gives downloadUrl in version object which redirects to primary.
            # But if primary is missing we might need specific file URL if available?
            # CivitAI structure: version['downloadUrl'] usually downloads primary.
            # If we want specific file, we construct it? No, usually downloadUrl is enough.
            # But the script uses dl_url from version object (line 64).
            pass
        else:
             print(f"No model file found for {name}")
             return

        target_dir = DIFFUSION_DIR if mtype == "checkpoint" else LORA_DIR
        target_path = target_dir / filename
        
        download_file(dl_url, target_path)
            
    except Exception as e:
        print(f"Error processing {mid}: {e}")

if __name__ == "__main__":
    for m in MODELS:
        process_model(m)
