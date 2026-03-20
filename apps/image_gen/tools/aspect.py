"""
Prompt Analyzer - Aspect Ratio Detection
=========================================

Analyzes prompts to determine the best aspect ratio.
Returns width and height based on keywords in the prompt.

Aspect Ratios:
    - normal:    512x512   (1:1)  - Default for objects, scenes
    - portrait:  512x768   (2:3)  - Vertical, people, characters
    - landscape: 768x512   (3:2)  - Horizontal, environments, wide shots

Usage:
    from apps.image_gen.tools.aspect import detect_aspect, get_dimensions
    
    width, height = detect_aspect("a portrait of a woman")  # Returns (512, 768)
    width, height = detect_aspect("wide landscape sunset")   # Returns (768, 512)
"""

from typing import Tuple, Literal

# Aspect ratio dimensions
ASPECT_RATIOS = {
    "normal":    (512, 512),   # 1:1 - Square
    "portrait":  (512, 768),   # 2:3 - Vertical
    "landscape": (768, 512),   # 3:2 - Horizontal
}

# Keywords that suggest portrait orientation (tall/vertical)
PORTRAIT_KEYWORDS = [
    # People/Characters
    "portrait", "person", "woman", "man", "girl", "boy", "face", "character",
    "standing", "full body", "fullbody", "full-body", "figure", "model",
    "selfie", "headshot", "bust", "torso", "solo",
    
    # Vertical compositions
    "tall", "vertical", "tower", "skyscraper", "building", "tree",
    "waterfall", "cliff", "lighthouse", "rocket", "sword", "staff",
    
    # Photography terms
    "close-up", "closeup", "close up", "upper body", "upper-body",
    "half body", "half-body", "cowboy shot", "medium shot",
]

# Keywords that suggest landscape orientation (wide/horizontal)
LANDSCAPE_KEYWORDS = [
    # Environments
    "landscape", "panorama", "panoramic", "wide shot", "wideshot", "wide-shot",
    "horizon", "skyline", "cityscape", "seascape", "mountainscape",
    
    # Scenes
    "scene", "environment", "background", "vista", "view", "scenery",
    "field", "ocean", "sea", "beach", "desert", "plains", "valley",
    
    # Wide compositions
    "wide", "horizontal", "banner", "cinematic", "establishing shot",
    "aerial", "birds eye", "bird's eye", "overhead", "drone",
    "room", "interior", "exterior", "architecture",
    
    # Multiple subjects
    "group", "crowd", "army", "horde", "battle", "war", "many",
]


def detect_aspect(prompt: str) -> Tuple[int, int]:
    """
    Analyze prompt and return best width and height.
    
    Args:
        prompt: The generation prompt
        
    Returns:
        Tuple of (width, height)
    
    Examples:
        detect_aspect("a beautiful woman portrait") -> (512, 768)
        detect_aspect("panoramic sunset over ocean") -> (768, 512)
        detect_aspect("a red apple")                 -> (512, 512)
    """
    prompt_lower = prompt.lower()
    
    # Count keyword matches
    portrait_score = sum(1 for kw in PORTRAIT_KEYWORDS if kw in prompt_lower)
    landscape_score = sum(1 for kw in LANDSCAPE_KEYWORDS if kw in prompt_lower)
    
    # Determine aspect ratio
    if portrait_score > landscape_score:
        return ASPECT_RATIOS["portrait"]
    elif landscape_score > portrait_score:
        return ASPECT_RATIOS["landscape"]
    else:
        return ASPECT_RATIOS["normal"]


def get_aspect_name(prompt: str) -> Literal["normal", "portrait", "landscape"]:
    """
    Get the aspect ratio name from a prompt.
    
    Args:
        prompt: The generation prompt
        
    Returns:
        One of: "normal", "portrait", "landscape"
    """
    prompt_lower = prompt.lower()
    
    portrait_score = sum(1 for kw in PORTRAIT_KEYWORDS if kw in prompt_lower)
    landscape_score = sum(1 for kw in LANDSCAPE_KEYWORDS if kw in prompt_lower)
    
    if portrait_score > landscape_score:
        return "portrait"
    elif landscape_score > portrait_score:
        return "landscape"
    else:
        return "normal"


def get_dimensions(aspect: Literal["normal", "portrait", "landscape"]) -> Tuple[int, int]:
    """
    Get dimensions for a specific aspect ratio.
    
    Args:
        aspect: One of "normal", "portrait", "landscape"
        
    Returns:
        Tuple of (width, height)
    """
    return ASPECT_RATIOS.get(aspect, ASPECT_RATIOS["normal"])


def analyze_prompt(prompt: str) -> dict:
    """
    Full prompt analysis returning all detection info.
    
    Args:
        prompt: The generation prompt
        
    Returns:
        Dict with aspect, width, height, and scores
    """
    prompt_lower = prompt.lower()
    
    portrait_score = sum(1 for kw in PORTRAIT_KEYWORDS if kw in prompt_lower)
    landscape_score = sum(1 for kw in LANDSCAPE_KEYWORDS if kw in prompt_lower)
    
    if portrait_score > landscape_score:
        aspect = "portrait"
    elif landscape_score > portrait_score:
        aspect = "landscape"
    else:
        aspect = "normal"
    
    width, height = ASPECT_RATIOS[aspect]
    
    return {
        "aspect": aspect,
        "width": width,
        "height": height,
        "portrait_score": portrait_score,
        "landscape_score": landscape_score,
        "detected_keywords": {
            "portrait": [kw for kw in PORTRAIT_KEYWORDS if kw in prompt_lower],
            "landscape": [kw for kw in LANDSCAPE_KEYWORDS if kw in prompt_lower],
        }
    }


# Quick test
if __name__ == "__main__":
    test_prompts = [
        "a beautiful woman in a red dress, portrait photography",
        "wide panoramic view of mountains at sunset, landscape",
        "a red apple on a table",
        "full body character design of a knight",
        "cinematic wide shot of a battle scene",
    ]
    
    for p in test_prompts:
        result = analyze_prompt(p)
        print(f"\nPrompt: {p[:50]}...")
        print(f"  Aspect: {result['aspect']} ({result['width']}x{result['height']})")
        print(f"  Scores: portrait={result['portrait_score']}, landscape={result['landscape_score']}")
