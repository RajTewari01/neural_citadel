"""
LLM Engine Factory
==================

Main engine class with factory pattern for creating appropriate engine
based on model type (transformers vs llama_cpp).
"""

from typing import Optional, Generator, Union
from pathlib import Path
import sys

# Path setup
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from configs.paths import LLM_MODELS, LLM_ENGINE_TYPES

# ANSI colors
YELLOW = '\033[1;103m'
RESET = '\033[0m'
GREEN = '\033[1;32m'
RED = '\033[1;31m'
CYAN = '\033[1;36m'


class LLMEngine:
    """
    Factory class for LLM engines.
    
    Automatically selects the appropriate engine (transformers or llama_cpp)
    based on the model type.
    
    Usage:
        # Simple usage
        engine = LLMEngine("deepseek_coder")
        response = engine.generate("Write binary search in Python")
        engine.unload()
        
        # Context manager (auto-cleanup)
        with LLMEngine("qwen_coder") as engine:
            for token in engine.stream("Write quicksort"):
                print(token, end="", flush=True)
    """
    
    def __init__(self, model_key: str, **kwargs):
        """
        Initialize the appropriate engine for the model.
        
        Args:
            model_key: Key from LLM_MODELS registry
            **kwargs: Engine-specific parameters
        """
        if model_key not in LLM_MODELS:
            available = list(LLM_MODELS.keys())
            raise ValueError(f"Unknown model: {model_key}. Available: {available}")
        
        self.model_key = model_key
        self.engine_type = LLM_ENGINE_TYPES.get(model_key, "llama_cpp")
        self._engine = None
        self._kwargs = kwargs
        
        print(f"{CYAN}[LLM] Creating engine for {model_key} ({self.engine_type}){RESET}")
    
    def _create_engine(self):
        """Lazy-create the appropriate engine."""
        if self._engine is not None:
            return
        
        from apps.llm_agent.engines.llama_cpp_engine import (
            LlamaCppEngine, DeepSeekCoderEngine, QwenCoderEngine,
            MistralEngine, TinyLlamaEngine
        )
        
        # Use specialized engines where available
        engine_map = {
            "deepseek_coder": DeepSeekCoderEngine,
            "qwen_coder": QwenCoderEngine,
            "mistral": MistralEngine,
            "tinyllama": TinyLlamaEngine,
        }
        
        if self.model_key in engine_map:
            self._engine = engine_map[self.model_key](**self._kwargs)
        else:
            self._engine = LlamaCppEngine(self.model_key, **self._kwargs)
    
    def load(self) -> None:
        """Load the model into memory."""
        self._create_engine()
        self._engine.load()
    
    def unload(self) -> None:
        """Unload model and free memory."""
        if self._engine:
            self._engine.unload()
    
    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate response (non-streaming).
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated text
        """
        self._create_engine()
        return self._engine.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )
    
    def stream(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> Generator[str, None, None]:
        """
        Stream tokens.
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Yields:
            Generated text tokens
        """
        self._create_engine()
        yield from self._engine.stream(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )
    
    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._engine is not None and self._engine.is_loaded
    
    def __enter__(self):
        """Context manager entry."""
        self.load()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.unload()
        return False
    
    @staticmethod
    def list_models() -> dict:
        """List all available models with their engine types."""
        return {k: LLM_ENGINE_TYPES.get(k, "llama_cpp") for k in LLM_MODELS.keys()}


# Convenience functions
def get_engine(model_key: str, **kwargs) -> LLMEngine:
    """Get an LLM engine for the specified model."""
    return LLMEngine(model_key, **kwargs)


def list_available_models() -> list:
    """List all available model keys."""
    return list(LLM_MODELS.keys())
