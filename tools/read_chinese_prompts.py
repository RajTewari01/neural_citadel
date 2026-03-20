import json
from pathlib import Path

files = {
    'ChineseInk': Path('assets/prompts/model_148239_prompts.json'),
    'MoXin': Path('assets/prompts/model_12597_prompts.json')
}

for name, p in files.items():
    if p.exists():
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"\n=== {name} ({data.get('model_name')}) ===")
            prompts = data.get('prompts', [])
            if prompts:
                # Top 1 
                top = prompts[0]
                print(f"Top Positive: {top['prompt'][:200]}")
                print(f"Top Negative: {top['negative_prompt'][:200]}")
                print(f"Settings: Steps={top.get('steps')}, CFG={top.get('cfg_scale')}, Sampler={top.get('sampler')}")
