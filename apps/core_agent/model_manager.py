"""
Model Lifecycle Manager
=======================
Handles strict VRAM management using the existing LLMEngine pattern.
Uses Mistral for routing + chat, delegates specialized tasks to subprocess.
"""

import gc
import logging
from typing import Optional

# Use existing LLM engine infrastructure
from apps.llm_agent.engine import LLMEngine

logger = logging.getLogger("core_agent.model_manager")

class ModelManager:
    """
    Manages Mistral model for routing + chat.
    Uses existing LLMEngine factory pattern.
    """
    
    def __init__(self, model_key: str = "mistral"):
        self.model_key = model_key
        self.engine: Optional[LLMEngine] = None
    
    def load(self) -> LLMEngine:
        """Load the model if not already loaded."""
        if self.engine and self.engine.is_loaded:
            return self.engine
        
        logger.info(f"🧠 Loading {self.model_key}...")
        self.engine = LLMEngine(self.model_key)
        self.engine.load()
        logger.info(f"✅ {self.model_key} loaded!")
        return self.engine
    
    def unload(self):
        """Unload model to free VRAM."""
        if self.engine:
            logger.info(f"🔻 Unloading {self.model_key} to free VRAM...")
            self.engine.unload()
            self.engine = None
            gc.collect()
    
    def generate(self, prompt: str, system_prompt: str = "", max_tokens: int = 512, temperature: float = 0.7) -> str:
        """Generate response using loaded model."""
        self.load()
        return self.engine.generate(prompt, system_prompt=system_prompt, max_tokens=max_tokens, temperature=temperature)
    
    def stream(self, prompt: str, system_prompt: str = "", max_tokens: int = 512, temperature: float = 0.7):
        """Stream response using loaded model."""
        self.load()
        yield from self.engine.stream(prompt, system_prompt=system_prompt, max_tokens=max_tokens, temperature=temperature)
    
    def run_external_tool(self, tool_callback):
        """Unload model, run tool, reload model."""
        self.unload()
        try:
            result = tool_callback()
            return result
        finally:
            logger.info("🔄 Reloading model after tool execution...")
            self.load()
