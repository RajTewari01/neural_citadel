"""
Image Generation Tools Package
==============================

Contains prompt enhancement and other utility tools.
- prompts.py: Prompt enhancement using CivitAI data
- aspect.py:  Automatic aspect ratio detection from prompts
"""

from .prompts import (
    PromptEnhancer,
    EnhancedPrompt,
    enhance_prompt,
    enhance_for_model,
    get_enhancer,
    list_available_models,
)

from .aspect import (
    detect_aspect,
    get_aspect_name,
    get_dimensions,
    analyze_prompt,
    ASPECT_RATIOS,
)

__all__ = [
    # Prompts
    'PromptEnhancer',
    'EnhancedPrompt', 
    'enhance_prompt',
    'enhance_for_model',
    'get_enhancer',
    'list_available_models',
    # Aspect
    'detect_aspect',
    'get_aspect_name',
    'get_dimensions',
    'analyze_prompt',
    'ASPECT_RATIOS',
]
