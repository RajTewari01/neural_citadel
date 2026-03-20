from huggingface_hub import hf_hub_download
from llama_cpp import Llama
from torch import cuda
from pathlib import Path
import logging
import gc
import os

# ====================================================
# CONFIGS AND MODEL PATH
# ====================================================

# ---------------- Base directory and model path ----------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_DIR = BASE_DIR / "Assets" / "Large_Language_Models" / "Qwen_Small_LLM"
DEBUG_FILE_PATH = BASE_DIR / 'Debug' / 'Debug_NuralUx_Light.config'

# ---------------- Model source configuration ----------------
REPO_ID = "Qwen/Qwen2.5-0.5B-Instruct-GGUF"
FILENAME = "qwen2.5-0.5b-instruct-q8_0.gguf"

# =================================================
# CHECKS PATHS AND DOWNLOAD ACCORDINGLY
# =================================================

if not MODEL_DIR.exists():
    MODEL_DIR.mkdir(exist_ok=True, parents=True)
    print(f"Downloading NuralUx Light model to: {MODEL_DIR}...")
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
CYAN = '\033[1;36m'
RED = '\033[1;31m'

# ====================================================
# LOGGING CONFIGURATION
# ====================================================

logging.basicConfig(
    filename=DEBUG_FILE_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)-8s - [%(filename)s:%(lineno)d] - %(message)s'
)

class NuralUxAgent:
    def __init__(self):
        gc.collect()
        cuda.empty_cache()
        self.logger = logging.getLogger(__file__)
        self.chat_history = []
        
        # Load the model
        self.llm = Llama(
            model_path=str(MODEL_PATH),
            n_ctx=8192,
            n_gpu_layers=-1,
            verbose=False
        )
    
    def unload_model(self):
        del self.llm
        gc.collect()
        cuda.empty_cache()

    def clean_output(self, text):
        """ enforces the persona by removing references to the base model creator """
        cleaned = text.replace("Alibaba Cloud", "Biswadeep Tewari")
        cleaned = cleaned.replace("Alibaba", "Raj")
        return cleaned

    def chat(self, user_input: str, debug_mode: bool = False) -> str:
        """Runs the chat generation loop."""
        
        if not user_input:
            return "Error: No input provided."
            
        if user_input.lower() == "reset":
            self.chat_history = []
            return "Memory Wiped."

        try:
            SYSTEM_PROMPT = """You are NuralUx, an AI assistant created by Biswadeep Tewari (Raj).
You are NOT from Alibaba. You are helpful, concise, and friendly."""

            # Build Prompt with history
            full_prompt = f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n"
            for sender, message in self.chat_history:
                full_prompt += f"<|im_start|>{sender}\n{message}<|im_end|>\n"
            full_prompt += f"<|im_start|>user\n{user_input}<|im_end|>\n<|im_start|>assistant\n"

            # Context Management (Crude truncation if too long)
            # A rough estimate: chars / 3 ~ tokens. 
            if len(full_prompt) / 3 > 8192:
                # Remove oldest interaction (user + assistant)
                if len(self.chat_history) >= 2:
                    self.chat_history.pop(0)
                    self.chat_history.pop(0)

            print(f"\n{CYAN}NuralUx (Light) Thinking...{RESET}")
        
            # Generate
            output = self.llm(
                full_prompt,
                max_tokens=1024,
                temperature=0.7,
                repeat_penalty=1.2,
                stop=["<|im_end|>"]
            )

            raw_response = output['choices'][0]['text']
            final_response = self.clean_output(raw_response)

            # Update history
            self.chat_history.append(("user", user_input))
            self.chat_history.append(("assistant", final_response))
            
            # Print response clearly
            print(f"{YELLOW}NuralUx: {final_response}{RESET}")
            print("\n" + "-"*40 + "\n")
            
            gc.collect()
            return final_response

        except Exception as e:
            print(f"{RED}Error occured.{RESET}")
            if debug_mode:
                import traceback
                print(f"\n{RED}CRITICAL ERROR:{RESET}")
                print(traceback.format_exc())
                error_msg = f"Error during chat generation: {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                return "Error: Unable to generate response."

if __name__ == '__main__':
    bot = NuralUxAgent()
    print("--- NuralUx AI (OFFLINE MODE) ---")
    print("Creator: Biswadeep Tewari (Raj)")
    
    while True:
        text = input(">> You: ")
        if text.lower() in ["exit", "quit"]:
            break
        bot.chat(text)