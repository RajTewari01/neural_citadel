"""
DiffusionBrush Pipeline - Detailed Digital Art Generation
=========================================================

Pipeline for generating high-fidelity digital art using the DiffusionBrush model.
Optimized for realistic textures, detailed compositions, and cinematic lighting.

Features:
    - Automatic aspect ratio detection (normal/portrait/landscape)
    - Shot type detection (close/mid/wide)
    - Integrated ControlNet support
    - Robust negative prompts for clean output
    - Prompt enhancement integration

Usage:
    from apps.image_gen.pipeline.diffusionbrush import get_config
    
    config = get_config(
        prompt="mystic forest with glowing mushrooms",
        aspect="landscape"
    )
"""

from pathlib import Path
from typing import Optional, Literal
import sys

# Add project root to path (adjusted to match ghost.py logic)
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from configs.paths import (
    MODELS_DIR,
    IMAGE_GEN_OUTPUT_DIR,
    get_controlnet_path,
    MODEL_DIFFUSIONBRUSH
)

from apps.image_gen.pipeline.pipeline_types import PipelineConfigs, ControlNetConfig
from apps.image_gen.pipeline.registry import register_pipeline

try:
    from ..tools import detect_aspect, enhance_prompt
    HAS_TOOLS = True
except ImportError:
    HAS_TOOLS = False

# Model and Output Paths
# Model and Output Paths
MODEL_DIFFUSIONBRUSH = MODEL_DIFFUSIONBRUSH
GENERATED_OUTPUT = IMAGE_GEN_OUTPUT_DIR / "diffusionbrush"

ASPECT_RATIOS = {
    "normal":    (512, 512),   # Square - objects, icons
    "portrait":  (512, 768),   # Vertical - characters, people
    "landscape": (768, 512),   # Horizontal - scenes, environments
}

# =============================================================================
# PROMPT TEMPLATES & STYLES (Derived from User Feedback)
# =============================================================================

COMMON_STYLE = "hyper realistic, 8k, epic composition, cinematic"

# Close-up: Focus on details, textures, and specific subjects
CLOSE_UP_TEMPLATE = (
    "{trigger}, {prompt}, "
    "(detailed close-up:1.2), (intricate texture:1.1), (macro photography:1.1), "
    "depth of field, soft lighting, " + COMMON_STYLE
)

# Mid-shot: Balanced composition of subject and surroundings
MID_SHOT_TEMPLATE = (
    "{trigger}, {prompt}, "
    "(medium shot:1.2), (balanced composition:1.1), "
    "dynamic lighting, volumetric fog, " + COMMON_STYLE
)

# Wide-shot: Scenery, landscapes, and atmosphere
WIDE_SHOT_TEMPLATE = (
    "{trigger}, {prompt}, "
    "(wide angle:1.2), (establishing shot:1.1), (panoramic view:1.1), "
    "atmospheric perspective, grand scale, " + COMMON_STYLE
)

# =============================================================================
# NEGATIVE PROMPTS (Robust Negatives from JSON)
# =============================================================================

COMMON_NEGATIVE = (
    "(((watermark, text, signature))), bad-picture-chill-75v, easynegative, "
    "greyscale, monochrome, bad anatomy, bad proportions, deformed, "
    "poorly drawn hands, extra fingers, extra limbs, blurry, low resolution, pixelated"
)

CLOSE_UP_NEGATIVE = (
    f"{COMMON_NEGATIVE}, ugly textures, out of focus, depth of field too shallow, "
    "distorted features, bad eyes, mutation"
)

MID_SHOT_NEGATIVE = (
    f"{COMMON_NEGATIVE}, awkward framing, flat lighting, boring composition, "
    "uninspired, floating limbs, disconnected parts"
)

WIDE_SHOT_NEGATIVE = (
    f"{COMMON_NEGATIVE}, repetitive patterns, tiling artifacts, distorted perspective, "
    "blurry horizon, empty space"
)


