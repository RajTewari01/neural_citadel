"""
Template Factory
================
Central registry for newspaper templates.
Handles instantiation of correct template classes based on style name.
"""

import sys
from pathlib import Path

# Ensure project root is in path for relative imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Now these imports will work regardless of CWD
from apps.newspaper_publisher.templates.classic import ClassicNewspaper
from apps.newspaper_publisher.templates.modern import ModernNewspaper
from apps.newspaper_publisher.templates.magazine import VibrantMagazine, STYLES as MAGAZINE_STYLES

# Export Magazine Styles for Runner CLI
STYLES = MAGAZINE_STYLES

def TemplateClass(filename, style_name='Classic'):
    """
    Factory function to return the appropriate newspaper/magazine instance.
    
    Args:
        filename (str): The output PDF path.
        style_name (str): The desired style (e.g., 'Classic', 'Modern', 'The Star', 'The Tech').
        
    Returns:
        Instance of a template class (ClassicNewspaper, ModernNewspaper, or VibrantMagazine).
    """
    s_lower = style_name.lower()
    
    # 1. Standard Templates
    if s_lower == 'classic':
        return ClassicNewspaper(filename)
    
    elif s_lower == 'modern':
        return ModernNewspaper(filename)
        
    # 2. Magazine Templates
    # Check if the style_name matches any known magazine substyle
    # case-insensitive check against keys
    mag_keys_lower = {k.lower(): k for k in MAGAZINE_STYLES.keys()}
    
    if s_lower in mag_keys_lower:
        # It is a specific magazine substyle (e.g. "The Star")
        real_style_name = mag_keys_lower[s_lower]
        return VibrantMagazine(filename, style_name=real_style_name)
    
    elif s_lower == 'magazine':
        # Generic 'Magazine' request -> Default to 'The Star' or similar
        # Ideally the runner should have selected a substyle, but as fallback:
        return VibrantMagazine(filename, style_name='The Star')
        
    # 3. Fallback
    else:
        print(f"[Factory] Warning: Unknown style '{style_name}'. Defaulting to Classic.")
        return ClassicNewspaper(filename)
