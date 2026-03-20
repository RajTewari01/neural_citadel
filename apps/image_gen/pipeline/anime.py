"""
Anime Pipeline
==============

Multi-model anime generation with intelligent model selection.

Models Available:
- meinamix: Best for general anime (trigger: "Meina")
- novaporn: High quality anime NSFW (trigger: "high quality photo")
- bloodorangemix: Hardcore anime style
- abyssorangemix: Hard anime style with vivid colors
- eerieorangemix: Eerie/horror anime style
- eerieorangemix_nsfw: NSFW variant of eerie style

Auto-detection features:
- Model selection based on prompt keywords
- Aspect ratio detection (portrait/landscape/square)
- Optimized settings per model
"""

import re
import random
from pathlib import Path
from typing import Literal, Optional
import sys
# Add project root to path
sys.path.insert(0, str(Path(__file__).parents[3]))

from configs.paths import DIFFUSION_MODELS, VAE_MODELS, IMAGE_GEN_OUTPUT_DIR
from apps.image_gen.pipeline.pipeline_types import PipelineConfigs, LoraConfig
from apps.image_gen.pipeline.registry import register_pipeline


# =============================================================================
# MODEL CONFIGURATIONS
# =============================================================================
# Each model has optimized settings based on community recommendations

MODEL_MAP = {
    "meinamix": {
        "file": DIFFUSION_MODELS["meinamix"],
        "trigger": "Meina",
        "vae": VAE_MODELS["anime"],
        "steps": 25,
        "cfg": 7.0,
        "description": "Best general-purpose anime model"
    },
    "novaporn": {
        "file": DIFFUSION_MODELS["novaporn"],
        "trigger": "high quality photo",
        "vae": VAE_MODELS["anime"],
        "steps": 25,
        "cfg": 7.5,
        "description": "High quality anime with photo-like quality"
    },
    "bloodorangemix": {
        "file": DIFFUSION_MODELS["bloodorangemix"],
        "trigger": "",
        "vae": VAE_MODELS["orangemix"],
        "steps": 25,
        "cfg": 6.5,
        "description": "Vivid hardcore anime style"
    },
    "abyssorangemix": {
        "file": DIFFUSION_MODELS["abyssorangemix"],
        "trigger": "",
        "vae": VAE_MODELS["orangemix"],
        "steps": 25,
        "cfg": 7.0,
        "description": "Deep vivid colors, hard style"
    },
    "eerieorangemix": {
        "file": DIFFUSION_MODELS["eerieorangemix_hard"],
        "trigger": "",
        "vae": VAE_MODELS["orangemix"],
        "steps": 25,
        "cfg": 6.0,
        "description": "Eerie/horror anime style"
    },
    "eerieorangemix_nsfw": {
        "file": DIFFUSION_MODELS["eerieorangemix_nsfw"],
        "trigger": "",
        "vae": VAE_MODELS["orangemix"],
        "steps": 25,
        "cfg": 6.5,
        "description": "NSFW eerie anime style"
    },
    "azovya": {
        "file": DIFFUSION_MODELS["azovya_rpg"],
        "trigger": "",
        "vae": VAE_MODELS["anime"],
        "steps": 25,
        "cfg": 7.0,
        "description": "RPG/fantasy anime art style"
    },
    "shiny_sissy": {
        "file": DIFFUSION_MODELS["shiny_sissy"],
        "trigger": "shiny sissy luxury latex dress for doll",
        "vae": VAE_MODELS["anime"],
        "steps": 25,
        "cfg": 7.0,
        "description": "Latex/shiny style anime"
    },
}


# =============================================================================
# PROMPT TEMPLATES
# =============================================================================

ANIME_TEMPLATE = (
    "{trigger}{prompt}, "
    "anime style, beautiful detailed eyes, intricate details, "
    "masterpiece, best quality, ultra detailed, 8k"
)

ANIME_NEGATIVE = (
    "(worst quality, low quality:1.4), (zombie, sketch, interlocked fingers, comic), "
    "(monochrome, grayscale), (bad anatomy), (deformed), (disfigured), "
    "lowres, bad hands, text, error, missing fingers, extra digit, fewer digits, "
    "cropped, worst quality, low quality, normal quality, jpeg artifacts, "
    "signature, watermark, username, blurry, artist name, "
    "bad feet, cropped, poorly drawn hands, poorly drawn face, mutation, deformed, "
    "ugly, blurry, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, "
    "out of frame, ugly, extra limbs, bad anatomy, gross proportions, malformed limbs, "
    "missing arms, missing legs, extra arms, extra legs, mutated hands, "
    "fused fingers, too many fingers, long neck"
)
# Model type
ModelType = Literal[
    "meinamix", "novaporn", "bloodorangemix", "abyssorangemix", 
    "eerieorangemix", "eerieorangemix_nsfw", "azovya", "shiny_sissy"
]
AspectType = Literal["portrait", "landscape", "square"]


# =============================================================================
# DETECTION FUNCTIONS
# =============================================================================

