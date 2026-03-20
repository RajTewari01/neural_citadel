import requests
from pathlib import Path

# Target Directory
LORA_DIR = Path(r"d:\neural_citadel\assets\models\image_gen\lora\car")
LORA_DIR.mkdir(parents=True, exist_ok=True)

# Models to Download (ID -> Name for logging)
MODELS = {
    "9424": "Mazda RX-7 FD3S",
    "169856": "Concept Sketch",
    "142144": "Autohome HS7",
    "276932": "Hanshin 5001 Jet Car",
    "27216": "Motorbike"
}

def download_model(model_id, name):
    print(f"Processing {name} (ID: {model_id})...")
    
    # 1. Get Model Details (to find download URL)
    api_url = f"https://civitai.com/api/v1/models/{model_id}"
    try:
        resp = requests.get(api_url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        # Get latest version
        latest_version = data["modelVersions"][0]
        download_url = latest_version["downloadUrl"]
        filename = latest_version["files"][0]["name"]
        
        # Sanitize filename if needed (simple check)
        filename = filename.replace("/", "_").replace("\\", "_")
        
        output_path = LORA_DIR / filename
        
        if output_path.exists():
            print(f"  - File already exists: {filename}")
            return filename

        print(f"  - Downloading {filename} from {download_url}...")
        
        # 2. Download File
        with requests.get(download_url, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
        print("  - Download complete!")
        return filename

    except Exception as e:
        print(f"  - Error: {e}")
        return None

if __name__ == "__main__":
    print(f"Downloading {len(MODELS)} models to {LORA_DIR}...")
    for mid, name in MODELS.items():
        download_model(mid, name)
