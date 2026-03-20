"""
Closeup Anime Pipeline - High-Quality Anime Portraits
===================================================

Pipeline specialized for "close-up" anime portraits, enforcing tight framing
and high detail using the CheckpointYesmix model and Violet Evergarden LoRA.

Features:
    - Strict "close up portrait" framing enforcement
    - FastNegativeV2 embedding integration
    - Customized VAE (Anime) settings
    - Configurable "violet_evergarden" style LoRA

Usage:
    from apps.image_gen.pipeline.closeup_anime import closeup_anime
    config = closeup_anime("a beautiful magical girl with glowing eyes")
"""

from pathlib import Path
from typing import Optional, Literal, List
import sys

# Add project root to path
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from configs.paths import (
    IMAGE_GEN_OUTPUT_DIR,
    LORA_MODELS,
    DIFFUSION_MODELS,  # Changed from MODEL_CLOSEUP_ANIME
    VAE_DIR,
    EMBEDDING_FASTNEGATIVE
)

from apps.image_gen.pipeline.pipeline_types import PipelineConfigs, LoraConfig
from apps.image_gen.pipeline.registry import register_pipeline

# Output Path
GENERATED_OUTPUT = IMAGE_GEN_OUTPUT_DIR / "closeup_anime"
GENERATED_OUTPUT.mkdir(parents=True, exist_ok=True)

# =============================================================================
# TEMPLATES & PROMPTS
# =============================================================================

# Forces a close-up composition with high quality keywords from Scraper
# Forces a close-up composition with high quality keywords from FaceBombMix
CLOSEUP_TEMPLATE = (
    "(ultra illustrated style:1.0), best quality, masterpiece, ((close up portrait)), "
    "{{{prompt}}}, depth of field, detailed eyes, intricate hair, anime style, "
    "key visual, vibrant colors, studio lighting, highly detailed"
)

# Standard Negative for Anime + FastNegative Embedding
NEGATIVE_EMBEDDING_TRIGGER = "FastNegativeV2"
COMMON_NEGATIVE = (
    f"{NEGATIVE_EMBEDDING_TRIGGER}, (worst quality, low quality:1.4), "
    "(full body, wide shot, distant:1.5), bad anatomy, bad hands, text, error, "
    "missing fingers, extra digit, fewer digits, cropped, jpeg artifacts, signature, watermark"
)


@register_pipeline(
    name="closeup_anime",
    keywords=["closeup anime", "anime portrait", "anime face", "anime close-up", 
              "magical girl", "violet evergarden", "anime headshot"],
    description="High-quality anime closeup portraits with Violet Evergarden LoRA",
    types={}
)
def get_config(
        prompt: str,
        use_style_lora: bool = True,
        width: int = 512,
        height: int = 768,
        use_template: bool = True
) -> PipelineConfigs:
    """
    Get Closeup Anime pipeline configuration.
    
    Args:
        prompt: User's image description
        use_style_lora: Whether to apply the Violet Evergarden LoRA (recommended)
        width: Image width
        height: Image height
        use_template: Whether to wrap prompt in closeup template
        
    Returns:
        PipelineConfigs object
    """
    
    # 1. Prepare Prompt
    if use_template:
        final_prompt = CLOSEUP_TEMPLATE.format(prompt=prompt)
    else:
        final_prompt = prompt

    # 2. Configure LoRAs
    loras = []
    if use_style_lora:
        print("[CloseupAnime] Applied 'Violet Evergarden' style LoRA")
        loras.append(LoraConfig(
            lora_path=LORA_MODELS["violet_evergarden"],
            scale=0.6  # Moderate strength for style influence without overriding
        ))

    # 3. Return Config
    return PipelineConfigs(
        base_model=DIFFUSION_MODELS["facebomb"],
        output_dir=GENERATED_OUTPUT,
        prompt=final_prompt,
        neg_prompt=COMMON_NEGATIVE,
        style_type="anime",  # Auto-selects R-ESRGAN 4x+ Anime6B
        
        # Use default baked-in VAE (external VAE downloads failing)
        vae="default",
        embeddings=[EMBEDDING_FASTNEGATIVE],
        
        scheduler_name="dpm++_2m_karras",
        width=width,
        height=height,
        steps=25,
        cfg=7.0,
        clip_skip=2,  # Standard for most anime models
        
        lora=loras,
        c_net=[],
    )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def closeup_anime(prompt: str, **kwargs) -> PipelineConfigs:
    """Quick config for anime closeups."""
    return get_config(prompt, **kwargs)


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    test_prompts = [
        "girl with silver hair looking at viewer, blue eyes",
    ]
    
    for p in test_prompts:
        print(f"\n{'='*60}")
        print(f"Prompt: {p}")
        config = closeup_anime(p)
        print(f"Model: {config.base_model.name}")
        print(f"VAE: {config.vae}")
        print(f"Embeddings: {[e.name for e in config.embeddings]}")
        print(f"LoRAs: {[l.lora_path.name for l in config.lora]}")
        print(f"Final Prompt: {config.prompt}")
