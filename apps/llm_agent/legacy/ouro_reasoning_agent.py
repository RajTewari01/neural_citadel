from transformers import AutoTokenizer, AutoModelForCausalLM, TextStreamer, AutoConfig
from transformers.dynamic_module_utils import get_class_from_dynamic_module
from pathlib import Path
from torch import cuda
import logging
import torch
import sys
import gc

# ====================================================
# CONFIGS
# ====================================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_DIR = BASE_DIR / "Assets" / "Large_Language_Models" / "Ouro_Model"
DEBUG_FILE_PATH = BASE_DIR / 'Debug' / 'Debug.config'

# Colors
YELLOW, RESET, GREEN, RED, CYAN = '\033[1;103m', '\033[0m', '\033[1;32m', '\033[1;31m', '\033[1;36m'

logging.basicConfig(filename=DEBUG_FILE_PATH, level=logging.INFO)

DEFAULT_SYSTEM_PROMPT = """You are NuralUx, a focused reasoning AI. Be concise.
1. State the core approach
2. Provide clean, working code
3. Explain briefly"""

# ====================================================
# RUNTIME HOT-PATCHER (In-Memory Fix)
# ====================================================

def apply_runtime_patch(model_class):
    """
    Dynamically injects methods into the loaded class in memory.
    This bypasses read-only file issues and regex matching failures.
    """
    print(f"{YELLOW}💉 Applying Runtime Hot-Patch to Memory...{RESET}")
    
    # We need to find the UniversalTransformerCache class inside the module that contains the model
    module = sys.modules[model_class.__module__]
    
    if hasattr(module, "UniversalTransformerCache"):
        CacheClass = getattr(module, "UniversalTransformerCache")
        
        # --- 1. Define the missing methods ---
        def get_mask_sizes(self, cache_position=None, layer_idx=0):
            # Patch for transformers > 4.40
            return self.get_seq_length(layer_idx), 0

        def get_usable_length(self, new_seq_length, layer_idx=0):
            # Patch for transformers > 4.40
            return self.get_seq_length(layer_idx)
            
        # --- 2. Inject them into the class ---
        if not hasattr(CacheClass, "get_mask_sizes"):
            setattr(CacheClass, "get_mask_sizes", get_mask_sizes)
        
        if not hasattr(CacheClass, "get_usable_length"):
            setattr(CacheClass, "get_usable_length", get_usable_length)
        
        # --- 3. Fix the __init__ (The setter error) ---
        def patched_init(self, max_cache_size=None):
            # Bypass the read-only check by using object.__setattr__
            object.__setattr__(self, 'key_cache', [])
            object.__setattr__(self, 'value_cache', [])
            object.__setattr__(self, 'layers', [])
            object.__setattr__(self, '_seen_tokens', 0)
            object.__setattr__(self, 'max_cache_size', max_cache_size)

        CacheClass.__init__ = patched_init
        
        print(f"{GREEN}✅ Runtime Patch Applied to {CacheClass.__name__}{RESET}")
    else:
        print(f"{RED}❌ Could not find UniversalTransformerCache in loaded module!{RESET}")

# ====================================================
# REASONING AGENT
# ====================================================

class ReasoningAgent:
    def __init__(self):
        gc.collect(); cuda.empty_cache()
        
        print(f"{CYAN}🔄 Initializing...{RESET}")
        self.tokenizer = AutoTokenizer.from_pretrained(
            str(MODEL_DIR), 
            local_files_only=True, 
            trust_remote_code=True
        )
        
        print(f"{CYAN}🚀 Loading Ouro Model...{RESET}")
        
        try:
            # Attempt 1: Load normally
            self.model = AutoModelForCausalLM.from_pretrained(
                str(MODEL_DIR),
                trust_remote_code=True,
                local_files_only=True,
                torch_dtype=torch.float16,
                device_map="auto",
                attn_implementation="eager"
            )
            
            # Patch immediately
            apply_runtime_patch(self.model.__class__)
            print(f"{GREEN}✅ Model Loaded & Patched.{RESET}")
            
        except AttributeError as e:
            print(f"{YELLOW}⚠️ Load failed ({e}). Attempting Pre-Load Patching...{RESET}")
            
            try:
                # Force load the module code without instantiating the model
                config = AutoConfig.from_pretrained(str(MODEL_DIR), trust_remote_code=True)
                class_ref = get_class_from_dynamic_module(config.auto_map["AutoModelForCausalLM"], str(MODEL_DIR))
                
                # Patch class definition in memory
                apply_runtime_patch(class_ref)
                
                print(f"{CYAN}🔄 Retrying Load...{RESET}")
                self.model = AutoModelForCausalLM.from_pretrained(
                    str(MODEL_DIR),
                    trust_remote_code=True,
                    local_files_only=True,
                    torch_dtype=torch.float16,
                    device_map="auto",
                    attn_implementation="eager"
                )
                print(f"{GREEN}✅ Model Loaded Successfully after Pre-Patching.{RESET}")
            except Exception as fatal_e:
                print(f"{RED}❌ Fatal Error: {fatal_e}{RESET}")
                sys.exit(1)

    def unload_model(self):
        """Cleanup model from memory"""
        print(f"{YELLOW}🧹 Unloading Model...{RESET}")
        if hasattr(self, 'model'):
            del self.model
        if hasattr(self, 'tokenizer'):
            del self.tokenizer
        
        # Force garbage collection
        gc.collect()
        # clear CUDA cache
        cuda.empty_cache()
        print(f"{GREEN}✅ Memory Cleared.{RESET}")

    def generate_reasoning(self, prompt: str):
        if not prompt: return
        try:
            formatted_prompt = (
                f"<|im_start|>system\n{DEFAULT_SYSTEM_PROMPT}<|im_end|>\n"
                f"<|im_start|>user\n{prompt}<|im_end|>\n"
                f"<|im_start|>assistant\n<|im_thought|>"
            )
            inputs = self.tokenizer(formatted_prompt, return_tensors="pt").to("cuda")
            
            print(f"\n{YELLOW}🧠 NuralUx Thinking...{RESET}\n" + "-"*40)
            
            self.model.generate(
                **inputs,
                streamer=TextStreamer(self.tokenizer, skip_prompt=True, skip_special_tokens=True),
                max_new_tokens=512,    
                do_sample=True,
                temperature=0.4,
                pad_token_id=self.tokenizer.eos_token_id,
                use_cache=False # CRITICAL FIX for tensor size mismatch
            )
            print("\n" + "-"*40 + "\n")

        except Exception as e:
            print(f"{RED}Error: {e}{RESET}")

if __name__ == '__main__':
    engine = ReasoningAgent()
    print("-" * 50)
    query = input("Enter query:\n>>> ")
    if not query.strip(): query = "Write Python code for Trapping Rain Water."
    
    try:
        engine.generate_reasoning(query)
    finally:
        # Ensure cleanup happens even if generation fails
        engine.unload_model()