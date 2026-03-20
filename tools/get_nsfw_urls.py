import requests
import json
import sys

# ID to Name mapping for clarity
models = {
    418386: "Realistic Lazy Mix",
    2661: "URPM",
    1031314: "PornMaster Pro",
    1706987: "Porn/Amateur LoRA",
    1686108: "Uniform LoRA",
    142273: "Transexual LoRA"
}

print("Fetching URLs...")
for model_id, name in models.items():
    try:
        r = requests.get(f"https://civitai.com/api/v1/models/{model_id}")
        r.raise_for_status()
        data = r.json()
        
        versions = data.get('modelVersions', [])
        if versions:
            latest = versions[0]
            dl_url = latest['downloadUrl']
            files = latest.get('files', [])
            filename = "unknown.safetensors"
            if files:
                # specific check for primary model file if possible, or just first safetensors
                for f in files:
                    if f['type'] == "Model" or f['name'].endswith('.safetensors') or f['name'].endswith('.ckpt'):
                         filename = f['name']
                         break
            
            print(f"ID {model_id} ({name}):\n  File: {filename}\n  URL: {dl_url}")
        else:
            print(f"ID {model_id}: No versions found.")
            
    except Exception as e:
        print(f"Error {model_id}: {e}")
