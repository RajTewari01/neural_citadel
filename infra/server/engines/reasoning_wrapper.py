"""
Reasoning Engine Wrapper (Persistent)
=====================================
Wrapper around standalone reasoning engine to provide persistent
interactive loop for the Server, without modifying the standalone file.
"""

import sys
import json
import io
import gc
from pathlib import Path

# Fix path to allow importing from infra
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

# Import setup from standalone (Reuse logic)
from infra.standalone.reasoning_engine import load_model, build_prompt, MAX_TOKENS, TEMPERATURE

def flush_print(msg: str):
    print(msg, flush=True)

def generate_interactive(llm, prompt: str, history: list):
    """Generate with Safe JSON output."""
    full_prompt = build_prompt(prompt, history)
    
    try:
        in_think_block = False
        
        stream = llm(
            full_prompt,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            stop=["<|im_end|>"],
            stream=True
        )
        
        for chunk in stream:
            token = chunk['choices'][0]['text']
            
            # Detect think block transitions
            if '<think>' in token and not in_think_block:
                flush_print("THINK_START")
                in_think_block = True
                token = token.replace('<think>', '')
            
            if '</think>' in token and in_think_block:
                token = token.replace('</think>', '')
                flush_print(f"TOKEN:{json.dumps(token)}")
                flush_print("THINK_END")
                in_think_block = False
                continue
            
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
    
    # Interactive Loop
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
                
            data = json.loads(line)
            prompt = data.get("prompt")
            # Handle optional history
            history = data.get("history", [])
            
            if not prompt:
                continue
                
            generate_interactive(llm, prompt, history)
            
        except json.JSONDecodeError:
            continue
        except Exception as e:
            flush_print(f"ERROR:System Error: {e}")
            
    # Cleanup will happen on exit
    
if __name__ == "__main__":
    main()
