#!/usr/bin/env python
"""
QR Studio Runner
================

CLI entry point for QR code generation.
Supports 374+ handler types for various data formats.

Usage:
    # List all available handlers
    python runner.py --list-handlers
    
    # SVG QR
    python runner.py --handler url --data "https://github.com" --svg --open
    
    # Gradient AUTO (random colors/mask/drawer) with QR in terminal
    python runner.py --handler url --data "https://google.com" --gradient auto --print_qr --open
    
    # Gradient MANUAL with hex colors
    python runner.py --handler url --data "https://example.com" \\
        --gradient manual --colors "#ff0000" "#00ff00" "#0000ff" \\
        --mask radial --drawer rounded --open
    
    # Gradient MANUAL with RGB colors
    python runner.py --handler wifi --data '{"ssid":"Home","password":"secret"}' \\
        --gradient manual --colors "(255,0,0)" "(0,255,0)" "(0,0,255)" \\
        --mask horizontal --open
        
    # QR with logo
    python runner.py --handler url --data "https://github.com" \\
        --gradient auto --logo "path/to/logo.png" --open
"""

import argparse
import json
import sys
from pathlib import Path

# =============================================================================
# PATH SETUP
# =============================================================================

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# =============================================================================
# IMPORTS
# =============================================================================

from apps.qr_studio.engine import QREngine
from apps.qr_studio.pipeline.svg import get_svg_config
from apps.qr_studio.pipeline.gradient import get_gradient_config, random_colors
from apps.qr_studio.pipeline.diffusion import get_diffusion_config
from apps.qr_studio.data import handlers as handler_module

# =============================================================================
# HANDLER LISTING
# =============================================================================

def list_all_handlers():
    """List all available handlers grouped by category."""
    print("=" * 70)
    print("[QR] QR Studio - Available Handlers (374+)")
    print("=" * 70)
    
    # Get HANDLERS registry from handlers module
    if hasattr(handler_module, 'HANDLERS'):
        handlers_registry = handler_module.HANDLERS
        for category, handlers in handlers_registry.items():
            print(f"\n[{category.upper()}]")
            print("-" * 40)
            handler_names = list(handlers.keys())
            # Print in columns
            for i in range(0, len(handler_names), 4):
                row = handler_names[i:i+4]
                print("  " + "  ".join(f"{h:<18}" for h in row))
    
    # Also show all format_ functions
    print("\n" + "=" * 70)
    print("📋 All format_* handlers (use handler name without 'format_' prefix):")
    print("-" * 70)
    
    all_funcs = [name[7:] for name in dir(handler_module) if name.startswith('format_')]
    for i in range(0, len(all_funcs), 5):
        row = all_funcs[i:i+5]
        print("  " + "  ".join(f"{h:<16}" for h in row))
    
    print("\n" + "=" * 70)
    print(f"Total handlers: {len(all_funcs)}")
    print("=" * 70)


# =============================================================================
# CLI ARGUMENT PARSER
# =============================================================================

def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="QR Studio - Generate styled QR codes with 374+ handler types",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all handlers
  python runner.py --list-handlers
  
  # Simple URL QR (SVG)
  python runner.py --handler url --data "https://github.com" --svg
  
  # WiFi QR with gradient (auto colors) and terminal display
  python runner.py --handler wifi --data '{"ssid":"Home","password":"123"}' --gradient auto --print_qr
  
  # Custom gradient with hex colors
  python runner.py --handler url --data "https://example.com" \\
      --gradient manual --colors "#ff5500" "#00ff55" "#5500ff" --mask radial
  
  # QR with logo
  python runner.py --handler url --data "https://github.com" --gradient auto --logo "logo.png"
  
