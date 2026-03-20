"""
Unified NSFW Pipeline (Porn/Futa/Trans)
=======================================

Comprehensive pipeline for high-quality NSFW generation.
Integrates:
- Realistic Lazy Mix (General)
- URPM (Uber Realistic Porn Merge) - High realism
- PornMaster Pro (Subreddit aesthetics)

LoRAs:
- Porn/Amateur (Global enhancer) -> Always active
- Uniform Slut (Trigger: "uniform")
- Transexual Woman (Trigger: "futa", "trans", "shemale")

User instructions:
"firat lora should be used always the second lora should be used to only if iys has uniform porn"
"""

import random
import re
from pathlib import Path
from typing import Literal, Optional, List, Tuple

import sys
# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from configs.paths import DIFFUSION_MODELS, IMAGE_GEN_OUTPUT_DIR, LORA_DIR, LORA_MODELS
from apps.image_gen.pipeline.pipeline_types import PipelineConfigs, LoraConfig
from apps.image_gen.pipeline.registry import register_pipeline

# =============================================================================
# CONSTANTS & CONFIGS
# =============================================================================

PORN_OUTPUT_DIR = IMAGE_GEN_OUTPUT_DIR / "nsfw"
PORN_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Triggers for PornMaster
PORNMASTER_TRIGGERS = [
    "reddit", "r/gonewild", "r/nsfw", "r/RealGirls", "r/cumsluts", 
    "r/LegalTeens", "r/collegesluts", "r/AsiansGoneWild", "r/pussy", 
    "r/milf", "r/adorableporn", "r/ass", "r/Nude_Selfie", "r/pawg", 
    "r/boobs", "r/celebnsfw", "r/bigasses", "r/juicyasians", "r/Latinas", 
    "r/GodPussy", "r/Amateur", "r/xsmallgirls", "r/18_19", "r/Gonewild18", 
    "r/asshole", "r/workgonewild", "r/nsfwcosplay", "r/palegirls", "r/paag", 
    "r/asstastic", "r/Upskirt", "r/TooCuteForPorn", "r/TinyTits", 
    "r/FitNakedChicks", "r/altgonewild", "r/traps", "r/FemBoys", 
    "r/GWCouples", "r/Boobies", "r/CuteLittleButts", "r/GirlswithGlasses", 
    "r/assholegonewild", "r/PetiteGoneWild", "r/BDSM"
]

# Common Aesthetics for PornMaster
PORNMASTER_QUALITY = "best quality, medium quality, high quality, best aesthetic"

# Models
MODELS = {
    "lazy_mix": {
        "file": DIFFUSION_MODELS["realistic_lazy_mix"],
        "trigger": "RAW photo, amateur, instagram, reddit, (film grain:1.2), Fujifilm XT3",
        "negative": "badhandv4, (deformed iris, deformed pupils, semi-realistic, cgi, 3d, sketch, cartoon, anime:1.4), text, close up, cropped, out of frame, worst quality, low quality, jpeg artifacts, ugly, duplicate, morbid, mutilated, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, mutation, deformed, blurry, dehydrated, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck",
        "description": "Realistic Lazy Mix - General Purpose",
        "steps": 25,
        "cfg": 5.0,
        "scheduler": "dpm++_sde_karras"
    },
    "urpm": {
        "file": DIFFUSION_MODELS["urpm"],
        "trigger": "raw photo, hyperrealistic, 8k, uhd",
        "negative": "(worst quality:2), (low quality:2), (monochrome), (grayscale), (bad_prompt_version2:0.8), (bad-hands-5:1.0), (easynegative:0.8), acne, skin spots, age spot, skin blemishes, bad feet, cropped, poorly drawn, extra limbs, bad anatomy, disfigured, deformed",
        "description": "URPM - Uber Realistic",
        "steps": 26,
        "cfg": 6.0,
        "scheduler": "dpm++_2m_karras" 
    },
    "pornmaster": {
        "file": DIFFUSION_MODELS["pornmaster"],
        "trigger": f"{PORNMASTER_QUALITY}, reddit",
        "negative": "(worst quality:2), (low quality:2), (normal quality:2), lowres, normal quality, ((monochrome)), ((grayscale)), skin spots, acnes, skin blemishes, age spot, glans, (bad hands, bad anatomy, bad body, bad face, bad teeth, bad arms, bad legs, deformities:1.3)",
        "description": "PornMaster Pro V8 - Subreddit Style",
        "steps": 25,
        "cfg": 6.0,
        "scheduler": "dpm++_2m_karras"
    },
    "realistic_futa": {
        "file": DIFFUSION_MODELS["realistic_futa"],
        "trigger": "hyperrealistic, 8k, uhd, best quality",
        "negative": "(worst quality:2), (low quality:2), (monochrome), (grayscale), bad anatomy, bad hands, bad body, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality",
        "description": "Realistic Futa - Specialized for Trans/Futa",
        "steps": 25,
        "cfg": 6.0,
        "scheduler": "dpm++_2m_karras",
        "model_config": "runwayml/stable-diffusion-v1-5"
    }
}

