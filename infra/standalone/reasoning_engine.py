"""
Reasoning Engine - DeepSeek R1
==============================

Standalone CLI for reasoning tasks using DeepSeek R1 model.
Runs in coreagentvenv via subprocess from PyQt GUI.

Usage:
    python reasoning_engine.py --prompt "What is 2+2?" [--history '[]']
    
Output Protocol:
    LOADED          - Model loaded successfully
    THINK_START     - Entering <think> block
    TOKEN:<text>    - Each token as it streams
    THINK_END       - Exiting </think> block
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

# Model configuration - optimized for 4GB VRAM
MODEL_PATH = Path(__file__).resolve().parents[2] / "assets" / "models" / "llm" / "llm" / "Deepseek_R1_Model" / "DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf"

# VRAM-optimized settings
N_CTX = 4096          # Context size (smaller = less VRAM)
N_BATCH = 256         # Batch size
N_GPU_LAYERS = -1     # Full GPU offload (7B Q4 fits in 4GB)
MAX_TOKENS = 1024     # Max output tokens (reduced to prevent rambling)
TEMPERATURE = 0.3     # Lower temperature for focused, factual responses


def flush_print(msg: str):
    """Print with immediate flush for real-time streaming."""
    print(msg, flush=True)


def load_model():
    """Load the DeepSeek R1 model."""
    try:
        from llama_cpp import Llama
        
        if not MODEL_PATH.exists():
            flush_print(f"ERROR:Model not found at {MODEL_PATH}")
            return None
        
        llm = Llama(
            model_path=str(MODEL_PATH),
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


def build_prompt(user_prompt: str, history: list) -> str:
    """Build the full prompt with history context."""
    
    messages = []
    
    # System message - strict, focused reasoning
    system_msg = """You are a precise reasoning assistant. Be CONCISE.

In <think>: Briefly identify what's being asked, then solve it step by step. Stay focused - no tangents.

After </think>: Give a clear, direct **Answer** with the key facts.

CRITICAL:
- Keep thinking SHORT (under 200 words)
- No rambling or "let me consider..." filler
- For simple questions, think briefly then answer
- State facts confidently, don't hedge unnecessarily"""
    
    messages.append(f"<|im_start|>system\n{system_msg}<|im_end|>")
    
    # Add history (last 3 Q&A pairs = 6 messages max)
    for msg in history[-6:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        messages.append(f"<|im_start|>{role}\n{content}<|im_end|>")
    
    # Current user message
    messages.append(f"<|im_start|>user\n{user_prompt}<|im_end|>")
    messages.append("<|im_start|>assistant\n<think>")
    
    return "\n".join(messages)


def generate(llm, prompt: str, history: list):
    """Generate response with streaming output."""
    
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
                flush_print(f"TOKEN:{token}")
                flush_print("THINK_END")
                in_think_block = False
                continue
            
            if token:
                flush_print(f"TOKEN:{token}")
        
        flush_print("DONE")
        
    except Exception as e:
        flush_print(f"ERROR:Generation failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="DeepSeek R1 Reasoning Engine")
    parser.add_argument("--prompt", type=str, required=True, help="User prompt")
    parser.add_argument("--history", type=str, default="[]", help="JSON history array")
    
    args = parser.parse_args()
    
    # Parse history
    try:
        history = json.loads(args.history)
    except json.JSONDecodeError:
        history = []
    
    # Load and generate
    llm = load_model()
    if llm is None:
        sys.exit(1)
    
    generate(llm, args.prompt, history)
    
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
