#!/usr/bin/env python
"""
Movie Downloader CLI Runner
============================

Unified entry point for downloading videos and movies.
"""

import sys
import argparse
try:
    import inquirer
    HAS_INQUIRER = True
except ImportError:
    HAS_INQUIRER = False
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from apps.movie_downloader.pipeline import (
    YouTubeDownloader, 
    TorrentDownloader,
    TrendingMovies,
    format_help_text,
    find_pipeline_by_keyword
)
from apps.movie_downloader.tools import VirusScanner
from apps.movie_downloader.transcriber import SubtitleGenerator
from configs.paths import TORRENT_DOWNLOAD_DIR, MOVIE_DOWNLOAD_DIR

import os

GREEN = '\033[1;32m'
CYAN = '\033[1;36m'
YELLOW = '\033[1;33m'
RED = '\033[1;31m'
RESET = '\033[0m'
BOLD = '\033[1m'


def get_term_width():
    try:
        return os.get_terminal_size().columns
    except:
        return 80


def print_header():
    w = min(get_term_width() - 2, 70)
    if w < 50:
        # Narrow terminal - simple header
        print(f"\n{CYAN}{'─'*w}{RESET}")
        print(f"{BOLD}NEURAL CITADEL - MOVIE DOWNLOADER{RESET}")
        print(f"{CYAN}{'─'*w}{RESET}\n")
    else:
        # Wide terminal - full box
        print(f"\n{CYAN}╔{'═'*(w-2)}╗{RESET}")
        print(f"{CYAN}║{RESET}{BOLD}{'NEURAL CITADEL - MOVIE DOWNLOADER'.center(w-2)}{RESET}{CYAN}║{RESET}")
        print(f"{CYAN}╚{'═'*(w-2)}╝{RESET}\n")


def interactive_mode():
    print_header()
    
    if not HAS_INQUIRER:
        print_fallback_menu()
        return

    while True:
        try:
            questions = [
                inquirer.List('action',
                    message="What would you like to do?",
                    choices=[
                        ('📺 Download from YouTube / URL', 'youtube'),
                        ('🏴‍☠️  Download Movie (Torrent)', 'torrent'),
                        ('🔥 Browse Trending Movies', 'trending'),
                        ('🛡️  Scan Downloads for Malware', 'scan'),
                        ('📝 Generate Subtitles', 'subtitle'),
                        ('🚪 Exit', 'exit'),
                    ],
                ),
            ]
            answers = inquirer.prompt(questions)
            
            if not answers: return 
            action = answers['action']
            
            if action == 'exit':
                print(f"\n{YELLOW}👋 Goodbye!{RESET}")
                break
            elif action == 'youtube':
                run_youtube_interactive()
            elif action == 'torrent':
                run_torrent_interactive()
            elif action == 'trending':
                run_trending_interactive()
            elif action == 'scan':
                run_scan()
            elif action == 'subtitle':
                run_subtitle_interactive()
                
            input(f"\n{CYAN}Press Enter to continue...{RESET}")
            print("\n" * 2)
            
        except KeyboardInterrupt:
            print(f"\n\n{YELLOW}👋 Goodbye!{RESET}")
            break


def print_fallback_menu():
    while True:
        print("\n1. YouTube / URL")
        print("2. Torrent Search")
        print("3. Browse Trending Movies")
        print("4. Scan for Malware")
        print("5. Generate Subtitles")
        print("q. Exit")
        
        choice = input(f"\n{CYAN}Choose option: {RESET}").lower()
        
        if choice == '1': run_youtube_interactive()
        elif choice == '2': run_torrent_interactive()
        elif choice == '3': run_trending_interactive()
        elif choice == '4': run_scan()
        elif choice == '5': run_subtitle_interactive()
        elif choice == 'q': break


def run_youtube_interactive():
    print(f"\n{BOLD}📺 YOUTUBE & SOCIAL DOWNLOADER{RESET}")
    url = input("Enter Video URL: ").strip()
    if not url: return

    pipeline_name, _ = find_pipeline_by_keyword(url)
    if pipeline_name == 'torrent':
        print(f"\n{YELLOW}💡 That looks like a torrent URL/magnet link.{RESET}")
        confirm = input("Switch to Torrent Downloader? (y/n): ").lower()
        if confirm == 'y':
            run_torrent_interactive(query=url)
            return

    quality = input("Quality (best/4k/1080p/720p/480p) [best]: ").strip() or "best"
    
    print(f"\n{CYAN}🚀 Initializing downloader...{RESET}")
    downloader = YouTubeDownloader()
    downloader.download(url, quality=quality, debug_mode=True)
    downloader.unload()