ModelType = Literal["lazy_mix", "urpm", "pornmaster", "realistic_futa"]

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _detect_model(prompt: str) -> str:
    """Detect model based on keywords."""
    p_lower = prompt.lower()
    
    # Priority 1: Trans/Futa (User Request)
    trans_keywords = ["trans", "futa", "shemale", "penis", "dickgirl", "t-girl", "testicles", "erection", "cock"]
    if any(k in p_lower for k in trans_keywords):
        return "realistic_futa"
    
    # PornMaster triggers (subreddit style)
    if "reddit" in p_lower or any(trigger.lower() in p_lower for trigger in PORNMASTER_TRIGGERS):
        return "pornmaster"
            
    if "urpm" in p_lower or "uber" in p_lower or "hyperrealistic" in p_lower or "amateur" in p_lower or "instagram" in p_lower or "mix" in p_lower:
        return "urpm"
        
    if "lazy" in p_lower:
        return "lazy_mix"
        
    # Default to URPM (Stable on 4GB VRAM)
    return "urpm"


def _detect_aspect(prompt: str) -> Tuple[int, int]:
    """Detect aspect ratio (portrait, landscape, square). Max 768px."""
    p_lower = prompt.lower()
    
    if "landscape" in p_lower or "wide" in p_lower or "16:9" in p_lower:
        return (768, 512)
    if "square" in p_lower or "1:1" in p_lower:
        return (512, 512)
    if "portrait" in p_lower or "vertical" in p_lower or "9:16" in p_lower:
        return (512, 768)
        
    # Default Portrait (9:16 approx)
    return (512, 768)


