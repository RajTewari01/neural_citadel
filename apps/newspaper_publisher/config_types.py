"""
News Publisher Configuration Types
===================================

Dataclasses for type-safe configuration, mirroring image_gen patterns.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional, List
import sys

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from configs.paths import NEWSPAPER_OUTPUT_DIR, NEWSPAPER_TEMP_DIR


# =============================================================================
# STANDARD TYPES
# =============================================================================

CategoryType = Literal["INDIA", "USA", "GLOBAL", "CUSTOM"]
StyleType = Literal["Classic", "Modern", "Magazine"]


# =============================================================================
# NEWS CONFIG DATACLASS
# =============================================================================

@dataclass
class NewsConfig:
    """
    Configuration for newspaper generation.
    
    Similar to PipelineConfigs in image_gen, this centralizes all settings
    for fetching, processing, and generating newspapers.
    
    Example:
        config = NewsConfig(
            category="INDIA",
            style="Magazine",
            substyle="The Tech",
            auto_open=True
        )
    """
    
    # --- 1. CORE SETTINGS (Required for meaningful generation) ---
    category: CategoryType
    style: StyleType
    
    # --- 2. STYLE OPTIONS ---
    substyle: Optional[str] = None  # For Magazine styles (e.g., "The Tech", "The Noir")
    
    # --- 3. OUTPUT ---
    output_dir: Path = field(default_factory=lambda: NEWSPAPER_OUTPUT_DIR)
    temp_dir: Path = field(default_factory=lambda: NEWSPAPER_TEMP_DIR)
    
    # --- 4. FETCHING BEHAVIOR ---
    limit_per_feed: int = 5            # Max articles per RSS feed (reduced to avoid 200+ pages)
    max_workers: int = 20              # ThreadPoolExecutor threads
    require_image: bool = True        # Discard articles without images
    
    # --- 5. IMAGE PROCESSING ---
    image_max_width: int = 600        # Resize images to this max width (optimization)
    image_quality: int = 85           # JPEG quality for temp images
    
    # --- 6. GENERATION ---
    language: str = "English"         # Target language for translation
    translation_mode: str = "online"  # "online" (Google) or "offline" (NLLB)
    auto_open: bool = False           # Open PDF after generation
    
    # --- 7. POST-INIT VALIDATION ---
    def __post_init__(self):
        # Convert strings to Path if needed
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)
        if isinstance(self.temp_dir, str):
            self.temp_dir = Path(self.temp_dir)
            
        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate category
        valid_categories = ["INDIA", "USA", "GLOBAL", "CUSTOM"]
        if self.category.upper() not in valid_categories:
            raise ValueError(f"Invalid category '{self.category}'. Must be one of: {valid_categories}")
        self.category = self.category.upper()
        
        # Validate style
        valid_styles = ["Classic", "Modern", "Magazine"]
        style_lower = self.style.lower()
        matched = [s for s in valid_styles if s.lower() == style_lower]
        if not matched:
            raise ValueError(f"Invalid style '{self.style}'. Must be one of: {valid_styles}")
        self.style = matched[0]
        
        # Validate limits
        if self.limit_per_feed <= 0:
            raise ValueError("limit_per_feed must be > 0")
        if self.max_workers <= 0:
            raise ValueError("max_workers must be > 0")
        if self.max_workers > 50:
            print(f"⚠️ Warning: max_workers={self.max_workers} is high, limiting to 50")
            self.max_workers = 50


# =============================================================================
# ARTICLE DATACLASS (For type hints)
# =============================================================================

@dataclass
class Article:
    """
    Represents a fetched news article.
    """
    title: str
    content: str
    author: str = "Staff Writer"
    category: str = "NEWS"
    image: Optional[str] = None  # Path to local temp file
    date: Optional[str] = None
    source_url: Optional[str] = None
