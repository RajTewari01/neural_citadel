"""
CLIP-Based Asset Scoring
=========================
Uses CLIP to score how well assets match a user's prompt.
Falls back to keyword matching if CLIP unavailable.
"""

import sys
from pathlib import Path
from typing import List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Try to import CLIP, fallback to keyword matching
try:
    import torch
    from PIL import Image
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


def score_assets_keyword(prompt: str, assets: List[Path]) -> List[Tuple[Path, float]]:
    """
    Score assets using simple keyword matching.
    
    Args:
        prompt: User's text prompt
        assets: List of asset paths
        
    Returns:
        List of (path, score) tuples, sorted by score descending
    """
    prompt_lower = prompt.lower()
    keywords = prompt_lower.split()
    
    scored = []
    for asset in assets:
        score = 0.0
        name_lower = asset.stem.lower().replace("_", " ").replace("-", " ")
        parent_lower = asset.parent.name.lower()
        
        for keyword in keywords:
            if len(keyword) < 3:  # Skip short words
                continue
            if keyword in name_lower:
                score += 2.0
            if keyword in parent_lower:
                score += 1.0
        
        scored.append((asset, score))
    
    # Sort by score descending
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def score_assets_clip(prompt: str, assets: List[Path]) -> List[Tuple[Path, float]]:
    """
    Score assets using CLIP embeddings.
    Requires transformers and torch.
    
    Args:
        prompt: User's text prompt
        assets: List of asset paths
        
    Returns:
        List of (path, score) tuples, sorted by score descending
    """
    if not HAS_TORCH:
        print("[WARN] CLIP unavailable, using keyword matching")
        return score_assets_keyword(prompt, assets)
    
    try:
        from transformers import CLIPProcessor, CLIPModel
        
        # Load CLIP model
        model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        
        # Process images
        images = [Image.open(p).convert("RGB") for p in assets]
        
        # Get embeddings
        inputs = processor(text=[prompt], images=images, return_tensors="pt", padding=True)
        outputs = model(**inputs)
        
        # Cosine similarity
        logits = outputs.logits_per_text.squeeze()
        scores = logits.softmax(dim=0).tolist()
        
        # Create scored list
        if isinstance(scores, float):
            scores = [scores]
        scored = list(zip(assets, scores))
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return scored
        
    except Exception as e:
        print(f"[WARN] CLIP scoring failed: {e}, using keyword matching")
        return score_assets_keyword(prompt, assets)


def get_best_asset(prompt: str, assets: List[Path], use_clip: bool = False) -> Optional[Path]:
    """
    Get the best matching asset for a prompt.
    
    Args:
        prompt: User's text prompt
        assets: List of asset paths
        use_clip: Whether to try CLIP scoring (slower but more accurate)
        
    Returns:
        Best matching asset path, or None if no assets
    """
    if not assets:
        return None
    
    if use_clip and HAS_TORCH:
        scored = score_assets_clip(prompt, assets)
    else:
        scored = score_assets_keyword(prompt, assets)
    
    if scored:
        return scored[0][0]
    return assets[0]
