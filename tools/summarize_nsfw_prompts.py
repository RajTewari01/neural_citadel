import json
from pathlib import Path
from collections import Counter

PROMPTS_DIR = Path(r"d:\neural_citadel\assets\prompts")

files = [
    "model_418386_prompts.json", # Lazy Mix
    "model_2661_prompts.json",   # URPM
    "model_1031314_prompts.json",# PornMaster
    "model_1686108_prompts.json",# Uniform
    "model_142273_prompts.json", # Trans
]

def analyze_file(filename):
    path = PROMPTS_DIR / filename
    if not path.exists():
        print(f"Skipping {filename}: Not found")
        return

    print(f"\n=== {filename} ===")
    try:
        data = json.load(open(path, encoding='utf-8'))
        
        # Handle dict structure
        if isinstance(data, dict):
            prompt_list = data.get('prompts', []) # Access the list!
        elif isinstance(data, list):
            prompt_list = data
        else:
            prompt_list = []

        # Positive Prompts
        prompts = [item.get('prompt', '') for item in prompt_list if isinstance(item, dict)]
        print(f"Total Prompts: {len(prompts)}")
        
        # Find common words (Trigger words usually appear often)
        # Simplified word count
        all_text = " ".join(prompts).lower()
        words = [w.strip(',.()[]') for w in all_text.split()]
        common = Counter(words).most_common(10)
        print(f"Common Words: {common}")
        
        # Top 3 Prompts by length (assuming detail = length) or just first few
        print("Top Prompt Snippets:")
        for i, p in enumerate(prompts[:3]):
            print(f"  {i+1}: {p[:150]}...")
            
        # Negative Prompts
        neg_prompts = [item.get('negativePrompt', '') for item in data if item.get('negativePrompt')]
        if neg_prompts:
            print(f"Sample Negative: {neg_prompts[0][:150]}...")
            
    except Exception as e:
        print(f"Error reading {filename}: {e}")

if __name__ == "__main__":
    for f in files:
        analyze_file(f)