Common Handlers:
  url, wifi, vcard, email, sms, phone_call, whatsapp, telegram_user,
  instagram_profile, twitter_profile, linkedin_profile, youtube_channel,
  bitcoin, ethereum, upi, paypal, spotify_track, github_profile, totp
        """
    )
    
    # --- Utility Arguments ---
    parser.add_argument(
        "--list-handlers",
        action="store_true",
        help="List all available handler types and exit"
    )
    
    # --- Required Arguments ---
    parser.add_argument(
        "--handler", "-H",
        type=str,
        help="Data handler type (url, wifi, vcard, email, phone_call, etc.)"
    )
    
    parser.add_argument(
        "--data", "-d",
        type=str,
        help="Data to encode. String for simple types, JSON for complex (e.g., '{\"ssid\":\"WiFi\"}')"
    )
    
    # --- Mode Selection (mutually exclusive) ---
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--svg",
        action="store_true",
        help="Generate SVG QR code"
    )
    mode_group.add_argument(
        "--gradient",
        type=str,
        choices=["auto", "manual"],
        help="Generate gradient QR. 'auto' = random colors (white background), 'manual' = specify colors"
    )
    mode_group.add_argument(
        "--diffusion",
        action="store_true",
        help="Generate AI artistic QR using Stable Diffusion + ControlNet (requires image_venv)"
    )
    
    # --- Diffusion Options ---
    parser.add_argument(
        "--prompt", "-p",
        type=str,
        default="",
        help="AI generation prompt for diffusion mode (e.g., 'enchanted forest, mystical')"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="realistic_digital",
        help="Diffusion model key (default: realistic_digital)"
    )
    parser.add_argument(
        "--control-scale",
        type=float,
        default=1.6,
        help="ControlNet scale - higher = more QR visible (default: 1.6)"
    )
    parser.add_argument(
        "--guidance-scale",
        type=float,
        default=7.0,
        help="CFG scale for prompt adherence (default: 7.0)"
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=25,
        help="Diffusion steps - more = better quality, slower (default: 25)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility"
    )
    
    # --- Gradient Options ---
    parser.add_argument(
        "--colors", "-c",
        nargs=3,
        metavar=("BACK", "CENTER", "EDGE"),
        help="3 colors: background, center/left/top, edge/right/bottom. "
             "Accepts: RGB tuple '(255,0,0)', hex '#ff0000', or named 'red'"
    )
    
    parser.add_argument(
        "--mask", "-m",
        type=str,
        choices=["horizontal", "vertical", "diagonal", "radial"],
        default="radial",
        help="Gradient mask type (default: radial)"
    )
    
    parser.add_argument(
        "--drawer",
        type=str,
        choices=["rounded", "square", "circle", "gapped"],
        default="rounded",
        help="QR module shape (default: rounded)"
    )
    
    # --- Output Options ---
    parser.add_argument(
        "--open", "-o",
        action="store_true",
        help="Open generated file after creation"
    )
    
    parser.add_argument(
        "--print_qr",
        action="store_true",
        help="Print QR code as ASCII art in terminal"
    )
    
    parser.add_argument(
        "--no-print",
        action="store_true",
        help="Don't print ASCII QR to terminal (deprecated, use --print_qr instead)"
    )
    
    # --- Advanced Options ---
    parser.add_argument(
        "--version", "-v",
        type=int,
        default=5,
        help="QR version 1-40 (default: 5)"
    )
    
    parser.add_argument(
        "--error-correction", "-e",
        type=str,
        choices=["L", "M", "Q", "H"],
        default="H",
        help="Error correction level (default: H)"
    )
    
    parser.add_argument(
        "--logo",
        type=str,
        help="Path to logo image for center overlay"
    )
    
    return parser


# =============================================================================
# DATA PARSING
# =============================================================================

# Simple handlers that take a single string argument
# Map: handler_name -> parameter_name
SIMPLE_HANDLERS = {
    # Web & URLs
    "url": "url",
    "deep_link": "scheme",
    "universal_link": "domain",
    
    # Communication
    "phone_call": "number",
    "sms": "number",
    "mms": "number",
    "email": "to",
    "facetime": "identifier",
    "whatsapp": "phone",
    "whatsapp_business": "phone",
    "telegram_user": "username",
    "telegram_message": "username",
    "telegram_bot": "bot_username",
    "signal": "phone",
    "viber": "phone",
    "skype_call": "username",
    "skype_chat": "username",
    "skype_video": "username",
    "zoom_meeting": "meeting_id",
    "google_meet": "meeting_code",
    "discord_invite": "invite_code",
    "threema_id": "threema_id",
    "session_id": "session_id",
    "matrix_user": "user_id",
    "xmpp": "jabber_id",
    
    # Social Media
    "instagram_profile": "username",
    "instagram_post": "shortcode",
    "facebook_profile": "username",
    "facebook_event": "event_id",
    "facebook_group": "group_id",
    "twitter_profile": "username",
    "twitter_tweet": "tweet_id",
    "linkedin_profile": "username",
    "linkedin_company": "company",
    "youtube_channel": "handle",
    "youtube_video": "video_id",
    "youtube_playlist": "playlist_id",
    "tiktok_profile": "username",
    "tiktok_video": "video_id",
    "snapchat_add": "username",
    "snapchat_lens": "lens_id",
    "pinterest_profile": "username",
    "reddit_profile": "username",
    "reddit_subreddit": "subreddit",
    "tumblr_blog": "blog_name",
    "mastodon_profile": "username",
    "threads_profile": "username",
    "bluesky_profile": "handle",
    "clubhouse_profile": "username",
    "bereal_profile": "username",
    
    # Finance
    "paypal": "username",
    "venmo": "username",
    "cash_app": "cashtag",
    "bitcoin": "address",
    "ethereum": "address",
    "usdt_erc20": "address",
    "usdt_trc20": "address",
    "litecoin": "address",
    "dogecoin": "address",
    "monero": "address",
    "solana": "address",
    "cardano": "address",
    "ripple": "address",
    "bnb": "address",
    "polygon_matic": "address",
    
    # Developer
    "github_profile": "username",
    "github_repo": "repo",
    "github_gist": "gist_id",
    "gitlab_project": "project",
    "bitbucket_repo": "repo",
    "npm_package": "package",
    "pypi_package": "package",
    "docker_hub": "repository",
    "notion_page": "page_id",
    "figma_file": "file_key",
    "miro_board": "board_id",
    
    # Media
    "spotify_uri": "uri",
    "spotify_track": "track_id",
    "spotify_playlist": "playlist_id",
    "spotify_artist": "artist_id",
    "apple_music_url": "url",
    "soundcloud_user": "username",
    "soundcloud_track": "track_url",
    "twitch_channel": "channel",
    "twitch_vod": "vod_id",
    "netflix_title": "title_id",
    "steam_profile": "steam_id",
    "steam_game": "app_id",
    "playstation_profile": "psn_id",
    "xbox_profile": "gamertag",
    
    # App Stores
    "google_play_app": "package_id",
    "apple_app_store": "app_id",
    "fdroid_app": "app_id",
    
    # Content
    "plain_text": "text",
    "normal": "text",
    "arxiv_paper": "arxiv_id",
    "doi": "doi",
    "isbn": "isbn",
    "wikipedia": "article",
    "google_search": "query",
    "amazon_product": "asin",
    
    # Asian Social
    "weibo": "user_id",
    "douyin": "user_id",
    "xiaohongshu": "user_id",
    "bilibili": "uid",
    "qq": "qq_number",
    "wechat_profile": "wechat_id",
    "line_profile": "line_id",
    "line_add_friend": "line_id",
    "kakaotalk": "kakao_id",
    "zalo": "zalo_id",
    
    # Real Estate
    "zillow_listing": "zpid",
    "realtor_listing": "listing_id",
    "redfin_listing": "listing_id",
    "trulia_listing": "listing_id",
    "apartments_listing": "listing_id",
    
    # NFT/Web3
    "opensea_nft": "asset_url",
    "metamask_connect": "address",
    "ens_domain": "domain",
    "ipfs_gateway": "cid",
    "etherscan_tx": "tx_hash",
    "etherscan_address": "address",
}


def parse_data(handler: str, data_str: str) -> dict:
    """
    Parse data string into dictionary for handler.
    
    Priority:
    1. Try JSON first (for multi-field handlers like wifi, vcard, deep_link)
    2. Fall back to simple handler wrapping for single-value strings
    """
    # Try JSON first for ALL handlers (allows GUI to send multi-field data)
    try:
        parsed = json.loads(data_str)
        # Only use JSON if it's a dict (not a plain number or string)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    
    # Fall back to simple handler logic for plain strings
    if handler in SIMPLE_HANDLERS:
        param_name = SIMPLE_HANDLERS[handler]
        return {param_name: data_str}
    
    # Try to get handler function and inspect its parameters
    handler_func = getattr(handler_module, f"format_{handler}", None)
    if handler_func:
        import inspect
        sig = inspect.signature(handler_func)
        params = list(sig.parameters.keys())
        if params:
            # Use first parameter name
            return {params[0]: data_str}
    
    # Fallback - use 'text' as generic parameter
    return {"text": data_str}


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def main():
    parser = create_parser()
    args = parser.parse_args()
    
    # --- Handle --list-handlers ---
    if args.list_handlers:
        list_all_handlers()
        sys.exit(0)
    
    # Validate required arguments
    if not args.handler:
        print("[ERROR] --handler is required")
        print("   Use --list-handlers to see all available handlers")
        sys.exit(1)
    
    if not args.data:
        print("[ERROR] --data is required")
        sys.exit(1)
    
    if not args.svg and not args.gradient and not args.diffusion:
        print("[ERROR] Must specify --svg, --gradient, or --diffusion")
        sys.exit(1)
    
    # Parse the data
    data = parse_data(args.handler, args.data)
    
    # Determine print_qr setting
    # --print_qr enables, --no-print disables. Default depends on neither being set.
    if args.print_qr:
        print_qr = True
    elif args.no_print:
        print_qr = False
    else:
        print_qr = True  # Default to printing
    
    print("=" * 60, flush=True)
    print("[QR] QR Studio", flush=True)
    print("=" * 60, flush=True)
    print(f"Handler: {args.handler}", flush=True)
    print(f"Data: {data}", flush=True)
    
    # Create engine
    engine = QREngine()
    
    # --- SVG MODE ---
    if args.svg:
        print(f"Mode: SVG", flush=True)
        config = get_svg_config(
            data=data,
            template_type=args.handler,
            module_drawer=args.drawer,
            logo_path=args.logo,
            print_qr=print_qr,
            version=args.version,
            error_correction=args.error_correction,
        )
        
        # Generate SVG
        print("-" * 60, flush=True)
        output_path = engine.generate(config, open_file=args.open)
    
    # --- GRADIENT MODE ---
    elif args.gradient:
        auto_mode = (args.gradient == "auto")
        print(f"Mode: Gradient ({'AUTO' if auto_mode else 'MANUAL'})", flush=True)
        
        if auto_mode:
            colors = None  # Will be randomized (with white background!)
            print("   Background: WHITE (always)")
        else:
            if not args.colors:
                print("[ERROR] --colors required for manual gradient mode")
                print("   Example: --colors '#ff0000' '#00ff00' '#0000ff'")
                sys.exit(1)
            colors = args.colors
        
        config = get_gradient_config(
            data=data,
            template_type=args.handler,
            auto_mode=auto_mode,
            colors=colors,
            mask=args.mask,
            module_drawer=args.drawer,
            logo_path=args.logo,
            print_qr=print_qr,
            version=args.version,
            error_correction=args.error_correction,
        )
        
        # Generate
        print("-" * 60)
        output_path = engine.generate(config, open_file=args.open)
    
    # --- DIFFUSION MODE ---
    elif args.diffusion:
        print(f"Mode: DIFFUSION (AI Artistic)")
        print(f"   Prompt: '{args.prompt[:50]}...'" if len(args.prompt) > 50 else f"   Prompt: '{args.prompt}'")
        
        # Step 1: Create base QR config (high contrast, no gradient)
        config = get_diffusion_config(
            data=data,
            template_type=args.handler,
            prompt=args.prompt,
            model=args.model,
            control_scale=args.control_scale,
            guidance_scale=args.guidance_scale,
            steps=args.steps,
            seed=args.seed,
            version=args.version,
            error_correction=args.error_correction,
        )
        
        # Step 2: Generate base QR (temp file)
        print("-" * 60, flush=True)
        print("[STEP 1] Generating base QR...", flush=True)
        base_qr_path = engine.generate(config, open_file=False)
        print(f"   Base QR: {base_qr_path}", flush=True)
        
        # Step 3: Run diffusion subprocess
        print("-" * 60, flush=True)
        print("[STEP 2] Running AI diffusion...", flush=True)
        output_path = engine.run_diffusion_subprocess(
            input_qr_path=base_qr_path,
            prompt=config.diffusion_prompt,
            model=config.diffusion_model,
            control_scale=config.diffusion_control_scale,
            guidance_scale=config.diffusion_guidance_scale,
            steps=config.diffusion_steps,
            seed=config.diffusion_seed,
            delete_input=True,  # Clean up temp file
        )
        
        if output_path is None:
            print("[ERROR] Diffusion failed", flush=True)
            sys.exit(1)
        
        if args.open:
            engine._open_file(output_path)
    
    print("-" * 60, flush=True)
    print(f"[OUTPUT] {output_path}", flush=True)
    print("=" * 60, flush=True)
    
    return output_path


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    main()

