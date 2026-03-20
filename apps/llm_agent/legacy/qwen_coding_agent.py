# qwen_coder_agent.py
from huggingface_hub import hf_hub_download
from llama_cpp import Llama
from torch import cuda
from pathlib import Path
import textwrap
import logging
import gc
import os

# ====================================================
# CONFIGS AND MODEL PATH
# ====================================================

# ---------------- Base directory and model path ----------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_DIR = BASE_DIR / "Assets" / "Large_Language_Models" / "Qwen_Coder_Model"
DEBUG_FILE_PATH = BASE_DIR / 'Debug' / 'Debug_Coder.config'

# ---------------- Model source configuration ----------------
"""
Model loading logic:
- The model file is first searched inside the local Assets/LLM directory.
- If the file is NOT found locally, it will be automatically downloaded
  from Hugging Face using the specified REPO_ID and FILENAME.
"""
REPO_ID = "bartowski/Qwen2.5-Coder-7B-Instruct-GGUF"
FILENAME = "Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf"

# =================================================
# CHECKS PATHS AND DOWNLOAD ACCORDINGLY
# =================================================

if not MODEL_DIR.exists():
    MODEL_DIR.mkdir(exist_ok=True, parents=True)
    print(f"Downloading Qwen Coder model to: {MODEL_DIR}...")
    try:
        MODEL_PATH = hf_hub_download(
            repo_id=REPO_ID,
            filename=FILENAME,
            local_dir=MODEL_DIR,
            local_dir_use_symlinks=False
        )
    except Exception as e: print(f"Error : [{e}]\nError failed to download.")
    else: print("Model Downloaded")

else: MODEL_PATH = MODEL_DIR / FILENAME

# ====================================================
# ANSII ESCAPE SEQUENCE
# ====================================================

YELLOW = '\033[1;103m'
RESET = '\033[0m'
GREEN = '\033[1;32m'
RED = '\033[1;31m'
CYAN = '\033[1;36m'

# ====================================================
# LOGGING CONFIGURATION
# ====================================================

logging.basicConfig(
    filename=DEBUG_FILE_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)-8s - [%(filename)s:%(lineno)d] - %(message)s'
)

class CodingAgent:
    def __init__(self):
        gc.collect()
        cuda.empty_cache()
        self.logger = logging.getLogger(__file__)
        # Load the model
        # Note: Qwen 2.5 Coder is very efficient.
        self.llm = Llama(
            model_path=str(MODEL_PATH),
            n_ctx=8192,                 # Qwen supports up to 32k, but 8192 is safe for 6GB VRAM
            n_gpu_layers=-1,            # Offload all layers to GPU
            verbose=False
        )
    
    def unload_model(self):
        del self.llm
        gc.collect()
        cuda.empty_cache()

    def generate_coding(self, prompt: str = None, debug_mode: bool = False) -> str:
        """Generates code using Qwen's specific ChatML format."""
        
        if not prompt:
            return "Error: No prompt provided."

        try:
            # Qwen uses ChatML format (<|im_start|>system...)
            # We strictly enforce "no filler" in the system prompt.
            PROMPT = f"""<|im_start|>system
You are an expert Python developer.
1. Write efficient, production-ready code.
2. DO NOT output conversational filler (e.g., "Here is the code").
3. DO NOT use Markdown backticks (```).
4. If you need to explain logic, use comments (#).<|im_end|>
<|im_start|>user
{prompt}<|im_end|>
<|im_start|>assistant
"""
            print(f"\n{YELLOW}Generating Code for: '{prompt.title()}'...{RESET}\n" + "-"*40)
        
            stream = self.llm(
                PROMPT,
                max_tokens=4096,  
                temperature=0.1,  # Low temp for precise coding
                stop=["<|im_end|>", "###"],
                stream=True
            )

            full_code = ""
            for chunk in stream:
                text = chunk['choices'][0]['text']
                print(GREEN + text + RESET, end="", flush=True)
                full_code += text

            print("\n" + "-"*40 + "\n")
            gc.collect()
            
            return full_code

        except Exception as e:
            print(f"{RED}Error occured.{RESET}")
            if debug_mode:
                import traceback
                print(f"\n{RED}CRITICAL ERROR:{RESET}")
                print(traceback.format_exc())
                error_msg = f"Error during code generation: {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                return "Error: Unable to generate code."

if __name__ == '__main__':
    engine = CodingAgent()
    text = input("Request Code [e.g., 'Write a fast binary search in Python']:\n>>> ")
    engine.generate_coding(prompt=text)