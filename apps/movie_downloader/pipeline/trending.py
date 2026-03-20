"""
Trending Movies Module
=======================

Aggregates trending/new movies from multiple sources.
"""

import logging
from typing import List, Dict, Any

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from .sources.yts import YTSClient

import os

def get_term_width():
    try:
        return os.get_terminal_size().columns
    except:
        return 80

YELLOW = '\033[1;33m'
RESET = '\033[0m'
GREEN = '\033[1;32m'
RED = '\033[1;31m'
CYAN = '\033[1;36m'
BLUE = '\033[1;34m'
MAGENTA = '\033[1;35m'


class TrendingMovies:
    """Aggregates trending movies from TPB and YTS."""
    
    TPB_TRENDING_URLS = [
        "https://apibay.org/precompiled/data_top100_recent.json",
        "https://apibay.se/precompiled/data_top100_recent.json",
    ]
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.yts = YTSClient()
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    def get_tpb_trending(self, debug_mode: bool = False) -> List[Dict]:
        if not HAS_REQUESTS:
            return []
        try:
            if debug_mode:
                print(f"{BLUE}⏳ Fetching TPB trending...{RESET}")
            for url in self.TPB_TRENDING_URLS:
                try:
                    resp = requests.get(url, headers=self.headers, timeout=10)
                    if resp.status_code == 200:
                        data = resp.json()
                        break
                except:
                    continue
            else:
                return []
            
            results = []
            for item in data:
                cat = int(item.get('category', 0))
                if 200 <= cat < 300:
                    results.append({
                        'name': item.get('name', 'Unknown'),
                        'seeders': str(item.get('seeders', 0)),
                        'size_str': f"{int(item.get('size', 0)) / (1024**3):.2f} GB",
                        'size': item.get('size', 0),
                        'info_hash': item.get('info_hash', ''),
                        'source': 'TPB',
                        'id': item.get('id', '')
                    })
            if debug_mode:
                print(f"{GREEN}   Found {len(results)} trending videos{RESET}")
            return results[:30]
        except Exception as e:
            self.logger.error(f"TPB trending failed: {e}")
            return []
    
    def get_all_trending(self, debug_mode: bool = False) -> Dict[str, List[Dict]]:
        tpb = self.get_tpb_trending(debug_mode)
        yts_pop = self.yts.get_trending(limit=15, debug_mode=debug_mode)
        yts_new = self.yts.get_latest(limit=15, debug_mode=debug_mode)
        
        # Filter out 0-seed torrents and sort by seeds
        def filter_and_sort(items):
            valid = [x for x in items if int(x.get('seeders', 0) or 0) > 0]
            return sorted(valid, key=lambda x: int(x.get('seeders', 0) or 0), reverse=True)
        
        return {
            'tpb_trending': filter_and_sort(tpb),
            'yts_popular': filter_and_sort(yts_pop),
            'yts_latest': filter_and_sort(yts_new)
        }
    
    def display_trending(self, debug_mode: bool = True):
        """Interactive display of trending movies."""
        w = min(get_term_width() - 2, 60)
        print(f"\n{GREEN}{'═'*w}{RESET}")
        print(f"{GREEN}🔥 TRENDING & NEW MOVIES{RESET}")
        print(f"{GREEN}{'═'*w}{RESET}\n")
        
        data = self.get_all_trending(debug_mode)
        all_movies = []
        
        if data['yts_popular']:
            print(f"{MAGENTA}━━━ 🏆 YTS Most Downloaded ━━━{RESET}\n")
            for m in data['yts_popular'][:10]:
                idx = len(all_movies) + 1
                rating = m.get('rating', 0)
                print(f"{CYAN}[{idx}]{RESET} {YELLOW}{m['name']}{RESET}")
                print(f"    ⭐ {rating}/10  🌱 {m['seeders']} seeds  💾 {m['size_str']}")
                all_movies.append(m)
            print()
        
        if data['yts_latest']:
            print(f"{MAGENTA}━━━ 🆕 Just Added (YTS) ━━━{RESET}\n")
            for m in data['yts_latest'][:5]:
                if any(x.get('hash') == m.get('hash') for x in all_movies):
                    continue
                idx = len(all_movies) + 1
                print(f"{CYAN}[{idx}]{RESET} {YELLOW}{m['name']}{RESET}")
                print(f"    🌱 {m['seeders']} seeds  💾 {m['size_str']}")
                all_movies.append(m)
            print()
        
        if data['tpb_trending']:
            print(f"{MAGENTA}━━━ 📈 TPB Hot Right Now ━━━{RESET}\n")
            for m in data['tpb_trending'][:10]:
                idx = len(all_movies) + 1
                print(f"{CYAN}[{idx}]{RESET} {YELLOW}{m['name'][:55]}{RESET}")
                print(f"    🌱 {m['seeders']} seeds  💾 {m['size_str']}")
                all_movies.append(m)
            print()
        
        if not all_movies:
            print(f"{RED}❌ Could not fetch trending data.{RESET}")
            return None
        
        w = min(get_term_width() - 2, 60)
        print(f"{GREEN}{'─'*w}{RESET}")
        choice = input(f"\n{CYAN}🔢 Enter number to download (or 'q' to quit): {RESET}")
        
        if choice.lower() == 'q':
            return None
        
        if choice.isdigit() and 0 < int(choice) <= len(all_movies):
            return all_movies[int(choice) - 1]
        
        print(f"{RED}Invalid choice{RESET}")
        return None
