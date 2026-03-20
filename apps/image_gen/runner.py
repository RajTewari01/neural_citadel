#!/usr/bin/env python
"""
Neural Citadel Image Generator - CLI Runner
============================================

Unified CLI for all image generation pipelines with registry-based discovery.
Uses isolated venv at: venvs/env/image_venv

Usage:
    # Basic usage
    python runner.py "beautiful anime girl" --style anime
    
    # With type and upscaling
    python runner.py "red sports car" --style car --type rx7 --upscale "R-ESRGAN 4x+"
    
    # With seed for reproducibility
    python runner.py "ghost in hallway" --style ghost --seed 42
    
    # Open result after generation
    python runner.py "zombie horde" --style zombie --type horde --open
    
    # Show all available styles and types
    python runner.py --list
    
    # Show detailed help
    python runner.py --help
"""

import argparse
import os
import sys
import platform
import subprocess
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def open_file(filepath: str):
    """Open file with default system application."""
    if not os.path.exists(filepath):
        print(f"[ERROR] File not found: {filepath}")
        return
        
    if platform.system() == 'Windows':
        os.startfile(filepath)
    elif platform.system() == 'Darwin':
        subprocess.call(('open', filepath))
    else:
        subprocess.call(('xdg-open', filepath))


def get_style_help(registry: dict) -> str:
    """Generate detailed help text for all styles."""
    lines = [
        "",
        "=" * 70,
        "AVAILABLE STYLES AND TYPES",
        "=" * 70,
        ""
    ]
    
    for name, info in sorted(registry.items()):
        lines.append(f"📦 --style {name}")
        lines.append(f"   {info['description']}")
        
        if info.get("types"):
            lines.append(f"   Available --type options:")
            for t, desc in info["types"].items():
                lines.append(f"      {t}: {desc}")
        else:
            lines.append("   (No sub-types available)")
        lines.append("")
    
    lines.append("=" * 70)
    return "\n".join(lines)


class CustomHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Custom formatter for better help display."""
    def __init__(self, prog, indent_increment=2, max_help_position=40, width=100):
        super().__init__(prog, indent_increment, max_help_position, width)


def main():
    # Import registry and discover pipelines
    from apps.image_gen.pipeline.registry import (
        discover_pipelines, 
        get_all_pipelines, 
        get_pipeline_names,
        get_pipeline_types
    )
    from apps.image_gen.engine import DiffusionEngine
    
    # Discover all pipelines
    discover_pipelines()
    registry = get_all_pipelines()
    available_styles = get_pipeline_names()
    
    # Build epilog with style details
    epilog = get_style_help(registry)
    
    # Setup CLI Arguments
    parser = argparse.ArgumentParser(
        prog="runner.py",
        description="""
