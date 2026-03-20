"""
Hyperrealistic Pipeline
=======================

Ultra-realistic human generation using top realistic checkpoints.

Models:
- Realistic Vision V6: Best for photorealistic humans
- DreamShaper 8: Versatile realistic/artistic balances
- NeverendingDream: High detail portraits
- Realistic Digital V6: Clean digital portraits
- Typhoon: Dramatic lighting

Features:
- Auto-model detection based on prompt style
- Optimized settings for photorealism
- Random model selection option
- 4GB VRAM safe resolutions
"""

import random
from pathlib import Path
from typing import Literal, Optional
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from configs.paths import (
    IMAGE_GEN_OUTPUT_DIR,
    DIFFUSION_MODELS
)
from apps.image_gen.pipeline.pipeline_types import PipelineConfigs
from apps.image_gen.pipeline.registry import register_pipeline


# =============================================================================
# MODEL CONFIGURATION
# =============================================================================

MODEL_MAP = {
    "realistic_vision": {
        "file": DIFFUSION_MODELS["realistic_vision"],
        "trigger": "",
        "description": "Realistic Vision V6 - Photorealistic humans",
        "steps": 25,
        "cfg": 7.0,
    },
    "dreamshaper": {
        "file": DIFFUSION_MODELS["dreamshaper"],
        "trigger": "",
        "description": "DreamShaper 8 - Versatile realism",
        "steps": 25,
        "cfg": 7.0,
    },
    "neverending": {
        "file": DIFFUSION_MODELS["neverending_dream"],
        "trigger": "",
        "description": "NeverendingDream - High detail",
        "steps": 25,
        "cfg": 7.0,
    },
    "digital": {
        "file": DIFFUSION_MODELS["realistic_digital"],
        "trigger": "",
        "description": "Realistic Digital V6 - Clean digital",
        "steps": 25,
        "cfg": 7.0,
    },
    "typhoon": {
        "file": DIFFUSION_MODELS["typhoon"],
        "trigger": "",
        "description": "Typhoon - Dramatic lighting",
        "steps": 25,
        "cfg": 6.0,
    },
}

ModelType = Literal["realistic_vision", "dreamshaper", "neverending", "digital", "typhoon"]


# =============================================================================
# PROMPT TEMPLATES
# =============================================================================

REALISTIC_TEMPLATE = (
    "{prompt}, "
    "photorealistic, hyperrealistic, ultra detailed skin texture, "
    "natural lighting, film grain, 8k uhd, dslr, soft lighting, "
    "high quality, masterpiece, sharp focus, professional photography, "
    "detailed eyes, realistic hair"
)

REALISTIC_NEGATIVE = (
    "(worst quality:2), (low quality:2), blurry, pixelated, "
    "anime, cartoon, drawing, painting, illustration, sketch, "
    "3d render, cgi, plastic skin, doll, mannequin, "
    "bad anatomy, deformed, ugly, missing limbs, extra limbs, "
    "bad hands, bad fingers, mutation, mutated, "
    "watermark, text, signature"
)


# =============================================================================
# ASPECT RATIOS - Optimized for 4GB VRAM (max 768px)
# =============================================================================

ASPECT_RATIOS = {
    "portrait": (512, 768),       # Standard portrait
    "landscape": (768, 512),      # Standard landscape
    "square": (512, 512),         # Square format
}

AspectType = Literal["portrait", "landscape", "square"]


# =============================================================================
# DETECTION FUNCTIONS
# =============================================================================

def _detect_model(prompt: str) -> ModelType:
    """Detect best model based on prompt keywords."""
    prompt_lower = prompt.lower()
    
    if "dream" in prompt_lower or "art" in prompt_lower:
        return "dreamshaper"
    if "digital" in prompt_lower or "clean" in prompt_lower:
        return "digital"
    if "dramatic" in prompt_lower or "cinematic" in prompt_lower:
        return "typhoon"
    if "detail" in prompt_lower or "intricate" in prompt_lower:
        return "neverending"
        
    return "realistic_vision"  # Default best


