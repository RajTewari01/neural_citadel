#!/usr/bin/env python
"""
Image Surgeon CLI Runner
=========================
Unified CLI for image surgery operations.
Uses venv: venvs/env/enhanced

Usage:
    # Background - solid color
    python runner.py --mode background --image photo.jpg --solid black
    
    # Background - transparent
    python runner.py --mode background --image photo.jpg --transparent
    
    # Background - from image
    python runner.py --mode background --image photo.jpg --bg sunset.jpg
    
    # Clothes - auto-select from prompt
    python runner.py --mode clothes --image photo.jpg --prompt "red evening dress"
    
    # Clothes - specific garment
    python runner.py --mode clothes --image photo.jpg --garment dress.png
    
    # With --open to view result
    python runner.py --mode clothes --image photo.jpg --prompt "denim jacket" --open
    
    # List available assets
    python runner.py --list
"""

import argparse
import os
import sys
import platform
import subprocess
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Named solid colors
SOLID_COLORS = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "gray": (128, 128, 128),
    "grey": (128, 128, 128),
    "yellow": (255, 255, 0),
    "cyan": (0, 255, 255),
    "magenta": (255, 0, 255),
    "orange": (255, 165, 0),
    "pink": (255, 192, 203),
    "purple": (128, 0, 128),
}


def open_file(filepath: str):
    """Open file with default system application (cross-platform)."""
    if not os.path.exists(filepath):
        print(f"[ERROR] File not found: {filepath}")
        return
    
    system = platform.system()
    if system == 'Windows':
        os.startfile(filepath)
    elif system == 'Darwin':  # macOS
        subprocess.call(['open', filepath])
    else:  # Linux and others
        subprocess.call(['xdg-open', filepath])


