"""
Llama.cpp Engine
=================

Engine implementation for GGUF models using llama-cpp-python.
Handles model loading, generation, and streaming.
"""

from typing import Optional, Generator
from pathlib import Path
from torch import cuda
import logging
import gc
import sys

# Path setup
_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from apps.llm_agent.engines.base_engine import BaseLLMEngine
from configs.paths import LLM_MODELS, LLM_HF_REPOS, LLM_DEBUG_DIR

# ANSI colors
YELLOW = '\033[1;103m'
RESET = '\033[0m'
GREEN = '\033[1;32m'
RED = '\033[1;31m'
CYAN = '\033[1;36m'

# Setup logging
LLM_DEBUG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=LLM_DEBUG_DIR / "llama_cpp.log",
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)-8s - %(message)s'
)
logger = logging.getLogger(__name__)


class LlamaCppEngine(BaseLLMEngine):
    """
    Engine for GGUF models using llama-cpp-python.
    
    Features:
        - Auto-download from HuggingFace if model missing
        - GPU acceleration with configurable layer offload
        - Streaming generation
        - Memory cleanup
    """
    
    def __init__(
        self,
        model_key: str,
        n_ctx: int = 4096,
        n_gpu_layers: int = -1,
        n_threads: int = 8,
        verbose: bool = False,
        **kwargs
    ):
        """
        Initialize llama.cpp engine.
        
        Args:
            model_key: Key from LLM_MODELS registry
            n_ctx: Context window size
            n_gpu_layers: Layers to offload to GPU (-1 = all)
            n_threads: CPU threads for inference
            verbose: Print llama.cpp debug info
        """
        if model_key not in LLM_MODELS:
            raise ValueError(f"Unknown model: {model_key}. Available: {list(LLM_MODELS.keys())}")
        
        model_dir = LLM_MODELS[model_key]
        super().__init__(model_dir, **kwargs)
        
        self.model_key = model_key
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self.n_threads = n_threads
        self.verbose = verbose
        self.llm = None
        
        # Get GGUF filename
        if model_key in LLM_HF_REPOS:
            self.gguf_filename = LLM_HF_REPOS[model_key]["filename"]
        else:
            # Try to find GGUF file in directory
            self.gguf_filename = self._find_gguf()
    
    def _find_gguf(self) -> Optional[str]:
        """Find GGUF file in model directory."""
        if not self.model_path.exists():
            return None
        for f in self.model_path.glob("*.gguf"):
            return f.name
        return None
    
    def _ensure_model(self) -> Path:
        """Ensure model exists, download if necessary."""
        gguf_path = self.model_path / self.gguf_filename
        
        if gguf_path.exists():
            return gguf_path
        
        # Auto-download from HuggingFace
        if self.model_key in LLM_HF_REPOS:
            print(f"{YELLOW}[DOWNLOAD] Model not found, downloading from HuggingFace...{RESET}")
            try:
                from huggingface_hub import hf_hub_download
                
                repo_info = LLM_HF_REPOS[self.model_key]
                self.model_path.mkdir(parents=True, exist_ok=True)
                
                hf_hub_download(
                    repo_id=repo_info["repo_id"],
                    filename=repo_info["filename"],
                    local_dir=self.model_path,
                    local_dir_use_symlinks=False
                )
                print(f"{GREEN}[OK] Model downloaded successfully!{RESET}")
                return gguf_path
            except Exception as e:
                logger.error(f"Failed to download model: {e}")
                raise RuntimeError(f"Failed to download model {self.model_key}: {e}")
        else:
            raise FileNotFoundError(f"Model not found at {gguf_path} and no HF repo configured")
    
    def load(self) -> None:
        """Load the GGUF model into memory."""
        if self._is_loaded:
            return
        
        # Cleanup before loading
        gc.collect()
        if cuda.is_available():
            cuda.empty_cache()
        
        gguf_path = self._ensure_model()
        
        print(f"{CYAN}[LOAD] Loading {self.model_key}...{RESET}")
        logger.info(f"Loading model: {gguf_path}")
        
        try:
            from llama_cpp import Llama
            
            self.llm = Llama(
                model_path=str(gguf_path),
                n_ctx=self.n_ctx,
                n_gpu_layers=self.n_gpu_layers,
                n_threads=self.n_threads,
                verbose=self.verbose
            )
            self._is_loaded = True
            print(f"{GREEN}[OK] Model loaded successfully!{RESET}")
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def unload(self) -> None:
        """Unload model and free memory."""
        if self.llm:
            del self.llm
            self.llm = None
        
        self._is_loaded = False
        gc.collect()
        if cuda.is_available():
            cuda.empty_cache()
        
        print(f"{YELLOW}[UNLOAD] Model unloaded, memory cleared.{RESET}")
        logger.info("Model unloaded")
    
    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        stop_tokens: list = None,
        **kwargs
    ) -> str:
        """Generate response (non-streaming)."""
        if not self._is_loaded:
            self.load()
        
        full_prompt = self._format_prompt(prompt, system_prompt)
        
        response = self.llm(
            full_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop_tokens or ["###", "<|im_end|>", "<|eot_id|>"],
            **kwargs
        )
        
        return response['choices'][0]['text']
    
    def stream(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        stop_tokens: list = None,
        **kwargs
    ) -> Generator[str, None, None]:
        """Stream tokens."""
        if not self._is_loaded:
            self.load()
        
        full_prompt = self._format_prompt(prompt, system_prompt)
        
        stream = self.llm(
            full_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop_tokens or ["###", "<|im_end|>", "<|eot_id|>"],
            stream=True,
            **kwargs
        )
        
        for chunk in stream:
            text = chunk['choices'][0]['text']
            yield text
    
    def _format_prompt(self, prompt: str, system_prompt: str) -> str:
        """
        Format prompt based on model type.
        Override in subclasses for specific formatting.
        """
        if system_prompt:
            return f"### System:\n{system_prompt}\n\n### User:\n{prompt}\n\n### Assistant:\n"
        return f"### User:\n{prompt}\n\n### Assistant:\n"


