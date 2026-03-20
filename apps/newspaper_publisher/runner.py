"""
Neural Citadel Newspaper Runner
===============================
CLI Execution for Newspaper Publisher.
Supports both Interactive Mode and Command Line Arguments.
Uses NewsConfig for type-safe configuration.
"""

import sys
import os
import argparse
import uuid
import random
import platform
import subprocess
from datetime import datetime
from pathlib import Path

# Project Root setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Core imports
from apps.newspaper_publisher.engine import NewsEngine
from apps.newspaper_publisher.config_types import NewsConfig
from apps.newspaper_publisher.templates import (
    discover_templates,
    get_template_names,
    get_substyles,
    format_help_text,
    MAG_STYLES
)

# Import Feed Lists
from apps.newspaper_publisher.rss_sites.global_news import feeds as global_feeds
from apps.newspaper_publisher.rss_sites.usa import feeds as usa_feeds
from apps.newspaper_publisher.rss_sites.india import feeds as india_feeds

# Imports from Config
from configs.paths import NEWSPAPER_OUTPUT_DIR

# Combine all feeds
ALL_FEEDS = global_feeds + usa_feeds + india_feeds
FEEDS_BY_REGION = {
    "GLOBAL": global_feeds,
    "USA": usa_feeds,
    "INDIA": india_feeds
}

def get_unique_categories():
    # Only return main Regions for the new logic
    return list(FEEDS_BY_REGION.keys())

def generate_output_path(style_name, category_name):
    """Generate a unique output path using UUID."""
    # Ensure directory exists (from config)
    NEWSPAPER_OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
    
    unique_id = uuid.uuid4().hex[:8]
    safe_cat = category_name.upper()
    safe_style = style_name.replace(" ", "_").lower()
    
    # Example: classic_INDIA_ALL_a1b2c3d4.pdf
    filename = f"{safe_style}_{safe_cat}_ALL_{unique_id}.pdf"
    return NEWSPAPER_OUTPUT_DIR / filename

def get_style_or_random_substyle(style_arg, substyle_arg):
    """
    Resolve the style argument.
    If 'magazine', use substyle or pick random.
    """
    final_style = style_arg
    
    if style_arg.lower() == 'magazine':
        if substyle_arg:
            # Verify substyle exists
            matches = [s for s in MAG_STYLES.keys() if substyle_arg.lower() in s.lower()]
            if matches:
                final_style = matches[0]
                print(f"   -> Selected Substyle: {final_style}")
            else:
                print(f"[ERROR] Invalid substyle '{substyle_arg}'. using Random.")
                final_style = random.choice(list(MAG_STYLES.keys()))
        else:
            # AUTO-SELECT Substyle
            final_style = random.choice(list(MAG_STYLES.keys()))
            print(f"   -> Auto-selected Magazine Style: {final_style}")
            
    return final_style

def run_headless(args):
    """Run in CLI mode with arguments."""
    
    # 1. Resolve Category/Region
    target_feeds = []
    category_name = "CUSTOM"
    
    if args.category:
        cat_key = args.category.upper()
        if cat_key in FEEDS_BY_REGION:
            target_feeds = FEEDS_BY_REGION[cat_key]
            category_name = cat_key
        else:
            print(f"[ERROR] Invalid Category '{args.category}'. Options: {', '.join(FEEDS_BY_REGION.keys())}")
            return
    elif args.url:
        # Fallback for single custom URL
        target_feeds = [{'name': 'Custom URL', 'url': args.url, 'category': 'Custom'}]
        category_name = "CUSTOM"
    else:
        print("[ERROR] You must specify --category (INDIA, USA, GLOBAL) or --url")
        return

    # 2. Resolve Style
    style = get_style_or_random_substyle(args.style, args.substyle)

    # 3. Execute
    run_engine_parallel(target_feeds, style, category_name, substyle=args.substyle, language=args.language)

