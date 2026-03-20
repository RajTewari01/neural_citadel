"""
Papercut / Origami Pipeline
============================

Two specialized models for creating papercut and origami style art:
- midjourney: Best for human figures, dragons, layered origami art (trigger: mdjrny-pprct)
- papercutcraft: Best for animals and creatures in origami style (trigger: Papercutcraft style)

Usage:
    from apps.image_gen.pipeline.papercut import get_papercut_config
    config = get_papercut_config("beautiful dragon origami", style="midjourney")
"""

from pathlib import Path
from typing import Optional, Literal
import sys,random

# Add project root to path
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from configs.paths import (
    IMAGE_GEN_OUTPUT_DIR,
    MODELS_DIR
)

from apps.image_gen.pipeline.pipeline_types import PipelineConfigs, LoraConfig
from apps.image_gen.pipeline.registry import register_pipeline

# Output Path
GENERATED_OUTPUT = IMAGE_GEN_OUTPUT_DIR / "papercut"
GENERATED_OUTPUT.mkdir(parents=True, exist_ok=True)

# Papercut model directory
PAPERCUT_DIR = MODELS_DIR / "diffusion" / "papercut"

# =============================================================================
# MODEL MAP - Two papercut models with trigger words
# =============================================================================

MODEL_MAP = {
    "midjourney": {
        "file": PAPERCUT_DIR / "midjourneyPapercut_v1.ckpt",
        "trigger": "mdjrny-pprct",
        "description": "Great for humans, dragons, layered origami art"
    },
    "papercutcraft": {
        "file": PAPERCUT_DIR / "papercutcraft_v1.ckpt",
        "trigger": "Papercutcraft style",
        "description": "Best for animals and creatures in origami style"
    },
}

# =============================================================================
# ASPECT RATIOS
# =============================================================================

ASPECT_RATIOS = {
    "portrait": (512, 768),
    "mid": (768, 768),
    "wide": (960, 540),
}

# =============================================================================
# TEMPLATES - Optimized for papercut/origami art
# =============================================================================

# Midjourney papercut template - for humans/dragons/layered art
MIDJOURNEY_TEMPLATE = (
    "{trigger}, {prompt}, "
    "masterpiece, best quality"
)

# Papercutcraft template - for animals/creatures
PAPERCUTCRAFT_TEMPLATE = (
    "{trigger}, {prompt}, "
    "masterpiece, best quality"
)

# Negative prompt for papercut art (from CivitAI)
PAPERCUT_NEGATIVE = (
    "(worst quality:1.2), (low quality:1.2), (normal quality:1.2), lowres, "
    "(frame:1.2), border,blurry"
)

# Style types
StyleType = Literal["midjourney", "papercutcraft"]
AspectType = Literal["portrait", "mid", "wide"]


def _detect_style(prompt: str) -> StyleType:
    """
    Detect which papercut model to use based on prompt keywords.
    Uses scoring system for better accuracy.
    - midjourney: humans, girls, women, dragons, people
    - papercutcraft: animals, creatures, birds, cats, dogs, etc.
    """
    import re
    prompt_lower = prompt.lower()
    
    # Human/dragon keywords with weights → midjourney
    midjourney_keywords = {
        # Strong human indicators (weight 2)
        "girl": 2, "woman": 2, "man": 2, "boy": 2, "lady": 2,
        "female": 2, "male": 2, "person": 2, "people": 2, "human": 2,
        "sexy": 2, "beautiful": 1, "portrait": 2, "face": 2,
        # Characters
        "geisha": 2, "samurai": 2, "warrior": 2, "knight": 2,
        "princess": 2, "queen": 2, "king": 2, "goddess": 2,
        "angel": 2, "demon": 2, "fairy": 1, "elf": 1, "wizard": 1,
        # Special
        "dragon": 2, "dragons": 2, "layered": 1, "layer": 1,
        "chinese": 1, "japanese": 1, "asian": 1,
    }
    
    # Animal keywords with weights → papercutcraft
    animal_keywords = {
        "animal": 3, "bird": 2, "cat": 2, "dog": 2, "fox": 2,
        "wolf": 2, "lion": 2, "tiger": 2, "elephant": 2,
        "rabbit": 2, "butterfly": 2, "fish": 2, "horse": 2,
        "deer": 2, "owl": 2, "eagle": 2, "swan": 2, "peacock": 2,
        "snake": 2, "frog": 2, "bear": 2, "panda": 2, "koala": 2,
        "creature": 1, "origami": 1,
    }
    
    # Calculate scores using word boundaries
    midjourney_score = 0
    papercutcraft_score = 0
    
    for keyword, weight in midjourney_keywords.items():
        # Use word boundary regex for accurate matching
        if re.search(rf'\b{keyword}\b', prompt_lower):
            midjourney_score += weight
    
    for keyword, weight in animal_keywords.items():
        if re.search(rf'\b{keyword}\b', prompt_lower):
            papercutcraft_score += weight
    
    # Return based on score
    if midjourney_score >= papercutcraft_score:
        return "midjourney"
    else:
        return "papercutcraft"


