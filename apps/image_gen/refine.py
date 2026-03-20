"""
Refinement Tool
===============
Runs strictly inside the 'image_venv' environment.
Handles:
1. Finding last generated image
2. Creating Canny edge map (using opencv)
3. Running DiffusionEngine with ControlNet
"""

import cv2
import sys
import argparse
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from apps.image_gen.engine import DiffusionEngine, ImageGenConfig
from apps.image_gen.pipeline.registry import get_all_pipelines

def find_last_image():
    """Find the most recent generated image."""
    generated_dir = PROJECT_ROOT / "assets" / "generated" / "images"
    if not generated_dir.exists(): return None
    
    # Get all PNGs excluding existing canny maps
    files = [f for f in generated_dir.rglob("*.png") if "_canny" not in f.name]
    if not files: return None
    
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return files[0]

def create_canny(image_path):
    """Create Canny edge map."""
    print(f"Creating Canny map from: {image_path.name}")
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
        
    edges = cv2.Canny(img, 100, 200)
    
    canny_path = image_path.parent / f"{image_path.stem}_canny.png"
    cv2.imwrite(str(canny_path), edges)
    return canny_path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--style", default="general")
    parser.add_argument("--upscale", default="cpu")
    # Add other necessary args...
    
    args = parser.parse_args()
    
    # 1. Find Image
    last_img = find_last_image()
    if not last_img:
        print("❌ No previous image found to refine.")
        return 1
        
    # 2. Make Canny
    try:
        canny_path = create_canny(last_img)
        print(f"✅ Canny map created: {canny_path}")
    except Exception as e:
        print(f"❌ Failed to create Canny: {e}")
        return 1
        
    # 3. Configure Engine
    # We reuse existing registry logic to get config
    registry = get_all_pipelines()
    if args.style not in registry:
        print(f"❌ Unknown style: {args.style}")
        return 1
        
    config_fn = registry[args.style]["get_config"]
    # Assuming config accepts control_image...
    # Just basic kwargs for now, expand as needed
    cfg = config_fn(prompt=args.prompt) 
    
    # Force ControlNet settings
    cfg.control_image = canny_path
    cfg.control_type = "canny"
    
    # 4. Run Generation
    print("🚀 Starting refinement generation...")
    engine = DiffusionEngine()
    saved = engine.generate(cfg)
    print(f"✨ Saved to: {saved}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
