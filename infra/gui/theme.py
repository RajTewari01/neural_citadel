# Theme System for Neural Citadel PyQt V3
# Light mode: Light blue + pink mini bar, white main background
# Dark mode: Black + red mini bar, dark main background, Instagram colors for collapsed orb

from dataclasses import dataclass
from typing import Dict


@dataclass
class Theme:
    """Color theme definition"""
    name: str
    
    # Main window
    bg_dark: str
    bg_panel: str
    text_primary: str
    border_color: str
    
    # Accents
    accent_1: str
    accent_2: str
    accent_3: str
    
    # Mini bar collapsed
    orb_gradient_start: str
    orb_gradient_end: str
    orb_border: str
    
    # Mini bar expanded
    bar_gradient_start: str
    bar_gradient_mid: str
    bar_gradient_end: str
    bar_text: str
    bar_input_bg: str
    bar_button_bg: str


# Dark Mode Theme (default)
DARK_THEME = Theme(
    name="dark",
    
    # Main window - pure black with Instagram accents
    bg_dark="#000000",
    bg_panel="#0a0a0a",
    text_primary="#ffffff",
    border_color="#1a1a1a",
    
    # Instagram gradient accents
    accent_1="#833AB4",  # Purple
    accent_2="#E1306C",  # Pink
    accent_3="#F77737",  # Orange
    
    # Mini bar collapsed - Instagram gradient (purple → pink)
    orb_gradient_start="#833AB4",  # Instagram purple
    orb_gradient_end="#E1306C",    # Instagram pink
    orb_border="rgba(255, 255, 255, 0.3)",
    
    # Mini bar expanded - Instagram colors + Black
    bar_gradient_start="rgba(10, 10, 15, 0.95)",
    bar_gradient_mid="rgba(15, 10, 20, 0.95)",
    bar_gradient_end="rgba(10, 10, 15, 0.95)",
    bar_text="#ffffff",
    bar_input_bg="rgba(30, 25, 35, 0.8)",
    bar_button_bg="#E1306C",  # Instagram pink
)

# Light Mode Theme
LIGHT_THEME = Theme(
    name="light",
    
    # Main window - warm pastel backgrounds
    bg_dark="#FFF0F0",       # Very light coral/pink
    bg_panel="#FFF8F8",      # Warm white panel
    text_primary="#4a3535",  # Warm dark brown text
    border_color="#E8C8C8",  # Light coral border
    
    # Warm pastel accents (light red, purple, orange)
    accent_1="#E88B8B",  # Light coral/red
    accent_2="#C49BD6",  # Light purple/lavender  
    accent_3="#F4A460",  # Sandy orange/peach
    
    # Mini bar collapsed - Light blue + Light pink (as requested)
    orb_gradient_start="#7EC8E3",  # Light blue
    orb_gradient_end="#FFB6C1",    # Light pink
    orb_border="rgba(255, 255, 255, 0.7)",
    
    # Mini bar expanded - Light blue + pink gradient (as requested)
    bar_gradient_start="rgba(126, 200, 227, 0.95)",
    bar_gradient_mid="rgba(184, 169, 201, 0.95)",
    bar_gradient_end="rgba(255, 182, 193, 0.95)",
    bar_text="#333333",
    bar_input_bg="rgba(255, 255, 255, 0.5)",
    bar_button_bg="#7EC8E3",  # Light blue
)


# Global theme manager
class ThemeManager:
    _current_theme: Theme = DARK_THEME
    _listeners = []
    
    @classmethod
    def get_theme(cls) -> Theme:
        return cls._current_theme
    
    @classmethod
    def set_theme(cls, theme: Theme):
        cls._current_theme = theme
        for listener in cls._listeners:
            listener(theme)
    
    @classmethod
    def toggle_theme(cls):
        if cls._current_theme.name == "dark":
            cls.set_theme(LIGHT_THEME)
        else:
            cls.set_theme(DARK_THEME)
        return cls._current_theme
    
    @classmethod
    def is_dark_mode(cls) -> bool:
        return cls._current_theme.name == "dark"
    
    @classmethod
    def add_listener(cls, callback):
        cls._listeners.append(callback)
    
    @classmethod
    def remove_listener(cls, callback):
        if callback in cls._listeners:
            cls._listeners.remove(callback)
