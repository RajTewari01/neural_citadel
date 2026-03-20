"""
Hacking Engine Wrapper (Persistent)
===================================
Wrapper around standalone hacking engine.
"""

import sys
import json
from pathlib import Path

# Setup Path
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

# Import from standalone
from infra.standalone.hacking_engine import load_model, build_prompt, MAX_TOKENS, TEMPERATURE, TOP_P, TOP_K, REPEAT_PENALTY

def flush_print(msg: str):
    print(msg, flush=True)

def generate_interactive(llm, prompt: str):
    full_prompt = build_prompt(prompt)
    
    try:
        stream = llm(
            full_prompt,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            top_k=TOP_K,
            repeat_penalty=REPEAT_PENALTY,
            stop=["<|im_end|>", "[/RESPONSE]", "[/SYSTEM]", "User:"],
            stream=True
        )
        
        for chunk in stream:
            token = chunk['choices'][0]['text']
            if token:
                flush_print(f"TOKEN:{json.dumps(token)}")
        
        flush_print("DONE")
        
    except Exception as e:
        flush_print(f"ERROR:Generation failed: {e}")

def main():
    # Load model
    llm = load_model()
    if llm is None:
        sys.exit(1)
        
    flush_print("READY")
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
                
            data = json.loads(line)
            prompt = data.get("prompt")
            
            if not prompt:
                continue
                
            generate_interactive(llm, prompt)
            
        except json.JSONDecodeError:
            continue
        except Exception as e:
            flush_print(f"ERROR:System Error: {e}")

if __name__ == "__main__":
    main()
