"""Scrape CivitAI images endpoint"""
import requests
import json

API_KEY = "62097c4aab513bd7cb7ec4969b394012"

# Try images endpoint with different params
print("Testing CivitAI Images API...")

r = requests.get(
    "https://civitai.com/api/v1/images",
    params={"modelId": 7240, "limit": 50, "sort": "Newest"},
    timeout=60,
    headers={"Authorization": f"Bearer {API_KEY}"}
)

print(f"Status: {r.status_code}")

if r.status_code == 200:
    data = r.json()
    items = data.get("items", [])
    print(f"Images returned: {len(items)}")
    
    prompts = []
    for img in items:
        meta = img.get("meta")
        if meta and isinstance(meta, dict) and meta.get("prompt"):
            prompts.append({
                "prompt": meta.get("prompt"),
                "negative_prompt": meta.get("negativePrompt", ""),
                "steps": meta.get("steps"),
                "cfg_scale": meta.get("cfgScale"),
                "sampler": meta.get("sampler"),
                "size": f"{img.get('width')}x{img.get('height')}",
            })
    
    print(f"Prompts with metadata: {len(prompts)}")
    
    if prompts:
        output = {
            "model_id": 7240,
            "model_name": "MeinaMix",
            "prompt_count": len(prompts),
            "prompts": prompts
        }
        
        with open("assets/prompts/meinamix_prompts.json", "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\nSaved {len(prompts)} prompts to meinamix_prompts.json")
        print(f"\nTop prompt:")
        print(f"  {prompts[0]['prompt'][:200]}...")
        print(f"  Steps: {prompts[0]['steps']}, CFG: {prompts[0]['cfg_scale']}, Sampler: {prompts[0]['sampler']}")
else:
    print(f"Error: {r.text[:500]}")
