"""
Ghost Pipeline - Realistic Ghost/Spirit Image Generation
=========================================================

Pipeline for generating realistic ghost, spirit, and supernatural images
using the GhostMix model with optimized settings.

Features:
    - Automatic aspect ratio detection (portrait/landscape/normal)
    - ControlNet support (canny, depth, openpose)
    - Prompt enhancement from CivitAI data
    - Configurable shot types (close-up, mid, wide)

Usage:
    from apps.image_gen.pipeline.ghost import get_config
    
    config = get_config(prompt="a ghostly figure in a dark hallway")
"""

from pathlib import Path
from typing import Optional, Literal
import sys

# Add project root to path
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from configs.paths import (
    MODELS_DIR, 
    IMAGE_GEN_OUTPUT_DIR, 
    CONTROLNET_MODELS,
    get_controlnet_path,
    MODEL_GHOSTMIX
)

# Import PipelineConfigs using full path to avoid conflict with builtin types
from apps.image_gen.pipeline.pipeline_types import PipelineConfigs, LoraConfig, ControlNetConfig
from apps.image_gen.pipeline.registry import register_pipeline

# Try to import tools (optional enhancement)
try:
    from ..tools import detect_aspect, enhance_prompt
    HAS_TOOLS = True
except ImportError:
    HAS_TOOLS = False


# =============================================================================
# PATHS
# =============================================================================

MODEL_GHOSTMIX = MODEL_GHOSTMIX
GENERATED_GHOST = IMAGE_GEN_OUTPUT_DIR / "ghost"


# =============================================================================
# ASPECT RATIOS
# =============================================================================

ASPECT_RATIOS = {
    "normal":    (512, 512),   # Square - objects, icons
    "portrait":  (512, 768),   # Vertical - characters, people
    "landscape": (768, 512),   # Horizontal - scenes, environments
}


# =============================================================================
# PROMPT TEMPLATES
# =============================================================================

# Close-up ghost portrait
CLOSE_UP_TEMPLATE = (
    "{trigger}, {prompt}, "
    "(detailed ghostly face:1.2), (ethereal glow:1.1), (translucent skin:1.1), "
    "(haunting eyes:1.2), (solo:1.3), (single spirit:1.2), "
    "(close-up portrait:1.2), volumetric fog, cinematic lighting, 8k, masterpiece"
)

# Mid-shot with environment
MID_SHOT_TEMPLATE = (
    "{trigger}, {prompt}, "
    "(ghostly figure:1.2), (medium shot:1.2), (ethereal presence:1.1), "
    "(haunted atmosphere:1.1), (misty environment:1.0), "
    "cinematic composition, 8k, masterpiece, horror movie still"
)

# Wide/environmental shot
WIDE_SHOT_TEMPLATE = (
    "{trigger}, {prompt}, "
    "(distant ghostly silhouette:1.1), (atmospheric fog:1.2), (haunted location:1.1), "
    "(wide shot:1.2), (establishing shot:1.1), "
    "volumetric lighting, cinematic, 8k, masterpiece, horror atmosphere"
)


# =============================================================================
# NEGATIVE PROMPTS
# =============================================================================

CLOSE_UP_NEGATIVE = (
    "(diptych:1.5), (split image:1.5), (collage:1.4), (multiple people:1.5), "
    "(crowd:1.4), (duplicate:1.3), blurry, haze, "
    "cartoon, anime, low quality, bad anatomy, deformed"
)

MID_SHOT_NEGATIVE = (
    "(overlapping bodies:1.4), (fused together:1.4), (clipping:1.3), "
    "diptych, split image, collage, blur, "
    "cartoon, anime, low quality, bad anatomy, deformed"
)

WIDE_SHOT_NEGATIVE = (
    "(overlapping:1.4), (close-up:1.3), (detailed faces:1.2), "
    "blur, cartoon, anime, low quality, bad anatomy"
)


# =============================================================================
# SHOT TYPE DETECTION
# =============================================================================

def _detect_shot_type(prompt: str) -> Literal["close", "mid", "wide"]:
    """
    Detect shot type from prompt keywords.
    
    Returns: "close", "mid", or "wide"
    """
    prompt_lower = prompt.lower()
    
    close_keywords = [
        "close-up", "closeup", "portrait", "face", "detailed", 
        "head", "bust", "solo", "single", "eyes"
    ]
    
    wide_keywords = [
        "wide", "panorama", "landscape", "scene", "environment",
        "establishing", "distant", "silhouette", "hallway", "room",
        "house", "mansion", "castle", "cemetery", "graveyard"
    ]
    
    # Check keywords
    close_score = sum(1 for kw in close_keywords if kw in prompt_lower)
    wide_score = sum(1 for kw in wide_keywords if kw in prompt_lower)
    
    if close_score > wide_score:
        return "close"
    elif wide_score > close_score:
        return "wide"
    else:
        return "mid"


# =============================================================================
# MAIN CONFIG FUNCTION
# =============================================================================