def _detect_model(prompt: str) -> ModelType:
    """
    Detect best anime model based on prompt keywords.
    Uses scoring system for specialty models, random for general anime.
    
    Logic:
    - If prompt matches shiny_sissy keywords -> use shiny_sissy (specialty)
    - If prompt matches other keywords -> use best keyword match
    - If no keywords match -> RANDOM from general anime models (excludes shiny_sissy)
    """
    prompt_lower = prompt.lower()
    
    # General anime models (for random selection when no keywords match)
    # NOTE: novaporn and shiny_sissy excluded - only via explicit keywords
    GENERAL_ANIME_MODELS = [
        "meinamix", "bloodorangemix", "abyssorangemix",
        "eerieorangemix", "eerieorangemix_nsfw", "azovya"
    ]
    
    # Specialty models that should ONLY be selected via keywords (not random)
    SPECIALTY_MODELS = ["shiny_sissy"]
    
    # Model keywords with weights
    model_keywords = {
        "meinamix": {
            "meina": 5, "cute": 2, "kawaii": 2, "moe": 2, 
            "school": 1, "uniform": 1, "idol": 2, "magical girl": 2
        },
        "novaporn": {
            "detailed": 1, "porn": 5, "semi realistic": 2, "naked": 5, "pussy": 5,
        },
        "bloodorangemix": {
            "blood": 3, 
        },
        "abyssorangemix": {
            "abyss": 5,
        },
        "eerieorangemix": {
            "eerie": 5, "horror": 3,
        },
        "eerieorangemix_nsfw": {
            "eerie nsfw": 5, "horror nsfw": 4, "creepy nsfw": 4, "horror": 5, "ghostly naked": 5
        },
        "azovya": {
            "rpg": 3, "fantasy": 3,
        },
        "shiny_sissy": {
            "latex": 5, "shiny": 3, "sissy": 6, "pvc": 3,
            "rubber": 3, "glossy": 2, "doll": 2, "femboy": 5
        },
    }
    
    # Calculate scores
    scores = {model: 0 for model in model_keywords}
    
    for model, keywords in model_keywords.items():
        for keyword, weight in keywords.items():
            if re.search(rf'\b{re.escape(keyword)}\b', prompt_lower):
                scores[model] += weight
    
    # Get best model by score
    best_model = max(scores, key=scores.get)
    
    # If best model has a score > 0, use it (keyword match found)
    if scores[best_model] > 0:
        return best_model
    
    # No keywords matched -> pick RANDOM from general anime models
    chosen = random.choice(GENERAL_ANIME_MODELS)
    print(f"🎲 No keyword match, randomly selected: {chosen}")
    return chosen


def _detect_aspect(prompt: str) -> tuple[str, int, int]:
    """
    Detect aspect ratio from prompt keywords.
    Returns: (aspect_name, width, height)
    """
    prompt_lower = prompt.lower()
    
    # Portrait keywords (taller than wide)
    portrait_keywords = [
        "portrait", "full body", "fullbody", "standing", "tall",
        "vertical", "phone wallpaper", "1girl", "1boy", "solo"
    ]
    
    # Landscape keywords (wider than tall)
    landscape_keywords = [
        "landscape", "wide", "panorama", "scenery", "background",
        "environment", "horizontal", "desktop wallpaper", "scene"
    ]
    
    # Square keywords
    square_keywords = [
        "square", "profile", "icon", "avatar", "headshot", "face"
    ]
    
    # Check for explicit aspect ratio mentions
    # 4GB VRAM safe sizes (max 768 on any side)
    if re.search(r'\b(16:9|widescreen|cinema)\b', prompt_lower):
        return ("landscape", 768, 432)
    if re.search(r'\b(9:16|vertical|phone)\b', prompt_lower):
        return ("portrait", 432, 768)
    if re.search(r'\b(1:1|square)\b', prompt_lower):
        return ("square", 512, 512)
    
    # Score-based detection
    portrait_score = sum(1 for kw in portrait_keywords if kw in prompt_lower)
    landscape_score = sum(1 for kw in landscape_keywords if kw in prompt_lower)
    square_score = sum(1 for kw in square_keywords if kw in prompt_lower)
    
    if landscape_score > portrait_score and landscape_score > square_score:
        return ("landscape", 768, 512)
    elif square_score > portrait_score:
        return ("square", 512, 512)
    else:
        # Default to portrait (most common for anime characters)
        return ("portrait", 512, 768)


# =============================================================================
# MAIN CONFIG FUNCTION
# =============================================================================

