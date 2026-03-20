"""
Template Registry System
=========================

Self-registration system for newspaper templates.
Mirrors image_gen/pipeline/registry.py patterns.

Usage:
    from apps.newspaper_publisher.templates.registry import register_template
    
    @register_template(
        name="classic",
        keywords=["classic", "newspaper", "traditional"],
        description="NYT-style classic layout"
    )
    class ClassicNewspaper(NewspaperTemplate):
        ...
"""

from typing import Dict, List, Any, Optional, Tuple, Type


# Global registry - populated when templates import this module
TEMPLATE_REGISTRY: Dict[str, Dict[str, Any]] = {}


def register_template(
    name: str,
    keywords: List[str],
    description: str = "",
    substyles: Optional[Dict[str, Any]] = None
):
    """
    Decorator to register a template class.
    
    Args:
        name: Unique template name (e.g., "classic", "magazine")
        keywords: List of keywords that match this template
        description: Human-readable description
        substyles: Dict of sub-styles (for Magazine) with their configs
    
    Example:
        @register_template(
            name="magazine",
            keywords=["magazine", "glossy", "vibrant"],
            description="Vibrant magazine with multiple substyles",
            substyles={"The Tech": {...}, "The Noir": {...}}
        )
        class VibrantMagazine(NewspaperTemplate): ...
    """
    def decorator(cls: Type):
        TEMPLATE_REGISTRY[name] = {
            "class": cls,
            "keywords": [kw.lower() for kw in keywords],
            "description": description,
            "name": name,
            "substyles": substyles or {}
        }
        return cls
    return decorator


def get_all_templates() -> Dict[str, Dict[str, Any]]:
    """Get all registered templates."""
    return TEMPLATE_REGISTRY


def get_template_names() -> List[str]:
    """Get list of all registered template names."""
    return list(TEMPLATE_REGISTRY.keys())


def get_template(name: str) -> Optional[Dict[str, Any]]:
    """Get a specific template by name."""
    return TEMPLATE_REGISTRY.get(name.lower())


def get_template_class(name: str, substyle: Optional[str] = None) -> Optional[Type]:
    """
    Get the template class for a given style name.
    
    Args:
        name: Style name (e.g., "Classic", "Magazine")
        substyle: Optional substyle for Magazine
        
    Returns:
        Template class ready to instantiate
    """
    template_info = get_template(name.lower())
    if not template_info:
        return None
    return template_info["class"]


def get_substyles(name: str) -> Dict[str, Any]:
    """Get available substyles for a template."""
    template = get_template(name)
    return template.get("substyles", {}) if template else {}


def find_template_by_keyword(text: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Find a template based on keywords in the text.
    
    Args:
        text: User input text to match against keywords
        
    Returns:
        Tuple of (template_name, template_info) or (None, None) if not found
    """
    text_lower = text.lower()
    
    # Score each template
    scores = {}
    for name, info in TEMPLATE_REGISTRY.items():
        score = 0
        for keyword in info["keywords"]:
            if keyword in text_lower:
                score += len(keyword)
        if score > 0:
            scores[name] = score
    
    if not scores:
        return None, None
    
    # Return highest scoring template
    best = max(scores, key=scores.get)
    return best, TEMPLATE_REGISTRY[best]


def format_help_text() -> str:
    """Format detailed help text showing all templates and their options."""
    lines = [
        "=" * 60,
        "NEURAL CITADEL - Newspaper Templates",
        "=" * 60,
        ""
    ]
    
    for name, info in sorted(TEMPLATE_REGISTRY.items()):
        lines.append(f"📰 {name.upper()}")
        lines.append(f"   {info['description']}")
        
        if info.get("substyles"):
            lines.append(f"   Substyles:")
            for substyle_name in list(info["substyles"].keys())[:5]:
                lines.append(f"      • {substyle_name}")
            if len(info["substyles"]) > 5:
                lines.append(f"      ... and {len(info['substyles']) - 5} more")
        lines.append("")
    
    return "\n".join(lines)


def discover_templates():
    """
    Import all template modules to trigger their @register_template decorators.
    Call this once at startup before using the registry.
    """
    # Import all template modules - their decorators auto-register
    from . import (
        classic,
        modern,
        magazine
    )


# Auto-discover is NOT called on import (call discover_templates() manually)
