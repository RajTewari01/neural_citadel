# deepseek_coding_agent.py
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
MODEL_DIR = BASE_DIR / "Assets" / "Large_Language_Models" / "Deepseek_Model"
DEBUG_FILE_PATH = BASE_DIR / 'Debug' / 'Debug.config'
# ---------------- Model source configuration ----------------
"""
Model loading logic:
- The model file is first searched inside the local Assets/LLM directory.
- If the file is NOT found locally, it will be automatically downloaded
  from Hugging Face using the specified REPO_ID and FILENAME.
- If the repository name or model filename changes upstream,
  this configuration must be updated accordingly.
"""
REPO_ID = "TheBloke/deepseek-coder-6.7B-instruct-GGUF"
FILENAME = "deepseek-coder-6.7b-instruct.Q4_K_M.gguf"

# =================================================
# CHECKS PATHS AND DOWNLOAD ACCORDINGLY
# =================================================

if not MODEL_DIR.exists():

    MODEL_DIR.mkdir(exist_ok=True,parents=True)
    print(f"Downloading model to: {MODEL_DIR}...")
    try :
        MODEL_PATH = hf_hub_download(
            repo_id=REPO_ID,
            filename=FILENAME,
            local_dir=MODEL_DIR,
            local_dir_use_symlinks=False
        )
    except Exception as e : print(f"Error : [{e}]\nError failed to download.")
    else : print("Model Downloaded")

else : MODEL_PATH = MODEL_DIR / 'deepseek-coder-6.7b-instruct.Q4_K_M.gguf'

# ====================================================
# ANSII ESCAPE SEQUENCE
# ====================================================

YELLOW = '\033[1;103m'
RESET = '\033[0m'
GREEN = '\033[1;32m'
RED = '\033[1;31m'

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
            # Note: For 6GB VRAM, n_gpu_layers=-1 will try to offload everything. 
            # If you get OOM errors, reduce n_gpu_layers (e.g., to 20 or 30).
        self.llm = Llama(
                model_path=str(MODEL_PATH), # Ensure path is string
                n_ctx=4096,                 # DeepSeek handles larger context well
                n_gpu_layers=-1,            # Offload all layers to GPU if possible
                verbose=False
            )
    
    def unload_model(self):
        del self.llm
        gc.collect()
        cuda.empty_cache()

    def generate_coding(self, prompt: str = None, debug_mode: bool = False) -> str:
        """Generates code with settings optimized for logic."""
        
        # Guard clause for empty prompts
        if not prompt:
            return "Error: No prompt provided."

        try:
            # Updated Prompt Template (DeepSeek/Alpaca format)
            PROMPT = f"""
                    ### Instruction:
                    You are an expert software engineer proficient in all modern languages (Python, JavaScript, C++, HTML, etc.).
                    Task: {prompt}
                    
                    Guidelines:
                    1. Write  efficient, best, production-ready code.
                    2. If the language is not specified, infer it from the task.
                    3. DO NOT output conversational filler (e.g., "Here is your code").
                    4. If you need to explain logic, use ONLY multi-line comments format (''' ... ''') or standard comments (# //).
                    5. **DO NOT use Markdown backticks (```) or language labels (python, c++, etc).
                    ### Response:
                    """
            PROMPT = textwrap.dedent(PROMPT).strip()
            print(f"\n{YELLOW}Generating Code for: '{prompt.title()}'...{RESET}\n" + "-"*40)
        
            # Stream the code
            stream = self.llm(
                PROMPT,           # Pass the formatted PROMPT, not the raw prompt
                max_tokens=2048,  # Plenty of space for long scripts
                temperature=0.2,  # Low temp = High precision (Less hallucination)
                stop=["###"],     # Stop signal for this specific model
                stream=True
            )

            full_code = ""
            for chunk in stream:
                text = chunk['choices'][0]['text']
                print(GREEN + text + RESET, end="", flush=True) # Printed in Green for visibility
                full_code += text

            print("\n" + "-"*40 + "\n")
            gc.collect()
            
            return full_code

        except Exception as e:
            print(f"{RED}Error occured.{RESET}")
            
            if debug_mode:
                # --- DEBUGGING BLOCK ---
                import traceback
                print(f"\n{RED}CRITICAL ERROR:{RESET}")
                print(traceback.format_exc()) # This prints the full error trace
                # -----------------------

                error_msg = f"Error during code generation: {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                return "Error: Unable to generate code due to an internal system error."
        

if __name__ == '__main__':
    engine = CodingAgent()
    text = input("Write the code [Please mention the writing to get proper results].\n>>>")
    print(engine.generate_coding(prompt=text),end='',flush=True)

