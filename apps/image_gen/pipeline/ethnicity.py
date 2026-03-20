"""
Ethnicity Portrait Pipeline
============================

Multiple models for generating realistic portraits of different ethnicities:
- asian: East Asian - Vietnamese/Japanese/Korean (asianrealisticSdlife) - trigger: girlvn01
- indian: Desi/South Asian (desiTadkaSD15Checkpoint) - trigger: desilatte, desimocha
- russian: Russian/Ukrainian/Eastern European (paamaRUSSIANWOMAN) - trigger: russia
- european: European/Western (kawaiiRealistic) - trigger: european
- chinese: Chinese realistic (majicmixRealistic) - trigger: chinese

Usage:
    from apps.image_gen.pipeline.ethnicity import get_ethnicity_config
    config = get_ethnicity_config("beautiful woman portrait", ethnicity="indian")
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
    DIFFUSION_MODELS,
    MODELS_DIR,
    LORA_MODELS
)

from apps.image_gen.pipeline.pipeline_types import PipelineConfigs, LoraConfig
from apps.image_gen.pipeline.registry import register_pipeline

# Output Path
GENERATED_OUTPUT = IMAGE_GEN_OUTPUT_DIR / "ethnicity"
GENERATED_OUTPUT.mkdir(parents=True, exist_ok=True)

# Ethnicity directory
ETHNICITY_DIR = MODELS_DIR / "diffusion" / "ethinicity"

# =============================================================================
# MODEL MAP - Models with trigger words
# =============================================================================

MODEL_MAP = {
    "asian": {
        "file": ETHNICITY_DIR / "asianrealisticSdlife_v60.safetensors",
        "trigger": "girlvn01",
        "description": "East Asian - Vietnamese/Japanese/Korean"
    },
    "indian": {
        "file": ETHNICITY_DIR / "desiTadkaSD15Checkpoint_v10.safetensors",
        "trigger": "desilatte, desimocha",
        "description": "South Asian - Indian/Desi"
    },
    "russian": {
        "file": ETHNICITY_DIR / "paamaRUSSIANWOMAN_paamaUKRAINEWOMANV1.safetensors",
        "trigger": "russia",
        "description": "Eastern European - Russian/Ukrainian"
    },
    "european": {
        "file": ETHNICITY_DIR / "kawaiiRealistic_v06.safetensors",
        "trigger": "european",
        "description": "Western European"
    },
    "chinese": {
        "file": ETHNICITY_DIR / "majicmixRealistic_v7.safetensors",
        "trigger": "chinese",
        "description": "Chinese realistic"
    },
}

# =============================================================================
# TEMPLATES
# =============================================================================

# Prompt template - trigger inserted automatically
ETHNICITY_TEMPLATE = (
    "{trigger}, {prompt}, "
    "beautiful, detailed face, natural skin, "
    "professional photography, 8k, masterpiece, best quality, ultra hd, detailed skin"
)

# Negative prompt for all ethnicities
ETHNICITY_NEGATIVE = (
    "(worst quality:2), (low quality:2), (normal quality:2), lowres, "
    "blurry, bad anatomy, bad hands, deformed, extra limbs, "
    "cartoon, anime, drawing, painting, disfigured, ugly, "
    "film grain, noise, grainy, text, watermark, signature, "
    "missing fingers, cropped, distorted, oversaturated"
)

# Ethnicity type
EthnicityType = Literal["asian", "indian", "russian", "european", "chinese"]


def _detect_ethnicity(prompt: str) -> EthnicityType:
    """
    Detect ethnicity from prompt keywords using scoring system.
    Returns: 'indian', 'asian', 'chinese', 'russian', or 'european'
    """
    import re
    prompt_lower = prompt.lower()
    
    # Ethnicity keywords with weights
    ethnicity_scores = {
        "indian": {
            "indian": 3, "desi": 3, "south asian": 2, "bollywood": 2, "hindi": 2,
            "punjabi": 2, "tamil": 2, "bengali": 2, "saree": 2, "sari": 2,
            "mumbai": 1, "delhi": 1, "hindu": 1, "curry": 1, "bindi": 2,
        },
        "russian": {
            "russian": 3, "ukrainian": 3, "slavic": 2, "eastern european": 2,
            "moscow": 2, "siberian": 1, "slav": 2, "russia": 3, "ukraine": 2,
        },
        "chinese": {
            "chinese": 3, "china": 3, "shanghai": 2, "beijing": 2, "hong kong": 2,
            "mandarin": 1, "cantonese": 1, "qipao": 2, "hanfu": 2, "dynasty": 1,
        },
        "asian": {
            "asian": 2, "vietnamese": 3, "japanese": 3, "korean": 3, "k-pop": 2,
            "thai": 2, "vietnam": 2, "japan": 2, "korea": 2, "tokyo": 1,
            "seoul": 1, "anime": 1, "idol": 2, "kpop": 2,
        },
        "european": {
            "european": 3, "western": 2, "american": 2, "british": 2, "french": 2,
            "german": 2, "italian": 2, "spanish": 2, "blonde": 2, "caucasian": 2,
            "white": 1, "scandinavian": 2, "nordic": 2, "celtic": 1,
        },
    }
    
    # Calculate scores for each ethnicity
    scores = {ethnicity: 0 for ethnicity in ethnicity_scores}
    
    for ethnicity, keywords in ethnicity_scores.items():
        for keyword, weight in keywords.items():
            if re.search(rf'\b{keyword}\b', prompt_lower):
                scores[ethnicity] += weight
    
    # Get the ethnicity with highest score
    best_ethnicity = max(scores, key=scores.get)
    
    # If no keywords matched, default to asian (most versatile)
    if scores[best_ethnicity] == 0:
        return "asian"
    
    return best_ethnicity


@register_pipeline(
    name="ethnicity",
    keywords=["indian", "asian", "russian", "chinese", "european", "desi", "korean",
              "japanese", "vietnamese", "slavic", "ukrainian", "bollywood", "kpop"],
    description="Realistic portraits of different ethnicities with specialized models",
    types={
        "asian": "East Asian (Vietnamese/Japanese/Korean)",
        "indian": "South Asian/Desi portraits",
        "russian": "Eastern European (Russian/Ukrainian)",
        "european": "Western European",
        "chinese": "Chinese realistic"
    }
)
def get_ethnicity_config(
        prompt: str,
        ethnicity: Optional[EthnicityType] = None,
        aspect: Optional[Literal["portrait", "mid", "wide"]] = "portrait",
        auto_detect: bool = True
) -> PipelineConfigs:
    """
    Get Ethnicity Portrait pipeline configuration.
    
    Args:
        prompt: Your portrait description
        ethnicity: "asian", "indian", "russian", "european", or "chinese"
        aspect: "portrait" (512x768), "mid" (768x768), or "wide" (960x540)
        auto_detect: If True, detect ethnicity from prompt keywords
        
    Returns:
        PipelineConfigs ready for engine.generate()
    """
    
    # Aspect ratio dimensions
    ASPECT_RATIOS = {
        "portrait": (512, 768),
        "mid": (768, 768),
        "wide": (960, 540),
    }
    
    # Auto-detect ethnicity if not specified
    if auto_detect and ethnicity is None:
        ethnicity = _detect_ethnicity(prompt)
    elif ethnicity is None:
        ethnicity = "asian"
    
    # Get model info
    model_info = MODEL_MAP.get(ethnicity, MODEL_MAP["asian"])
    selected_model = model_info["file"]
    trigger = model_info["trigger"]
    
    # Get dimensions
    width, height = ASPECT_RATIOS.get(aspect, ASPECT_RATIOS["portrait"])
    
    print(f"🌍 [Ethnicity] Mode: {ethnicity.upper()} ({model_info['description']})")
    print(f"   Model: {selected_model.name}")
    print(f"   Trigger: {trigger}")
    print(f"   Aspect: {aspect} ({width}x{height})")
    
    # Build final prompt
    final_prompt = ETHNICITY_TEMPLATE.format(trigger=trigger, prompt=prompt)

    # LoRA Logic
    # LoRA Logic
    loras = []
    
    # Robust Polaroid Detection
    # Matches: polaroid, poloroid, instant photo, instax
    import re
    if re.search(r'\b(polaroid|poloroid|instax|instant photo)\b', prompt.lower()):
        print("📸 Polaroid Style Detected: Adding LoRA")
        loras.append(LoraConfig(
            lora_path=LORA_MODELS["polaroid"],
            scale=0.8
        ))
    
    return PipelineConfigs(
        base_model=selected_model,
        output_dir=GENERATED_OUTPUT,
        prompt=final_prompt,
        neg_prompt=ETHNICITY_NEGATIVE,
        vae="realistic",  # ft_mse VAE works well
        style_type="realistic",  # Auto-selects R-ESRGAN 4x+
        embeddings=[],
        scheduler_name="dpm++_2m_karras",  # Common in CivitAI examples
        width=width,
        height=height,
        steps=25,
        cfg=7.5,
        lora=loras,
        c_net=[],
    )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def asian_portrait(prompt: str, **kwargs) -> PipelineConfigs:
    """East Asian portrait (Vietnamese/Japanese/Korean)."""
    return get_ethnicity_config(prompt, ethnicity="asian", **kwargs)

def indian_portrait(prompt: str, **kwargs) -> PipelineConfigs:
    """South Asian/Desi portrait (Indian)."""
    return get_ethnicity_config(prompt, ethnicity="indian", **kwargs)

def russian_portrait(prompt: str, **kwargs) -> PipelineConfigs:
    """Eastern European portrait (Russian/Ukrainian)."""
    return get_ethnicity_config(prompt, ethnicity="russian", **kwargs)

def european_portrait(prompt: str, **kwargs) -> PipelineConfigs:
    """Western European portrait."""
    return get_ethnicity_config(prompt, ethnicity="european", **kwargs)

def chinese_portrait(prompt: str, **kwargs) -> PipelineConfigs:
    """Chinese realistic portrait."""
    return get_ethnicity_config(prompt, ethnicity="chinese", **kwargs)


if __name__ == "__main__":
    print("Testing ethnicity pipeline configurations...")
    
    test_cases = [
        ("beautiful indian woman in traditional saree",),
        ("korean idol with perfect makeup",),
        ("russian model with blue eyes",),
        ("elegant european woman portrait",),
        ("chinese beauty in silk dress",),
    ]
    
    for (prompt,) in test_cases:
        print(f"\n{'='*60}")
        print(f"Prompt: {prompt[:50]}...")
        config = get_ethnicity_config(prompt)
        print(f"  Model: {config.base_model.name}")
        print(f"  Size: {config.width}x{config.height}")
        print(f"  Steps: {config.steps}")
        print("  ✅ OK")
