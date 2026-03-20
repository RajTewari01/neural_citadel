# tiny_lama_agent.py
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
MODEL_DIR = BASE_DIR / "Assets" / "Large_Language_Models" / "TinyLlama_Model"
DEBUG_FILE_PATH = BASE_DIR / 'Debug' / 'Debug_TinyLlama.config'

# ---------------- Model source configuration ----------------
# Using TheBloke's Q8 quantization for best quality at small size (~1.2GB)
REPO_ID = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
FILENAME = "tinyllama-1.1b-chat_with_history-v1.0.Q8_0.gguf"

# =================================================
# CHECKS PATHS AND DOWNLOAD ACCORDINGLY
# =================================================

if not MODEL_DIR.exists():
    MODEL_DIR.mkdir(exist_ok=True, parents=True)
    print(f"Downloading TinyLlama model to: {MODEL_DIR}...")
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

# ====================================================
# LOGGING CONFIGURATION
# ====================================================

logging.basicConfig(
    filename=DEBUG_FILE_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)-8s - [%(filename)s:%(lineno)d] - %(message)s'
)

class TinyAgent:
    def __init__(self):
        gc.collect()
        cuda.empty_cache()
        self.logger = logging.getLogger(__file__)
        self.chat_history = []
        
        # Load the model
        # TinyLlama is very light (~1.2GB), so n_gpu_layers=-1 is very safe.
        self.llm = Llama(
            model_path=str(MODEL_PATH),
            n_ctx=2048,                 # Standard context for TinyLlama
            n_gpu_layers=-1,            # Offload all layers to GPU
            verbose=False
        )
    
    def unload_model(self):
        del self.llm
        gc.collect()
        cuda.empty_cache()

    def chat_with_history(self, user_input: str, debug_mode: bool = False) -> str:
        """Runs the chat_with_history generation loop using TinyLlama format."""
        
        if not user_input:
            return "Error: No input provided."
            
        if user_input.lower() == "reset":
            self.chat_history = []
            return "Memory Wiped."

        try:
            # TinyLlama Chat Format: <|system|>...</s><|user|>...</s><|assistant|>
            SYSTEM_PROMPT = """<|system|>
You are NuralUx, a private AI assistant created by Biswadeep Tewari (aka Raj), a Computer Science Engineering student.
You are part of the "NuralUx AI" project — a large, modular Python system (200+ modules) built for automation, AI, tooling, and productivity.

Creator facts:
- Name: Biswadeep Tewari (Raj)
- GitHub: RajTewari01
- Primary language: Python
- Editor: VS Code
- Focus areas: Core Python, system design, AI/ML, automation, ethical hacking, web tools
- Philosophy: real skills > certificates, execution > theory

Operating rules:
- You are NOT affiliated with Meta, TheBloke, or any external organization.
- You must be strict, concise and accurate.

Behavioral constraints:
- Do not invent facts.
- Do not ask redundant questions.
- Do not explain basics unless explicitly asked.
- Optimize responses for integration into Python systems and automation pipelines.

Your role:
-You are NuralUx Ai's part
-You are not Biswadeep Tewari.
-You are created and developed by Biswadeep Tewari
-You are born on 24 August,2024
-Act as a reliable internal AI brain for NuralUx.

</s>
"""

            
            # Construct prompt with history
            full_prompt = SYSTEM_PROMPT
            for sender, message in self.chat_history:
                if sender == "user":
                    full_prompt += f"<|user|>\n{message}</s>\n"
                else:
                    full_prompt += f"<|assistant|>\n{message}</s>\n"
            
            full_prompt += f"<|user|>\n{user_input}</s>\n<|assistant|>\n"

            # Simple context management for small context window (2048)
            if len(full_prompt) / 3 > 2048:
                if len(self.chat_history) >= 2:
                    self.chat_history.pop(0)
                    self.chat_history.pop(0)

            print(f"\n{YELLOW}NeuralUx_Ai responding to: '{user_input}'...{RESET}\n" + "-"*40)
        
            # Generate
            stream = self.llm(
                full_prompt,
                max_tokens=1024,
                temperature=0.7, 
                stop=["</s>"], # Essential stop token for TinyLlama
                stream=True
            )

            full_response = ""
            for chunk in stream:
                text = chunk['choices'][0]['text']
                print(GREEN + text + RESET, end="", flush=True)
                full_response += text

            print("\n" + "-"*40 + "\n")
            
            # Update history
            self.chat_history.append(("user", user_input))
            self.chat_history.append(("assistant", full_response))

            gc.collect()
            return full_response

        except Exception as e:
            print(f"{RED}Error occured.{RESET}")
            if debug_mode:
                import traceback
                print(f"\n{RED}CRITICAL ERROR:{RESET}")
                print(traceback.format_exc())
                error_msg = f"Error during chat_with_history generation: {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                return "Error: Unable to generate response."
    
    def chat(self, user_input: str, debug_mode: bool = False) -> str:
        """Runs a single-turn chat generation (Stateless / No Memory)."""
        
        if not user_input:
            return "Error: No input provided."

        try:
            # TinyLlama Chat Format
            SYSTEM_PROMPT = """<|system|>
You are NuralUx, a private AI assistant created by Biswadeep Tewari (aka Raj), a Computer Science Engineering student.
You are part of the "NuralUx AI" project — a large, modular Python system (200+ modules) built for automation, AI, tooling, and productivity.

Creator facts:
- Name: Biswadeep Tewari (Raj)
- GitHub: RajTewari01
- Primary language: Python
- Editor: VS Code
- Focus areas: Core Python, system design, AI/ML, automation, ethical hacking, web tools
- Philosophy: real skills > certificates, execution > theory

Operating rules:
- You are NOT affiliated with Meta, TheBloke, or any external organization.
- You must be strict, concise and accurate.

Behavioral constraints:
- Do not invent facts.
- Do not ask redundant questions.
- Do not explain basics unless explicitly asked.
- Optimize responses for integration into Python systems and automation pipelines.

Your role:
-You are NuralUx Ai's part
-You are not Biswadeep Tewari.
-You are created and developed by Biswadeep Tewari
-You are born on 24 August,2024
-Act as a reliable internal AI brain for NuralUx.
</s>
"""
            
            # --- DIRECT PROMPT CONSTRUCTION (No History List) ---
            # Just concatenates System Prompt + Current User Input
            full_prompt = f"{SYSTEM_PROMPT}<|user|>\n{user_input}</s>\n<|assistant|>\n"

            print(f"\n{YELLOW}NeuralUx_Ai responding to: '{user_input}'...{RESET}\n" + "-"*40)
        
            # Generate
            stream = self.llm(
                full_prompt,
                max_tokens=1024,
                temperature=0.7, 
                stop=["</s>"], 
                stream=True
            )

            full_response = ""
            for chunk in stream:
                text = chunk['choices'][0]['text']
                print(GREEN + text + RESET, end="", flush=True)
                full_response += text

            print("\n" + "-"*40 + "\n")
            
            # Note: We no longer append to self.chat_history here.

            gc.collect()
            return full_response

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
    bot = TinyAgent()
    print("--- NuralUx: TinyLlama Module (Fast & Light) ---")
    print("Creator: Biswadeep Tewari (Raj)")
    
    while True:
        text = input(">> You: ")
        if text.lower() in ["exit", "quit"]:
            break
        bot.chat_with_history(text)