@register_pipeline(
    name="anime",
    keywords=["anime", "kawaii", "moe", "meina", "novaporn", "bloodorangemix", "abyssorangemix", 
              "eerie anime", "rpg", "fantasy", "azovya", "latex", "shiny sissy"],
    description="Multi-model anime generation with intelligent model selection",
    types={
        "meinamix": "Best for general anime (cute, kawaii)",
        "novaporn": "High quality anime with photo-like quality",
        "bloodorangemix": "Vivid hardcore anime style",
        "abyssorangemix": "Deep vivid colors, hard style",
        "eerieorangemix": "Eerie/horror anime style",
        "azovya": "RPG/fantasy anime art style",
        "shiny_sissy": "Latex/shiny style anime"
    }
)
def get_anime_config(
        prompt: str,
        model: Optional[ModelType] = None,
        aspect: Optional[AspectType] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        auto_detect: bool = True,
        random_model: bool = False
) -> PipelineConfigs:
    """
    Get Anime pipeline configuration.
    
    Args:
        prompt: Your anime art description
        model: Specific model or None for auto-detect
        aspect: "portrait", "landscape", or "square" (auto-detected if None)
        width: Override width (auto-detected from aspect if None)
        height: Override height (auto-detected from aspect if None)
        auto_detect: Whether to auto-detect model from prompt
        random_model: If True, pick a random model
        
    Returns:
        PipelineConfigs ready for engine.generate()
    """
    
    # Model selection
    if random_model:
        model = random.choice(list(MODEL_MAP.keys()))
        print(f"🎲 Random Anime Model: {model}")
    elif model is None and auto_detect:
        model = _detect_model(prompt)
        print(f"🔍 Auto-detected Model: {model}")
    elif model is None:
        model = "meinamix"  # Default
    
    if model not in MODEL_MAP:
        print(f"⚠️ Unknown model '{model}', using meinamix")
        model = "meinamix"
    
    selected = MODEL_MAP[model]
    print(f"🎨 Anime Mode: {model} - {selected['description']}")
    
    # Aspect ratio / dimensions
    if width is None or height is None:
        if aspect is not None:
            # 4GB VRAM safe sizes
            aspect_map = {
                "portrait": (512, 768),
                "landscape": (768, 512),
                "square": (512, 512)
            }
            width, height = aspect_map.get(aspect, (512, 768))
        else:
            # Auto-detect aspect
            detected_aspect, width, height = _detect_aspect(prompt)
            print(f"📐 Detected Aspect: {detected_aspect} ({width}x{height})")
    
    # Build trigger
    trigger = selected["trigger"]
    trigger_prefix = f"({trigger}:1.2), " if trigger else ""
    
    # Build final prompt
    final_prompt = ANIME_TEMPLATE.format(
        trigger=trigger_prefix,
        prompt=prompt
    )
    
    # Output directory
    output_dir = IMAGE_GEN_OUTPUT_DIR / "anime" / model
    output_dir.mkdir(parents=True, exist_ok=True)
    
    return PipelineConfigs(
        base_model=selected["file"],
        output_dir=output_dir,
        prompt=final_prompt,
        vae=selected.get("vae"),
        style_type="anime",  # Auto-selects R-ESRGAN 4x+ Anime6B
        
        scheduler_name="dpm++_2m_karras",  # Best for anime
        
        triggers=trigger if trigger else None,
        neg_prompt=ANIME_NEGATIVE,
        
        width=width,
        height=height,
        steps=selected["steps"],
        cfg=selected["cfg"],
        clip_skip=None,  # Common for anime models is 2
    )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def anime_cute(prompt: str, **kwargs) -> PipelineConfigs:
    """Cute kawaii anime style with MeinaMix."""
    return get_anime_config(prompt, model="meinamix", **kwargs)


def anime_vivid(prompt: str, **kwargs) -> PipelineConfigs:
    """Vivid colorful anime with BloodOrangeMix."""
    return get_anime_config(prompt, model="bloodorangemix", **kwargs)


def anime_horror(prompt: str, **kwargs) -> PipelineConfigs:
    """Eerie/horror anime style."""
    return get_anime_config(prompt, model="eerieorangemix", **kwargs)


def anime_rpg(prompt: str, **kwargs) -> PipelineConfigs:
    """Fantasy RPG anime style."""
    return get_anime_config(prompt, model="azovya", **kwargs)


def anime_portrait(prompt: str, **kwargs) -> PipelineConfigs:
    """Portrait aspect anime."""
    return get_anime_config(prompt, aspect="portrait", **kwargs)


def anime_landscape(prompt: str, **kwargs) -> PipelineConfigs:
    """Landscape/scenery anime."""
    return get_anime_config(prompt, aspect="landscape", **kwargs)


def anime_random(prompt: str, **kwargs) -> PipelineConfigs:
    """Random model selection."""
    return get_anime_config(prompt, random_model=True, **kwargs)


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("Testing anime pipeline detection...\n")
    
    test_prompts = [
        "cute kawaii girl in school uniform, Meina style",
        "dark horror ghost girl in haunted mansion, eerie",
        "fantasy warrior elf with sword and armor, rpg",
        "latex maid outfit, shiny glossy",
        "beautiful scenery landscape with mountains",
        "1girl standing full body portrait",
        "vivid colorful magical girl transformation",
    ]
    
    for prompt in test_prompts:
        print(f"\n📝 Prompt: {prompt[:50]}...")
        config = get_anime_config(prompt)
        print(f"   Model: {config.base_model.name}")
        print(f"   Size: {config.width}x{config.height}")
        print(f"   Steps: {config.steps}, CFG: {config.cfg}")
