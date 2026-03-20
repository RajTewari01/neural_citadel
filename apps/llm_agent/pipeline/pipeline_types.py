"""
LLM Pipeline Types
==================

Configuration dataclasses for LLM generation pipelines.
"""

from dataclasses import dataclass, field
from typing import Optional, Literal, List
from pathlib import Path


EngineType = Literal["llama_cpp", "transformers"]
ModelKey = Literal[
    "deepseek_coder", "deepseek_r1", "qwen_coder", "qwen_small",
    "mistral", "dolphin_qwen", "tinyllama", "nsfw_story", "realistic_rp"
]


@dataclass
class LLMConfig:
    """
    Configuration for LLM generation.
    
    Attributes:
        model_key: Key from LLM_MODELS registry
        prompt: User prompt to generate response for
        system_prompt: System instructions (optional)
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature (0.0 = deterministic, 1.0 = random)
        stream: Enable token-by-token streaming
        stop_tokens: List of stop sequences
        
    Engine-specific:
        n_ctx: Context window size (llama_cpp)
        n_gpu_layers: GPU layers to offload (llama_cpp, -1 = all)
        use_cache: Enable KV cache (transformers)
    """
    # Required
    model_key: ModelKey
    prompt: str
    
    # Generation params
    system_prompt: str = ""
    max_tokens: int = 2048
    temperature: float = 0.7
    stream: bool = True
    stop_tokens: List[str] = field(default_factory=lambda: ["###", "<|im_end|>", "<|eot_id|>"])
    
    # llama_cpp specific
    n_ctx: int = 4096
    n_gpu_layers: int = -1
    n_threads: int = 8
    
    # transformers specific
    use_cache: bool = False  # Disable for Ouro compatibility
    
    def __post_init__(self):
        # Validate model key
        valid_keys = [
            "deepseek_coder", "deepseek_r1", "qwen_coder", "qwen_small",
            "mistral", "dolphin_qwen", "tinyllama", "nsfw_story", "realistic_rp"
        ]
        if self.model_key not in valid_keys:
            raise ValueError(f"Invalid model_key: {self.model_key}. Valid: {valid_keys}")


@dataclass  
class CodingConfig(LLMConfig):
    """Optimized config for code generation."""
    temperature: float = 0.2  # Low temp for precise code
    max_tokens: int = 4096
    stream: bool = True
    system_prompt: str = "You are an expert software engineer. Write efficient, production-ready code."


@dataclass
class ReasoningConfig(LLMConfig):
    """Optimized config for reasoning tasks."""
    temperature: float = 0.4
    max_tokens: int = 512
    stream: bool = True
    system_prompt: str = "You are a focused reasoning AI. Be concise and logical."


@dataclass
class CreativeConfig(LLMConfig):
    """Optimized config for creative writing."""
    temperature: float = 0.85
    max_tokens: int = 2048
    stream: bool = True
    system_prompt: str = "You are a professional creative writer. Write vivid, engaging content."


@dataclass
class ChatConfig(LLMConfig):
    """Optimized config for conversational chat."""
    temperature: float = 0.7
    max_tokens: int = 1024
    stream: bool = True
    system_prompt: str = "You are a helpful assistant."