# Specialized engines for specific models
class DeepSeekCoderEngine(LlamaCppEngine):
    """Engine optimized for DeepSeek Coder models."""
    
    def __init__(self, **kwargs):
        super().__init__("deepseek_coder", n_ctx=4096, **kwargs)
    
    def _format_prompt(self, prompt: str, system_prompt: str) -> str:
        sys = system_prompt or "You are an expert software engineer."
        return f"""### Instruction:
{sys}
Task: {prompt}

Guidelines:
1. Write efficient, production-ready code.
2. DO NOT output conversational filler.
3. Use comments for explanations.
### Response:
"""


class QwenCoderEngine(LlamaCppEngine):
    """Engine optimized for Qwen Coder models."""
    
    def __init__(self, **kwargs):
        super().__init__("qwen_coder", n_ctx=8192, **kwargs)
    
    def _format_prompt(self, prompt: str, system_prompt: str) -> str:
        sys = system_prompt or "You are an expert Python developer."
        return f"""<|im_start|>system
{sys}<|im_end|>
<|im_start|>user
{prompt}<|im_end|>
<|im_start|>assistant
"""


class MistralEngine(LlamaCppEngine):
    """Engine optimized for Mistral models."""
    
    def __init__(self, **kwargs):
        super().__init__("mistral", n_ctx=4096, **kwargs)
    
    def _format_prompt(self, prompt: str, system_prompt: str) -> str:
        if system_prompt:
            return f"<s>[INST] {system_prompt}\n\n{prompt} [/INST]"
        return f"<s>[INST] {prompt} [/INST]"


class TinyLlamaEngine(LlamaCppEngine):
    """Engine for TinyLlama - fast and lightweight."""
    
    def __init__(self, **kwargs):
        super().__init__("tinyllama", n_ctx=2048, **kwargs)
    
    def _format_prompt(self, prompt: str, system_prompt: str) -> str:
        sys = system_prompt or "You are a helpful assistant."
        return f"""<|system|>
{sys}</s>
<|user|>
{prompt}</s>
<|assistant|>
"""
