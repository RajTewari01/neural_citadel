"""
BLIP Image Captioner Runner
============================

CLI runner for BLIP image captioning, called via subprocess from PyQt GUI.
Uses image_captioner venv with PyTorch CPU + transformers.

Usage:
    python runner.py <image_path> [--task <task>]
    
    Tasks:
        caption (default): Brief caption
        detailed: Conditional caption
        
Output:
    Prints caption to stdout (prefixed with CAPTION:)
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def load_model():
    """Load BLIP model (cached after first load)."""
    from transformers import BlipProcessor, BlipForConditionalGeneration
    import torch
    
    model_name = "Salesforce/blip-image-captioning-base"
    cache_dir = PROJECT_ROOT / "assets" / "models" / "photo-recognizer"
    
    print("[BLIP] Loading model...", file=sys.stderr)
    
    # Try to load from cache first (offline mode)
    try:
        processor = BlipProcessor.from_pretrained(
            model_name, 
            cache_dir=cache_dir,
            local_files_only=True
        )
        
        model = BlipForConditionalGeneration.from_pretrained(
            model_name,
            cache_dir=cache_dir,
            torch_dtype=torch.float32,
            local_files_only=True
        )
    except Exception as e:
        print(f"[BLIP] Model not cached, downloading... ({e})", file=sys.stderr)
        # Download if not cached
        processor = BlipProcessor.from_pretrained(
            model_name, 
            cache_dir=cache_dir
        )
        
        model = BlipForConditionalGeneration.from_pretrained(
            model_name,
            cache_dir=cache_dir,
            torch_dtype=torch.float32
        )
    
    print("[BLIP] Model loaded!", file=sys.stderr)
    return processor, model


def run_service():
    """Run in continuous service mode, reading paths from stdin."""
    print("[BLIP] Starting service mode...", file=sys.stderr)
    try:
        processor, model = load_model()
        print("READY", flush=True)  # Signal ready state
        
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                # Parse optional task: "path|task" or just "path"
                if "|" in line:
                    image_path, task = line.split("|", 1)
                else:
                    image_path, task = line, "caption"
                
                if not Path(image_path).exists():
                    print(f"[BLIP] Image not found: {image_path}", file=sys.stderr)
                    continue
                
                # Process
                caption = caption_image_loaded(processor, model, image_path, task)
                
                # Only output valid captions (not errors)
                if not caption.startswith("Error"):
                    print(f"CAPTION:{caption}", flush=True)
                else:
                    print(f"[BLIP] {caption}", file=sys.stderr)
                
            except Exception as e:
                print(f"[BLIP] Error processing: {e}", file=sys.stderr)
                
    except Exception as e:
        print(f"[BLIP] Fatal Service Error: {e}", file=sys.stderr)
        sys.exit(1)


def caption_image_loaded(processor, model, image_path: str, task: str = "caption") -> str:
    """Generate caption using loaded model."""
    from PIL import Image
    import torch
    
    # Load image
    try:
        if not Path(image_path).exists():
            return f"Error: File not found: {image_path}"
            
        image = Image.open(image_path).convert("RGB")
        
        # Verify image is valid
        if image is None or image.size[0] == 0 or image.size[1] == 0:
            return "Error: Invalid image dimensions"
            
    except Exception as e:
        return f"Error loading image: {e}"
    
    # Process
    try:
        # Conditional captioning for "detailed" task
        if task == "detailed":
            text = "a photograph of"
            inputs = processor(image, text, return_tensors="pt")
        else:
            # Unconditional captioning
            inputs = processor(image, return_tensors="pt")
        
        # Generate
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=50)
        
        # Decode
        caption = processor.decode(out[0], skip_special_tokens=True)
        
        return caption.strip()
        
    except Exception as e:
        import traceback
        print(f"[BLIP] Exception: {traceback.format_exc()}", file=sys.stderr)
        return f"Error generating: {e}"


def main():
    parser = argparse.ArgumentParser(description="BLIP Image Captioner")
    parser.add_argument("image_path", nargs="?", help="Path to image file (optional in service mode)")
    parser.add_argument("--task", choices=["caption", "detailed"], default="caption",
                       help="Caption task type")
    parser.add_argument("--service", action="store_true", help="Run in continuous service mode")
    
    args = parser.parse_args()
    
    if args.service:
        run_service()
        return 0
        
    if not args.image_path:
        parser.print_help()
        return 1
    
    if not Path(args.image_path).exists():
        print(f"Error: Image not found: {args.image_path}", file=sys.stderr)
        return 1
    
    try:
        processor, model = load_model()
        caption = caption_image_loaded(processor, model, args.image_path, args.task)
        print(f"CAPTION:{caption}")  # Output to stdout
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
