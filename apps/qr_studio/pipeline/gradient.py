"""
Gradient QR Code Pipeline
=========================

Configuration pipeline for gradient QR code generation.
Supports auto mode (random colors) and manual mode (user-defined colors).

Usage:
    from apps.qr_studio.pipeline.gradient import get_gradient_config, gradient_radial
    
    # Auto mode - random colors
    config = get_gradient_config(
        data={"url": "https://example.com"},
        template_type="url",
        auto_mode=True
    )
    
    # Manual mode - user colors
    config = get_gradient_config(
        data={"url": "https://example.com"},
        template_type="url",
        colors=["#ffffff", "#ff0000", "#0000ff"],
        mask="radial"
    )
"""

from pathlib import Path
from typing import Optional, Union, Dict, Literal, List, Tuple
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

from configs.paths import QR_CODE_GRADIENT_DIR
from apps.qr_studio.pipeline.pipeline_types import QRConfig, TemplateType, GradientDirection

# =============================================================================
# TYPES
# =============================================================================

ModuleStyle = Literal["rounded", "square", "circle", "gapped"]
MaskType = Literal["horizontal", "vertical", "diagonal", "radial"]
ColorInput = Union[str, Tuple[int, int, int]]  # Hex, named, or RGB tuple

# =============================================================================
# STYLE DESCRIPTIONS
# =============================================================================

MASK_DESCRIPTIONS = {
    "horizontal": "Left to right gradient",
    "vertical": "Top to bottom gradient",
    "diagonal": "Corner to corner gradient",
    "radial": "Center outward gradient",
}

DRAWER_DESCRIPTIONS = {
    "rounded": "Rounded corners - modern look",
    "square": "Sharp corners - classic style",
    "circle": "Circular dots - artistic",
    "gapped": "Spaced squares - minimal",
}

# =============================================================================
# OPTIONS FOR RANDOM SELECTION
# =============================================================================

MASK_OPTIONS: List[MaskType] = ["horizontal", "vertical", "diagonal", "radial"]
DRAWER_OPTIONS: List[ModuleStyle] = ["rounded", "square", "circle", "gapped"]

# =============================================================================
# CHECKING PATHS
# =============================================================================

QR_CODE_GRADIENT_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def random_rgb() -> Tuple[int, int, int]:
    """Generate random RGB color tuple."""
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))


def random_colors() -> List[Tuple[int, int, int]]:
    """Generate 3 random colors for gradient: [back, center, edge]."""
    return [
        (255, 255, 255),  # White background (always)
        random_rgb(),     # Center/left/top color
        random_rgb(),     # Edge/right/bottom color
    ]


# =============================================================================
# MAIN CONFIG FUNCTION
# =============================================================================

def get_gradient_config(
    data: Dict,
    template_type: TemplateType = "normal",
    auto_mode: bool = False,
    colors: Optional[List[ColorInput]] = None,
    mask: Optional[MaskType] = None,
    module_drawer: Optional[ModuleStyle] = None,
    output_dir: Path = QR_CODE_GRADIENT_DIR,
    logo_path: Optional[Union[str, Path]] = None,
    print_qr: bool = True,
    version: Optional[int] = 5,
    error_correction: Literal["L", "M", "Q", "H"] = "H",
) -> QRConfig:
    """
    Get Gradient QR pipeline configuration.
    
    Args:
        data: Parameters for the template handler
              Example: {"url": "https://example.com"}
        template_type: Handler type (url, wifi, vcard, etc.)
        auto_mode: If True, randomly select colors, mask, and drawer
        colors: List of 3 colors [back, center/left/top, edge/right/bottom]
                Each color can be: RGB tuple, hex string, or named color
                Example: [(255,255,255), "#ff0000", "blue"]
        mask: Gradient mask type (horizontal, vertical, diagonal, radial)
        module_drawer: QR module shape (rounded, square, circle, gapped)
        output_dir: Save location (default: QR_CODE_GRADIENT_DIR)
        logo_path: Optional logo to embed in center
        print_qr: Print ASCII QR to terminal
        version: QR version 1-40 (None=auto)
        error_correction: L(7%), M(15%), Q(25%), H(30%)
        
    Returns:
        QRConfig ready for engine.generate()
    """
    
    # --- AUTO MODE: Random everything ---
    if auto_mode:
        colors = random_colors()
        mask = random.choice(MASK_OPTIONS)
        module_drawer = random.choice(DRAWER_OPTIONS)
        print(f"[AUTO] Gradient: {mask}, Drawer: {module_drawer}")
        print(f"   Colors: back={colors[0]}, center={colors[1]}, edge={colors[2]}")
    
    # --- MANUAL MODE: Validate inputs ---
    else:
        if colors is None:
            raise ValueError("colors required in manual mode. Use auto_mode=True for random.")
        if len(colors) != 3:
            raise ValueError("colors must have exactly 3 values: [back, center, edge]")
        if mask is None:
            mask = "radial"  # Default mask
        if module_drawer is None:
            module_drawer = "rounded"  # Default drawer
    
    # Use higher error correction if logo is present
    if logo_path and error_correction != "H":
        error_correction = "H"
        print("[WARN] Using error_correction='H' for logo embedding")
    
    print(f"[GRADIENT] Template: {template_type}")
    print(f"   Mask: {mask} ({MASK_DESCRIPTIONS.get(mask, '')})")
    print(f"   Drawer: {module_drawer} ({DRAWER_DESCRIPTIONS.get(module_drawer, '')})")
    if logo_path:
        print(f"   Logo: {Path(logo_path).name}")
    
    return QRConfig(
        template_type=template_type,
        output_dir=output_dir,
        version=version,
        error_correction=error_correction,
        module_drawer=module_drawer,
        output_type="png",  # Gradients require PNG
        print_qr=print_qr,
        data=data,
        logo_path=Path(logo_path) if logo_path else None,
        gradient_direction=mask,
        gradient_colors=colors,
    )


