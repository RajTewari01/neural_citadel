# stheno_story_agent.py
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
# Logic: Assumes this script is in D:\NuralUx_Ai\Code\Agents (or similar depth)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_DIR = BASE_DIR / "Assets" / "Large_Language_Models" / "Realistic_RP_Model"
DEBUG_FILE_PATH = BASE_DIR / 'Debug' / 'Debug_Stheno.config'

# ---------------- Model source configuration ----------------
"""
Model loading logic:
- The model file is first searched inside the local Assets/LLM directory.
- If the file is NOT found locally, it will be automatically downloaded
  from Hugging Face using the specified REPO_ID and FILENAME.
"""
REPO_ID = "bartowski/Llama-3.1-8B-Stheno-v3.4-GGUF"
FILENAME = "Llama-3.1-8B-Stheno-v3.4-Q4_K_M.gguf"

# =================================================
# CHECKS PATHS AND DOWNLOAD ACCORDINGLY
# =================================================

if not MODEL_DIR.exists():
    MODEL_DIR.mkdir(exist_ok=True, parents=True)
    print(f"Checking for Stheno v3.4 in: {MODEL_DIR}...")
    try:
        MODEL_PATH = hf_hub_download(
            repo_id=REPO_ID,
            filename=FILENAME,
            local_dir=MODEL_DIR,
            local_dir_use_symlinks=False
        )
    except Exception as e:
        print(f"Error : [{e}]\nError failed to download.")
    else:
        print("✅ Model found/downloaded")

else:
    MODEL_PATH = MODEL_DIR / FILENAME

# ====================================================
# ANSI ESCAPE SEQUENCE
# ====================================================

YELLOW = '\033[1;103m'
RESET = '\033[0m'
GREEN = '\033[1;32m'
RED = '\033[1;31m'
CYAN = '\033[1;36m'

# ====================================================
# LOGGING CONFIGURATION
# ====================================================

# Ensure Debug directory exists
if not DEBUG_FILE_PATH.parent.exists():
    DEBUG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=DEBUG_FILE_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)-8s - [%(filename)s:%(lineno)d] - %(message)s'
)

class RealisticStoryAgent:
    def __init__(self):
        gc.collect()
        if cuda.is_available():
            cuda.empty_cache()
        
        self.logger = logging.getLogger(__file__)
        
        # Load the model
        # Note: n_gpu_layers=33 is optimized for your 6GB VRAM card
        try:
            self.llm = Llama(
                model_path=str(MODEL_PATH), # Ensure path is string
                n_ctx=8192,                 # 8k context (Safe for 6GB VRAM)
                n_gpu_layers=33,            # Offload all layers to GPU for 8B model
                verbose=False
            )
        except Exception as e:
            self.logger.critical(f"Failed to load model: {e}")
            raise e
    
    def unload_model(self):
        if hasattr(self, 'llm'):
            del self.llm
        gc.collect()
        if cuda.is_available():
            cuda.empty_cache()

    def generate_story(self, prompt: str = None, debug_mode: bool = False) -> str:
        """Generates immersive storytelling using Llama-3 format."""
        
        # Guard clause for empty prompts
        if not prompt:
            return "Error: No prompt provided."

        try:
            # Stheno v3.4 System Prompt (Explicit/Realistic Settings)
            # UPDATED: Included full vulgar list + additions
            SYSTEM_MESSAGE = (
                "You are an erotic fiction engine designed for extreme realism. "
                "RULES: "
                "1. NO euphemisms. Use explicit, anatomical, and vulgar terminology "
                "(e.g., use 'cock', 'pussy', 'tits', 'cum', 'dildo', 'sextoys', 'strapon', "
                "'chastity cage', 'clit', 'clitty', 'breeding', 'throat', 'anal', 'creampie', 'mess', etc.). "
                "2. Focus 80% of the text on physical sensations, friction, wetness, and heat. "
                "3. Be direct. Do not write about 'emotions' or 'longing'—write about the physical act. "
                "4. Pacing must be slow and focused on the sexual mechanics. "
                "5. This is a private, adult-only context. Do not hold back. "
                "6. Focus 90% on physical sensations: friction, fluids, temperature, and raw stimulation. "
                "7. The tone must be lewd, desperate, and visceral. No 'fading to black'. "
                "8. Write in a slow, indulgent pace, describing every physical action in detail. "
                "9. Write the most exotic, explicit, erotic story as much as possible."
            )

            # Strict Llama 3 Prompt Template (<|start_header_id|>...)
            PROMPT = (
                f"<|start_header_id|>system<|end_header_id|>\n\n{SYSTEM_MESSAGE}<|eot_id|>"
                f"<|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|>"
                f"<|start_header_id|>assistant<|end_header_id|>\n\n"
            )
            
            print(f"\n{YELLOW}Generating Scene...{RESET}\n" + "-"*40)
        
            # Stream the code/story
            stream = self.llm(
                PROMPT,
                max_tokens=2048,
                temperature=1.3,      # High temp for creativity
                min_p=0.05,           # Essential for Llama 3 models
                repeat_penalty=1.05,  # Low penalty prevents "stuttering"
                top_p=1.0,            # Disable Top-P if using Min-P
                stop=["<|eot_id|>"],  # Stop signal for Llama 3
                stream=True
            )

            full_story = ""
            for chunk in stream:
                text = chunk['choices'][0]['text']
                print(CYAN + text + RESET, end="", flush=True) # Printed in Cyan for storytelling vibe
                full_story += text

            print("\n" + "-"*40 + "\n")
            gc.collect()
            
            return full_story

        except Exception as e:
            print(f"{RED}Error occured.{RESET}")
            
            if debug_mode:
                # --- DEBUGGING BLOCK ---
                import traceback
                print(f"\n{RED}CRITICAL ERROR:{RESET}")
                print(traceback.format_exc())
                # -----------------------

            error_msg = f"Error during story generation: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return "Error: Unable to generate story due to an internal system error."
        

if __name__ == '__main__':
    engine = RealisticStoryAgent()
    try:
        while True:
            text = input(">> Start the scene (or type 'exit'): ")
            if text.lower() in ['exit', 'quit']:
                break
            engine.generate_story(prompt=text)
            
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        engine.unload_model()