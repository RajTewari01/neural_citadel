"""
Space / Sci-Fi Pipeline
=======================

Deep space and cosmic scene generation with cinematic quality.

Model: deepSpaceDiffusion_v1.ckpt
Best for: Space scenes, sci-fi, cosmic, galaxies, nebulae, spaceships, planets

Features:
- Auto-detection with space/sci-fi keywords
- Landscape and ultra-wide aspect ratios (best for space scenes)
- Optimized settings for cosmic imagery
"""

import re
from pathlib import Path
from typing import Literal, Optional
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from configs.paths import DIFFUSION_MODELS, IMAGE_GEN_OUTPUT_DIR
from apps.image_gen.pipeline.pipeline_types import PipelineConfigs
from apps.image_gen.pipeline.registry import register_pipeline


# =============================================================================
# MODEL CONFIGURATION
# =============================================================================

SPACE_MODEL = DIFFUSION_MODELS["deep_space"]

# Optimized settings for space scenes
SPACE_SETTINGS = {
    "steps": 25,
    "cfg": 7.5,
    "scheduler": "euler_a",  # Fast and creative for space scenes
}


# =============================================================================
# PROMPT TEMPLATES
# =============================================================================

SPACE_TEMPLATE = (
    "{prompt}, "
    "deep space, cosmic, nebula, stars, galaxies, "
    "sci-fi, cinematic lighting, 8k, masterpiece, ultra detailed, "
    "volumetric lighting, god rays, epic scale"
)

SPACE_NEGATIVE = (
    "(worst quality:2), (low quality:2), blurry, pixelated, "
    "cartoon, anime, drawing, painting, "
    "earth surface, ground, buildings, people, faces, "
    "text, watermark, signature, logo"
)


# =============================================================================
# ASPECT RATIOS - Optimized for 4GB VRAM (max 768 on any side)
# =============================================================================

ASPECT_RATIOS = {
    "landscape": (768, 512),      # 3:2 - Standard landscape
    "wide": (768, 432),           # 16:9 - Cinematic wide
    "ultrawide": (768, 384),      # 2:1 - Ultra wide panorama
    "square": (512, 512),         # 1:1 - Social media
    "portrait": (512, 768),       # 2:3 - Vertical (rare for space)
}

AspectType = Literal["landscape", "wide", "ultrawide", "square", "portrait"]


# =============================================================================
# SCENE TYPE DETECTION
# =============================================================================

def _detect_scene_type(prompt: str) -> str:
    """
    Detect specific space scene type for enhanced prompting.
    """
    prompt_lower = prompt.lower()
    
    scene_keywords = {
        "nebula": ["nebula", "cloud", "gas", "dust", "colorful", "orion", "crab", "pillars"],
        "galaxy": ["galaxy", "milky way", "andromeda", "spiral", "elliptical", "stars"],
        "planet": ["planet", "mars", "jupiter", "saturn", "rings", "moon", "lunar", "surface"],
        "spaceship": ["spaceship", "spacecraft", "ship", "vessel", "starship", "cruiser", "fighter"],
        "astronaut": ["astronaut", "spacewalk", "eva", "suit", "floating", "zero gravity"],
        "blackhole": ["black hole", "blackhole", "singularity", "event horizon", "warp"],
        "station": ["station", "orbital", "habitat", "colony", "dock", "bay"],
        "alien": ["alien", "extraterrestrial", "otherworldly", "strange", "exotic"],
        "star": ["star", "sun", "solar", "corona", "flare", "supernova", "explosion"],
    }
    
    # Score each scene type
    scores = {scene: 0 for scene in scene_keywords}
    
    for scene, keywords in scene_keywords.items():
        for kw in keywords:
            if kw in prompt_lower:
                scores[scene] += 1
    
    # Return best match or "general"
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"


def _detect_aspect(prompt: str) -> tuple[str, int, int]:
    """
    Detect best aspect ratio from prompt.
    Defaults to wide for space scenes.
    """
    prompt_lower = prompt.lower()
    
    # Explicit aspect mentions
    if re.search(r'\b(ultrawide|anamorphic|2\.4:1|cinematic)\b', prompt_lower):
        return ("ultrawide", *ASPECT_RATIOS["ultrawide"])
    if re.search(r'\b(wide|panorama|2:1)\b', prompt_lower):
        return ("wide", *ASPECT_RATIOS["wide"])
    if re.search(r'\b(16:9|landscape|desktop)\b', prompt_lower):
        return ("landscape", *ASPECT_RATIOS["landscape"])
    if re.search(r'\b(square|1:1|instagram)\b', prompt_lower):
        return ("square", *ASPECT_RATIOS["square"])
    if re.search(r'\b(portrait|vertical|phone|9:16)\b', prompt_lower):
        return ("portrait", *ASPECT_RATIOS["portrait"])
    
    # Default to wide for space (most epic look)
    return ("wide", *ASPECT_RATIOS["wide"])


# =============================================================================
# SCENE-SPECIFIC ENHANCEMENTS
# =============================================================================

