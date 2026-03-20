"""
Coding Pipeline
===============

Specialized pipeline for code generation tasks.
Optimized for precision, logic, and clean output.
"""

from typing import Union, Generator
from apps.llm_agent.engine import LLMEngine
from apps.llm_agent.pipeline.pipeline_types import CodingConfig

DEFAULT_MODEL = "deepseek_coder"


def generate_code(
    prompt: str,
    model: str = DEFAULT_MODEL,
    stream: bool = True,
    **kwargs
) -> Union[str, Generator[str, None, None]]:
    """
    Generate code for a given prompt.
    
    Args:
        prompt: Task description or code snippet
        model: Model to use (default: deepseek_coder)
        stream: Whether to stream output
        **kwargs: Additional engine arguments
        
    Returns:
        Generated code string or generator of tokens
    """
    config = CodingConfig(model_key=model, prompt=prompt)
    
    # Override defaults with kwargs if provided
    temperature = kwargs.get("temperature", config.temperature)
    max_tokens = kwargs.get("max_tokens", config.max_tokens)
    system_prompt = kwargs.get("system_prompt", config.system_prompt)
    
    engine = LLMEngine(model, **kwargs)
    
    if stream:
        return engine.stream(
            prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
    else:
        return engine.generate(
            prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )


def explain_code(
    code: str,
    model: str = DEFAULT_MODEL,
    stream: bool = True
) -> Union[str, Generator[str, None, None]]:
    """
    Explain a piece of code.
    """
    prompt = f"Explain the following code logic:\n\n{code}"
    return generate_code(prompt, model, stream, system_prompt="You are an expert code instructor.")