def list_assets():
    """Display available assets."""
    from apps.image_surgeon.pipeline.registry import discover_assets
    
    print("\n" + "=" * 60)
    print("AVAILABLE ASSETS")
    print("=" * 60)
    
    # Clothes
    print("\n[CLOTHES]")
    clothes = discover_assets("clothes")
    if clothes:
        for category, items in clothes.items():
            print(f"   {category}/")
            for item in items[:5]:  # Show max 5 per category
                print(f"      - {item.name}")
            if len(items) > 5:
                print(f"      ... and {len(items) - 5} more")
    else:
        print("   (No clothes found)")
    
    # Backgrounds
    print("\n[BACKGROUNDS]")
    backgrounds = discover_assets("backgrounds")
    if backgrounds:
        for category, items in backgrounds.items():
            print(f"   {category}/")
            for item in items[:5]:
                print(f"      - {item.name}")
            if len(items) > 5:
                print(f"      ... and {len(items) - 5} more")
    else:
        print("   (No backgrounds found)")
    
    # Solid colors
    print("\n[SOLID COLORS] (use with --solid)")
    colors_per_row = 4
    color_list = list(SOLID_COLORS.keys())
    for i in range(0, len(color_list), colors_per_row):
        row = color_list[i:i+colors_per_row]
        print("   " + ", ".join(row))
    
    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        prog="runner.py",
        description="""
╔═══════════════════════════════════════════════════════════════════════╗
║              IMAGE SURGEON - AI Image Manipulation                    ║
║                                                                       ║
║  Replace backgrounds, change clothes using AI-powered pipelines       ║
╚═══════════════════════════════════════════════════════════════════════╝
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Mode selection
    parser.add_argument(
        "--mode", "-m",
        type=str,
        choices=["background", "clothes", "auto"],
        help="Operation mode: 'background', 'clothes', or 'auto'"
    )
    
    # Input image
    parser.add_argument(
        "--image", "-i",
        type=str,
        help="Path to input image"
    )
    
    # Background options
    parser.add_argument(
        "--solid", "-s",
        type=str,
        choices=list(SOLID_COLORS.keys()),
        help="Solid background color (black, white, red, etc.)"
    )
    parser.add_argument(
        "--transparent", "-t",
        action="store_true",
        help="Transparent background"
    )
    parser.add_argument(
        "--bg",
        type=str,
        help="Path to background image"
    )
    
    # Clothes options
    parser.add_argument(
        "--garment", "-g",
        type=str,
        help="Path to garment image"
    )
    
    # Shared options
    parser.add_argument(
        "--prompt", "-p",
        type=str,
        help="Text prompt (for background generation or garment selection)"
    )
    parser.add_argument(
        "--upscale", "-u",
        type=float,
        default=4.0,
        help="Upscale factor (default: 4.0)"
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=40,
        help="Inference steps (default: 40)"
    )
    
    # Output options
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output filename (without extension)"
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open result after generation"
    )
    
    # Auto mode
    parser.add_argument(
        "--auto",
        type=str,
        help="Auto mode: \"{background_prompt, clothes_prompt}\" for combined processing"
    )
    
    # List assets
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available assets and exit"
    )
    
    args = parser.parse_args()
    
    # Handle --list
    if args.list:
        list_assets()
        return 0
    
    # Validate required args
    if not args.mode:
        parser.error("--mode is required (use --list to see available assets)")
    if not args.image:
        parser.error("--image is required")
    if not Path(args.image).exists():
        parser.error(f"Image not found: {args.image}")
    
    # Handle auto mode - parse "{bg_prompt, clothes_prompt}"
    bg_prompt = None
    clothes_prompt = None
    if args.mode == "auto":
        if args.auto:
            # Parse "{bg_prompt, clothes_prompt}" format
            auto_str = args.auto.strip()
            if auto_str.startswith("{") and auto_str.endswith("}"):
                content = auto_str[1:-1]  # Remove braces
                if "," in content:
                    parts = content.split(",", 1)
                    bg_prompt = parts[0].strip()
                    clothes_prompt = parts[1].strip()
                else:
                    parser.error("Auto format: \"{background_prompt, clothes_prompt}\"")
            else:
                parser.error("Auto format: \"{background_prompt, clothes_prompt}\"")
        else:
            parser.error("--auto requires format: \"{background_prompt, clothes_prompt}\"")
    
    # Build config
    from apps.image_surgeon.pipeline.pipeline_types import SurgeonConfig
    
    config = SurgeonConfig(
        mode=args.mode,
        input_image=Path(args.image),
        prompt=args.prompt,
        solid_color=SOLID_COLORS.get(args.solid) if args.solid else None,
        transparent=args.transparent,
        background_image=Path(args.bg) if args.bg else None,
        garment_path=Path(args.garment) if args.garment else None,
        upscale=args.upscale,
        steps=args.steps,
        output_name=args.output,
        auto_open=args.open,
        bg_prompt=bg_prompt,
        clothes_prompt=clothes_prompt
    )
    
    # Print header
    print("\n" + "=" * 60)
    print("IMAGE SURGEON")
    print("=" * 60)
    print(f"Mode: {args.mode.upper()}")
    print(f"Input: {Path(args.image).name}")
    if args.mode == "auto":
        print(f"Background: {bg_prompt}")
        print(f"Clothes: {clothes_prompt}")
    elif args.prompt:
        print(f"Prompt: {args.prompt}")
    if args.solid:
        print(f"Solid: {args.solid}")
    print("=" * 60 + "\n")
    
    # Run engine
    try:
        from apps.image_surgeon.engine import ImageSurgeonEngine
        
        engine = ImageSurgeonEngine()
        result_path = engine.process(config)
        engine.unload()
        
        print("\n" + "=" * 60)
        print("SUCCESS!")
        print(f"Output: {result_path}")
        print("=" * 60)
        
        if args.open:
            print("Opening...")
            open_file(str(result_path))
        
        return 0
        
    except KeyboardInterrupt:
        print("\nCancelled by user")
        return 130
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
