from typing import List, Dict, Optional, Union, Literal
from dataclasses import dataclass, field
from pathlib import Path

# =============================================================================
# STANDARD ASPECT RATIOS (use these across all pipelines)
# =============================================================================

STANDARD_ASPECTS = {
    "portrait": (512, 768),    # Vertical - characters, people
    "landscape": (768, 512),   # Horizontal - scenes, environments
    "normal": (512, 512),      # Square - icons, objects
}

# ControlNet helper class for strict writings
@dataclass
class ControlNetConfig:
    control_type: Literal["canny", "depth", "openpose"]
    image_path: Union[str, Path]  # The generic 'image' input (depth map, canny edge, etc.)
    scale: float = 1.0
    
    def __post_init__(self):
        if isinstance(self.image_path, str):
            self.image_path = Path(self.image_path)
        if not self.image_path.exists(): raise FileNotFoundError(self.image_path)
        if not self.image_path.is_file(): raise FileNotFoundError('image path must be a file path')
        

# Lora helper class for strict writing
@dataclass
class LoraConfig:

    lora_path: Union[str, Path]
    scale: float = 1.0
    lora_trigger_word: Optional[str] = None

    def __post_init__(self):
        if isinstance(self.lora_path, str):
            self.lora_path = Path(self.lora_path)
        if not self.lora_path.is_file(): raise FileNotFoundError('lora_path must be a file path')

@dataclass
class PipelineConfigs:
    
    # --- 1. MANDATORY FIELDS (Must come first) ---
    base_model: Union[str, Path]      # Diffusion checkpoints paths.
    output_dir: Union[str, Path]      # Output paths for the generated image.
    prompt: str                       # The style of image user needed.
    vae: Optional[Union[
        Literal["anime", "realistic", "semi-realistic", "default"],
        str,
        Path
    ]] = 'realistic'                  # Default: realistic VAE for general use
    
    # --- 2. PROMPTS & TRIGGERS ---
    embeddings: List[Path] = field(default_factory=list) # Textual inversion embeddings to load
    neg_prompt: str = ''              # The style you dont want in your image.
    triggers: Optional[str] = None    # Words that can trigger a particular style.

    # --- 3. STYLE TYPE (for auto upscaler selection) ---
    style_type: Literal["anime", "realistic"] = "realistic"
    # anime → R-ESRGAN 4x+ Anime6B
    # realistic → R-ESRGAN 4x+

    # --- 4. BEHAVIOR ---
    scheduler_name: Literal[
        "euler_a",                  # Fast, low VRAM, good default
        "dpm++_2m_karras",          # Best quality, deterministic, low VRAM
        "dpm++_sde_karras",         # Stochastic, natural variation, medium VRAM
        "dpm++_2m_sde_karras",      # Hybrid: 2M + SDE, balanced
        "ddim",                     # Deterministic, good for img2img
        "lms"                       # Smooth gradients, needs more steps
    ] = "euler_a"
    add_details: bool = False       # If True, run Diffusion upscale first (expensive)
 
    # --- 5. NUMBERS (int & float) ---
    height: int = 512               # Default Height.
    width: int = 768                # Default Width.
    steps: int = 25                 # Default steps for sd 1.5 models.
    cfg: float = 7.0                # Default classifier free guidance (CFG) scale
    # - Lower (< 5): More natural/realistic lighting, but the AI might ignore prompt details.
    # - Higher (> 7): Follows prompt strictly, but images may look "burnt" or unnatural.

    # --- 6. OPTIONAL INTEGERS ---
    clip_skip: Optional[int] = None   # Paricular model(not for all to generate a creative style)
    seed: Optional[int] = None        # To generate a particular type of image (seed control img_style)

    # --- 7. BOOLEANS ---
    img_template: bool = False

    # --- 8. LORA ---
    lora: List[LoraConfig] = field(default_factory=list)  # Defaultfactory usecase >>> create new list in every pipeline

    # --- 9. CONTROLNET ---
    c_net: List[ControlNetConfig] = field(default_factory=list)  # Mostly used for getting the particular noise from the image

    # --- 10. CONFIG FILES ---
    model_config: Optional[str] = None # HuggingFace model config (for safetensors that need base config)

    # --- 10. POST INIT VALIDATION ---
    def __post_init__(self):
        # Convert strings to Path objects
        if isinstance(self.base_model, str):
            self.base_model = Path(self.base_model)
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)
            
        # Ensure dimensions are multiples of 8
        if self.height % 8 != 0:
            self.height = ((self.height // 8) * 8)
        if self.width % 8 != 0:
            self.width = ((self.width // 8) * 8)
            
        # Inject triggers into prompt
        if self.triggers:
            if self.triggers.lower() not in self.prompt.lower():
                self.prompt = f'{self.triggers} {self.prompt}'
                
        # Validation checks
        if not self.base_model.exists(): raise FileNotFoundError(self.base_model)
        if not self.base_model.is_file(): raise FileNotFoundError('base_model must be a file path')
        
        if self.steps <= 0: raise ValueError("Steps needs to be more than 0.")
        if self.steps >= 45: raise ValueError("Steps needs to be less than 45.")
        
        if self.cfg <= 0: raise ValueError("CFG needed to be more than 0")
        if self.cfg >= 15: raise ValueError("CFG needed to be less than 15")
        
        if not self.output_dir.exists(): self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if self.scheduler_name == "dpm++_2m_karras" and self.steps > 26:
            raise ValueError("dpm++_2m_karras is unsafe above 26 steps on low VRAM")