def _detect_aspect(prompt: str) -> tuple[str, int, int]:
    """Detect aspect ratio from prompt."""
    prompt_lower = prompt.lower()
    
    if "landscape" in prompt_lower or "wide" in prompt_lower or "scenery" in prompt_lower:
        return ("landscape", 768, 512)
    if "square" in prompt_lower or "icon" in prompt_lower:
        return ("square", 512, 512)
        
    # Default to portrait for humans
    return ("portrait", 512, 768)


# =============================================================================
# MAIN CONFIG FUNCTION
# =============================================================================

@register_pipeline(
    name="hyperrealistic",
    keywords=["hyperrealistic", "realistic", "photorealistic", "photo", "dreamshaper",
              "real person", "realistic vision", "typhoon", "neverending dream"],
    description="Ultra-realistic human generation using top realistic checkpoints",
    types={
        "realistic_vision": "Realistic Vision V6 - Photorealistic humans",
        "dreamshaper": "DreamShaper 8 - Versatile realism",
        "neverending": "NeverendingDream - High detail",
        "digital": "Realistic Digital V6 - Clean digital",
        "typhoon": "Typhoon - Dramatic lighting"
    }
)
def get_hyperrealistic_config(
        prompt: str,
        model: Optional[ModelType] = None,
        aspect: Optional[AspectType] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        random_model: bool = False,
) -> PipelineConfigs:
    """
    Get Hyperrealistic pipeline configuration.
    
    Args:
        prompt: Description of the human/scene
        model: Specific model or None for auto-detect
        aspect: "portrait", "landscape", or "square"
        width: Override width
        height: Override height
        random_model: If True, selects a random model
        
    Returns:
        PipelineConfigs ready for engine.generate()
    """
    
    # Model Selection
    if random_model:
        model = random.choice(list(MODEL_MAP.keys()))
        print(f"🎲 Random Hyperrealistic Model: {model}")
    elif model is None:
        model = _detect_model(prompt)
        print(f"🔍 Auto-detected Model: {model}")
        
    selected = MODEL_MAP[model]
    print(f"📸 Hyperrealistic Mode: {selected['description']}")
    
    # Aspect/Size
    if width is None or height is None:
        if aspect is not None:
            width, height = ASPECT_RATIOS.get(aspect, (512, 768))
        else:
            detected_aspect, width, height = _detect_aspect(prompt)
            print(f"📐 Detected Aspect: {detected_aspect} ({width}x{height})")
            
    # Build prompt
    final_prompt = REALISTIC_TEMPLATE.format(prompt=prompt)
    
    # Output directory
    output_dir = IMAGE_GEN_OUTPUT_DIR / "hyperrealistic" / model
    output_dir.mkdir(parents=True, exist_ok=True)
    
    return PipelineConfigs(
        base_model=selected["file"],
        output_dir=output_dir,
        prompt=final_prompt,
        style_type="realistic",  # Auto-selects R-ESRGAN 4x+
        
        # dpm++_2m_karras is best for realism but euler_a is safer for VRAM
        scheduler_name="dpm++_2m_karras", 
        
        neg_prompt=REALISTIC_NEGATIVE,
        
        width=width,
        height=height,
        steps=selected["steps"],
        cfg=selected["cfg"],
    )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def real_portrait(prompt: str, **kwargs) -> PipelineConfigs:
    """Generate realistic portrait."""
    return get_hyperrealistic_config(prompt, aspect="portrait", **kwargs)

def real_landscape(prompt: str, **kwargs) -> PipelineConfigs:
    """Generate realistic landscape/scene."""
    return get_hyperrealistic_config(prompt, aspect="landscape", **kwargs)

def real_random(prompt: str, **kwargs) -> PipelineConfigs:
    """Generate with random realistic model."""
    return get_hyperrealistic_config(prompt, random_model=True, **kwargs)


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("Testing hyperrealistic pipeline...\n")
    
    prompts = [
        "beautiful young woman with freckles, natural light",
        "cinematic dramatic lighting man in rain",
        "clean digital art style cyber woman",
        "dreamy intricate fantasy princess",
    ]
    
    for p in prompts:
        print(f"\n📝 Prompt: {p}")
        config = get_hyperrealistic_config(p)
        print(f"   Model: {config.base_model.name}")
        print(f"   Size: {config.width}x{config.height}")