SCENE_ENHANCEMENTS = {
    "nebula": "colorful gas clouds, cosmic dust, stellar nursery, ethereal glow, ",
    "galaxy": "billions of stars, spiral arms, cosmic scale, deep field, ",
    "planet": "planetary surface, atmospheric haze, orbital view, alien world, ",
    "spaceship": "sleek design, engine glow, hull details, space dock, ",
    "astronaut": "space suit, helmet reflection, tether, earth in background, ",
    "blackhole": "gravitational lensing, accretion disk, warped light, extreme gravity, ",
    "station": "modular structure, solar panels, docking bay, rotating habitat, ",
    "alien": "bioluminescent, strange geometry, exotic colors, otherworldly, ",
    "star": "plasma surface, solar flares, corona, stellar wind, ",
    "general": "",
}


# =============================================================================
# MAIN CONFIG FUNCTION
# =============================================================================

@register_pipeline(
    name="space",
    keywords=["space", "galaxy", "nebula", "planet", "spaceship", "sci-fi", "cosmic",
              "stars", "astronaut", "black hole", "orbital", "alien world"],
    description="Deep space and cosmic scene generation with cinematic quality",
    types={}
)
def get_space_config(
        prompt: str,
        aspect: Optional[AspectType] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        enhance_scene: bool = True,
) -> PipelineConfigs:
    """
    Get Space/Sci-Fi pipeline configuration.
    
    Args:
        prompt: Your space scene description
        aspect: "landscape", "wide", "ultrawide", "square", or "portrait"
        width: Override width
        height: Override height
        enhance_scene: Add scene-specific enhancements to prompt
        
    Returns:
        PipelineConfigs ready for engine.generate()
    """
    
    # Detect scene type
    scene_type = _detect_scene_type(prompt)
    print(f"🚀 Space Mode: {scene_type.upper()} scene")
    
    # Aspect ratio / dimensions
    if width is None or height is None:
        if aspect is not None:
            width, height = ASPECT_RATIOS.get(aspect, ASPECT_RATIOS["wide"])
            print(f"📐 Aspect: {aspect} ({width}x{height})")
        else:
            detected_aspect, width, height = _detect_aspect(prompt)
            print(f"📐 Auto-detected: {detected_aspect} ({width}x{height})")
    
    # Build enhanced prompt
    enhancement = SCENE_ENHANCEMENTS.get(scene_type, "") if enhance_scene else ""
    
    final_prompt = SPACE_TEMPLATE.format(
        prompt=f"{enhancement}{prompt}"
    )
    
    # Output directory
    output_dir = IMAGE_GEN_OUTPUT_DIR / "space" / scene_type
    output_dir.mkdir(parents=True, exist_ok=True)
    
    return PipelineConfigs(
        base_model=SPACE_MODEL,
        output_dir=output_dir,
        prompt=final_prompt,
        style_type="realistic",  # Auto-selects R-ESRGAN 4x+
        
        scheduler_name=SPACE_SETTINGS["scheduler"],
        
        neg_prompt=SPACE_NEGATIVE,
        
        width=width,
        height=height,
        steps=SPACE_SETTINGS["steps"],
        cfg=SPACE_SETTINGS["cfg"],
    )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def space_nebula(prompt: str, **kwargs) -> PipelineConfigs:
    """Generate nebula/gas cloud scenes."""
    return get_space_config(f"nebula {prompt}", **kwargs)


def space_galaxy(prompt: str, **kwargs) -> PipelineConfigs:
    """Generate galaxy scenes."""
    return get_space_config(f"galaxy {prompt}", **kwargs)


def space_planet(prompt: str, **kwargs) -> PipelineConfigs:
    """Generate planetary scenes."""
    return get_space_config(f"planet {prompt}", **kwargs)


def space_spaceship(prompt: str, **kwargs) -> PipelineConfigs:
    """Generate spaceship/vehicle scenes."""
    return get_space_config(f"spaceship {prompt}", **kwargs)


def space_cinematic(prompt: str, **kwargs) -> PipelineConfigs:
    """Ultra-wide cinematic space scene."""
    return get_space_config(prompt, aspect="ultrawide", **kwargs)


def space_panorama(prompt: str, **kwargs) -> PipelineConfigs:
    """Wide panoramic space scene."""
    return get_space_config(prompt, aspect="wide", **kwargs)


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("Testing space pipeline detection...\n")
    
    test_prompts = [
        "colorful nebula with stars and cosmic dust",
        "massive spiral galaxy with billions of stars",
        "alien planet with rings and multiple moons",
        "sleek spaceship approaching space station",
        "astronaut floating in zero gravity, earth below",
        "black hole with accretion disk, warped starlight",
        "epic ultrawide cinematic space battle",
    ]
    
    for prompt in test_prompts:
        print(f"\n📝 Prompt: {prompt[:50]}...")
        config = get_space_config(prompt)
        print(f"   Model: {config.base_model.name}")
        print(f"   Size: {config.width}x{config.height}")
        print(f"   Steps: {config.steps}, CFG: {config.cfg}")
