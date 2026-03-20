"""
Drawing/Watercolor Pipeline
===========================

Artistic drawing and watercolor styles using specialized models.

Models:
- Rachel Walker: Watercolor/Ink style (trigger: "rachelwalker style")
- Matcha Pixiv: Anime drawing/sketch style (trigger: "Matchapix")
- Pareidolia Gateway: Surreal/Abstract artistic style (trigger: "sks place")

Features:
- Auto-adds style-specific triggers and negative prompts
- Optimized for artistic output
- Random model selection option
- 4GB VRAM safe resolutions
"""

from pathlib import Path
from typing import Literal, Optional, List, Any, Dict
import random
import re
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from configs.paths import DIFFUSION_MODELS, IMAGE_GEN_OUTPUT_DIR, LORA_DIR
from apps.image_gen.pipeline.pipeline_types import PipelineConfigs, LoraConfig
from apps.image_gen.pipeline.registry import register_pipeline

LORA_STYLE_DIR = LORA_DIR / "style"


# =============================================================================
# MODEL CONFIGURATION
# =============================================================================

# Drawing models are stored in 'drawing_model' directory in user's request
# We need to map them to files. 
# Assuming they are added to DIFFUSION_MODELS in paths.py or we reference them directly if not.
# Since they might not be in the dictionary yet (as I didn't see them in previous view_file of paths.py),
# I will define strict paths here for now or use the dictionary if I update paths.py.
# The user's request showed them in: "Assets/model/Image_Generation_checkpoints/drawing_model"
# which maps to D:\neural_citadel\assets\models\image_gen\diffusion\drawing_model

DRAWING_DIR = Path("d:/neural_citadel/assets/models/image_gen/diffusion/drawing_model")

MODEL_MAP = {
    "rachel_walker": {
        "file": DRAWING_DIR / "rachelWalkerStyle_v1.ckpt",
        "trigger": "rachelwalker style",
        "enhancement": "watercolor painting, white background, (paper texture), high quality, denoise, clean, soft colors",
        "negative": "halftone, moire, artifacts, compression artifacts, jpeg artifacts, noise, cartoon, 3d, easynegative",
        "description": "Rachel Walker - Watercolor & Ink",
        "steps": 25,
        "cfg": 7.0,
    },
    "matcha_pixiv": {
        "file": DRAWING_DIR / "matchaPixivStyle_10.ckpt",
        "trigger": "in the style of Matchapix",
        "enhancement": "masterpiece, best quality, ((colorful)), (super delicate), anime style, intricate details, lineart",
        "negative": "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, jpeg artifacts, signature, watermark, username, blurry, easynegative",
        "description": "Matcha Pixiv - Anime Sketch",
        "steps": 35,  
        "cfg": 9.5,   
        "scheduler": "euler_a", 
    },
    "pareidolia": {
        "file": DRAWING_DIR / "pareidoliaGateway_v1.ckpt",
        "trigger": "sks place",
        "enhancement": "sketch,intricate, elegant, highly detailed, digital painting, artstation, concept art, smooth, sharp focus, symmetry",
        "negative": "blurry, artifacts, smudge, cartoon, 3d, deformed, poorly drawn, easynegative",
        "description": "Pareidolia Gateway - Surreal Art",
        "steps": 30,
        "cfg": 7.0,
    },
    "chinese_ink": {
        "file": DRAWING_DIR / "ChineseInkComicStrip_v10.ckpt",
        "trigger": "shuimobysim, wuchangshuo, bonian, zhenbanqiao, badashanren",
        "enhancement": "chinese ink painting, masterpiece, best quality, traditional chinese art, mountain, lake, peach blossom, scroll painting",
        "negative": "easynegative, white background, low quality, worst quality, lowres, glitch, deformed, mutated, ugly, disfigured, text, watermark",
        "description": "Chinese Ink - Traditional Scroll Painting",
        "steps": 26,
        "cfg": 7.0,
        "lora": {
             "path": LORA_STYLE_DIR / "MoXinV1.safetensors",
             "scale": 0.8
        }
    }
}

ModelType = Literal["rachel_walker", "matcha_pixiv", "pareidolia", "chinese_ink"]


# =============================================================================
# PROMPT TEMPLATES
# =============================================================================

DRAWING_TEMPLATE = (
    "{trigger}, {enhancement}, {prompt}, "
    "masterpiece, best quality, ultra detailed, 8k, "
    "sharp focus, professional art"
)