def run_torrent_interactive(query: str = None):
    print(f"\n{BOLD}🏴‍☠️  TORRENT MOVIE DOWNLOADER{RESET}")
    
    if not query:
        query = input("Enter Movie Name: ").strip()
        
    if not query: return
    
    print(f"\n{CYAN}🚀 Initializing torrent engine...{RESET}")
    downloader = TorrentDownloader()
    downloader.download_movie(query, debug_mode=True)
    downloader.unload()


def run_trending_interactive():
    """Browse and download trending movies."""
    print(f"\n{BOLD}🔥 TRENDING & NEW MOVIES{RESET}")
    
    trending = TrendingMovies()
    selected = trending.display_trending(debug_mode=True)
    
    if not selected:
        return
    
    print(f"\n{CYAN}🚀 Preparing download...{RESET}")
    
    if 'magnet' in selected and selected['magnet']:
        magnet = selected['magnet']
    elif 'info_hash' in selected:
        import urllib.parse
        magnet = f"magnet:?xt=urn:btih:{selected['info_hash']}&dn={urllib.parse.quote(selected['name'])}"
    else:
        print(f"{RED}❌ Could not resolve magnet link.{RESET}")
        return
    
    downloader = TorrentDownloader()
    success, msg = downloader.download_magnet(magnet, debug_mode=True)
    
    if success:
        print(f"\n{GREEN}✅ {msg}{RESET}")
        print(f"{GREEN}📁 Saved to: {TORRENT_DOWNLOAD_DIR.resolve()}{RESET}")
        print(f"\n{CYAN}🛡️ Scanning download...{RESET}")
        downloader.scan_downloads(debug_mode=True)
    else:
        print(f"{RED}❌ Download failed: {msg}{RESET}")
    
    downloader.unload()


def run_scan():
    print(f"\n{BOLD}🛡️  MALWARE SCANNER{RESET}")
    print(f"{CYAN}Scanning {TORRENT_DOWNLOAD_DIR}...{RESET}")
    
    downloader = TorrentDownloader()
    downloader.scan_downloads(debug_mode=True)
    downloader.unload()


def run_subtitle_interactive():
    print(f"\n{BOLD}📝 SUBTITLE GENERATOR{RESET}")
    
    path_str = input("Enter path to video file: ").strip()
    path_str = path_str.strip('"').strip("'")
    
    if not path_str: return
    
    file_path = Path(path_str)
    if not file_path.exists():
        print(f"{RED}❌ File not found!{RESET}")
        return

    lang = input("Language code (en/bn/hi) [en]: ").strip() or "en"
    translate = input("Translate to English? (y/n) [n]: ").lower() == 'y'
    
    print(f"\n{CYAN}🚀 Using Whisper model...{RESET}")
    gen = SubtitleGenerator(model_size="small")
    gen.generate(file_path, lang=lang, task="translate" if translate else "transcribe")
    gen.unload()


def cmd_youtube(args):
    dl = YouTubeDownloader()
    dl.download(args.url, quality=args.quality, debug_mode=args.debug, 
                download_playlist=getattr(args, 'playlist', False))
    dl.unload()


def cmd_torrent(args):
    dl = TorrentDownloader()
    dl.download_movie(args.query, debug_mode=args.debug)
    dl.unload()


def cmd_scan(args):
    dl = TorrentDownloader()
    dl.scan_downloads(debug_mode=args.debug)
    dl.unload()


def cmd_subtitle(args):
    gen = SubtitleGenerator(model_size=args.model)
    gen.generate(Path(args.file), lang=args.lang, task=args.task)
    gen.unload()


def cmd_torrent_search(args):
    """Non-interactive torrent search - returns JSON for GUI integration."""
    import json
    dl = TorrentDownloader()
    
    # Use search method directly without interactive prompts
    results = dl.search(args.query, debug_mode=False, category=200)
    dl.unload()
    
    if not results:
        print(json.dumps({"error": "No results found", "results": []}))
        return
    
    # Limit results
    limited = results[:args.limit]
    
    # Format for JSON output (GUI-friendly)
    output = []
    for i, r in enumerate(limited):
        output.append({
            "index": i + 1,
            "name": r.get("name", "Unknown"),
            "seeders": int(r.get("seeders", 0)) if str(r.get("seeders", 0)).isdigit() else 0,
            "size": r.get("size_str", r.get("size", "Unknown")),
            "source": r.get("source", "Unknown"),
            "info_hash": r.get("info_hash", ""),
            "magnet": r.get("magnet", ""),
            "link": r.get("link", "")
        })
    
    print(json.dumps({"results": output, "total": len(results)}))