def _detect_shot_type(prompt: str) -> Literal["close", "mid", "wide"]:
    """
    Detect shot type from prompt keywords.
    
    Returns: "close", "mid", or "wide"
    """
    prompt_lower = prompt.lower()
    
    close_keywords = [
        "close-up", "closeup", "portrait", "face", "detailed", 
        "head", "bust", "solo", "single", "eyes", "macro"
    ]
    
    wide_keywords = [
        "wide", "panorama", "landscape", "scene", "environment",
        "establishing", "distant", "silhouette", "hallway", "room",
        "house", "mansion", "castle", "cemetery", "graveyard", "forest", "city", "ocean"
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
    

@register_pipeline(
    name="diffusionbrush",
    keywords=["diffusionbrush", "digital art", "painterly", "hyper realistic", 
              "cinematic", "epic composition", "concept art"],
    description="High-fidelity digital art with realistic textures and cinematic lighting",
    types={}
)
def get_config(
    prompt:str,
    control_image:Optional[Path]=None,
    control_type:Optional[Literal["canny","depth","openpose"]]=None,
    aspect:Optional[Literal["normal","portrait","landscape"]]=None,
    shot_type:Optional[Literal["close","mid","wide"]]=None,
    use_enhancement:bool=True,
) -> PipelineConfigs:
    """
    Get DiffusionBrush pipeline configuration.
    
    Args:
        prompt: User's image description
        control_image: Optional path for ControlNet input
        control_type: Type of ControlNet ("canny", etc.)
        aspect: Force aspect ratio ("normal", "portrait", "landscape")
        shot_type: Force shot type ("close", "mid", "wide")
        use_enhancement: Whether to use prompt enhancement tools
        
    Returns:
        PipelineConfigs object
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
        aspect = "landscape"  # Default for this general-purpose painterly model
    
    width, height = ASPECT_RATIOS[aspect]
    
    # 2. Auto-detect shot type if not specified
    if shot_type is None:
        shot_type = _detect_shot_type(prompt)
    
    # 3. Select template based on shot type
    if shot_type == "close":
        print("[DIFFUSIONBRUSH] Mode: CLOSE-UP (details, face)")
        template = CLOSE_UP_TEMPLATE
        negative = CLOSE_UP_NEGATIVE
        trigger = "detailed view"
    elif shot_type == "wide":
        print("[DIFFUSIONBRUSH] Mode: WIDE SHOT (environment, atmosphere)")
        template = WIDE_SHOT_TEMPLATE
        negative = WIDE_SHOT_NEGATIVE
        trigger = "medium shot,mid-shot"
    else: # shot_type == "mid"
        print("[DIFFUSIONBRUSH] Mode: MID-SHOT (figure + environment)")
        template = MID_SHOT_TEMPLATE
        negative = MID_SHOT_NEGATIVE
        trigger = "wide angle,ultra-wide angle"

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
                    scale=0.8  # Stronger control for brush style
                )
            )
            print(f"   🎮 ControlNet: {control_type} enabled")
    
    # 7. Ensure output directory exists
    try:
        if not GENERATED_OUTPUT.exists():
            GENERATED_OUTPUT.mkdir(parents=True, exist_ok=True)
    except:pass
    
    # 8. Return config
    return PipelineConfigs(
        base_model=MODEL_DIFFUSIONBRUSH,
        output_dir=GENERATED_OUTPUT,
        prompt=final_prompt,
        neg_prompt=negative,
        vae="realistic",  # Use realistic VAE
        style_type="realistic",  # Auto-selects R-ESRGAN 4x+
        
        scheduler_name="dpm++_2m_karras", # Optimized for painterly details
        
        width=width,
        height=height,
        steps=25,
        cfg=7.0,
        
        lora=[],
        c_net=controlnets,
    )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def portrait_brush(prompt: str, **kwargs) -> PipelineConfigs:
    """Quick config for portrait digital art."""
    return get_config(prompt, aspect="portrait", shot_type="close", **kwargs)


def landscape_brush(prompt: str, **kwargs) -> PipelineConfigs:
    """Quick config for landscape digital art."""
    return get_config(prompt, aspect="landscape", shot_type="wide", **kwargs)


def brush_with_canny(prompt: str, reference_image: Path, **kwargs) -> PipelineConfigs:
    """DiffusionBrush config with Canny ControlNet from reference image."""
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
    # Test the pipeline config with DiffusionBrush specific prompts
    test_prompts = [
        "a majestic cyberpunk city with neon lights and rain",
        "close-up portrait of a warrior with intricate armor details",
        "wide landscape of a fantasy kingdom with floating islands",
    ]
    
    for p in test_prompts:
        print(f"\n{'='*60}")
        print(f"Prompt: {p[:50]}...")
        config = get_config(p)
        print(f"  Size: {config.width}x{config.height}")
        print(f"  Model: {config.base_model.name}")
        print(f"  Scheduler: {config.scheduler_name}")
        print(f"  Shot Type Detected: {_detect_shot_type(p)}")