╔═══════════════════════════════════════════════════════════════════════╗
║             NEURAL CITADEL - Image Generation Engine                  ║
║                                                                       ║
║  Generate high-quality AI images using various specialized pipelines  ║
╚═══════════════════════════════════════════════════════════════════════╝
        """,
        epilog=epilog,
        formatter_class=CustomHelpFormatter
    )
    
    # Positional argument
    parser.add_argument(
        "prompt", 
        type=str, 
        nargs="?",  # Optional to allow --list without prompt
        help="The image prompt describing what you want to generate"
    )
    
    # Required style argument
    parser.add_argument(
        "--style", "-s",
        type=str,
        choices=available_styles,
        help="Which pipeline style to use (see below for options)"
    )
    
    # Optional type (sub-style)
    parser.add_argument(
        "--type", "-t",
        type=str,
        default=None,
        help="Sub-type for the selected style (varies by style, see --list)"
    )
    
    # Aspect ratio override (forces dimensions regardless of prompt)
    parser.add_argument(
        "--aspect", "-a",
        type=str,
        choices=["portrait", "landscape", "normal"],
        default=None,
        help="Force aspect ratio: portrait (512x768), landscape (768x512), normal (512x512)"
    )
    
    # Add details flag (Diffusion upscaling - expensive)
    parser.add_argument(
        "--add_details", "-d",
        action="store_true",
        help="Use Diffusion upscaler to hallucinate details (slow, runs before ESRGAN)"  
    )
    
    # Scheduler options
    parser.add_argument(
        "--scheduler",
        type=str,
        choices=["euler_a", "dpm++_2m_karras", "dpm++_sde_karras", "dpm++_2m_sde_karras", "ddim", "lms"],
        default=None,
        help="Scheduler to use (default: pipeline-specific)"
    )
    
    # Seed for reproducibility
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility (optional)"
    )
    
    # Steps override
    parser.add_argument(
        "--steps",
        type=int,
        default=None,
        help="Number of inference steps (default: pipeline-specific, max 45)"
    )
    
    # ControlNet options
    parser.add_argument(
        "--control_image",
        type=str,
        default=None,
        help="Path to image for ControlNet guidance"
    )
    
    parser.add_argument(
        "--control_type",
        type=str,
        choices=["canny", "depth", "openpose"],
        default=None,
        help="Type of ControlNet to use with --control_image"
    )
    
    # Output options
    parser.add_argument(
        "--open", "-o",
        action="store_true",
        help="Open the generated image after saving"
    )
    
    # List all styles
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="Show all available styles and their types, then exit"
    )
    
    args = parser.parse_args()
    
    # Handle --list
    if args.list:
        print(get_style_help(registry))
        return 0
    
    # Validate required arguments
    if not args.prompt:
        parser.error("prompt is required (or use --list to see available styles)")
    
    if not args.style:
        parser.error("--style is required. Use --list to see available styles.")
    
    # Validate type against selected style
    if args.type:
        valid_types = get_pipeline_types(args.style)
        if valid_types and args.type not in valid_types:
            print(f"\n[ERROR] Invalid --type '{args.type}' for style '{args.style}'")
            print(f"Valid types: {', '.join(valid_types.keys())}")
            return 1
    
    # Get the config function from registry
    print(f"\n{'='*60}")
    print(f"🎨 NEURAL CITADEL - Image Generator")
    print(f"{'='*60}")
    print(f"📦 Style: {args.style.upper()}")
    if args.type:
        print(f"🔹 Type: {args.type}")
    print(f"📝 Prompt: {args.prompt[:60]}...")
    print(f"{'='*60}\n")
    
    try:
        pipeline_info = registry[args.style]
        config_function = pipeline_info["get_config"]
        
        # Build kwargs for the config function
        kwargs = {"prompt": args.prompt}
        
        # Handle style-specific type arguments
        if args.style == "car" and args.type:
            kwargs["style"] = args.type
        elif args.style == "anime" and args.type:
            kwargs["model"] = args.type
        elif args.style == "difconsistency" and args.type:
            kwargs["style"] = args.type
        elif args.style == "drawing" and args.type:
            kwargs["model_override"] = args.type
        elif args.style == "ethnicity" and args.type:
            kwargs["ethnicity"] = args.type
        elif args.style == "horror" and args.type:
            kwargs["shot_type"] = args.type
        elif args.style == "hyperrealistic" and args.type:
            kwargs["model"] = args.type
        elif args.style == "papercut" and args.type:
            kwargs["style"] = args.type
        elif args.style == "nsfw" and args.type:
            kwargs["model_override"] = args.type
        elif args.style == "zombie" and args.type:
            if args.type == "chinese":
                kwargs["zombie_type"] = "chinese"
            else:
                kwargs["shot_type"] = args.type
        
        # ControlNet support
        if args.control_image:
            kwargs["control_image"] = Path(args.control_image)
        if args.control_type:
            kwargs["control_type"] = args.control_type
        
        # Get the configuration
        config = config_function(**kwargs)
        
        # Apply overrides
        if args.aspect:
            # Aspect override takes priority over prompt detection
            aspects = {"portrait": (512, 768), "landscape": (768, 512), "normal": (512, 512)}
            config.width, config.height = aspects[args.aspect]
            print(f"📐 Aspect override: {args.aspect} ({config.width}x{config.height})")
        if args.add_details:
            config.add_details = True
        if args.scheduler:
            config.scheduler_name = args.scheduler
        if args.seed is not None:
            config.seed = args.seed
        if args.steps:
            config.steps = args.steps
            
        print(f"✓ Config loaded successfully")
        print(f"  Model: {config.base_model.name}")
        print(f"  Size: {config.width}x{config.height}")
        print(f"  Steps: {config.steps}, Scheduler: {config.scheduler_name}")
        print(f"  Style Type: {config.style_type} (auto-selects upscaler)")
        if config.add_details:
            print(f"  🎨 Add Details: Diffusion upscale enabled (slow)")
        if config.seed:
            print(f"  Seed: {config.seed}")
        
    except Exception as e:
        print(f"\n❌ Error loading config: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Run the Engine
    try:
        print(f"\n🚀 Starting generation...")
        engine = DiffusionEngine()
        saved_path = engine.generate(config)
        
        print(f"\n{'='*60}")
        print(f"✨ SUCCESS!")
        print(f"📁 Image saved at: {saved_path}")
        print(f"{'='*60}")
        
        engine.unload()
        
        if args.open:
            print("📂 Opening image...")
            open_file(str(saved_path))
        
        return 0
        
    except KeyboardInterrupt:
        print("\n🛑 Generation cancelled by user.")
        return 130
    except Exception as e:
        print(f"\n❌ Critical Engine Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
