"""
Horror Pipeline - Dark Horror & Dread Image Generation
=======================================================

Pipeline for generating horror-themed images optimized for the majicMIX Horror checkpoint.
Based on CivitAI prompts from model 49216.

Features:
    - Multiple shot types (portrait, character, scene, landscape)
    - Horror-specific prompt templates
    - Optimized negative prompts for horror art
    - Auto-detection of shot type from prompt

Usage:
    from apps.image_gen.pipeline.horror import get_horror_config
    config = get_horror_config("vampire in gothic castle")
"""

from pathlib import Path
from typing import Optional, Literal
import sys

# Add project root to path
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from configs.paths import (
    IMAGE_GEN_OUTPUT_DIR,
    MODEL_HORROR
)

from apps.image_gen.pipeline.pipeline_types import PipelineConfigs, LoraConfig
from apps.image_gen.pipeline.registry import register_pipeline

# Output Path
GENERATED_OUTPUT = IMAGE_GEN_OUTPUT_DIR / "horror"
GENERATED_OUTPUT.mkdir(parents=True, exist_ok=True)

# =============================================================================
# TEMPLATES - Based on CivitAI majicMIX Horror prompts
# =============================================================================

# Portrait - close-up glamour horror
PORTRAIT_TEMPLATE = (
    "horror art, dread, {prompt}, "
    "(glamour portrait:1.3), (close-up:1.2), creepy, eerie, "
    "dramatic lighting, unity 8k wallpaper, ultra detailed, "
    "masterpiece, best quality, cinematic"
)

# Character - full body horror character
CHARACTER_TEMPLATE = (
    "horror art, dread, {prompt}, "
    "extremely detailed, dynamic angle, "
    "the most beautiful form of chaos, elegant, vivid colours, "
    "masterpiece, best quality, 8k, cinematic"
)

# Scene - environmental horror
SCENE_TEMPLATE = (
    "horror art, dread, {prompt}, "
    "creepy eerie, horror, scary, frightening, ghastly, "
    "photorealistic, wide angle shot, intricate, "
    "masterpiece, best quality, ultra detailed, 8k"
)

# Landscape - wide horror panorama
LANDSCAPE_TEMPLATE = (
    "{prompt}, "
    "horror art, dread, atmospheric, haunted, "
    "(panorama:1.2), (wide shot:1.2), "
    "unity 8k wallpaper, masterpiece, best quality"
)

# Action - dynamic horror shots
ACTION_TEMPLATE = (
    "horror art, dread, {prompt}, "
    "(action shot:1.3), (dynamic movement:1.2), "
    "terrifying, unnerving, unsettling, "
    "80mm, horror lighting, masterpiece, best quality, ultra detailed"
)

# =============================================================================
# NEGATIVE PROMPTS - From CivitAI horror model examples
# =============================================================================

HORROR_NEGATIVE = (
    "ng_deepnegative_v1_75t, badhandv4, "
    "(worst quality:2), (low quality:2), (normal quality:2), lowres, "
    "bad anatomy, bad hands, normal quality, ((monochrome)), ((grayscale)), "
    "cartoon, anime, sketch, watermark"
)

# Shot type definitions
ShotType = Literal["portrait", "character", "scene", "landscape", "action"]


def _detect_shot_type(prompt: str) -> ShotType:
    """Detect shot type from prompt keywords."""
    prompt_lower = prompt.lower()
    
    portrait_keywords = [
        "close-up", "closeup", "portrait", "face", "glamour", "headshot",
        "bust", "detailed face", "eyes"
    ]
    action_keywords = [
        "action", "running", "chasing", "fighting", "dynamic", "movement",
        "attack", "jumping", "flying"
    ]
    landscape_keywords = [
        "panorama", "wide", "landscape", "vista", "distant", "horizon",
        "sky", "cityscape", "establishing"
    ]
    scene_keywords = [
        "room", "hallway", "tunnel", "corridor", "mansion", "castle",
        "graveyard", "cemetery", "forest", "ruins", "abandoned", "haunted",
        "interior", "environment"
    ]
    
    # Score each type
    for kw in portrait_keywords:
        if kw in prompt_lower:
            return "portrait"
    for kw in action_keywords:
        if kw in prompt_lower:
            return "action"
    for kw in landscape_keywords:
        if kw in prompt_lower:
            return "landscape"
    for kw in scene_keywords:
        if kw in prompt_lower:
            return "scene"
    
    return "character"  # default for horror characters


