"""
Diffusion QR Code Pipeline
==========================

Configuration pipeline for AI-generated artistic QR codes using Stable Diffusion + ControlNet.
This pipeline creates a base QR config optimized for diffusion processing.

The actual diffusion happens in a subprocess running in the image_venv environment.

Usage:
    from apps.qr_studio.pipeline.diffusion import get_diffusion_config
    
    config = get_diffusion_config(
        data={"url": "https://example.com"},
        template_type="url",
        prompt="forest theme, natural",
    )
    
    # Generate base QR, then run diffusion subprocess
    base_path = engine.generate(config)
    final_path = engine.run_diffusion_subprocess(base_path, config.diffusion_prompt)
"""

from pathlib import Path
from typing import Optional, Dict, Literal, Union
import sys

# =============================================================================
# PATH SETUP
# =============================================================================

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# =============================================================================
# IMPORTS
# =============================================================================

from configs.paths import QR_CODE_DIFFUSION_DIR
from apps.qr_studio.pipeline.pipeline_types import QRConfig, TemplateType

# =============================================================================
# ENSURE DIRECTORIES
# =============================================================================

QR_CODE_DIFFUSION_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# DIFFUSION CONFIG DATACLASS EXTENSION
# =============================================================================

class DiffusionQRConfig(QRConfig):
    """
    Extended QRConfig with diffusion-specific settings.
    The base QRConfig is used to generate an initial high-contrast QR,
    then diffusion_* fields control the AI transformation.
    """
    
    # Diffusion parameters (passed to subprocess)
    diffusion_prompt: str = ""
    diffusion_model: str = "realistic_digital"
    diffusion_control_scale: float = 1.6
    diffusion_guidance_scale: float = 7.0
    diffusion_steps: int = 25
    diffusion_seed: Optional[int] = None
    
    def __init__(
        self,
        diffusion_prompt: str = "",
        diffusion_model: str = "realistic_digital",
        diffusion_control_scale: float = 1.6,
        diffusion_guidance_scale: float = 7.0,
        diffusion_steps: int = 25,
        diffusion_seed: Optional[int] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.diffusion_prompt = diffusion_prompt
        self.diffusion_model = diffusion_model
        self.diffusion_control_scale = diffusion_control_scale
        self.diffusion_guidance_scale = diffusion_guidance_scale
        self.diffusion_steps = diffusion_steps
        self.diffusion_seed = diffusion_seed


# =============================================================================
# MAIN CONFIG FUNCTION
# =============================================================================

def get_diffusion_config(
    data: Dict,
    template_type: TemplateType = "url",
    prompt: str = "",
    model: str = "realistic_digital",
    control_scale: float = 1.6,
    guidance_scale: float = 7.0,
    steps: int = 25,
    seed: Optional[int] = None,
    error_correction: Literal["L", "M", "Q", "H"] = "H",
    version: Optional[int] = 5,
) -> DiffusionQRConfig:
    """
    Get Diffusion QR pipeline configuration.
    
    Creates a high-contrast base QR config optimized for ControlNet processing.
    The base QR uses:
    - High error correction (H) for better AI readability
    - Square modules for cleaner ControlNet input
    - Simple B&W colors (no gradients)
    
    Args:
        data: Parameters for the template handler
              Example: {"url": "https://example.com"}
        template_type: Handler type (url, wifi, vcard, etc.)
        prompt: AI generation prompt (e.g., "forest theme")
        model: Diffusion model key (default: realistic_digital)
        control_scale: ControlNet influence (higher = more QR visible)
        guidance_scale: CFG scale for prompt adherence
        steps: Diffusion steps (more = better quality, slower)
        seed: Random seed for reproducibility
        error_correction: L(7%), M(15%), Q(25%), H(30%)
        version: QR version 1-40 (None=auto)
        
    Returns:
        DiffusionQRConfig ready for engine.generate() + diffusion subprocess
    """
    
    print(f"[DIFFUSION] Template: {template_type}")
    print(f"   Prompt: '{prompt[:50]}...'" if len(prompt) > 50 else f"   Prompt: '{prompt}'")
    print(f"   Model: {model}")
    print(f"   Control Scale: {control_scale}, CFG: {guidance_scale}, Steps: {steps}")
    
    return DiffusionQRConfig(
        # Base QR settings (optimized for ControlNet)
        template_type=template_type,
        output_dir=QR_CODE_DIFFUSION_DIR,
        version=version,
        error_correction=error_correction,
        module_drawer="square",  # Square modules = cleaner ControlNet input
        output_type="png",       # Must be PNG for diffusion
        print_qr=False,          # Don't print ASCII (messy with diffusion output)
        data=data,
        logo_path=None,          # No logo for diffusion input
        gradient_direction=None, # No gradient for diffusion input
        gradient_colors=None,
        
        # Diffusion parameters
        diffusion_prompt=prompt,
        diffusion_model=model,
        diffusion_control_scale=control_scale,
        diffusion_guidance_scale=guidance_scale,
        diffusion_steps=steps,
        diffusion_seed=seed,
    )


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    print("Testing Diffusion QR pipeline configuration...\n")
    
    config = get_diffusion_config(
        data={"url": "https://github.com"},
        template_type="url",
        prompt="enchanted forest, mystical, glowing mushrooms",
        control_scale=1.8,
    )
    
    print(f"\n[OK] Base QR Config:")
    print(f"   template_type: {config.template_type}")
    print(f"   output_dir: {config.output_dir}")
    print(f"   module_drawer: {config.module_drawer}")
    
    print(f"\n✅ Diffusion Config:")
    print(f"   prompt: {config.diffusion_prompt}")
    print(f"   model: {config.diffusion_model}")
    print(f"   control_scale: {config.diffusion_control_scale}")
    print(f"   steps: {config.diffusion_steps}")
