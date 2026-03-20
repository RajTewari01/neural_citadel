"""
Asset Registry and Discovery
=============================
Discovers available garments/backgrounds from asset folders.
Implements scoring system to match prompt to best asset.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import sys

# Add project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Asset directories
CLOTHES_DIR = PROJECT_ROOT / "assets" / "apps_assets" / "image_surgeon" / "clothes"
BACKGROUNDS_DIR = PROJECT_ROOT / "assets" / "apps_assets" / "image_surgeon" / "backgrounds"


def discover_assets(asset_type: str = "clothes") -> Dict[str, List[Path]]:
    """
    Discover available assets organized by category.
    
    Args:
        asset_type: "clothes" or "backgrounds"
        
    Returns:
        Dict mapping category name to list of asset paths
    """
    base_dir = CLOTHES_DIR if asset_type == "clothes" else BACKGROUNDS_DIR
    
    if not base_dir.exists():
        return {}
    
    assets = {}
    
    # Check for category subdirectories
    for item in base_dir.iterdir():
        if item.is_dir():
            category = item.name
            files = list(item.glob("*.png")) + list(item.glob("*.jpg")) + list(item.glob("*.jpeg"))
            if files:
                assets[category] = files
        elif item.suffix.lower() in [".png", ".jpg", ".jpeg"]:
            # Files directly in base dir
            if "uncategorized" not in assets:
                assets["uncategorized"] = []
            assets["uncategorized"].append(item)
    
    return assets


def get_all_assets(asset_type: str = "clothes") -> List[Path]:
    """Get flat list of all assets."""
    discovered = discover_assets(asset_type)
    all_assets = []
    for category_assets in discovered.values():
        all_assets.extend(category_assets)
    return all_assets


def get_best_match(prompt: str, asset_type: str = "clothes") -> Optional[Path]:
    """
    Find best matching asset for a given prompt.
    Uses simple keyword matching (CLIP can be added later).
    
    Args:
        prompt: User's text prompt (e.g., "red evening dress")
        asset_type: "clothes" or "backgrounds"
        
    Returns:
        Path to best matching asset, or None if no assets
    """
    assets = get_all_assets(asset_type)
    
    if not assets:
        return None
    
    # Simple keyword scoring
    prompt_lower = prompt.lower()
    keywords = prompt_lower.split()
    
    best_score = 0
    best_asset = assets[0]  # Default to first asset
    
    for asset in assets:
        score = 0
        name_lower = asset.stem.lower()
        parent_lower = asset.parent.name.lower()
        
        for keyword in keywords:
            if keyword in name_lower:
                score += 2  # Filename match worth more
            if keyword in parent_lower:
                score += 1  # Category match
        
        if score > best_score:
            best_score = score
            best_asset = asset
    
    return best_asset


def list_categories(asset_type: str = "clothes") -> List[str]:
    """List available asset categories."""
    return list(discover_assets(asset_type).keys())


def get_assets_by_category(category: str, asset_type: str = "clothes") -> List[Path]:
    """Get assets in a specific category."""
    discovered = discover_assets(asset_type)
    return discovered.get(category, [])
