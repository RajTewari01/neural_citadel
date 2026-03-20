"""
TinyLlama Server - Persistent LLM subprocess
=============================================

Runs as a persistent server that accepts prompts via stdin and returns responses.
Keeps the model loaded in memory to avoid repeated loading time.

Usage:
    python tinyllama_server.py
    # Then send prompts via stdin, one per line
    # Responses returned via stdout
"""
import sys
import gc
from pathlib import Path

MODEL_PATH = Path("d:/neural_citadel/assets/models/llm/llm/TinyLlama_Model/tinyllama-1.1b-chat-v1.0.Q8_0.gguf")

N_CTX = 2048
N_GPU_LAYERS = -1
MAX_TOKENS = 256
TEMPERATURE = 0.7


def main():
    from llama_cpp import Llama
    
    if not MODEL_PATH.exists():
        print("ERROR:Model not found", flush=True)
        sys.exit(1)
    
    # Signal that we're loading
    print("LOADING", flush=True)
    
    llm = Llama(
        model_path=str(MODEL_PATH),
        n_ctx=N_CTX,
        n_gpu_layers=N_GPU_LAYERS,
        verbose=False
    )
    
    # Signal ready
    print("READY", flush=True)
    
    # Build prompt template
    SYS_TAG = "<" + "|system|" + ">"
    END_TAG = "<" + "/s" + ">"
    USER_TAG = "<" + "|user|" + ">"
    ASST_TAG = "<" + "|assistant|" + ">"
    system_msg = "You are a helpful AI. Keep responses short for voice."
    
    # Process prompts from stdin
    for line in sys.stdin:
        prompt = line.strip()
        if not prompt:
            continue
        
        if prompt == "QUIT":
            break
        
        # Build full prompt
        full_prompt = SYS_TAG + "\n" + system_msg + END_TAG + "\n"
        full_prompt += USER_TAG + "\n" + prompt + END_TAG + "\n"
        full_prompt += ASST_TAG + "\n"
        
        # Generate
        output = llm(
            full_prompt,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            stop=[END_TAG],
            echo=False
        )
        
        response = output["choices"][0]["text"].strip()
        
        # Send response (single line, escape newlines)
        safe_response = response.replace("\n", " ")
        print(f"RESPONSE:{safe_response}", flush=True)
    
    # Cleanup
    del llm
    gc.collect()
    print("SHUTDOWN", flush=True)


if __name__ == "__main__":
    main()
