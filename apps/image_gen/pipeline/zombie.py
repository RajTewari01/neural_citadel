"""
Zombie Pipeline - Walking Dead & Chinese Qing Zombies
======================================================

Pipeline for generating zombie images with multiple modes:
- Close-up portraits (single zombie)
- Mid-shot (2-3 zombies)
- Horde (wide shot, many zombies)
- Chinese Qing dynasty jiangshi (with LoRA)

Usage:
    from apps.image_gen.pipeline.zombie import get_zombie_config
    config = get_zombie_config("rotting zombie in abandoned hospital", shot_type="close")
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
    LORA_MODELS,
    MODEL_WALKING_DEAD,
    MODEL_MAJICMIX
)

from apps.image_gen.pipeline.pipeline_types import PipelineConfigs, LoraConfig
from apps.image_gen.pipeline.registry import register_pipeline

# Output Path
GENERATED_OUTPUT = IMAGE_GEN_OUTPUT_DIR / "zombies"
GENERATED_OUTPUT.mkdir(parents=True, exist_ok=True)

# =============================================================================
# TEMPLATES - Based on your proven zombie template
# =============================================================================

# Close-up portrait - single zombie
CLOSE_UP_TEMPLATE = (
    "{trigger}, {prompt}, "
    "(solo:1.3), (single subject:1.2), (one zombie only:1.2), "
    "(detailed rotting face:1.2), (skull:1.1), (peeling skin:1.1), "
    "(close-up portrait:1.2), cinematic lighting, 8k, masterpiece, movie still"
)

# Mid-shot - 2-3 zombies
MID_SHOT_TEMPLATE = (
    "{trigger}, {prompt}, "
    "(two to three zombies:1.2), (small group:1.1), (medium shot:1.2), "
    "(distinct separate individuals:1.3), (spacing between subjects:1.2), "
    "(rotting faces:1.0), (horror scene:1.1), "
    "cinematic, 8k, masterpiece, movie still"
)

# Horde - wide shot with many zombies
HORDE_TEMPLATE = (
    "{trigger}, {prompt}, "
    "(silhouettes:1.1), (distant figures:1.0), (atmospheric fog:1.1), "
    "(wide shot:1.2), crowd of zombies, horror movie scene, 8k, masterpiece"
)

# Chinese Qing Zombie (jiangshi)
CHINESE_ZOMBIE_TEMPLATE = (
    "{trigger}, {prompt}, "
    "Chinese Qing dynasty zombie, jiangshi, hopping vampire, "
    "traditional Chinese costume, paper talisman on forehead, "
    "stiff arms, horror, 8k, masterpiece"
)

# =============================================================================
# NEGATIVE PROMPTS
# =============================================================================

CLOSE_UP_NEGATIVE = (
    "(worst quality:2), (low quality:2), (normal quality:2), lowres, "
    "(diptych:1.5), (side by side:1.5), (split image:1.5), (collage:1.4), (grid:1.4), "
    "(multiple people:1.5), (crowd:1.4), (group:1.4), (two faces:1.4), "
    "(overlapping:1.3), (fused:1.3), (duplicate:1.3), "
    "3d, cartoon, anime, sketches, blurry, haze, smooth skin, plastic, "
    "bad anatomy, bad hands, deformed, extra limbs, ((monochrome)), ((grayscale))"
)

MID_SHOT_NEGATIVE = (
    "(worst quality:2), (low quality:2), (normal quality:2), lowres, "
    "(overlapping bodies:1.4), (fused together:1.4), (merged subjects:1.4), "
    "(clipping:1.3), (touching:1.2), (crowd:1.3), (horde:1.3), "
    "diptych, split image, collage, grid, "
    "3d, cartoon, anime, sketches, blur, smooth skin, plastic, "
    "bad anatomy, bad hands, deformed, extra limbs, ((monochrome)), ((grayscale))"
)

HORDE_NEGATIVE = (
    "(worst quality:2), (low quality:2), (normal quality:2), lowres, "
    "(overlapping bodies:1.5), (fused together:1.5), (merged subjects:1.5), "
    "(clipping:1.3), (detailed faces:1.2), (close-up:1.3), "
    "3d, cartoon, anime, sketches, blur, smooth skin, plastic, "
    "bad anatomy, bad hands, deformed, extra limbs, ((monochrome)), ((grayscale))"
)

CHINESE_ZOMBIE_NEGATIVE = (
    "(worst quality:2), (low quality:2), (normal quality:2), lowres, "
    "western zombie, rotting skin, gore, blood, "
    "3d, cartoon, anime, sketches, blurry, "
    "bad anatomy, bad hands, deformed, extra limbs, ((monochrome)), ((grayscale))"
)

# Shot type definitions
ShotType = Literal["close", "mid", "horde"]
ZombieType = Literal["normal", "chinese"]


def _detect_shot_type(prompt: str) -> ShotType:
    """Detect shot type from prompt keywords."""
    prompt_lower = prompt.lower()
    
    close_keywords = [
        "close-up", "closeup", "portrait", "face", "single", "one zombie",
        "detailed", "macro", "head", "bust", "solo"
    ]
    mid_keywords = [
        "two", "three", "2", "3", "couple", "few", "small group",
        "mid shot", "medium shot", "mid-shot", "pair"
    ]
    horde_keywords = [
        "horde", "hordes", "crowd", "crowds", "many", "group", "groups",
        "army", "armies", "swarm", "wave", "apocalypse", "invasion",
        "herd", "mob", "pack", "multiple", "several", "dozens",
        "wide shot", "far", "distant", "panorama", "landscape"
    ]
    
    for kw in horde_keywords:
        if kw in prompt_lower:
            return "horde"
    for kw in mid_keywords:
        if kw in prompt_lower:
            return "mid"
    for kw in close_keywords:
        if kw in prompt_lower:
            return "close"
    
    return "close"  # default


def _detect_zombie_type(prompt: str) -> ZombieType:
    """Detect if Chinese zombie is requested using scoring system."""
    import re
    prompt_lower = prompt.lower()
    
    # Chinese zombie keywords with weights
    chinese_keywords = {
        "chinese": 3, "qing": 3, "jiangshi": 3, "hopping vampire": 3,
        "china": 2, "dynasty": 2, "talisman": 2, "paper talisman": 2,
        "mandarin": 1, "temple": 1, "ancient china": 3, "qing dynasty": 3,
        "hopping": 2, "hong kong": 1, "mr vampire": 2,
    }
    
    # Western/normal zombie keywords
    normal_keywords = {
        "walking dead": 3, "rotting": 2, "undead": 2, "apocalypse": 2,
        "gore": 2, "blood": 1, "brain": 2, "western": 2, "american": 1,
        "resident evil": 2, "infection": 2, "outbreak": 2, "virus": 1,
    }
    
    chinese_score = 0
    normal_score = 0
    
    for keyword, weight in chinese_keywords.items():
        if re.search(rf'\b{keyword}\b', prompt_lower):
            chinese_score += weight
    
    for keyword, weight in normal_keywords.items():
        if re.search(rf'\b{keyword}\b', prompt_lower):
            normal_score += weight
    
    # Return based on score (chinese needs to win clearly)
    if chinese_score > normal_score:
        return "chinese"
    else:
        return "normal"


@register_pipeline(
    name="zombie",
    keywords=["zombie", "undead", "walking dead", "jiangshi", "horde", "rotting",
              "apocalypse", "infection", "chinese zombie", "qing dynasty"],
    description="Walking Dead and Chinese Qing zombies with multiple shot types",
    types={
        "close": "Close-up portrait of single zombie",
        "mid": "Mid-shot with 2-3 zombies",
        "horde": "Wide shot with zombie horde",
        "chinese": "Chinese Qing dynasty jiangshi"
    }
)
def get_zombie_config(
        prompt: str,
        shot_type: Optional[ShotType] = None,
        zombie_type: Optional[ZombieType] = None,
        auto_detect: bool = True
) -> PipelineConfigs:
    """
    Get Zombie pipeline configuration.
    
    Args:
        prompt: Your zombie scene description
        shot_type: "close", "mid", or "horde" (auto-detected if None)
        zombie_type: "normal" or "chinese" (auto-detected if None)
        auto_detect: If True, detect shot/zombie type from prompt
        
    Returns:
        PipelineConfigs ready for engine.generate()
    """
    
    # Auto-detect types if not specified
    if auto_detect and shot_type is None:
        shot_type = _detect_shot_type(prompt)
    elif shot_type is None:
        shot_type = "close"
        
    if auto_detect and zombie_type is None:
        zombie_type = _detect_zombie_type(prompt)
    elif zombie_type is None:
        zombie_type = "normal"
    
    # Configure based on zombie type
    loras = []
    
    if zombie_type == "chinese":
        print(f"[Zombie] Mode: CHINESE QING (jiangshi with LoRA)")
        base_model = MODEL_MAJICMIX
        template = CHINESE_ZOMBIE_TEMPLATE
        negative = CHINESE_ZOMBIE_NEGATIVE
        trigger = "Chinese_Qing_Zombie"
        width, height = 512, 768
        
        loras.append(LoraConfig(
            lora_path=LORA_MODELS["chinese_zombie"],
            scale=0.8
        ))
    else:
        # Walking Dead zombie
        base_model = MODEL_WALKING_DEAD
        trigger = "RottingZombie person"
        
        if shot_type == "horde":
            print(f"[Zombie] Mode: HORDE (wide shot, many zombies)")
            template = HORDE_TEMPLATE
            negative = HORDE_NEGATIVE
            width, height = 960, 640
        elif shot_type == "mid":
            print(f"[Zombie] Mode: MID-SHOT (2-3 zombies)")
            template = MID_SHOT_TEMPLATE
            negative = MID_SHOT_NEGATIVE
            width, height = 768, 768
        else:
            print(f"[Zombie] Mode: CLOSE-UP (portrait, single zombie)")
            template = CLOSE_UP_TEMPLATE
            negative = CLOSE_UP_NEGATIVE
            width, height = 512, 768
    
    # Build final prompt
    final_prompt = template.format(trigger=trigger, prompt=prompt)

    return PipelineConfigs(
        base_model=base_model,
        output_dir=GENERATED_OUTPUT,
        prompt=final_prompt,
        neg_prompt=negative,
        vae="realistic",  # ft_mse VAE works well
        style_type="realistic",  # Auto-selects R-ESRGAN 4x+
        embeddings=[],
        scheduler_name="euler_a",  # Your original used euler_a
        width=width,
        height=height,
        steps=30,
        cfg=7.0,
        lora=loras,
        c_net=[],
    )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def zombie_closeup(prompt: str, **kwargs) -> PipelineConfigs:
    """Single zombie portrait."""
    return get_zombie_config(prompt, shot_type="close", zombie_type="normal", **kwargs)

def zombie_midshot(prompt: str, **kwargs) -> PipelineConfigs:
    """Small group of 2-3 zombies."""
    return get_zombie_config(prompt, shot_type="mid", zombie_type="normal", **kwargs)

def zombie_horde(prompt: str, **kwargs) -> PipelineConfigs:
    """Crowd of zombies, wide shot."""
    return get_zombie_config(prompt, shot_type="horde", zombie_type="normal", **kwargs)

def chinese_zombie(prompt: str, **kwargs) -> PipelineConfigs:
    """Chinese Qing dynasty jiangshi zombie."""
    return get_zombie_config(prompt, zombie_type="chinese", **kwargs)


if __name__ == "__main__":
    print("Testing zombie pipeline configurations...")
    
    test_cases = [
        ("rotting zombie in abandoned hospital",),
        ("horde of zombies attacking city", ),
        ("chinese qing dynasty zombie with talisman",),
    ]
    
    for (prompt,) in test_cases:
        print(f"\n{'='*60}")
        print(f"Prompt: {prompt[:50]}...")
        config = get_zombie_config(prompt)
        print(f"  Model: {config.base_model.name}")
        print(f"  Size: {config.width}x{config.height}")
        print(f"  LoRAs: {[l.lora_path.name for l in config.lora] if config.lora else 'None'}")
        print("  ✅ OK")
