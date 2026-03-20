"""
Code Engine Wrapper (Persistent)
================================
Wrapper around standalone code engine to provide persistent
interactive loop for the Server.
"""

import sys
import json
import argparse
from pathlib import Path

# Setup Path
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

# Import from standalone
from infra.standalone.code_engine import load_model, build_prompt, MAX_TOKENS, TEMPERATURE, N_CTX, N_BATCH, N_GPU_LAYERS

def flush_print(msg: str):
    print(msg, flush=True)

def generate_interactive(llm, prompt: str, model_name: str):
    """Generate code with proper streaming protocol."""
    full_prompt = build_prompt(prompt, model_name)
    
    try:
        # Code generation usually doesn't need "thinking" logic like Reasoning
        # Just pure stream
        stream = llm(
            full_prompt,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            stop=["<|im_end|>", "### Response:", "<|endoftext|>"], # Add common stops
            stream=True
        )
        
        for chunk in stream:
            token = chunk['choices'][0]['text']
            if token:
                # Use strict TOKEN protocol
                flush_print(f"TOKEN:{json.dumps(token)}")
        
        flush_print("DONE")
        
    except Exception as e:
        flush_print(f"ERROR:Generation failed: {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="deepseek", help="deepseek or qwen")
    args = parser.parse_args()
    
    # Load model once
    llm = load_model(args.model)
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
            # We don't change model mid-stream for persistent process
            
            if not prompt:
                continue
                
            generate_interactive(llm, prompt, args.model)
            
        except json.JSONDecodeError:
            continue
        except Exception as e:
            flush_print(f"ERROR:System Error: {e}")

if __name__ == "__main__":
    main()
