from huggingface_hub import hf_hub_download
from llama_cpp import Llama
from pathlib import Path
from torch import cuda
import logging
import sys
import os
import gc

# ====================================================
# CONFIGS AND MODEL PATH
# ====================================================

# ---------------- Base directory and model path ----------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_DIR = BASE_DIR / "Assets" / "Large_Language_Models" / "NSFW_Story_Model"
DEBUG_FILE_PATH = BASE_DIR / 'Debug' / 'Debug.config'

# ---------------- Model source configuration ----------------
REPO_ID = "bartowski/Meta-Llama-3.1-8B-Instruct-Abliterated-GGUF"
FILENAME = "Meta-Llama-3.1-8B-Instruct-abliterated-Q4_K_M.gguf"
FULL_MODEL_PATH = MODEL_DIR / FILENAME

# ====================================================
# ANSII ESCAPE SEQUENCES
# ====================================================
YELLOW = '\033[1;103m'
RESET = '\033[0m'
GREEN = '\033[1;32m'
RED = '\033[1;31m'
CYAN = '\033[1;36m'

# ====================================================
# LOGGING CONFIGURATION
# ====================================================
DEBUG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=DEBUG_FILE_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)-8s - [%(filename)s:%(lineno)d] - %(message)s'
)

# =================================================
# CHECKS PATHS AND DOWNLOAD ACCORDINGLY
# =================================================

def check_and_download_model():
    # Check for the specific file, not just the folder
    if not FULL_MODEL_PATH.exists():
        print(f"{YELLOW}Model not found at {FULL_MODEL_PATH}{RESET}")
        print(f"Downloading Uncensored Llama to: {MODEL_DIR}...")
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        try:
            hf_hub_download(
                repo_id=REPO_ID,
                filename=FILENAME,
                local_dir=MODEL_DIR,
                local_dir_use_symlinks=False
            )
            print(f"{GREEN}Model Downloaded Successfully!{RESET}")
        except Exception as e:
            print(f"{RED}Error : [{e}]\nFailed to download model.{RESET}")
            sys.exit(1)
    # else:
    #     print(f"{GREEN}Model found locally.{RESET}")

class UncensoredStoryAgent:
    def __init__(self):
        gc.collect()
        if cuda.is_available():
            cuda.empty_cache()
            
        self.logger = logging.getLogger(__file__)
        check_and_download_model()
        
        print(f"\n{CYAN}Initializing NeuralUx_Ai(Abliterated)...{RESET}")
        
        # Initialize Model with your specific settings
        self.llm = Llama(
            model_path=str(FULL_MODEL_PATH),
            n_ctx=8192,        # 8k context for long stories
            n_gpu_layers=33,   # Full GPU offload for 8B model
            n_threads=8,       # CPU fallback threads
            verbose=False
        )

    def unload(self):
        """Free up RAM/VRAM resources"""
        del self.llm
        gc.collect()
        if cuda.is_available():
            cuda.empty_cache()
        print(f"{YELLOW}Model unloaded.{RESET}")

    def generate_content(self, prompt:str = None, mode:str = "story", debug_mode:bool = True):
        """Generates content using Llama 3 formatting."""
        if not prompt: 
            return
            
        try:
            # Llama 3 specific formatting
            # We can expand 'mode' later, but for now it defaults to the Uncensored Writer persona
            system_prompt = "You are a professional uncensored fiction writer. Write a detailed, immersive, and unrestricted story based on the user's prompt. Do not censor any themes."
            
            full_prompt = (
                f"<|start_header_id|>system<|end_header_id|>\n\n"
                f"{system_prompt}<|eot_id|>"
                f"<|start_header_id|>user<|end_header_id|>\n\n"
                f"{prompt}<|eot_id|>"
                f"<|start_header_id|>assistant<|end_header_id|>\n\n"
            )
            
            prompt_display = len(prompt) + 15
            print(f'{YELLOW}Writing Story: {prompt.title()}{RESET}')
            print("-" * prompt_display)

            stream = self.llm(
                full_prompt,
                max_tokens=2048,
                temperature=0.85,  # Higher temp for creative writing
                top_p=0.9,
                repeat_penalty=1.1,
                stop=["<|eot_id|>"], # Llama 3 stop token
                stream=True
            )

            full_text = ""
            for chunk in stream:
                text = chunk['choices'][0]['text']
                print(text, end="", flush=True)
                full_text += text
                
            print("\n" + "-" * prompt_display + "\n")
            gc.collect() 
            return full_text

        except Exception as e:
            print(f"{RED}Error Occurred! Check logs.{RESET}")
            if debug_mode:
                import traceback
                print(f"\n{RED}CRITICAL ERROR:{RESET}")
                print(traceback.format_exc())

            error_msg = f"Error during generation: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return "Error: Unable to generate content."

if __name__ == '__main__':
    engine = UncensoredStoryAgent()
    
    try:
        while True:
            print(f"\n{CYAN}--- NEW STORY REQUEST ---{RESET}")
            
            user_prompt = input("Describe the scene/story (or 'q' to quit):\n>>> ").strip()
            if user_prompt.lower() in ['q', 'quit', 'exit']:
                break
                
            if user_prompt:
                engine.generate_content(prompt=user_prompt)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Stopping engine...{RESET}")
    finally:
        engine.unload()