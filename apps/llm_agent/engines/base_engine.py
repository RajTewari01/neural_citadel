"""
Base Engine Abstract Class
===========================

Defines the interface for all LLM engines.
"""

from abc import ABC, abstractmethod
from typing import Optional, Generator
from pathlib import Path


class BaseLLMEngine(ABC):
    """Abstract base class for LLM engines."""
    
    def __init__(self, model_path: Path, **kwargs):
        """
        Initialize the engine with model path.
        
        Args:
            model_path: Path to the model directory or file
            **kwargs: Engine-specific configuration
        """
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self._is_loaded = False
    
    @abstractmethod
    def load(self) -> None:
        """Load the model into memory."""
        pass
    
    @abstractmethod
    def unload(self) -> None:
        """Unload the model and free GPU/RAM."""
        pass
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate a response for the given prompt.
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text response
        """
        pass
    
    @abstractmethod
    def stream(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> Generator[str, None, None]:
        """
        Stream tokens for the given prompt.
        
        Args:
            prompt: User prompt
            system_prompt: System instructions  
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional generation parameters
            
        Yields:
            Generated text tokens
        """
        pass
    
    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._is_loaded
    
    def __enter__(self):
        """Context manager entry."""
        self.load()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure cleanup."""
        self.unload()
        return False
