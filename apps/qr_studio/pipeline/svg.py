"""
SVG QR Code Pipeline
====================

Configuration pipeline for SVG QR code generation.
Returns QRConfig objects ready for the QR engine.

Usage:
    from apps.qr_studio.pipeline.svg import get_svg_config
    config = get_svg_config(data={"url": "https://example.com"}, template_type="url")
"""

from pathlib import Path
from typing import Optional, Union, Dict, Literal
import sys
import random

# =============================================================================
# PATH SETUP
# =============================================================================

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# =============================================================================
# IMPORTS
# =============================================================================

from configs.paths import QR_CODE_SVG_DIR
from apps.qr_studio.pipeline.pipeline_types import QRConfig, TemplateType, GradientDirection

# =============================================================================
# MODULE DRAWER STYLES
# =============================================================================

ModuleStyle = Literal["rounded", "square", "circle", "gapped"]
STYLE_DESCRIPTIONS = {
    "rounded": "Rounded corners - modern, friendly look",
    "square": "Sharp corners - classic QR style", 
    "circle": "Circular dots - artistic style",
    "gapped": "Spaced squares - airy, minimal look",
}

# =============================================================================
# GRADIENT DIRECTIONS
# =============================================================================

GRADIENT_OPTIONS: list[GradientDirection] = ["horizontal", "vertical", "diagonal", "radial"]

# =============================================================================
# CHECKING PATHS
# =============================================================================

QR_CODE_SVG_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# MAIN CONFIG FUNCTION
# =============================================================================

def get_svg_config(
    data: Dict,
    template_type: TemplateType = "normal",
    module_drawer: ModuleStyle = "rounded",
    output_dir: Path = QR_CODE_SVG_DIR,
    logo_path: Optional[Union[str, Path]] = None,
    gradient_direction: Optional[GradientDirection] = None,  # None = solid, "random" picks one
    print_qr: bool = True,
    version: Optional[int] = 5,
    error_correction: Literal["L", "M", "Q", "H"] = "H",
) -> QRConfig:
    """
    Get SVG QR pipeline configuration.
    
    Args:
        data: Parameters for the template handler
              Example: {"url": "https://example.com"} for template_type="url"
        template_type: Handler type (url, wifi, vcard, upi, etc.)
        module_drawer: QR module shape style
        output_dir: Save location (default: QR_CODE_SVG_DIR)
        logo_path: Optional logo to embed in center
        gradient_direction: Gradient style (horizontal/vertical/diagonal/radial)
                           Pass "random" to randomly pick one
        print_qr: Print ASCII QR to terminal
        version: QR version 1-40 (None=auto)
        error_correction: L(7%), M(15%), Q(25%), H(30%)
        
    Returns:
        QRConfig ready for engine.generate()
    """
    
    # Handle random gradient selection
    if gradient_direction == "random":
        gradient_direction = random.choice(GRADIENT_OPTIONS)
        print(f"[RANDOM] Gradient: {gradient_direction}")
    
    # Use higher error correction if logo is present
    if logo_path and error_correction != "H":
        error_correction = "H"
        print("[WARN] Using error_correction='H' for logo embedding")
    
    print(f"[SVG] Template: {template_type}")
    print(f"   Style: {module_drawer} ({STYLE_DESCRIPTIONS.get(module_drawer, '')})")
    if gradient_direction:
        print(f"   Gradient: {gradient_direction}")
    if logo_path:
        print(f"   Logo: {Path(logo_path).name}")
    
    return QRConfig(
        template_type=template_type,
        output_dir=output_dir,
        version=version,
        error_correction=error_correction,
        module_drawer=module_drawer,
        output_type="svg",
        print_qr=print_qr,
        data=data,
        logo_path=Path(logo_path) if logo_path else None,
        gradient_direction=gradient_direction,
    )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def svg_url(url: str, **kwargs) -> QRConfig:
    """Config for URL QR."""
    return get_svg_config(data={"url": url}, template_type="url", **kwargs)

def svg_wifi(ssid: str, password: str, encryption: str = "WPA", **kwargs) -> QRConfig:
    """Config for WiFi QR."""
    return get_svg_config(
        data={"ssid": ssid, "password": password, "encryption": encryption},
        template_type="wifi", **kwargs
    )

def svg_phone(number: str, **kwargs) -> QRConfig:
    """Config for phone call QR."""
    return get_svg_config(data={"number": number}, template_type="phone_call", **kwargs)

def svg_email(to: str, subject: str = "", body: str = "", **kwargs) -> QRConfig:
    """Config for email QR."""
    return get_svg_config(
        data={"to": to, "subject": subject, "body": body},
        template_type="email", **kwargs
    )

def svg_text(text: str, **kwargs) -> QRConfig:
    """Config for plain text QR."""
    return get_svg_config(data={"text": text}, template_type="normal", **kwargs)


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    print("Testing SVG QR pipeline configurations...\n")
    
    test_cases = [
        ("URL", svg_url("https://github.com")),
        ("WiFi", svg_wifi("MyNetwork", "password123")),
        ("Phone", svg_phone("+1234567890")),
    ]
    
    for name, config in test_cases:
        print(f"\n{'='*40}")
        print(f"[OK] {name} Config:")
        print(f"   template_type: {config.template_type}")
        print(f"   module_drawer: {config.module_drawer}")
        print(f"   data: {config.data}")