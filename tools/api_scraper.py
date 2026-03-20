"""
CivitAI API Scraper (Fast, Authenticated)
==========================================

Uses your CivitAI API key to fetch prompts from any model.

Usage:
    python api_scraper.py https://civitai.com/models/46294
"""

import requests
import json
import re
import sys
from pathlib import Path


# Your CivitAI API Key
API_KEY = "62097c4aab513bd7cb7ec4969b394012"


class CivitAIClient:
    """CivitAI API client with authentication."""
    
    BASE_URL = "https://civitai.com/api/v1"
    
    def __init__(self, api_key: str):
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        })
    
    def get_model(self, model_id: int) -> dict:
        """Get model info including images."""
        url = f"{self.BASE_URL}/models/{model_id}"
        response = self.session.get(url, timeout=120)
        response.raise_for_status()
        return response.json()
    
    def get_images(self, model_id: int = None, limit: int = 50) -> list:
        """Get images for a model."""
        url = f"{self.BASE_URL}/images"
        params = {"limit": limit, "sort": "Most Reactions"}
        if model_id:
            params["modelId"] = model_id
        
        response = self.session.get(url, params=params, timeout=120)
        response.raise_for_status()
        return response.json().get('items', [])
    
    def get_image(self, image_id: int) -> dict:
        """Get single image details."""
        url = f"{self.BASE_URL}/images/{image_id}"
        response = self.session.get(url, timeout=120)
        response.raise_for_status()
        return response.json()


def extract_model_id(url: str) -> int:
    """Extract model ID from CivitAI URL."""
    match = re.search(r'/models/(\d+)', url)
    if match:
        return int(match.group(1))
    return None


def extract_image_id(url: str) -> int:
    """Extract image ID from CivitAI URL."""
    match = re.search(r'/images/(\d+)', url)
    if match:
        return int(match.group(1))
    return None


def scrape_model(client: CivitAIClient, model_id: int) -> list:
    """Scrape all prompts from a model."""
    
    print(f"Fetching model {model_id}...")
    
    # Get model info (includes some images)
    model = client.get_model(model_id)
    print(f"Model: {model.get('name')}")
    
    # Get more images from gallery
    print("Fetching gallery images...")
    images = client.get_images(model_id, limit=100)
    print(f"Found {len(images)} images")
    
    prompts = []
    
    for img in images:
        meta = img.get('meta')
        if not meta:
            continue
        
        # Handle dict-like meta
        if not isinstance(meta, dict):
            continue
        
        # CivitAI API sometimes nests meta inside meta
        if 'meta' in meta and isinstance(meta.get('meta'), dict):
            meta = meta.get('meta', {})
        
        prompt = meta.get('prompt')
        
        if prompt:
            prompts.append({
                'prompt': prompt,
                'negative_prompt': meta.get('negativePrompt', ''),
                'steps': meta.get('steps'),
                'cfg_scale': meta.get('cfgScale'),
                'sampler': meta.get('sampler'),
                'seed': meta.get('seed'),
                'size': f"{img.get('width')}x{img.get('height')}",
                'reactions': img.get('stats', {}).get('heartCount', 0),
            })
    
    # Sort by reactions
    prompts.sort(key=lambda x: x.get('reactions', 0), reverse=True)
    
    print(f"Extracted {len(prompts)} prompts with metadata")
    return prompts


def main():
    if len(sys.argv) < 2:
        print("Usage: python api_scraper.py <civitai_url> [civitai_url_2 ...]")
        sys.exit(1)
    
    client = CivitAIClient(API_KEY)
    
    for url in sys.argv[1:]:
        print(f"\nProcessing: {url}")
        if '/images/' in url:
            # Single image
            image_id = extract_image_id(url)
            if image_id:
                print(f"Fetching image {image_id}...")
                try:
                    img = client.get_image(image_id)
                    meta = img.get('meta') or {}
                    if meta.get('prompt'):
                        print("\n=== PROMPT ===")
                        print(f"Prompt: {meta.get('prompt')}")
                        print(f"\nNegative: {meta.get('negativePrompt', '')}")
                        print(f"\nSteps: {meta.get('steps')}, CFG: {meta.get('cfgScale')}, Sampler: {meta.get('sampler')}")
                    else:
                        print("No prompt metadata (hidden by uploader)")
                except Exception as e:
                    print(f"Error: {e}")
        else:
            # Model page
            model_id = extract_model_id(url)
            if model_id:
                try:
                    prompts = scrape_model(client, model_id)
                    
                    if prompts:
                        print("\n" + "="*60)
                        print("TOP 5 PROMPTS (by reactions)")
                        print("="*60)
                        
                        for i, p in enumerate(prompts[:5], 1):
                            print(f"\n--- #{i} ({p.get('reactions', 0)} hearts) ---")
                            print(f"Prompt: {p['prompt'][:150]}...")
                            print(f"Negative: {p['negative_prompt'][:80]}...")
                            print(f"Settings: {p['steps']} steps, CFG {p['cfg_scale']}, {p['sampler']}")
                        
                        # Save all
                        output = Path(__file__).parent.parent / "assets" / "prompts" / f"model_{model_id}_prompts.json"
                        output.parent.mkdir(parents=True, exist_ok=True)
                        
                        with open(output, 'w', encoding='utf-8') as f:
                            json.dump({
                                'model_id': model_id,
                                'prompt_count': len(prompts),
                                'prompts': prompts,
                            }, f, indent=2, ensure_ascii=False)
                        
                        print(f"\n✓ Saved {len(prompts)} prompts to: {output}")
                    else:
                        print(f"No prompts found for model {model_id}")
                except Exception as e:
                    print(f"Error processing model {model_id}: {e}")

if __name__ == "__main__":
    main()