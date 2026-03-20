"""
TinyLlama CLI - Subprocess wrapper for TinyLlama
Runs in coreagentvenv. Called via subprocess from voice pipeline.
Usage: python tinyllama_cli.py --prompt "Hello"
"""
import argparse
import sys
from pathlib import Path

MODEL_PATH = Path("d:/neural_citadel/assets/models/llm/llm/TinyLlama_Model/tinyllama-1.1b-chat-v1.0.Q8_0.gguf")

N_CTX = 2048
N_GPU_LAYERS = -1
MAX_TOKENS = 256
TEMPERATURE = 0.7


def generate(prompt: str) -> str:
    from llama_cpp import Llama
    
    if not MODEL_PATH.exists():
        return "Model not found"
    
    llm = Llama(
        model_path=str(MODEL_PATH),
        n_ctx=N_CTX,
        n_gpu_layers=N_GPU_LAYERS,
        verbose=False
    )
    
    # TinyLlama chat format - build prompt with string concatenation
    system_msg = "You are a helpful AI. Keep responses short for voice."
    SYS_TAG = "<" + "|system|" + ">"
    END_TAG = "<" + "/s" + ">"
    USER_TAG = "<" + "|user|" + ">"
    ASST_TAG = "<" + "|assistant|" + ">"
    
    full_prompt = SYS_TAG + "\n" + system_msg + END_TAG + "\n"
    full_prompt += USER_TAG + "\n" + prompt + END_TAG + "\n"
    full_prompt += ASST_TAG + "\n"
    
    output = llm(
        full_prompt,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        stop=[END_TAG],
        echo=False
    )
    
    response = output["choices"][0]["text"].strip()
    
    # Cleanup
    del llm
    import gc
    gc.collect()
    
    return response


def main():
    parser = argparse.ArgumentParser(description="TinyLlama CLI")
    parser.add_argument("--prompt", type=str, required=True, help="User prompt")
    args = parser.parse_args()
    
    response = generate(args.prompt)
    print(response)


if __name__ == "__main__":
    main()