def interactive_menu():
    print("\n" + "="*60)
    print(" [NEWS] NEURAL CITADEL NEWSPAPER PUBLISHER")
    print("="*60 + "\n")
    
    # 1. Select Region (Category)
    regions = list(FEEDS_BY_REGION.keys())
    print("SELECT REGION:")
    for i, r in enumerate(regions):
        print(f"  [{i+1}] {r} ({len(FEEDS_BY_REGION[r])} feeds)")
    
    try:
        r_idx = int(input("\nChoice (Number): ")) - 1
        selected_region = regions[r_idx]
        target_feeds = FEEDS_BY_REGION[selected_region]
    except:
        print("Invalid selection, defaulting to GLOBAL.")
        selected_region = "GLOBAL"
        target_feeds = FEEDS_BY_REGION["GLOBAL"]

    # 2. Select Style
    print("\nSELECT STYLE:")
    print("  [Standard]")
    print("  [1] Classic")
    print("  [2] Modern")
    print("  [Magazine]")
    
    mag_base_idx = 3
    mag_styles = sorted(list(MAG_STYLES.keys()))
    # Option to random magazine
    print(f"  [{mag_base_idx}] Random Magazine Style")
    
    # List specific magazines
    for i, s in enumerate(mag_styles):
        print(f"  [{i+mag_base_idx+1}] {s}")
        
    try:
        sel = int(input("\nChoice (Number): "))
        if sel == 1: selected_style = 'Classic'
        elif sel == 2: selected_style = 'Modern'
        elif sel == 3: 
            selected_style = random.choice(mag_styles)
            print(f"   -> Randomly picked: {selected_style}")
        else:
            idx = sel - (mag_base_idx + 1)
            if 0 <= idx < len(mag_styles):
                selected_style = mag_styles[idx]
            else:
                print("Invalid style, using Classic.")
                selected_style = 'Classic'
    except:
        print("Invalid selection, using Classic.")
        selected_style = 'Classic'

    # Execute
    run_engine_parallel(target_feeds, selected_style, selected_region)

import platform
import subprocess

def open_file(path):
    """
    Open file using the OS default application in a cross-platform way.
    """
    system = platform.system()
    try:
        if system == 'Windows':
            os.startfile(path)
        elif system == 'Darwin':  # macOS
            subprocess.run(['open', str(path)], check=True)
        elif system == 'Linux':
            subprocess.run(['xdg-open', str(path)], check=True)
        else:
            print(f"[WARN] Automatic open not supported on {system}")
    except Exception as e:
        print(f"[ERROR] Failed to open file: {e}")