@register_pipeline(
    name="ghost",
    keywords=["ghost", "spirit", "ethereal", "haunted", "spectral", "ghostly",
              "translucent", "paranormal", "apparition", "phantom"],
    description="Realistic ghost and spirit image generation with GhostMix model",
    types={}
)
def get_config(
    prompt: str,
    control_image: Optional[Path] = None,
    control_type: Optional[Literal["canny", "depth", "openpose"]] = None,
    aspect: Optional[Literal["normal", "portrait", "landscape"]] = None,
    shot_type: Optional[Literal["close", "mid", "wide"]] = None,
    use_enhancement: bool = True,
) -> PipelineConfigs:
    """
    Get ghost pipeline configuration.
    
    Args:
        prompt: User's prompt describing the ghost/spirit image
        control_image: Optional path to control image for ControlNet
        control_type: Type of ControlNet to use ("canny", "depth", "openpose")
        aspect: Force aspect ratio ("normal", "portrait", "landscape")
                If None, auto-detects from prompt
        shot_type: Force shot type ("close", "mid", "wide")
                   If None, auto-detects from prompt
        use_enhancement: Whether to enhance prompt with CivitAI data
    
    Returns:
        PipelineConfigs ready for the engine
    """
    
    # 1. Auto-detect aspect ratio if not specified
    if aspect is None and HAS_TOOLS:
        width, height = detect_aspect(prompt)
        if width == height:
            aspect = "normal"
        elif height > width:
            aspect = "portrait"
        else:
            aspect = "landscape"
    elif aspect is None:
        aspect = "portrait"  # Default for ghosts/characters
    
    width, height = ASPECT_RATIOS[aspect]
    
    # 2. Auto-detect shot type if not specified
    if shot_type is None:
        shot_type = _detect_shot_type(prompt)
    
    # 3. Select template based on shot type
    if shot_type == "close":
        print("[GHOST] Mode: CLOSE-UP (details, face)")
        template = CLOSE_UP_TEMPLATE
        negative = CLOSE_UP_NEGATIVE
        trigger = "ethereal ghost"
    elif shot_type == "wide":
        print("[GHOST] Mode: WIDE SHOT (environment, atmosphere)")
        template = WIDE_SHOT_TEMPLATE
        negative = WIDE_SHOT_NEGATIVE
        trigger = "haunted scene"
    else: # shot_type == "mid"
        print("[GHOST] Mode: MID-SHOT (figure + environment)")
        template = MID_SHOT_TEMPLATE
        negative = MID_SHOT_NEGATIVE
        trigger = "ghostly presence"
    
    # 4. Build final prompt
    final_prompt = template.format(trigger=trigger, prompt=prompt)
    
    # 5. Optional: Enhance with CivitAI data
    if use_enhancement and HAS_TOOLS:
        try:
            enhanced = enhance_prompt(prompt, width=width, height=height)
            # Merge quality boosters if available
            if enhanced.negative_prompt:
                negative = f"{negative}, {enhanced.negative_prompt}"
        except:
            pass  # Silently fail enhancement
    
    # 6. Handle ControlNet
    controlnets = []
    if control_image and control_type:
        if Path(control_image).exists():
            controlnets.append(
                ControlNetConfig(
                    control_type=control_type,
                    image_path=control_image,
                    scale=0.7  # Moderate control for ghostly effects
                )
            )
            print(f"   🎮 ControlNet: {control_type} enabled")
    
    # 7. Ensure output directory exists
    GENERATED_GHOST.mkdir(parents=True, exist_ok=True)
    
    # 8. Return config
    return PipelineConfigs(
        base_model=MODEL_GHOSTMIX,
        output_dir=GENERATED_GHOST,
        prompt=final_prompt,
        neg_prompt=negative,
        vae="realistic",  # Use realistic VAE for ghost details
        style_type="realistic",  # Auto-selects R-ESRGAN 4x+
        
        scheduler_name="euler_a",
        
        width=width,
        height=height,
        steps=30,
        cfg=7.0,
        
        lora=[],  # No LoRAs by default
        c_net=controlnets,
    )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def portrait_ghost(prompt: str, **kwargs) -> PipelineConfigs:
    """Quick config for portrait ghost shot."""
    return get_config(prompt, aspect="portrait", shot_type="close", **kwargs)


def scene_ghost(prompt: str, **kwargs) -> PipelineConfigs:
    """Quick config for wide haunted scene."""
    return get_config(prompt, aspect="landscape", shot_type="wide", **kwargs)


def ghost_with_canny(prompt: str, reference_image: Path, **kwargs) -> PipelineConfigs:
    """Ghost config with Canny ControlNet from reference image."""
    return get_config(
        prompt, 
        control_image=reference_image, 
        control_type="canny", 
        **kwargs
    )


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    # Test the pipeline config
    test_prompts = [
        "a ghostly woman in a white dress floating in a dark hallway",
        "close-up portrait of a spirit with glowing eyes",
        "wide shot of a haunted mansion with ghostly silhouettes",
    ]
    
    for p in test_prompts:
        print(f"\n{'='*60}")
        print(f"Prompt: {p[:50]}...")
        config = get_config(p)
        print(f"  Size: {config.width}x{config.height}")
        print(f"  Model: {config.base_model.name}")
        print(f"  Scheduler: {config.scheduler_name}")
