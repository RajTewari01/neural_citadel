"""
Pipeline Configuration Types
=============================
Dataclasses for image surgery pipeline configurations.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple, Union


@dataclass
class SurgeonConfig:
    """Configuration for image surgery operations."""
    
    # Required
    mode: str  # "clothes" | "background"
    input_image: Path
    
    # Prompt-based selection
    prompt: Optional[str] = None
    
    # Background options
    solid_color: Optional[Tuple[int, int, int]] = None
    background_image: Optional[Path] = None
    transparent: bool = False
    
    # Clothes options
    garment_path: Optional[Path] = None
    
    # Processing
    upscale: float = 4.0
    steps: int = 40
    
    # Output
    output_dir: Optional[Path] = None
    output_name: Optional[str] = None
    auto_open: bool = False
    
    # Advanced
    sam_model: str = "large"
    save_raw_extract: bool = False  # True for background mode
    
    # Auto mode prompts
    bg_prompt: Optional[str] = None
    clothes_prompt: Optional[str] = None
    
    def __post_init__(self):
        self.input_image = Path(self.input_image)
        if self.garment_path:
            self.garment_path = Path(self.garment_path)
        if self.background_image:
            self.background_image = Path(self.background_image)
        if self.output_dir:
            self.output_dir = Path(self.output_dir)
        
        # Auto-set save_raw_extract based on mode
        if self.mode == "background":
            self.save_raw_extract = True
