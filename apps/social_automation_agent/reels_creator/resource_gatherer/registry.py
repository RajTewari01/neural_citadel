"""
Pipeline Registry System
=========================

A central registry for managing media generation pipelines.
This system allows developers to register new pipeline configurations 
using a simple decorator, eliminating the need to modify core logic 
when adding new styles or capabilities.

Usage:
    from apps.social_automation_agent.reels_creator.resource_gatherer.registry import register_pipeline
    
    @register_pipeline(
        name="zombie_mode",
        api_name="sdxl_turbo",
        keywords=["undead", "zombie", "horror"],
        description="Generates high-contrast horror themed images.",
        availability_type={"fast": "Low Res", "hd": "High Res"}
    )
    def get_zombie_config(prompt: str, **kwargs):
        return PipelineConfig(...)
"""

from typing import Any, Optional, Dict, List, Callable

# --- Global Registry Storage ---
# Stores metadata and factory functions for all registered pipelines.
# Structure: { "pipeline_name": { "func": <callable>, "keywords": [...], ... } }
PIPELINE_REGISTRY: Dict[str, Dict[str, Any]] = {}


def register_pipeline(
    name: str,
    api_name: str,
    keywords: List[str],
    description: str,
    availability_type: Dict[str, str]
):
    """
    Decorator to register a pipeline's configuration factory.
    
    This function wraps the configuration loader and adds it to the global
    PIPELINE_REGISTRY, making it discoverable by the main application.

    Args:
        name (str): Unique internal identifier (e.g., "car", "zombie").
        api_name (str): The specific model/API to use (e.g., "dalle-3", "stability").
        keywords (List[str]): List of triggers that activate this pipeline.
        description (str): Human-readable help text for CLI/UI.
        availability_type (Dict[str,str]): Map of available sub-modes (e.g., {'fast': 'Draft'}).
    """
    
    def decorator(func: Callable):
        # Register the function and its metadata
        PIPELINE_REGISTRY[name] = {
            "factory_func": func,  # The function that generates the config
            "api_name": api_name,
            "keywords": keywords,
            "description": description,
            "availability_type": availability_type,
        }
        
        # Return the function unchanged so it can still be called normally if needed
        return func
        
    return decorator


def get_pipeline_by_name(name: str) -> Optional[Dict[str, Any]]:
    """
    Directly retrieve a pipeline by its unique name.
    
    Args:
        name: The unique string ID of the pipeline.
        
    Returns:
        The pipeline metadata dict, or None if not found.
    """
    return PIPELINE_REGISTRY.get(name)


def find_pipeline_by_keyword(user_input: str) -> Optional[str]:
    """
    Scans all registered pipelines to find one that matches the user's input string.
    
    Args:
        user_input: The raw string from the user (e.g., "I want a zombie video").
        
    Returns:
        The 'name' of the matching pipeline, or None.
    """
    sanitized_input = user_input.lower()
    
    for pipe_name, metadata in PIPELINE_REGISTRY.items():
        # Check if any of this pipeline's keywords exist in the input string
        for keyword in metadata.get("keywords", []):
            if keyword.lower() in sanitized_input:
                return pipe_name
                
    return None