DRAWING_NEGATIVE = (
    "(worst quality:2), (low quality:2), blurry, pixelated, "
    "photo, photorealistic, realism, 3d, cgi, render, "
    "bad anatomy, deformed, ugly, missing limbs, "
    "watermark, text, signature, username, "
    "cropped, lowres, jpeg artifacts"
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
    
    if re.search(r'\b(chinese|ink|scroll|brush|shuimo|wuchangshuo)\b', prompt_lower) or "scroll painting" in prompt_lower:
        return "chinese_ink"
    if re.search(r'\b(water|ink|paint|paper)\b', prompt_lower):
        return "rachel_walker"
    if re.search(r'\b(anime|sketch|pixiv)\b', prompt_lower):
        return "matcha_pixiv"
    if re.search(r'\b(surreal|dream|abstract)\b', prompt_lower):
        return "pareidolia"
        
    return "rachel_walker"  # Default


def _detect_aspect(prompt: str, override: Optional[str] = None) -> tuple[str, int, int]:
    """Detect aspect ratio from prompt or use override."""
    if override and override in ASPECT_RATIOS:
        w, h = ASPECT_RATIOS[override]
        return (override, w, h)
        
    prompt_lower = prompt.lower()
    
    if "landscape" in prompt_lower or "wide" in prompt_lower or "scenery" in prompt_lower:
        return ("landscape", 768, 512)
    if "square" in prompt_lower or "icon" in prompt_lower:
        return ("square", 512, 512)
        
    # Default to portrait for art
    return ("portrait", 512, 768)


# =============================================================================
# MAIN CONFIG FUNCTION
# =============================================================================

@register_pipeline(
    name="drawing",
    keywords=["drawing", "watercolor", "ink", "sketch", "chinese ink", "scroll painting",
              "matcha", "pixiv", "pareidolia", "surreal", "rachel walker"],
    description="Artistic drawing and watercolor styles using specialized models",
    types={
        "rachel_walker": "Watercolor & ink style",
        "matcha_pixiv": "Anime sketch style from Pixiv",
        "pareidolia": "Surreal/abstract artistic style",
        "chinese_ink": "Traditional Chinese scroll painting"
    }
)
def get_drawing_config(
    prompt: str,
    aspect_ratio: Optional[str] = None,
    random_model: bool = False,
    model_override: Optional[ModelType] = None,
) -> PipelineConfigs:
    """
    Get Drawing/Watercolor pipeline configuration.
    
    Args:
        prompt: Description of the artwork
        aspect_ratio: "portrait", "landscape", or "square"
        random_model: If True, selects a random model
        model_override: Specific model to use, overrides auto-detection and random_model
        
    Returns:
        PipelineConfigs ready for engine.generate()
    """
    
    # Model Selection
    if model_override:
        model = model_override
        print(f"✨ Model Override: {model}")
    elif random_model:
        model = random.choice(list(MODEL_MAP.keys()))
        print(f"🎲 Random Drawing Model: {model}")
    else:
        model = _detect_model(prompt)
        print(f"🔍 Auto-detected Model: {model}")
        
    selected = MODEL_MAP[model]
    print(f"🎨 Drawing Mode: {selected['description']}")
    
    # Aspect/Size
    _, width, height = _detect_aspect(prompt, aspect_ratio)
    print(f"📐 Aspect: {aspect_ratio if aspect_ratio else 'auto-detected'} ({width}x{height})")
            
    # Build prompt with model specific triggers/enhancements
    final_prompt = f"{selected['enhancement']}, {prompt}"
    if selected.get("trigger"):
        final_prompt = f"{selected['trigger']}, {final_prompt}"
    
    # Output directory
    output_dir = IMAGE_GEN_OUTPUT_DIR / "drawing" / model
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Use model-specific negative or default
    negative_prompt = selected.get("negative", "easynegative, worst quality, low quality")
    
    # Prepare LoRAs
    loras: List[LoraConfig] = []
    if "lora" in selected:
        l_conf = selected["lora"]
        loras.append(LoraConfig(
            lora_path=l_conf["path"],
            scale=l_conf["scale"]
        ))
    
    return PipelineConfigs(
        base_model=selected["file"],
        output_dir=output_dir,
        prompt=final_prompt,
        style_type="anime",  # Auto-selects R-ESRGAN 4x+ Anime6B
        
        scheduler_name=selected.get("scheduler", "euler_a"), 
        
        neg_prompt=negative_prompt,
        
        width=width,
        height=height,
        steps=selected["steps"],
        cfg=selected["cfg"],
        lora=loras
    )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def draw_watercolor(prompt: str, **kwargs) -> PipelineConfigs:
    """Generate watercolor art using Rachel Walker style."""
    return get_drawing_config(prompt, model_override="rachel_walker", **kwargs)

def draw_sketch(prompt: str, **kwargs) -> PipelineConfigs:
    """Generate anime-style sketch using Matcha Pixiv."""
    return get_drawing_config(prompt, model_override="matcha_pixiv", **kwargs)

def draw_surreal(prompt: str, **kwargs) -> PipelineConfigs:
    """Generate surreal art using Pareidolia."""
    return get_drawing_config(prompt, model_override="pareidolia", **kwargs)

def draw_chinese(prompt: str, **kwargs) -> PipelineConfigs:
    """Generate Chinese Ink Scroll painting."""
    return get_drawing_config(prompt, model_override="chinese_ink", **kwargs)

def draw_random(prompt: str, **kwargs) -> PipelineConfigs:
    """Generate with random drawing model."""
    return get_drawing_config(prompt, random_model=True, **kwargs)


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("Testing drawing pipeline...\n")
    
    prompts = [
        "a giraffe in the evening, watercolor painting",
        "anime girl sketching in notebook",
        "surreal floating islands in sky",
        "chinese scroll painting of mountains",
    ]
    
    for p in prompts:
        print(f"\n📝 Prompt: {p}")
        config = get_drawing_config(p)
        print(f"   Model: {config.base_model.name}")
        if config.lora:
            print(f"   LoRA: {[l.lora_path.name for l in config.lora]}")
        print(f"   Size: {config.width}x{config.height}")
