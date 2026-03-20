import json
from pathlib import Path

base = Path('assets/prompts')
files = {
    'Rachel': base / 'model_1122_prompts.json',
    'Matcha': base / 'model_1128_prompts.json',
    'Pareidolia': base / 'model_1242_prompts.json'
}

for name, p in files.items():
    if p.exists():
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"\n=== {name} ({data.get('model_name')}) ===")
            prompts = data.get('prompts', [])
            if prompts:
                # Get top 3 to see trends
                for i, top in enumerate(prompts[:3]):
                    print(f"\n--- Top {i+1} ---")
                    print(f"Positive: {top['prompt'][:100]}...")
                    print(f"Negative: {top['negative_prompt'][:100]}...")
    else:
        print(f"{name}: Not found")