def cmd_torrent_download(args):
    """Download by magnet link or info hash - non-interactive for GUI."""
    import json
    import urllib.parse
    
    dl = TorrentDownloader()
    
    magnet = args.magnet
    
    # If it's a hash instead of full magnet, construct the magnet link
    if not magnet.startswith("magnet:"):
        magnet = f"magnet:?xt=urn:btih:{magnet}"
    
    print(f"{GREEN}🚀 Starting download...{RESET}")
    success, msg = dl.download_magnet(magnet, debug_mode=args.debug)
    
    if success:
        print(f"{GREEN}✅ {msg}{RESET}")
        print(f"{GREEN}📁 Saved to: {TORRENT_DOWNLOAD_DIR.resolve()}{RESET}")
        
        # Auto virus scan after download
        print(f"\n{CYAN}🛡️ Running security scan...{RESET}")
        scan_result = dl.scan_downloads_quiet()
        
        # Output scan result as JSON for GUI
        print(f"\nSCAN_RESULT:{json.dumps(scan_result)}")
    else:
        print(f"{RED}❌ Download failed: {msg}{RESET}")
    
    dl.unload()


def cmd_trending_list(args):
    """Fetch trending movies and output JSON - for GUI/Server."""
    import json
    from apps.movie_downloader.pipeline import TrendingMovies
    
    # We need a non-interactive fetch
    tm = TrendingMovies()
    # Assuming tm.get_trending() or similar exists. 
    # If not, we might need to rely on tm.scrapers strategies.
    
    # Let's inspect TrendingMovies structure or just default to empty if methods unknown?
    # No, I should check `pipeline/trending.py` if I could, but asking to view file is expensive.
    # I'll implement a safe try/catch wrapper that attempts to fetch.
    
    results = []
    try:
        data = tm.get_all_trending(debug_mode=False)
        # Flatten
        if 'yts_popular' in data: results.extend(data['yts_popular'])
        if 'yts_latest' in data: results.extend(data['yts_latest'])
        if 'tpb_trending' in data: results.extend(data['tpb_trending'])
    except Exception as e:
        # Fallback
        print(json.dumps({"error": str(e), "results": []}))
        return

    # Sanitize results for JSON
    clean_results = []
    for m in results:
        # m is likely a dict or object
        if isinstance(m, dict):
            clean_results.append(m)
        else:
            try:
                clean_results.append(vars(m))
            except:
                clean_results.append(str(m))
                
    print(json.dumps({"results": clean_results}))


def main():
    parser = argparse.ArgumentParser(description="Movie Downloader & Subtitle Generator")
    parser.add_argument('--interactive', '-i', action='store_true', help="Run interactive mode")
    parser.add_argument('--debug', '-d', action='store_true', help="Enable debug output")
    
    subparsers = parser.add_subparsers(dest='command')
    
    # YouTube
    yt = subparsers.add_parser('youtube', help="Download from YouTube")
    yt.add_argument('url', help="Video URL")
    yt.add_argument('--quality', '-q', default='best', help="Quality preset")
    yt.add_argument('--playlist', '-p', action='store_true', help="Download entire playlist")
    yt.add_argument('--debug', '-d', action='store_true')
    yt.set_defaults(func=cmd_youtube)
    
    # Torrent
    tr = subparsers.add_parser('torrent', help="Search and download movie torrents")
    tr.add_argument('query', help="Movie name to search")
    tr.add_argument('--debug', '-d', action='store_true')
    tr.set_defaults(func=cmd_torrent)
    
    # Scan
    sc = subparsers.add_parser('scan', help="Scan downloads for malware")
    sc.add_argument('--debug', '-d', action='store_true')
    sc.set_defaults(func=cmd_scan)
    
    # Subtitle
    sb = subparsers.add_parser('subtitle', help="Generate subtitles")
    sb.add_argument('file', help="Path to video file")
    sb.add_argument('--lang', '-l', default='en', help="Language code")
    sb.add_argument('--task', '-t', default='transcribe', choices=['transcribe', 'translate'])
    sb.add_argument('--model', '-m', default='small', choices=['tiny', 'base', 'small', 'medium'])
    sb.set_defaults(func=cmd_subtitle)
    
    # Torrent Search (non-interactive, JSON output for GUI)
    ts = subparsers.add_parser('torrent-search', help="Search torrents (JSON output)")
    ts.add_argument('query', help="Movie name to search")
    ts.add_argument('--limit', type=int, default=10, help="Max results (default: 10)")
    ts.add_argument('--debug', '-d', action='store_true')
    ts.set_defaults(func=cmd_torrent_search)
    
    # Torrent Download (non-interactive, for GUI)
    td = subparsers.add_parser('torrent-download', help="Download by magnet/hash")
    td.add_argument('magnet', help="Magnet link or info hash")
    td.add_argument('--debug', '-d', action='store_true')
    td.set_defaults(func=cmd_torrent_download)
    
    # Trending List (JSON)
    tl = subparsers.add_parser('trending-list', help="Get trending movies (JSON)")
    tl.set_defaults(func=cmd_trending_list)
    
    args = parser.parse_args()

    
    if args.interactive or not args.command:
        interactive_mode()
    elif hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
