"""
DifConsistency Pipeline - Photorealistic Consistency with specialized LoRAs
===========================================================================

Pipeline for generating ultra-consistent photorealistic images using the 
DifConsistency ecosystem (Checkpoint + VAE + Emb + LoRAs).

Features:
    - Integrated VAE and Negative Embedding support
    - "Photo" and "Detail" LoRA workflow support
    - Specialized prompts for high-fidelity photography

Usage:
    from apps.image_gen.pipeline.difconsistency import photo_consistency
    config = photo_consistency("a delicious burger on a wooden table")
"""

from pathlib import Path
from typing import Optional, Literal, List
import sys

# Add project root to path
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from configs.paths import (
    MODELS_DIR,
    IMAGE_GEN_OUTPUT_DIR,
    LORA_MODELS,
    MODEL_DIFCONSISTENCY,
    VAE_DIFCONSISTENCY,
    EMBEDDING_DIFCONSISTENCY_NEG
)

from apps.image_gen.pipeline.pipeline_types import PipelineConfigs, LoraConfig
from apps.image_gen.pipeline.registry import register_pipeline

# Output Path
GENERATED_OUTPUT = IMAGE_GEN_OUTPUT_DIR / "difconsistency"
GENERATED_OUTPUT.mkdir(parents=True, exist_ok=True)

# =============================================================================
# TEMPLATES & PROMPTS
# =============================================================================

# Standard template from DifConsistency documentation
PHOTO_TEMPLATE = (
    "Photography of a {{{prompt}}}, highly detailed, instagram flickr, sharp focus, "
    "canon 5d f16.0 style, natural lighting, ultra-realistic"
)

# The negative embedding trigger word (filename stem)
NEGATIVE_EMBEDDING_TRIGGER = "difConsistency_negative_v2" 
COMMON_NEGATIVE = f"{NEGATIVE_EMBEDDING_TRIGGER}, (worst quality, low quality:1.4), watermark, simplistic"


@register_pipeline(
    name="difconsistency",
    keywords=["difconsistency", "consistent", "photo consistency", "photography", 
              "photorealistic", "flickr", "instagram", "canon"],
    description="Ultra-consistent photorealistic images with DifConsistency ecosystem",
    types={
        "photo": "Photo LoRA for balanced realism",
        "detail": "Detail LoRA for texture and sharpness",
        "raw": "Base checkpoint only"
    }
)
def get_config(
        prompt: str,
        style: Literal["photo", "detail", "raw"] = "photo",
        width: int = 512,
        height: int = 768,
        use_template: bool = True
) -> PipelineConfigs:
    """
    Get DifConsistency pipeline configuration.
    
    Args:
        prompt: User's image description
        style: "photo" (Photo LoRA), "detail" (Detail LoRA), or "raw" (Base only)
        width: Image width
        height: Image height
        use_template: Whether to wrap prompt in standard photography template
        
    Returns:
        PipelineConfigs object
    """
    
    # 1. Prepare Prompt
    if use_template:
        final_prompt = PHOTO_TEMPLATE.format(prompt=prompt)
    else:
        final_prompt = prompt

    # 2. Configure LoRAs based on style
    loras = []
    
    if style == "photo":
        print("[DifConsistency] Mode: PHOTO (Balance + Realism)")
        loras.append(LoraConfig(
            lora_path=LORA_MODELS["dif_consistency_photo"],
            scale=0.5
        ))
    elif style == "detail":
        print("[DifConsistency] Mode: DETAIL (Texture + Sharpness)")
        loras.append(LoraConfig(
            lora_path=LORA_MODELS["dif_consistency_detail"],
            scale=0.55  # Recommended strength
        ))
    else:
        print("[DifConsistency] Mode: RAW (Base Checkpoint)")

    # 3. Return Config
    return PipelineConfigs(
        base_model=MODEL_DIFCONSISTENCY,
        output_dir=GENERATED_OUTPUT,
        prompt=final_prompt,
        neg_prompt=COMMON_NEGATIVE,
        style_type="realistic",  # Auto-selects R-ESRGAN 4x+
        
        # Critical: Use the custom VAE and Embedding
        vae=VAE_DIFCONSISTENCY,
        embeddings=[EMBEDDING_DIFCONSISTENCY_NEG],
        
        scheduler_name="dpm++_2m_karras",
        width=width,
        height=height,
        steps=25,
        cfg=6.0,  # Slightly lower CFG recommended for realism
        
        lora=loras,
        c_net=[],
    )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def photo_consistency(prompt: str, **kwargs) -> PipelineConfigs:
    """Quick config for photorealistic results."""
    return get_config(prompt, style="photo", **kwargs)

def detail_consistency(prompt: str, **kwargs) -> PipelineConfigs:
    """Quick config for high-detail results."""
    return get_config(prompt, style="detail", **kwargs)

def raw_consistency(prompt: str, **kwargs) -> PipelineConfigs:
    """Quick config using only the base checkpoint."""
    return get_config(prompt, style="raw", **kwargs)


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    test_prompts = [
        "a delicious burger on a wooden table",
        "portrait of a futuristic cyborg",
    ]
    
    for p in test_prompts:
        print(f"\n{'='*60}")
        print(f"Prompt: {p}")
        config = photo_consistency(p)
        print(f"Model: {config.base_model.name}")
        print(f"VAE: {config.vae.name}")
        print(f"Embeddings: {[e.name for e in config.embeddings]}")
        print(f"LoRAs: {[l.lora_path.name for l in config.lora]}")
