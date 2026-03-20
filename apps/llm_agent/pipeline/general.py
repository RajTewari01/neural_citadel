"""
General Knowledge Pipeline
==========================

Standard conversational pipeline with multi-persona support.
Uses Mistral 7B as the default engine for these tasks.
"""

from typing import Union, Generator
from apps.llm_agent.engine import LLMEngine

# User specified Mistral for these personas
DEFAULT_MODEL = "mistral"

# Exact prompts from user request
PERSONAS = {
    "default": "You are a helpful assistant.",
    
    "philosopher": (
        "You are a wise and contemplative philosopher. "
        "Reflect deeply on the concept of: {prompt}. "
        "Explore the ethical, metaphysical, and existential implications. "
        "Use analogies, question the nature of reality, and offer a perspective that challenges the status quo. "
        "Your tone should be profound, calm, and intellectual."
    ),
    
    "therapist": (
        "You are a compassionate and empathetic counselor. "
        "The user is feeling: {prompt}. "
        "Respond with validation, kindness, and gentle guidance. "
        "Do not judge. Focus on active listening techniques and offering comforting perspectives. "
        "Make the user feel heard and safe. (Note: You are a supportive AI, not a doctor)."
    ),
    
    "teacher": (
        "You are an expert professor with a gift for explaining complex topics simply. "
        "Teach me about: {prompt}. "
        "Break the concept down into clear, logical steps or bullet points. "
        "Use real-world examples to make it easy to understand. "
        "End with a quick summary or a fun fact to help it stick."
    ),
    
    "reddit": (
        "You are a Reddit user posting on a popular subreddit (like r/TIFU or r/confession). "
        "Write a viral post about: {prompt}. "
        "Use a first-person perspective ('I'), informal internet slang, and a dramatic or humorous tone. "
        "Include a catchy title at the start. "
        "Make it sound personal, raw, and engaging, like a real human confession."
    ),
    
    "anything": (
        "You are the master of everything, the best in anything ever present in the world. "
        "{prompt}, make the best/excellent for any humans ever lived."
    )
}

# Temperature settings from user request
PERSONA_TEMPS = {
    "default": 0.7,
    "philosopher": 0.8,
    "therapist": 0.6,
    "teacher": 0.3,
    "reddit": 1.1,
    "anything": 0.7
}


def chat(
    prompt: str,
    model: str = DEFAULT_MODEL,
    persona: str = "default",
    stream: bool = True,
    system_prompt: str = None,
    **kwargs
) -> Union[str, Generator[str, None, None]]:
    """
    Run a chat interaction with a specific persona.
    
    Args:
        prompt: User input
        model: Model to use (default: mistral)
        persona: One of ['philosopher', 'therapist', 'teacher', 'reddit', 'anything']
    """
    
    # Resolve system prompt
    # Note: The user's prompts include "{prompt}". We need to format them.
    # However, standard chat systems separate system prompt from user message.
    # Mistral usually takes [INST] ... [/INST].
    # The user provided prompt templates that INCLUDE the user prompt in the system instruction?
    # Actually, looking at the user's snippet: "Reflect deeply on the concept of: {prompt}."
    # This implies the whole thing is the prompt passed to the model.
    # But usually we want a reusable system prompt.
    # I will adapt this: The persona text becomes the system prompt, and we append the user prompt normally
    # UNLESS the persona text explicitly needs formatting.
    
    raw_persona_text = PERSONAS.get(persona, PERSONAS["default"])
    
    # Check if persona text expects formatting
    if "{prompt}" in raw_persona_text:
        # If the persona text includes {prompt}, it's practically a template for the USER functionality
        # We should treat it as the "System + User" instruction.
        full_instruction = raw_persona_text.format(prompt=prompt)
        # We pass this as the PROMPT to the engine, and leave system prompt empty/minimal?
        # Or pass it as system prompt?
        # Let's pass it as the system prompt to set the behavior, and user prompt as confirmation.
        # Actually, if it contains the prompt, it IS the prompt.
        final_system_prompt = "" # We'll bake it into the prompt
        final_user_prompt = full_instruction
    else:
        final_system_prompt = raw_persona_text
        final_user_prompt = prompt
        
    # Manual override
    if system_prompt:
        final_system_prompt = system_prompt
        final_user_prompt = prompt
    
    # Resolve temperature
    temperature = kwargs.get("temperature", PERSONA_TEMPS.get(persona, 0.7))
    max_tokens = kwargs.get("max_tokens", 1024)
    
    engine = LLMEngine(model, **kwargs)
    
    if stream:
        return engine.stream(
            final_user_prompt,
            system_prompt=final_system_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
    else:
        return engine.generate(
            final_user_prompt,
            system_prompt=final_system_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
