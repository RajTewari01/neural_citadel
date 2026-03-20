# deepseek_reasoning_agent.py
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
MODEL_DIR = BASE_DIR / "Assets" / "Large_Language_Models" / "Deepseek_R1_Model"
DEBUG_FILE_PATH = BASE_DIR / 'Debug' / 'Debug_Reasoner.config'

# ---------------- Model source configuration ----------------
"""
Model loading logic:
- The model file is first searched inside the local Assets/LLM directory.
- If the file is NOT found locally, it will be automatically downloaded.
"""
REPO_ID = "bartowski/DeepSeek-R1-Distill-Qwen-7B-GGUF"
FILENAME = "DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf"

# =================================================
# CHECKS PATHS AND DOWNLOAD ACCORDINGLY
# =================================================

if not MODEL_DIR.exists():
    MODEL_DIR.mkdir(exist_ok=True, parents=True)
    print(f"Downloading DeepSeek Reasoner to: {MODEL_DIR}...")
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
BLUE = '\033[1;34m' # Changed to Blue for "Thinking"
RED = '\033[1;31m'

# ====================================================
# LOGGING CONFIGURATION
# ====================================================

logging.basicConfig(
    filename=DEBUG_FILE_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)-8s - [%(filename)s:%(lineno)d] - %(message)s'
)

class ReasoningAgent:
    def __init__(self):
        gc.collect()
        cuda.empty_cache()
        self.logger = logging.getLogger(__file__)
        self.llm = Llama(
            model_path=str(MODEL_PATH),
            n_ctx=8192,                 # Reasoning chains can get long
            n_gpu_layers=-1,
            verbose=False
        )
    
    def unload_model(self):
        del self.llm
        gc.collect()
        cuda.empty_cache()

    def generate_reasoning(self, prompt: str = None, debug_mode: bool = False) -> str:
        """Generates a response with explicit reasoning steps."""
        
        if not prompt:
            return "Error: No prompt provided."

        try:
            # DeepSeek R1 prompt engineering
            # We explicitly ask it to think before answering
            PROMPT = f"""<|im_start|>system
You are a logic specialist. 
1. Before answering, you must analyze the problem step-by-step.
2. Use a <think> block for your internal monologue.
3. Provide the final conclusion clearly after the thinking block.<|im_end|>
<|im_start|>user
{prompt}<|im_end|>
<|im_start|>assistant
"""
            print(f"\n{YELLOW}NeuralUx_Ai Thinking on: '{prompt.title()}'...{RESET}\n" + "-"*40)
        
            stream = self.llm(
                PROMPT,
                max_tokens=4096,
                temperature=0.6, # Slightly higher temp helps the "thought chain" flow
                stop=["<|im_end|>"],
                stream=True
            )

            full_response = ""
            for chunk in stream:
                text = chunk['choices'][0]['text']
                # Highlight "Thinking" process vs "Answer" if possible, 
                # but for now we just print standard stream.
                print(BLUE + text + RESET, end="", flush=True)
                full_response += text

            print("\n" + "-"*40 + "\n")
            gc.collect()
            
            return full_response

        except Exception as e:
            print(f"{RED}Error occured.{RESET}")
            if debug_mode:
                import traceback
                print(f"\n{RED}CRITICAL ERROR:{RESET}")
                print(traceback.format_exc())
                error_msg = f"Error during reasoning: {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                return "Error: Unable to generate reasoning."

if __name__ == '__main__':
    engine = ReasoningAgent()
    text = input("State your logic problem [e.g., 'Plan a 3-tier architecture for my app']:\n>>> ")
    engine.generate_reasoning(prompt=text)