@register_pipeline(
    name="horror",
    keywords=["horror", "scary", "dread", "vampire", "creepy", "terrifying",
              "nightmare", "dark", "frightening", "ghastly", "unnerving"],
    description="Dark horror and dread image generation with majicMIX Horror",
    types={
        "portrait": "Close-up glamour horror portrait",
        "character": "Full body horror character",
        "scene": "Environmental horror scene",
        "landscape": "Wide horror panorama",
        "action": "Dynamic action horror shot"
    }
)
def get_horror_config(
        prompt: str,
        shot_type: Optional[ShotType] = None,
        auto_detect: bool = True
) -> PipelineConfigs:
    """
    Get Horror pipeline configuration.
    
    Args:
        prompt: Your horror scene description
        shot_type: "portrait", "character", "scene", "landscape", or "action"
        auto_detect: If True, detect shot type from prompt
        
    Returns:
        PipelineConfigs ready for engine.generate()
    """
    
    # Auto-detect type if not specified
    if auto_detect and shot_type is None:
        shot_type = _detect_shot_type(prompt)
    elif shot_type is None:
        shot_type = "character"
    
    # Configure based on shot type
    if shot_type == "portrait":
        print(f"[Horror] Mode: PORTRAIT (glamour horror close-up)")
        template = PORTRAIT_TEMPLATE
        width, height = 512, 768
    elif shot_type == "action":
        print(f"[Horror] Mode: ACTION (dynamic horror)")
        template = ACTION_TEMPLATE
        width, height = 768, 768
    elif shot_type == "landscape":
        print(f"[Horror] Mode: LANDSCAPE (wide horror panorama)")
        template = LANDSCAPE_TEMPLATE
        width, height = 960, 540
    elif shot_type == "scene":
        print(f"[Horror] Mode: SCENE (environmental horror)")
        template = SCENE_TEMPLATE
        width, height = 768, 768
    else:  # character
        print(f"[Horror] Mode: CHARACTER (full body horror)")
        template = CHARACTER_TEMPLATE
        width, height = 576, 768
    
    # Build final prompt
    final_prompt = template.format(prompt=prompt)

    return PipelineConfigs(
        base_model=MODEL_HORROR,
        output_dir=GENERATED_OUTPUT,
        prompt=final_prompt,
        neg_prompt=HORROR_NEGATIVE,
        vae="realistic",  # ft_mse VAE works well for horror
        style_type="realistic",  # Auto-selects R-ESRGAN 4x+
        embeddings=[],
        scheduler_name="dpm++_2m_karras",  # Most common in CivitAI examples
        width=width,
        height=height,
        steps=23,  # Model works well at 20 steps
        cfg=7.0,
        lora=[],
        c_net=[],
    )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def horror_portrait(prompt: str, **kwargs) -> PipelineConfigs:
    """Close-up horror glamour portrait."""
    return get_horror_config(prompt, shot_type="portrait", **kwargs)

def horror_character(prompt: str, **kwargs) -> PipelineConfigs:
    """Full body horror character."""
    return get_horror_config(prompt, shot_type="character", **kwargs)

def horror_scene(prompt: str, **kwargs) -> PipelineConfigs:
    """Environmental horror scene."""
    return get_horror_config(prompt, shot_type="scene", **kwargs)

def horror_landscape(prompt: str, **kwargs) -> PipelineConfigs:
    """Wide horror panorama."""
    return get_horror_config(prompt, shot_type="landscape", **kwargs)

def horror_action(prompt: str, **kwargs) -> PipelineConfigs:
    """Dynamic action horror shot."""
    return get_horror_config(prompt, shot_type="action", **kwargs)


if __name__ == "__main__":
    print("Testing horror pipeline configurations...")
    
    test_cases = [
        ("vampire portrait with glowing red eyes",),
        ("terrifying ghost chasing through dark tunnel",),
        ("haunted mansion at midnight",),
        ("horror landscape with blood moon",),
    ]
    
    for (prompt,) in test_cases:
        print(f"\n{'='*60}")
        print(f"Prompt: {prompt[:50]}...")
        config = get_horror_config(prompt)
        print(f"  Model: {config.base_model.name}")
        print(f"  Size: {config.width}x{config.height}")
        print(f"  Steps: {config.steps}")
        print("  ✅ OK")
