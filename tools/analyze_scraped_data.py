import json
from pathlib import Path
from collections import Counter

PROMPTS_DIR = Path(r"d:\neural_citadel\assets\prompts")

def analyze_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    model_id = data.get('model_id')
    prompts = data.get('prompts', [])
    
    if not prompts:
        print(f"[{model_id}] No prompts found.")
        return

    # metrics
    all_neg = [p.get('negative_prompt', '') for p in prompts if p.get('negative_prompt')]
    top_prompt = prompts[0]['prompt']
    
    print(f"--- Model {model_id} ---")
    print(f"Top Prompt Sample: {top_prompt[:100]}...")
    if all_neg:
        print(f"Common Negative Start: {all_neg[0][:100]}...")
    print("")

if __name__ == "__main__":
    files = list(PROMPTS_DIR.glob("model_*.json"))
    for p in files:
        analyze_file(p)
