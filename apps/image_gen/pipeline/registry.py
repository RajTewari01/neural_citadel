"""
Pipeline Registry System
=========================

Self-registration system for image generation pipelines.
Scales to any number of pipelines without hardcoded keywords.

Usage:
    from apps.image_gen.pipeline.registry import register_pipeline
    
    @register_pipeline(
        name="my_style",
        keywords=["keyword1", "keyword2"],
        description="My awesome style",
        types={"type1": "Description", "type2": "Description"}
    )
    def get_config(prompt: str, **kwargs):
        return PipelineConfig(...)
"""

from typing import Dict, List, Callable, Optional, Tuple, Any


# Global registry - populated when pipelines import this module
PIPELINE_REGISTRY: Dict[str, Dict[str, Any]] = {}


def register_pipeline(
    name: str,
    keywords: List[str],
    description: str = "",
    category: str = "image",
    types: Optional[Dict[str, str]] = None
):
    """
    Decorator to register a pipeline's get_config function.
    
    Args:
        name: Unique pipeline name (e.g., "car", "zombie")
        keywords: List of keywords that trigger this pipeline
        description: Human-readable description
        category: Category type (default: "image")
        types: Dict of sub-types and their descriptions (for --type arg)
    
    Example:
        @register_pipeline(
            name="car",
            keywords=["car", "vehicle", "automobile"],
            description="Car generation with LoRA styles",
            types={"rx7": "Mazda RX7 JDM style", "sedan": "Generic sedan"}
        )
        def get_car_config(prompt, style=None, **kwargs):
            ...
    """
    def decorator(func: Callable):
        PIPELINE_REGISTRY[name] = {
            "get_config": func,
            "keywords": [kw.lower() for kw in keywords],
            "description": description,
            "category": category,
            "name": name,
            "types": types or {}
        }
        return func
    return decorator


def get_all_pipelines() -> Dict[str, Dict[str, Any]]:
    """Get all registered pipelines."""
    return PIPELINE_REGISTRY


def get_pipeline_names() -> List[str]:
    """Get list of all registered pipeline names."""
    return list(PIPELINE_REGISTRY.keys())


def get_pipeline(name: str) -> Optional[Dict[str, Any]]:
    """Get a specific pipeline by name."""
    return PIPELINE_REGISTRY.get(name)


def find_pipeline_by_keyword(text: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Find a pipeline based on keywords in the text.
    
    Args:
        text: User input text to match against keywords
        
    Returns:
        Tuple of (pipeline_name, pipeline_info) or (None, None) if not found
    """
    text_lower = text.lower()
    
    # Score each pipeline
    scores = {}
    for name, info in PIPELINE_REGISTRY.items():
        score = 0
        for keyword in info["keywords"]:
            if keyword in text_lower:
                score += len(keyword)  # Longer matches = higher score
        if score > 0:
            scores[name] = score
    
    if not scores:
        return None, None
    
    # Return highest scoring pipeline
    best = max(scores, key=scores.get)
    return best, PIPELINE_REGISTRY[best]


def get_all_keywords() -> Dict[str, List[str]]:
    """Get a mapping of pipeline names to their keywords."""
    return {name: info["keywords"] for name, info in PIPELINE_REGISTRY.items()}


def get_pipeline_types(name: str) -> Dict[str, str]:
    """Get available types for a pipeline."""
    pipeline = get_pipeline(name)
    return pipeline.get("types", {}) if pipeline else {}


def format_help_text() -> str:
    """Format detailed help text showing all pipelines and their options."""
    lines = [
        "=" * 70,
        "NEURAL CITADEL - Image Generation Pipelines",
        "=" * 70,
        ""
    ]
    
    for name, info in sorted(PIPELINE_REGISTRY.items()):
        lines.append(f"📦 {name.upper()}")
        lines.append(f"   {info['description']}")
        lines.append(f"   Keywords: {', '.join(info['keywords'][:5])}...")
        
        if info.get("types"):
            lines.append(f"   Types (--type):")
            for t, desc in info["types"].items():
                lines.append(f"      {t}: {desc}")
        lines.append("")
    
    return "\n".join(lines)


def discover_pipelines():
    """
    Import all pipeline modules to trigger their @register_pipeline decorators.
    Call this once at startup before using the registry.
    """
    # Import all pipeline modules - their decorators auto-register
    from . import (
        anime,
        cars,
        closeup_anime,
        difconsistency,
        diffusionbrush,
        drawing,
        ethnicity,
        ghost,
        horror,
        hyperrealistic,
        papercut,
        porn,
        space,
        zombie
    )


# Auto-discover on import (optional - can also call discover_pipelines() manually)
# discover_pipelines()  # Uncomment to auto-discover