@register_pipeline(
    name="nsfw",
    keywords=["nsfw", "porn", "nude", "naked", "subreddit", "reddit", "gonewild",
              "uncensored", "explicit", "futa", "trans", "amateur", "uniform"],
    description="Comprehensive NSFW generation with multiple models and LoRAs",
    types={
        "lazy_mix": "Realistic Lazy Mix - General purpose NSFW",
        "urpm": "URPM - Uber Realistic Porn Merge",
        "pornmaster": "PornMaster Pro V8 - Subreddit aesthetics",
        "realistic_futa": "Specialized for Trans/Futa content"
    }
)
def get_porn_config(
    prompt: str,
    aspect_ratio: Optional[str] = None,
    model_override: Optional[ModelType] = None,
    force_trans: bool = False,
    force_uniform: bool = False
) -> PipelineConfigs:
    """
    Generate configurations for NSFW pipeline.
    """
    
    # 1. Determine Model
    model_key = model_override if model_override else _detect_model(prompt)
    model_data = MODELS.get(model_key, MODELS["lazy_mix"])
    print(f"Model: {model_data['description']}")
    
    # 2. Dimensions
    if aspect_ratio == "landscape":
        width, height = 768, 512
    elif aspect_ratio == "square":
        width, height = 512, 512
    elif aspect_ratio == "portrait":
        width, height = 512, 768
    else:
        width, height = _detect_aspect(prompt)
    
    print(f"Size: {width}x{height}")
        
    # 3. LoRA Logic & Prompt Injection
    loras: List[LoraConfig] = []
    current_prompt = prompt
    p_lower = prompt.lower()
    
    # Global LoRA: Porn/Amateur (Always On)
    # Using 'porn_amateur' from LORA_MODELS (teenBody-v1.safetensors)
    loras.append(LoraConfig(
        lora_path=LORA_MODELS["porn_amateur"],
        scale=0.6 
    ))
    
    # Uniform LoRA
    if force_uniform or "uniform" in p_lower:
        print("Uniform LoRA Activated")
        loras.append(LoraConfig(
            lora_path=LORA_MODELS["uniform_slut"],
            scale=0.8,
            lora_trigger_word="slut uniform"
        ))
        if "slut uniform" not in p_lower:
             current_prompt += ", slut uniform"
        
    # Trans LoRA
    trans_keywords = ["trans", "futa", "shemale", "penis", "dickgirl", "t-girl", "testicles", "erection", "cock"]
    if force_trans or any(k in p_lower for k in trans_keywords):
        print("Trans/Futa LoRA Activated")
        loras.append(LoraConfig(
            lora_path=LORA_MODELS["trans_woman"],
            scale=0.85,
            lora_trigger_word="1girl futanari penis erection breasts testicles"
        ))
        if "futanari" not in p_lower and "penis" not in p_lower:
            current_prompt += ", 1girl futanari penis erection breasts testicles"

    # 4. Construct Final Prompt
    # Inject Model Trigger
    final_prompt = f"{model_data['trigger']}, {current_prompt}"
    
    # Inject NSFW Terms if missing (User Request: "fetch me high quality naked nsfw pic evr=erytine")
    nsfw_terms = ["naked", "nude", "nsfw", "uncensored"]
    if not any(t in p_lower for t in nsfw_terms):
         final_prompt += ", naked, nude, nsfw, uncensored, explicit"
    
    # Add subreddit tags for PornMaster if generic
    if model_key == "pornmaster":
        if not any(sub.lower() in p_lower for sub in PORNMASTER_TRIGGERS):
            final_prompt += ", r/RealGirls, r/nsfw, r/gonewild"

    return PipelineConfigs(
        base_model=model_data["file"],
        output_dir=PORN_OUTPUT_DIR,
        prompt=final_prompt,
        neg_prompt=model_data["negative"],
        style_type="realistic",  # Auto-selects R-ESRGAN 4x+
        width=width,
        height=height,
        steps=model_data["steps"],
        cfg=model_data["cfg"],
        scheduler_name=model_data.get("scheduler", "dpm++_2m_karras"),
        model_config=model_data.get("model_config"),
        lora=loras
    )

# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def draw_porn(prompt: str, **kwargs) -> PipelineConfigs:
    """General NSFW generation."""
    return get_porn_config(prompt, **kwargs)

def draw_futa(prompt: str, **kwargs) -> PipelineConfigs:
    """Futa/Trans specific generation."""
    return get_porn_config(prompt, force_trans=True, **kwargs)


# =============================================================================
# TEST
# =============================================================================
if __name__ == "__main__":
    print("Testing Porn Pipeline...")
    
    prompts = [
        "schoolgirl in uniform classroom",
        "futanari with large erection",
        "r/gonewild selfie in mirror",
        "lazy morning in bed"
    ]
    
    for p in prompts:
        print(f"\nPrompt: {p}")
        c = get_porn_config(p)
        print(f"Model: {c.base_model.name}")
        print(f"LoRAs: {[l.lora_path.name for l in c.lora]}")
