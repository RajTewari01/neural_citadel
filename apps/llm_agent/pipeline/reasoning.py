"""
Reasoning Pipeline
==================

Specialized pipeline for logic, math, and complex reasoning tasks.
Defaults to DeepSeek R1 key-based reasoning.
"""

from typing import Union, Generator
from apps.llm_agent.engine import LLMEngine

DEFAULT_MODEL = "deepseek_r1"


def solve(
    prompt: str,
    model: str = DEFAULT_MODEL,
    stream: bool = True,
    **kwargs
) -> Union[str, Generator[str, None, None]]:
    """
    Solve a reasoning or math problem.
    """
    
    # DeepSeek R1 specific prompting usually helps
    system_prompt = kwargs.get("system_prompt", "You are a highly capable reasoning engine. Solve the problem step-by-step.")
    
    engine = LLMEngine(model, **kwargs)
    
    if stream:
        return engine.stream(
            prompt,
            system_prompt=system_prompt,
            max_tokens=kwargs.get("max_tokens", 4096), # Reasoning needs space
            temperature=kwargs.get("temperature", 0.6)
        )
    else:
        return engine.generate(
            prompt,
            system_prompt=system_prompt,
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=kwargs.get("temperature", 0.6)
        )
