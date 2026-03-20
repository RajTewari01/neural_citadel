"""
Code Engine - DeepSeek Coder / Qwen Coder
==========================================

Standalone CLI for coding assistance using coder models.
Runs in coreagentvenv via subprocess from PyQt GUI.

Usage:
    python code_engine.py --prompt "Write a function to sort a list" --model deepseek
    python code_engine.py --prompt "Create a REST API" --model qwen
    
Output Protocol:
    LOADED          - Model loaded successfully
    TOKEN:<text>    - Each token as it streams
    DONE            - Generation complete
    ERROR:<msg>     - Error occurred
"""

import argparse
import json
import sys
import gc
import io
from pathlib import Path

# Ensure UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Model paths
MODELS_DIR = Path(__file__).resolve().parents[2] / "assets" / "models" / "llm" / "llm"

MODEL_PATHS = {
    "deepseek": MODELS_DIR / "Deepseek_Model" / "deepseek-coder-6.7b-instruct.Q4_K_M.gguf",
    "qwen": MODELS_DIR / "Qwen_Coder_Model" / "Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf"
}

# VRAM-optimized settings
N_CTX = 4096
N_BATCH = 256
N_GPU_LAYERS = -1
MAX_TOKENS = 2048
TEMPERATURE = 0.3  # Lower for more deterministic code


def flush_print(msg: str):
    """Print with immediate flush for real-time streaming."""
    print(msg, flush=True)


def load_model(model_name: str):
    """Load the selected coder model."""
    try:
        from llama_cpp import Llama
        
        model_path = MODEL_PATHS.get(model_name)
        if not model_path or not model_path.exists():
            flush_print(f"ERROR:Model not found: {model_name}")
            return None
        
        llm = Llama(
            model_path=str(model_path),
            n_ctx=N_CTX,
            n_batch=N_BATCH,
            n_gpu_layers=N_GPU_LAYERS,
            verbose=False
        )
        
        flush_print("LOADED")
        return llm
        
    except Exception as e:
        flush_print(f"ERROR:Failed to load model: {e}")
        return None


def build_prompt(user_prompt: str, model_name: str) -> str:
    """Build the prompt based on model type."""
    
    system_msg = """You are an expert programmer. Write clean, efficient, well-commented code.
If the user asks for code, provide complete working code with proper structure.
Include necessary imports and handle edge cases."""

    if model_name == "deepseek":
        # DeepSeek format
        return f"""<|begin_of_sentence|>You are an AI programming assistant.
### Instruction:
{user_prompt}

### Response:
"""
    else:
        # Qwen format
        return f"""<|im_start|>system
{system_msg}<|im_end|>
<|im_start|>user
{user_prompt}<|im_end|>
<|im_start|>assistant
"""


def generate(llm, prompt: str, model_name: str):
    """Generate code with streaming output."""
    
    full_prompt = build_prompt(prompt, model_name)
    
    try:
        stop_tokens = ["<|im_end|>", "<|end_of_sentence|>", "### Instruction:"]
        
        stream = llm(
            full_prompt,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            stop=stop_tokens,
            stream=True
        )
        
        for chunk in stream:
            token = chunk['choices'][0]['text']
            if token:
                # Use JSON encoding to safely handle newlines and special chars
                safe_token = json.dumps(token)
                flush_print(f"TOKEN:{safe_token}")
        
        flush_print("DONE")
        
    except Exception as e:
        flush_print(f"ERROR:Generation failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Code Engine - DeepSeek/Qwen Coder")
    parser.add_argument("--prompt", type=str, required=True, help="User prompt")
    parser.add_argument("--model", type=str, choices=["deepseek", "qwen"], 
                        default="deepseek", help="Model to use")
    
    args = parser.parse_args()
    
    # Load and generate
    llm = load_model(args.model)
    if llm is None:
        sys.exit(1)
    
    generate(llm, args.prompt, args.model)
    
    # Cleanup
    del llm
    gc.collect()
    
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ImportError:
        pass


if __name__ == "__main__":
    main()