def run_engine_parallel(feeds, style_name, category_name, should_open=False, substyle=None, language="English", translation_mode="online"):
    """
    Run the engine using NewsConfig for type-safe execution.
    """
    print(f"\n[START] Initializing Engine for CATEGORY: {category_name}")
    print(f"   Target Feeds: {len(feeds)}")
    print(f"   Style: {style_name}")
    print(f"   Language: {language} (mode: {translation_mode})")
    
    # Build NewsConfig
    # Determine base style
    if style_name.lower() in ['classic', 'modern', 'magazine']:
        base_style = style_name.capitalize()
    else:
        # If style_name is a magazine substyle, style is Magazine
        base_style = 'Magazine'
        substyle = style_name
    
    try:
        config = NewsConfig(
            category=category_name,
            style=base_style,
            substyle=substyle,
            auto_open=should_open,
            language=language,
            translation_mode=translation_mode
        )
    except ValueError as e:
        print(f"[ERROR] Config Error: {e}")
        return
    
    engine = NewsEngine()
    
    try:
        # 1. Fetch using new config-based API
        articles = engine.fetch_with_config(config, feeds)
        
        if not articles:
            print("[ERROR] No articles found from any source.")
            return

        # 2. Generate using new config-based API
        output_path = engine.generate_with_config(config, articles)
        
        print(f"\n[DONE] PDF Saved: {output_path.name}")
        print(f"   Path: {output_path}")
        
        # Open file if requested via config
        if config.auto_open:
            print(f"   Opening file...")
            open_file(output_path)
                
    except Exception as e:
        print(f"\n[ERROR] Error during execution: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # ALWAYS Cleanup temp images
        engine.cleanup()

def main():
    parser = argparse.ArgumentParser(description="Neural Citadel Newspaper Runner")
    
    parser.add_argument("--message", default=None, help=argparse.SUPPRESS) # Handle internal args if any
    
    # Modes
    parser.add_argument("--interactive", "-i", action="store_true", help="Force interactive mode")
    
    # Arguments for Headless
    parser.add_argument("--category", "-c", type=str, choices=['INDIA', 'USA', 'GLOBAL'], help="Region/Category of feeds")
    parser.add_argument("--url", "-u", type=str, help="Single custom RSS URL")
    
    parser.add_argument("--style", type=str, choices=['Classic', 'Modern', 'Magazine'], help="Publication Style")
    parser.add_argument("--substyle", type=str, help="Magazine Substyle. If omitted, random is chosen.")
    parser.add_argument("--language", type=str, default="English", help="Target Language (e.g., Hindi, Spanish, Bengali)")
    
    # Translation Mode
    trans_group = parser.add_mutually_exclusive_group()
    trans_group.add_argument("--online", action="store_true", help="Use Google Translate (fast, requires internet)")
    trans_group.add_argument("--offline", action="store_true", help="Use NLLB model (slow, no internet needed)")
    
    # Open Flag
    parser.add_argument("--open", action="store_true", help="Automatically open the generated PDF")
    
    args = parser.parse_args()

    # Logic: 
    # If no args provided OR --interactive flag -> Interactive Mode
    # If args provided -> Headless Mode
    
    # Check if any "headless" args are present
    has_headless_args = (args.category or args.url or args.style)
    
    if args.interactive or not has_headless_args:
        interactive_menu()
    else:
        # Enforce style if in headless mode
        if not args.style:
             print("[ERROR] You must specify --style when using CLI mode.")
             return
        
        # Resolve Category/Region
        target_feeds = []
        category_name = "CUSTOM"
        
        if args.category:
            cat_key = args.category.upper()
            if cat_key in FEEDS_BY_REGION:
                target_feeds = FEEDS_BY_REGION[cat_key]
                category_name = cat_key
            else:
                print(f"[ERROR] Invalid Category '{args.category}'. Options: {', '.join(FEEDS_BY_REGION.keys())}")
                return
        elif args.url:
            target_feeds = [{'name': 'Custom URL', 'url': args.url, 'category': 'Custom'}]
            category_name = "CUSTOM"
        else:
            print("[ERROR] You must specify --category (INDIA, USA, GLOBAL) or --url")
            return

        # Resolve Style
        style = get_style_or_random_substyle(args.style, args.substyle)

        # Determine translation mode
        trans_mode = "offline" if args.offline else "online"

        # Execute
        run_engine_parallel(target_feeds, style, category_name, should_open=args.open, language=args.language, translation_mode=trans_mode)

# Need to update interactive menu to use default open behavior or pass it in? 
# For now, let's assume interactive mode always opens or we ask? 
# The user said "add this tag to open", usually refers to CLI. 
# Let's keep interactive simple, maybe auto-open there as it's "interactive".

def interactive_menu():
    print("\n" + "="*60)
    print(" 📰 NEURAL CITADEL NEWSPAPER PUBLISHER")
    print("="*60 + "\n")
    
    # ... (Selection logic same as before, see context) ...
    # 1. Select Region
    regions = list(FEEDS_BY_REGION.keys())
    print("SELECT REGION:")
    for i, r in enumerate(regions):
        print(f"  [{i+1}] {r} ({len(FEEDS_BY_REGION[r])} feeds)")
    
    try:
        r_idx = int(input("\nChoice (Number): ")) - 1
        selected_region = regions[r_idx]
        target_feeds = FEEDS_BY_REGION[selected_region]
    except:
        selected_region = "GLOBAL"
        target_feeds = FEEDS_BY_REGION["GLOBAL"]

    # 2. Select Style
    print("\nSELECT STYLE:")
    print("  [Standard]")
    print("  [1] Classic")
    print("  [2] Modern")
    print("  [Magazine]")
    
    mag_base_idx = 3
    mag_styles = sorted(list(MAG_STYLES.keys()))
    print(f"  [{mag_base_idx}] Random Magazine Style")
    
    for i, s in enumerate(mag_styles):
        print(f"  [{i+mag_base_idx+1}] {s}")
        
    try:
        sel = int(input("\nChoice (Number): "))
        if sel == 1: selected_style = 'Classic'
        elif sel == 2: selected_style = 'Modern'
        elif sel == 3: 
            selected_style = random.choice(mag_styles)
            print(f"   -> Randomly picked: {selected_style}")
        else:
            idx = sel - (mag_base_idx + 1)
            selected_style = mag_styles[idx]
    except:
        selected_style = 'Classic'
        
    # Ask for open? Or just default to True for interactive? 
    # Let's default to True for interactive as it's user-driven.
    run_engine_parallel(target_feeds, selected_style, selected_region, should_open=True)

if __name__ == "__main__":
    main()
