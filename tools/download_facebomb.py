
import requests
import os
from pathlib import Path
from tqdm import tqdm

API_KEY = "62097c4aab513bd7cb7ec4969b394012"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

# Target Directory
ETHNICITY_DIR = Path(r"d:\neural_citadel\assets\models\image_gen\diffusion\ethinicity")
ETHNICITY_DIR.mkdir(parents=True, exist_ok=True)

# Using generic download logic for FaceBombMix
# Assuming latest version or specific one? User gave ID 7152 (Model ID).
# I'll check metadata first to get correct filename and download URL.
MODEL_ID = 7152

def get_model_file():
    print(f"Fetching metadata for Model {MODEL_ID}...")
    r = requests.get(f"https://civitai.com/api/v1/models/{MODEL_ID}", headers=HEADERS)
    r.raise_for_status()
    data = r.json()
    
    versions = data.get('modelVersions', [])
    if not versions:
        raise ValueError("No versions found")
        
    latest = versions[0]
    filename = latest['files'][0]['name']
    dl_url = latest['downloadUrl']
    
    print(f"Found: {latest['name']} -> {filename}")
    
    target_path = ETHNICITY_DIR / filename
    
    if target_path.exists():
        print("File already exists.")
        return target_path
        
    print(f"Downloading to {target_path}...")
    with requests.get(dl_url, headers=HEADERS, stream=True) as r:
        r.raise_for_status()
        total_size = int(r.headers.get('content-length', 0))
        with open(target_path, 'wb') as f, tqdm(total=total_size, unit='B', unit_scale=True) as bar:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
                bar.update(len(chunk))
    print("Done.")
    return target_path

if __name__ == "__main__":
    get_model_file()
