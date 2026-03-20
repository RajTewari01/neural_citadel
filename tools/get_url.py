import requests
import json

ids = [148239, 12597]

for model_id in ids:
    try:
        r = requests.get(f"https://civitai.com/api/v1/models/{model_id}")
        r.raise_for_status()
        data = r.json()
        
        # Get primary file of latest version
        versions = data.get('modelVersions', [])
        if versions:
            latest = versions[0]
            dl_url = latest['downloadUrl']
            filename = latest['files'][0]['name']
            print(f"ID {model_id}: {filename} -> {dl_url}")
    except Exception as e:
        print(f"Error {model_id}: {e}")
