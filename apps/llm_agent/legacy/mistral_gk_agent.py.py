# mistral_gk_ageny.py
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
MODEL_DIR = BASE_DIR / "Assets" / "Large_Language_Models" / "Mistral_7b_model"
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
REPO_ID = "TheBloke/Mistral-7B-Instruct-v0.2-GGUF"
FILENAME = "mistral-7b-instruct-v0.2.Q4_K_M.gguf"

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

else : MODEL_PATH = MODEL_DIR / "mistral-7b-instruct-v0.2.Q4_K_M.gguf"

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

class  GeneralKnowledgeAgent:
    def __init__(self):
        gc.collect()
        cuda.empty_cache()
        self.logger = logging.getLogger(__file__)
        print(f"\nInitializing NeuralUx_Ai...")
        self.llm = Llama(
                model_path=str(MODEL_PATH),
                n_ctx=2048, 
                n_gpu_layers=-1, 
                verbose=False
            )
    def unload(self):
        gc.collect()
        del self.llm
        if cuda.is_available():cuda.empty_cache()

    def generate_content(self, prompt:str = None, mode:str = "poem", debug_mode:bool = True):
        """Generates content based on the selected mode with optimized settings."""
        if not prompt: return
        try:
            # 1. Define the "Brain" and Settings for each mode
            # Format: "Mode": (Prompt, Temperature)
            # 1. Define the "Brain" and Settings for each mode
            # Format: "Mode": (Prompt, Temperature)
            mode_settings = {
                # --- CREATIVE WRITING ---
                "poem": (
                    f"[INST] You are a visionary poet known for weaving complex emotions into vivid imagery. "
                    f"Write a masterpiece poem about: {prompt}. "
                    f"Use original metaphors, sensory details, and rhythmic elegance. "
                    f"Do not just describe the subject; capture its hidden essence and evoke deep feeling in the reader. [/INST]", 
                    0.9 
                ),
                "story": (
                    f"[INST] You are a master storyteller with a talent for gripping narratives. "
                    f"Write a compelling short story based on: {prompt}. "
                    f"Start with a strong hook that grabs attention immediately. "
                    f"Focus on 'show, don't tell' by using visceral sensory details and deep character psychology. "
                    f"Build tension and drive the plot toward a memorable or twisting conclusion. [/INST]", 
                    1.0 
                ),
                
                # --- NEW MODES ---
                
                # Mode 3: PHILOSOPHER - Abstract, deep, and thought-provoking
                "philosopher": (
                    f"[INST] You are a wise and contemplative philosopher. "
                    f"Reflect deeply on the concept of: {prompt}. "
                    f"Explore the ethical, metaphysical, and existential implications. "
                    f"Use analogies, question the nature of reality, and offer a perspective that challenges the status quo. "
                    f"Your tone should be profound, calm, and intellectual. [/INST]",
                    0.8 # Balanced for creativity but focused thought
                ),

                # Mode 4: THERAPIST - Empathetic, listening, and comforting
                "therapist": (
                    f"[INST] You are a compassionate and empathetic counselor. "
                    f"The user is feeling: {prompt}. "
                    f"Respond with validation, kindness, and gentle guidance. "
                    f"Do not judge. Focus on active listening techniques and offering comforting perspectives. "
                    f"Make the user feel heard and safe. (Note: You are a supportive AI, not a doctor). [/INST]",
                    0.6 # Lower temp for consistent, stable, and safe responses
                ),

                # Mode 5: TEACHER - Clear, structured, and educational
                "teacher": (
                    f"[INST] You are an expert professor with a gift for explaining complex topics simply. "
                    f"Teach me about: {prompt}. "
                    f"Break the concept down into clear, logical steps or bullet points. "
                    f"Use real-world examples to make it easy to understand. "
                    f"End with a quick summary or a fun fact to help it stick. [/INST]",
                    0.3 # Low temp to ensure factual accuracy and structure
                ),

                # Mode 6: REDDIT STORY - Informal, dramatic, and "viral" style
                "reddit": (
                    f"[INST] You are a Reddit user posting on a popular subreddit (like r/TIFU or r/confession). "
                    f"Write a viral post about: {prompt}. "
                    f"Use a first-person perspective ('I'), informal internet slang, and a dramatic or humorous tone. "
                    f"Include a catchy title at the start. "
                    f"Make it sound personal, raw, and engaging, like a real human confession. [/INST]",
                    1.1 # Very high temp for maximum chaos and creativity
                ),
                "anything":(
                    f'[INST]You are the master of everything,the best in anything ever present in the world.'
                    f'{prompt}, make the best/excellent for any humans ever lived.[/INST]',
                    0.7
                        )
            }
            full_prompt, temp = mode_settings.get(mode, mode_settings['poem'])            
            prompt_count = len(prompt) + len('Generating...')
            print(f'{YELLOW}Generating : {prompt.title()}{RESET}')
            
            stream = self.llm(
            full_prompt,
            max_tokens=1024 , # Give code more space
            temperature=temp, # <--- DYNAMIC TEMPERATURE
            stop=["</s>"],
            stream=True
            )

            full_text = ""
            for chunk in stream:
                text = chunk['choices'][0]['text']
                print(text, end="", flush=True)
                full_text += text
            gc.collect()
            print("\n" + "-"*prompt_count + "\n")
            return full_text
        except Exception as e:
            if debug_mode:
                import traceback
                print(f"\n{RED}CRITICAL ERROR:{RESET}")
                print(traceback.format_exc()) # This prints the full error trace
                # -----------------------

                error_msg = f"Error during code generation: {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                return "Error: Unable to generate code due to an internal system error."
            else : print(f"{RED}Error Occured!\nPlease use debug_mode = True or the logs to find out the problem in detailed version.{RESET}")
            
if __name__ == '__main__':
    engine = GeneralKnowledgeAgent()
    while True:
        model_typr = input("Enter Model type:\n>>>" )
        user_prompt = input("Enter Prompt:\n>>>" )
        engine.generate_content(mode=model_typr,prompt=user_prompt)
    # ----------------------------------Testing------------------------------------
    # # Dictionary mapping Modes to specific Test Prompts
    # test_scenarios = {
    #     "poem": "The sound of rain hitting a tin roof at midnight",
    #     "story": "A detective discovers his own name on the suspect list",
    #     "philosopher": "If a machine thinks, does it have a soul?",
    #     "therapist": "I feel like I'm falling behind my peers and running out of time",
    #     "teacher": "Quantum Entanglement",
    #     "reddit": "I accidentally sent a meme to my boss instead of the quarterly report"
    # }

    # print(f"\n{YELLOW}=== STARTING AUTOMATED SYSTEM TEST ==={RESET}")
    # print(f"Testing {len(test_scenarios)} different AI personalities...\n")

    # # Loop through every mode and run a test generation
    # for mode, prompt in test_scenarios.items():
    #     print(f"{GREEN}>>> TESTING MODE: {mode.upper()}{RESET}")
    #     print(f"Prompt: {prompt}")
        
    #     # Run the generation
    #     engine.generate_content(prompt=prompt, mode=mode, debug_mode=True)
        
    #     print(f"{YELLOW}--------------------------------------------------{RESET}\n")

    # print(f"{GREEN}=== TEST SEQUENCE COMPLETE ==={RESET}")
            
                
