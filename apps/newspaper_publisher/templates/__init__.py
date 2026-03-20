"""
Newspaper Publisher Templates
==============================

Template classes for different newspaper/magazine styles.
Uses a self-registering pattern for extensibility.
"""

from .classic import ClassicNewspaper
from .modern import ModernNewspaper
from .magazine import VibrantMagazine, STYLES as MAG_STYLES

# Registry system
from .registry import (
    discover_templates,
    get_all_templates,
    get_template_names,
    get_template_class,
    get_substyles,
    format_help_text,
    TEMPLATE_REGISTRY
)

# Legacy dict for backwards compatibility
TEMPLATES = {
    'classic': ClassicNewspaper,
    'modern': ModernNewspaper,
    'magazine': VibrantMagazine
}

__all__ = [
    'ClassicNewspaper',
    'ModernNewspaper', 
    'VibrantMagazine',
    'MAG_STYLES',
    'TEMPLATES',
    'discover_templates',
    'get_all_templates',
    'get_template_names',
    'get_template_class',
    'get_substyles',
    'format_help_text',
    'TEMPLATE_REGISTRY'
]