@register_pipeline(
    name="papercut",
    keywords=["papercut", "origami", "kirigami", "paper art", "paper craft",
              "scherenschnitte", "shadowbox", "silhouette", "layered paper"],
    description="Papercut and origami style art with specialized models",
    types={
        "midjourney": "Great for humans, dragons, layered origami art",
        "papercutcraft": "Best for animals and creatures in origami style"
    }
)
def get_papercut_config(
        prompt: str,
        style: Optional[StyleType] = None,
        aspect: Optional[AspectType] = "mid",
        auto_detect: bool = True
) -> PipelineConfigs:
    """
    Get Papercut/Origami pipeline configuration.
    
    Args:
        prompt: Your papercut art description
        style: "midjourney" (humans/dragons) or "papercutcraft" (animals)
        aspect: "portrait" (512x768), "mid" (768x768), or "wide" (960x540)
        auto_detect: If True, detect style from prompt keywords
        
    Returns:
        PipelineConfigs ready for engine.generate()
    """
    
    # Auto-detect style if not specified
    if auto_detect and style is None:
        style = _detect_style(prompt)
    elif style is None:
        style = "midjourney"
    
    # Get model info
    model_info = MODEL_MAP.get(style, MODEL_MAP["midjourney"])
    selected_model = model_info["file"]
    trigger = model_info["trigger"]
    
    # Select template
    if style == "papercutcraft":
        template = PAPERCUTCRAFT_TEMPLATE
    else:
        template = MIDJOURNEY_TEMPLATE
    
    # Get dimensions
    width, height = ASPECT_RATIOS.get(aspect, ASPECT_RATIOS["mid"])
    
    print(f"✂️ [Papercut] Style: {style.upper()} ({model_info['description']})")
    print(f"   Model: {selected_model.name}")
    print(f"   Trigger: {trigger}")
    print(f"   Aspect: {aspect} ({width}x{height})")
    
    # Build final prompt
    final_prompt = template.format(trigger=trigger, prompt=prompt)

    return PipelineConfigs(
        base_model=selected_model,
        output_dir=GENERATED_OUTPUT,
        prompt=final_prompt,
        neg_prompt=PAPERCUT_NEGATIVE,
        vae="realistic",  # ft_mse VAE works well
        style_type="realistic",  # Auto-selects R-ESRGAN 4x+
        embeddings=[],
        scheduler_name= 'dpm++_sde_karras',  # Euler a - most common in CivitAI, faster
        width=width,
        height=height,
        steps=25,  # From CivitAI (20-30 range)
        cfg=7.5,   # From CivitAI (7-9.5 range)
        lora=[],
        c_net=[],
    )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def papercut_human(prompt: str, **kwargs) -> PipelineConfigs:
    """Layered papercut art of humans/people."""
    return get_papercut_config(prompt, style="midjourney", **kwargs)

def papercut_dragon(prompt: str, **kwargs) -> PipelineConfigs:
    """Layered papercut art of dragons."""
    return get_papercut_config(prompt, style="midjourney", **kwargs)

def papercut_animal(prompt: str, **kwargs) -> PipelineConfigs:
    """Origami style animals and creatures."""
    return get_papercut_config(prompt, style="papercutcraft", **kwargs)

def papercut_portrait(prompt: str, **kwargs) -> PipelineConfigs:
    """Portrait aspect ratio papercut."""
    return get_papercut_config(prompt, aspect="portrait", **kwargs)

def papercut_wide(prompt: str, **kwargs) -> PipelineConfigs:
    """Wide aspect ratio papercut panorama."""
    return get_papercut_config(prompt, aspect="wide", **kwargs)


if __name__ == "__main__":
    print("Testing papercut pipeline configurations...")
    
    test_cases = [
        ("beautiful origami dragon with intricate folds",),
        ("origami fox in forest paper art",),
        ("layered paper art of a samurai warrior",),
        ("paper craft butterfly with colorful wings",),
    ]
    
    for (prompt,) in test_cases:
        print(f"\n{'='*60}")
        print(f"Prompt: {prompt[:50]}...")
        config = get_papercut_config(prompt)
        print(f"  Model: {config.base_model.name}")
        print(f"  Size: {config.width}x{config.height}")
        print(f"  Steps: {config.steps}")
        print("  ✅ OK")