# =============================================================================
# CONVENIENCE FUNCTIONS - AUTO MODE
# =============================================================================

def gradient_auto(data: Dict, template_type: TemplateType = "url", **kwargs) -> QRConfig:
    """Gradient QR with random colors and mask."""
    return get_gradient_config(data=data, template_type=template_type, auto_mode=True, **kwargs)


# =============================================================================
# CONVENIENCE FUNCTIONS - SPECIFIC MASKS
# =============================================================================

def gradient_radial(
    data: Dict,
    template_type: TemplateType = "url",
    colors: Optional[List[ColorInput]] = None,
    auto_mode: bool = False,
    **kwargs
) -> QRConfig:
    """Radial gradient (center outward)."""
    if auto_mode:
        colors = random_colors()
    elif colors is None:
        colors = random_colors()
    return get_gradient_config(
        data=data, template_type=template_type,
        colors=colors, mask="radial", **kwargs
    )


def gradient_horizontal(
    data: Dict,
    template_type: TemplateType = "url",
    colors: Optional[List[ColorInput]] = None,
    auto_mode: bool = False,
    **kwargs
) -> QRConfig:
    """Horizontal gradient (left to right)."""
    if auto_mode:
        colors = random_colors()
    elif colors is None:
        colors = random_colors()
    return get_gradient_config(
        data=data, template_type=template_type,
        colors=colors, mask="horizontal", **kwargs
    )


def gradient_vertical(
    data: Dict,
    template_type: TemplateType = "url",
    colors: Optional[List[ColorInput]] = None,
    auto_mode: bool = False,
    **kwargs
) -> QRConfig:
    """Vertical gradient (top to bottom)."""
    if auto_mode:
        colors = random_colors()
    elif colors is None:
        colors = random_colors()
    return get_gradient_config(
        data=data, template_type=template_type,
        colors=colors, mask="vertical", **kwargs
    )


def gradient_diagonal(
    data: Dict,
    template_type: TemplateType = "url",
    colors: Optional[List[ColorInput]] = None,
    auto_mode: bool = False,
    **kwargs
) -> QRConfig:
    """Diagonal gradient (corner to corner)."""
    if auto_mode:
        colors = random_colors()
    elif colors is None:
        colors = random_colors()
    return get_gradient_config(
        data=data, template_type=template_type,
        colors=colors, mask="diagonal", **kwargs
    )


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    print("Testing Gradient QR pipeline configurations...\n")
    
    # Test 1: Auto mode
    print("📍 Test 1: Auto Mode")
    config = gradient_auto(data={"url": "https://github.com"})
    print(f"   [OK] gradient_direction: {config.gradient_direction}")
    print(f"   ✅ gradient_colors: {config.gradient_colors}")
    
    # Test 2: Manual radial
    print("\n📍 Test 2: Manual Radial")
    config = gradient_radial(
        data={"url": "https://google.com"},
        colors=["#ffffff", "#ff5500", "#0055ff"]
    )
    print(f"   [OK] gradient_direction: {config.gradient_direction}")
    print(f"   ✅ colors: {config.gradient_colors}")
    
    # Test 3: Horizontal with RGB tuples
    print("\n📍 Test 3: Horizontal with RGB")
    config = gradient_horizontal(
        data={"url": "https://example.com"},
        colors=[(255, 255, 255), (255, 0, 0), (0, 0, 255)]
    )
    print(f"   [OK] gradient_direction: {config.gradient_direction}")
    print(f"   ✅ colors: {config.gradient_colors}")
    
    print("\n" + "=" * 50)
    print("All tests passed!")
