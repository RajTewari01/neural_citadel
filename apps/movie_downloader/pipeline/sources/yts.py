"""
YTS.mx API Source
==================

High-quality movie torrents with clean REST API.
"""

import logging
import urllib.parse
from typing import Optional, List, Dict, Any

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

YELLOW = '\033[1;33m'
RESET = '\033[0m'
GREEN = '\033[1;32m'
RED = '\033[1;31m'
CYAN = '\033[1;36m'
BLUE = '\033[1;34m'


class YTSClient:
    """YTS.mx API client for movie torrents."""
    
    BASE_URLS = [
        "https://yts.mx/api/v2",
        "https://yts.torrentbay.st/api/v2",
    ]
    
    TRACKERS = [
        "udp://open.demonii.com:1337/announce",
        "udp://tracker.openbittorrent.com:80",
        "udp://tracker.coppersurfer.tk:6969",
        "udp://tracker.opentrackr.org:1337/announce",
    ]
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = self.BASE_URLS[0]
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
    def _get_working_api(self) -> str:
        for url in self.BASE_URLS:
            try:
                resp = requests.get(f"{url}/list_movies.json?limit=1", headers=self.headers, timeout=5)
                if resp.status_code == 200 and resp.json().get('status') == 'ok':
                    return url
            except:
                continue
        return self.BASE_URLS[0]
    
    def _build_magnet(self, torrent: Dict) -> str:
        hash_val = torrent.get('hash', '')
        name = urllib.parse.quote(torrent.get('title', 'Unknown'))
        trackers = '&'.join([f"tr={urllib.parse.quote(t)}" for t in self.TRACKERS])
        return f"magnet:?xt=urn:btih:{hash_val}&dn={name}&{trackers}"
    
    def search(self, query: str, quality: str = "all", debug_mode: bool = False) -> List[Dict]:
        if not HAS_REQUESTS:
            return []
        results = []
        try:
            if debug_mode:
                print(f"{BLUE}⏳ Fetching YTS...{RESET}")
            self.base_url = self._get_working_api()
            params = {'query_term': query, 'limit': 50, 'sort_by': 'seeds', 'order_by': 'desc'}
            if quality != "all":
                params['quality'] = quality
            resp = requests.get(f"{self.base_url}/list_movies.json", params=params, headers=self.headers, timeout=10)
            if resp.status_code != 200:
                return []
            data = resp.json()
            if data.get('status') != 'ok':
                return []
            movies = data.get('data', {}).get('movies', [])
            for movie in movies:
                title = movie.get('title', 'Unknown')
                year = movie.get('year', '')
                for torrent in movie.get('torrents', []):
                    quality = torrent.get('quality', '')
                    results.append({
                        'name': f"{title} ({year}) [{quality}] - YTS",
                        'seeders': str(torrent.get('seeds', 0)),
                        'size_str': torrent.get('size', '0'),
                        'size': torrent.get('size_bytes', 0),
                        'quality': quality,
                        'hash': torrent.get('hash', ''),
                        'magnet': self._build_magnet({'hash': torrent.get('hash', ''), 'title': f"{title} {year}"}),
                        'imdb': movie.get('imdb_code', ''),
                        'source': 'YTS',
                        'id': torrent.get('hash', ''),
                        'username': 'YTS.mx'
                    })
        except Exception as e:
            self.logger.error(f"YTS search failed: {e}")
        return results
    
    def get_trending(self, limit: int = 20, debug_mode: bool = False) -> List[Dict]:
        if not HAS_REQUESTS:
            return []
        try:
            if debug_mode:
                print(f"{BLUE}⏳ Fetching YTS trending...{RESET}")
            self.base_url = self._get_working_api()
            resp = requests.get(f"{self.base_url}/list_movies.json", 
                params={'limit': limit, 'sort_by': 'download_count', 'order_by': 'desc', 'quality': '1080p'},
                headers=self.headers, timeout=10)
            if resp.status_code != 200:
                return []
            data = resp.json()
            movies = data.get('data', {}).get('movies', [])
            results = []
            for movie in movies:
                torrents = movie.get('torrents', [])
                best = next((t for t in torrents if t.get('quality') == '1080p'), torrents[0] if torrents else None)
                if best:
                    results.append({
                        'name': f"{movie.get('title')} ({movie.get('year')})",
                        'seeders': str(best.get('seeds', 0)),
                        'size_str': best.get('size', 'Unknown'),
                        'quality': best.get('quality', ''),
                        'rating': movie.get('rating', 0),
                        'hash': best.get('hash', ''),
                        'magnet': self._build_magnet({'hash': best.get('hash', ''), 'title': f"{movie.get('title')} {movie.get('year')}"}),
                        'source': 'YTS',
                        'id': best.get('hash', '')
                    })
            return results
        except Exception as e:
            self.logger.error(f"YTS trending failed: {e}")
            return []

    def get_latest(self, limit: int = 20, debug_mode: bool = False) -> List[Dict]:
        if not HAS_REQUESTS:
            return []
        try:
            if debug_mode:
                print(f"{BLUE}⏳ Fetching YTS latest...{RESET}")
            self.base_url = self._get_working_api()
            resp = requests.get(f"{self.base_url}/list_movies.json",
                params={'limit': limit, 'sort_by': 'date_added', 'order_by': 'desc'},
                headers=self.headers, timeout=10)
            if resp.status_code != 200:
                return []
            data = resp.json()
            movies = data.get('data', {}).get('movies', [])
            results = []
            for movie in movies:
                torrents = movie.get('torrents', [])
                best = next((t for t in torrents if t.get('quality') == '1080p'), torrents[0] if torrents else None)
                if best:
                    results.append({
                        'name': f"{movie.get('title')} ({movie.get('year')})",
                        'seeders': str(best.get('seeds', 0)),
                        'size_str': best.get('size', 'Unknown'),
                        'quality': best.get('quality', ''),
                        'rating': movie.get('rating', 0),
                        'hash': best.get('hash', ''),
                        'magnet': self._build_magnet({'hash': best.get('hash', ''), 'title': f"{movie.get('title')} {movie.get('year')}"}),
                        'source': 'YTS',
                        'id': best.get('hash', '')
                    })
            return results
        except Exception as e:
            self.logger.error(f"YTS latest failed: {e}")
            return []
