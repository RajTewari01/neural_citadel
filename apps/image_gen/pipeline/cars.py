"""
Cars Pipeline - Based on Proven CarDiffusionEngine
===================================================

This pipeline is adapted from the user's working car_diffusion_model_v2.py
which produces high-quality car images.

Key settings from working script:
- DPMSolverMultistepScheduler with karras sigmas
- Prompt: "{trigger}, {prompt}, clean, smooth, whole car, noise free, best quality, 16k, masterpiece, ultra hd"
- Negative: "film grain, noise, grainy, ISO noise, speckles..." (no grain!)
- CFG: 7.0, Steps: 25
- Manual LoRA injection for reliability

Usage:
    from apps.image_gen.pipeline.cars import get_car_config
    config = get_car_config("midnight blue sports car", style="rx7")
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
    MODEL_REALISTIC_VISION
)

from apps.image_gen.pipeline.pipeline_types import PipelineConfigs, LoraConfig
from apps.image_gen.pipeline.registry import register_pipeline

# Output Path
GENERATED_OUTPUT = IMAGE_GEN_OUTPUT_DIR / "cars"
GENERATED_OUTPUT.mkdir(parents=True, exist_ok=True)

# =============================================================================
# LORA MAP - Exact settings from working script
# =============================================================================

CAR_STYLE_MAP = {
    "sketch":    {"lora_key": "car_sketch",    "trigger": "car sketch",              "strength": 1.3},
    "sedan":     {"lora_key": "car_sedan",     "trigger": "car",                     "strength": 0.8},
    "retro":     {"lora_key": "car_retro",     "trigger": "retromoto",               "strength": 0.8},
    "speedtail": {"lora_key": "car_speedtail", "trigger": "speedtail sport car",     "strength": 0.8},
    "f1":        {"lora_key": "car_f1",        "trigger": "f1lm sports car",         "strength": 0.8},
    "mx5":       {"lora_key": "car_mx5",       "trigger": "mx5na",                   "strength": 0.8},
    "autohome":  {"lora_key": "car_autohome",  "trigger": "autohome car(hqhs5)",     "strength": 0.8},
    "amsdr":     {"lora_key": "car_amsdr",     "trigger": "amsdr",                   "strength": 0.8},
    # New additions
    "rx7":       {"lora_key": "car_rx7",       "trigger": "fd3s car vehicle",        "strength": 0.8},
    "jetcar":    {"lora_key": "car_jetcar",    "trigger": "Hanshin5000",             "strength": 0.8},
    "motorbike": {"lora_key": "car_motorbike", "trigger": "yhmotorbike",             "strength": 0.8},
}

CarStyle = Literal[
    "sketch", "sedan", "retro", "speedtail", "f1", "mx5", 
    "autohome", "amsdr", "rx7", "jetcar", "motorbike"
]

# =============================================================================
# PROMPTS - Exact format from working script (PROVEN TO WORK!)
# =============================================================================

# The magic template that produces clean cars
CAR_PROMPT_SUFFIX = (
    "clean, smooth, whole car, noise free, "
    "best quality, 16k, masterpiece, ultra hd"
)

# Critical: Blocks film grain and noise - key to clean output
CAR_NEGATIVE = (
    "film grain, noise, grainy, ISO noise, speckles, deformed, "
    "cropped out, partial car, bad anatomy, cropped out, "
    "cartoon, text, low quality, watermark, no duplicate, blur, ugly, "
    "distorted, deformed, extra wheels, oversaturated, small details"
)

# Train/JetCar uses different prompt style
TRAIN_PROMPT_SUFFIX = (
    "train, locomotive, railroad tracks, train station, "
    "best quality, ultra-detailed, illustration, scenery"
)

TRAIN_NEGATIVE = (
    "(worst quality:1.4), (low quality:1.4), text, error, cropped, signature, "
    "watermark, username, monochrome, nsfw, car, road, highway"
)


def _detect_car_style(prompt: str) -> CarStyle:
    """Detect car style from prompt keywords using scoring system."""
    import re
    prompt_lower = prompt.lower()
    
    # Style keywords with weights - based on CivitAI prompt analysis
    style_keywords = {
        "sketch": {"sketch": 3, "drawing": 2, "pencil": 2, "line art": 2, "lineart": 2, "illustration": 1},
        "sedan": {
            "sedan": 3, "saloon": 2, "family car": 2, "four door": 1, "4 door": 1,
            "luxury car": 2, "executive": 1, "bmw": 2, "mercedes": 2, "audi": 2,
            "everyday": 1, "commute": 1
        },
        "retro": {
            "retro": 3, "vintage": 3, "classic": 2, "old school": 2, "retromoto": 3,
            "70s": 2, "80s": 2, "60s": 2, "50s": 2, "1950s": 2, "1960s": 2, "1970s": 2, "1980s": 2,
            "porsche": 3, "steampunk": 2, "bioshockpunk": 2, "film grain": 1, "grainy": 1,
            "kodachrome": 2, "analog": 1, "retro car": 3, "old car": 2, "classic car": 3
        },
        "speedtail": {
            "speedtail": 3, "mclaren speedtail": 3, "golden hour": 1, "lonely road": 1,
            "sport car": 2, "sportscar": 2, "hypercar": 2
        },
        "f1": {
            "f1": 3, "f1lm": 3, "mclaren f1": 3, "mclaren": 3,
            "formula": 2, "racing": 2, "racecar": 2, "formula one": 3, "race car": 2,
            "synthwave": 1, "lightwave": 1
        },
        "mx5": {"mx5": 3, "miata": 3, "mazda mx": 3, "roadster": 2, "mx-5": 3, "na": 1},
        "autohome": {"autohome": 3, "chinese car": 2, "byd": 2, "geely": 2, "hqhs5": 3},
        "amsdr": {"taxi": 3, "cab": 2, "yellow cab": 3, "amsdr": 3, "street": 1, "city": 1, "urban": 1, "new york": 1},
        "rx7": {
            "rx7": 3, "rx-7": 3, "fd3s": 3, "mazda rx": 3, "fd": 2,
            "rotary": 2, "wankel": 2, "jdm": 2, "japanese car": 2,
            "drift": 2, "initial d": 2, "night": 1, "cyberpunk": 1, "tokyo": 1, "neon": 1
        },
        "jetcar": {"train": 3, "locomotive": 3, "railway": 2, "railroad": 2, "station": 1, "hanshin": 3},
        "motorbike": {
            "motorbike": 3, "motorcycle": 3, "bike": 2, "yhmotorbike": 3,
            "yamaha": 2, "honda": 1, "harley": 2, "superbike": 2, "rider": 1
        },
    }
    
    # Calculate scores
    scores = {style: 0 for style in style_keywords}
    
    for style, keywords in style_keywords.items():
        for keyword, weight in keywords.items():
            if re.search(rf'\b{keyword}\b', prompt_lower):
                scores[style] += weight
    
    # Get best style
    best_style = max(scores, key=scores.get)
    
    # Default to amsdr if no keywords matched (general purpose)
    if scores[best_style] == 0:
        return "amsdr"
    
    return best_style


@register_pipeline(
    name="car",
    keywords=["car", "vehicle", "automobile", "sedan", "rx7", "rx-7", "mx5", "miata", "f1", 
              "speedtail", "retro", "vintage", "classic car", "taxi", "train", "motorbike"],
    description="Car generation with LoRA styles for various vehicle types",
    types={
        "sketch": "Car sketch drawing style",
        "sedan": "Generic sedan/family car",
        "retro": "Vintage/classic cars (Porsche, 70s-80s)",
        "speedtail": "McLaren Speedtail hypercar",
        "f1": "McLaren F1 racing style",
        "mx5": "Mazda MX5/Miata roadster",
        "autohome": "Chinese car style",
        "amsdr": "Taxi/urban street cars",
        "rx7": "Mazda RX7 FD3S JDM",
        "jetcar": "Trains and locomotives",
        "motorbike": "Motorcycles and bikes"
    }
)
def get_car_config(
        prompt: str,
        style: CarStyle = None,
        width: int = 768,
        height: int = 512,
        auto_detect: bool = True,
) -> PipelineConfigs:
    """
    Get Car pipeline configuration using proven settings.
    
    Args:
        prompt: Your description (e.g., "midnight blue sports car on mountain road")
        style: Car LoRA style to use (auto-detected if None)
        width: Image width (default 768)
        height: Image height (default 512)
        auto_detect: If True, detect style from prompt keywords
    
    Returns:
        PipelineConfigs ready for engine.generate()
    """
    
    # Auto-detect style if not specified
    if auto_detect and style is None:
        style = _detect_car_style(prompt)
    elif style is None:
        style = "amsdr"
    
    style_info = CAR_STYLE_MAP.get(style)
    if not style_info:
        print(f"[Cars] Warning: Invalid style '{style}', defaulting to 'amsdr'")
        style_info = CAR_STYLE_MAP["amsdr"]
        style = "amsdr"

    trigger = style_info["trigger"]
    
    # Build prompt in proven format: "{trigger}, {prompt}, clean, smooth..."
    if style == "jetcar":
        # Train uses different template
        final_prompt = f"{trigger}, {prompt}, {TRAIN_PROMPT_SUFFIX}"
        negative_prompt = TRAIN_NEGATIVE
    else:
        # Standard car template (proven to work)
        final_prompt = f"{trigger}, {prompt}, {CAR_PROMPT_SUFFIX}"
        negative_prompt = CAR_NEGATIVE

    # Configure LoRA
    lora_path = LORA_MODELS[style_info["lora_key"]]
    lora_config = LoraConfig(
        lora_path=lora_path,
        scale=style_info["strength"]
    )
    
    print(f"[Cars] Mode: {style.upper()} | LoRA: {lora_path.name} | Trigger: '{trigger}'")

    return PipelineConfigs(
        base_model=MODEL_REALISTIC_VISION,
        output_dir=GENERATED_OUTPUT,
        prompt=final_prompt,
        neg_prompt=negative_prompt,
        vae='realistic',  # ft_mse VAE for photorealistic output
        style_type="realistic",  # Auto-selects R-ESRGAN 4x+
        embeddings=[],
        # DPMSolverMultistepScheduler with karras - matches your working script
        scheduler_name="dpm++_2m_karras",
        width=width,
        height=height,
        steps=25,      # From your working script
        cfg=7.0,       # From your working script (guidance_scale=7.0)
        lora=[lora_config],
        c_net=[],
    )


if __name__ == "__main__":
    # Quick verification
    print("Testing car pipeline configurations...")
    
    test_cases = [
        ("amsdr", "classic yellow taxi, new york city, times square, busy street"),  # AMSDR = any country taxi
        ("rx7", "midnight blue sports car, mountain road, sunset"),
        ("jetcar", "train arriving at station, cherry blossoms"),
        ("retro", "vintage red convertible, coastal highway, golden hour"),
    ]
    
    for style, prompt in test_cases:
        print(f"\n{'='*60}")
        config = get_car_config(prompt, style=style)
        print(f"  Full Prompt: {config.prompt[:80]}...")
        print(f"  Negative: {config.neg_prompt[:50]}...")
        print(f"  Steps: {config.steps}, CFG: {config.cfg}")
        print("  ✅ OK")
