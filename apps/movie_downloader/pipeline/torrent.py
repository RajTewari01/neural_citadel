"""
Torrent Download Pipeline
==========================

Multi-source torrent search and download using TPB, 1337x, and YTS APIs.
"""

import gc
import os
import sys
import stat
import time
import logging
import platform
import subprocess
import urllib.parse
import traceback
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from configs.paths import TORRENT_DOWNLOAD_DIR, ARIA2_EXE, EXE_DIR, DEBUG_LOG_DIR
from .registry import register_pipeline, DownloadConfig
from .sources.yts import YTSClient

# Colors
YELLOW = '\033[1;33m'
RESET = '\033[0m'
GREEN = '\033[1;32m'
RED = '\033[1;31m'
CYAN = '\033[1;36m'
BLUE = '\033[1;34m'
MAGENTA = '\033[1;35m'

DEBUG_LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = DEBUG_LOG_DIR / "torrent.log"

logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)-8s - %(message)s')

def get_term_width():
    try:
        return os.get_terminal_size().columns
    except:
        return 80


class Aria2NotFoundError(Exception):
    pass


class APIMirrorManager:
    """Dynamic mirror discovery for ThePirateBay API."""
    
    PRIMARY_MIRRORS = [
        "https://apibay.org",
        "https://apibay.se",
        "https://apithepiratebay.org",
    ]
    
    _cached_mirror: Optional[str] = None
    _cache_time: float = 0
    _cache_duration: int = 3600
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    def _test_mirror(self, base_url: str, timeout: int = 5) -> bool:
        try:
            test_url = f"{base_url.rstrip('/')}/q.php?q=test&cat=0"
            response = requests.get(test_url, headers=self.headers, timeout=timeout)
            if response.status_code == 200:
                return isinstance(response.json(), list)
        except:
            pass
        return False
    
    def get_working_mirror(self, debug_mode: bool = False) -> str:
        if self._cached_mirror and (time.time() - self._cache_time < self._cache_duration):
            return self._cached_mirror
        
        if debug_mode:
            print(f"\n{BLUE}🔄 Finding working API mirror...{RESET}")
        
        for mirror in self.PRIMARY_MIRRORS:
            if debug_mode:
                print(f"{CYAN}   ├─ Testing: {mirror}{RESET}", end=" ")
            if self._test_mirror(mirror):
                if debug_mode:
                    print(f"{GREEN}✓ Working!{RESET}")
                self._cached_mirror = mirror
                self._cache_time = time.time()
                return mirror
            elif debug_mode:
                print(f"{RED}✗ Failed{RESET}")
        
        return "https://apibay.org"
    
    def clear_cache(self):
        self._cached_mirror = None
        self._cache_time = 0


class Scraper1337x:
    """Backup scraper for 1337x.to."""
    
    BASE_URLS = ["https://1337x.to", "https://1337x.so", "https://1337x.st"]
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    def _get_working_domain(self) -> str:
        for url in self.BASE_URLS:
            try:
                if requests.get(url, headers=self.headers, timeout=3).status_code == 200:
                    return url
            except:
                continue
        return self.BASE_URLS[0]

    def search(self, query: str) -> List[Dict]:
        results = []
        try:
            base_url = self._get_working_domain()
            search_url = f"{base_url}/search/{urllib.parse.quote(query)}/1/"
            resp = requests.get(search_url, headers=self.headers, timeout=10)
            if resp.status_code != 200:
                return []
            soup = BeautifulSoup(resp.text, 'html.parser')
            table = soup.find('table')
            if not table:
                return []
            for row in table.find_all('tr')[1:]:
                cols = row.find_all('td')
                if len(cols) < 2:
                    continue
                name_col = cols[0]
                links = name_col.find_all('a')
                if len(links) < 2:
                    continue
                link_tag = links[1]
                name = link_tag.text.strip()
                link = link_tag['href']
                if not link.startswith('http'):
                    link = f"{base_url}{link}"
                seeds = cols[1].text.strip() if len(cols) > 1 else "0"
                size = cols[4].text.strip() if len(cols) > 4 else "Unknown"
                uploader = cols[5].text.strip() if len(cols) > 5 else "Unknown"
                results.append({
                    'name': name,
                    'seeders': seeds,
                    'size_str': size,
                    'link': link,
                    'username': uploader,
                    'source': '1337x',
                    'id': link
                })
        except Exception as e:
            self.logger.error(f"1337x search failed: {e}")
        return results

    def get_magnet(self, url: str) -> Optional[str]:
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            for a in soup.find_all('a', href=True):
                if a['href'].startswith('magnet:?'):
                    return a['href']
        except Exception as e:
            self.logger.error(f"1337x magnet fetch failed: {e}")
        return None


class TorrentDownloader:
    """Multi-source torrent downloader with TPB, 1337x, and YTS support."""
    
    BLOCK_LIST = [".exe", ".bat", ".vbs", ".msi", ".cmd", ".scr", ".lnk"]
    WARNING_LIST = [".zip", ".rar", ".iso", ".7z", ".dmg"]
    
    def __init__(self):
        if not HAS_DEPS:
            raise ImportError("Missing: requests, beautifulsoup4")
        gc.collect()
        self.logger = logging.getLogger(__name__)
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        self.os_type = platform.system()
        self.mirror_manager = APIMirrorManager()
        self.scraper_1337x = Scraper1337x()
        self.yts_client = YTSClient()
        
        # Import virus scanner lazily
        try:
            from ..tools.virus_scanner import VirusScanner
            self.virus_scanner = VirusScanner()
        except:
            self.virus_scanner = None
        
        self.aria_executable = self._get_aria_path()
        if not Path(self.aria_executable).exists() and self.os_type == "Windows":
            raise Aria2NotFoundError(f"aria2c not found at: {self.aria_executable}")
        TORRENT_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        print(f'{GREEN}{"Torrent Downloader Ready".center(50, "-")}{RESET}')
    
    def _get_aria_path(self) -> str:
        if self.os_type == "Windows":
            return str(ARIA2_EXE)
        elif self.os_type == "Linux":
            return "aria2c"
        elif self.os_type == "Darwin":
            return "aria2c"
        raise OSError("Unsupported OS")
    
    def get_trackers(self) -> str:
        try:
            url = "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_best.txt"
            response = requests.get(url, timeout=5)
            return response.text.replace('\n\n', ',').replace('\n', ',')
        except:
            return "udp://tracker.opentrackr.org:1337/announce,udp://tracker.openbittorrent.com:6969/announce"
    
    def search(self, query: str, debug_mode: bool = False, category: int = 200) -> Optional[List[Dict]]:
        """Search multiple sources for torrents."""
        if not query:
            return None
        
        if debug_mode:
            w = min(get_term_width() - 2, 60)
            print(f"\n{GREEN}{'='*w}{RESET}")
            print(f"{GREEN}🔍 Searching for: {CYAN}'{query}'{RESET} (Category: {category})")
            print(f"{GREEN}{'='*w}{RESET}")
        
        # TPB Results
        tpb_results = []
        try:
            mirror_url = self.mirror_manager.get_working_mirror(debug_mode)
            search_url = f'{mirror_url}/q.php?q={urllib.parse.quote(query)}&cat={category}'
            if debug_mode:
                print(f"\n{BLUE}📡 TPB API: {search_url}{RESET}")
                print(f"{BLUE}⏳ Fetching TPB...{RESET}")
            resp = requests.get(search_url, headers=self.headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data and not (isinstance(data, list) and len(data) == 1 and data[0].get('id') == '0'):
                for item in data:
                    item['source'] = 'TPB'
                    item['size_str'] = f"{int(item['size']) / (1024**3):.2f} GB"
                tpb_results = data
        except Exception as e:
            self.logger.error(f"TPB Search failed: {e}")
        
        # 1337x Results
        if debug_mode:
            print(f"{BLUE}⏳ Fetching 1337x...{RESET}")
        x1337_results = self.scraper_1337x.search(query)
        
        # YTS Results
        yts_results = self.yts_client.search(query, debug_mode=debug_mode)
        
        # Combine
        all_results = tpb_results + x1337_results + yts_results
        
        if not all_results:
            if debug_mode:
                print(f"\n{RED}❌ No results found{RESET}")
            return None
        
        # Relevance scoring - but seeders are MORE important
        def calculate_score(item):
            name = item.get('name', '').lower()
            q_words = set(query.lower().split())
            n_words = set(name.split())
            score = 0
            if query.lower() in name:
                score += 20  # Reduced from 100
            if q_words.issubset(n_words):
                score += 10  # Reduced from 50
            score += (len(q_words & n_words) * 2)
            return score
        
        for item in all_results:
            try:
                item['_seeds_int'] = int(item.get('seeders', 0))
            except:
                item['_seeds_int'] = 0
        
        # Sort by: SEEDERS FIRST (descending), then relevance score
        all_results.sort(key=lambda x: (x['_seeds_int'], calculate_score(x)), reverse=True)
        
        if debug_mode:
            print(f"\n{GREEN}✅ Found {len(all_results)} results (TPB: {len(tpb_results)}, 1337x: {len(x1337_results)}, YTS: {len(yts_results)})!{RESET}")
        
        return all_results
    
    def check_reputation(self, torrent: Dict, debug_mode: bool = False) -> Dict[str, Any]:
        """Pre-download reputation check."""
        warnings = []
        risk_score = 0
        
        if debug_mode:
            print(f"\n{BLUE}🔍 Running security checks...{RESET}")
        
        try:
            name = torrent.get('name', '').lower()
            
            # Handle size
            size_val = torrent.get('size', 0)
            size_mb = 0
            if isinstance(size_val, (int, float)):
                size_mb = float(size_val) / (1024**2)
            elif isinstance(size_val, str):
                if size_val.isdigit():
                    size_mb = float(size_val) / (1024**2)
                else:
                    val = size_val.upper().replace(',', '')
                    if 'GB' in val:
                        size_mb = float(val.replace('GB', '').strip()) * 1024
                    elif 'MB' in val:
                        size_mb = float(val.replace('MB', '').strip())
            
            try:
                seeders = int(torrent.get('seeders', 0))
            except:
                seeders = 0
            
            # Check for executables
            for ext in self.BLOCK_LIST:
                if ext in name:
                    warnings.append(f"🚨 Executable detected ({ext})")
                    risk_score += 100
            
            # Video size check
            video_exts = ['.mp4', '.mkv', '.avi', '.mov', '.wmv']
            if any(ext in name for ext in video_exts) and size_mb < 100:
                warnings.append(f"⚠️ Video too small ({size_mb:.1f}MB)")
                risk_score += 50
            
            # Low seeders
            if seeders < 3:
                warnings.append(f"⚠️ Very few seeders ({seeders})")
                risk_score += 20
            
            if risk_score >= 100:
                risk_level, safe = 'CRITICAL', False
            elif risk_score >= 50:
                risk_level, safe = 'HIGH', False
            elif risk_score >= 20:
                risk_level, safe = 'MEDIUM', True
            else:
                risk_level, safe = 'LOW', True
            
            result = {'safe': safe, 'risk_level': risk_level, 'risk_score': risk_score,
                     'warnings': warnings, 'seeders': seeders, 'size_mb': size_mb}
            
            if debug_mode:
                if risk_level in ['CRITICAL', 'HIGH']:
                    w = min(get_term_width() - 2, 60)
                    print(f"\n{RED}{'═'*w}{RESET}")
                    print(f"{RED}🚨 {risk_level} RISK - Score: {risk_score}/100{RESET}")
                else:
                    w = min(get_term_width() - 2, 60)
                    print(f"\n{GREEN}{'─'*w}{RESET}")
                    print(f"{GREEN}✅ LOW RISK - Score: {risk_score}/100{RESET}")
                print(f"{CYAN}   Seeders: {seeders} | Size: {size_mb:.1f} MB{RESET}")
            
            return result
        except Exception as e:
            return {'safe': True, 'risk_level': 'UNKNOWN', 'risk_score': 0, 'warnings': []}
    
    def download_magnet(self, magnet_link: str, debug_mode: bool = False) -> Tuple[bool, str]:
        """Download via magnet link using aria2c."""
        try:
            trackers = self.get_trackers()
            cmd = [
                self.aria_executable,
                "--seed-time=0",
                "--file-allocation=none",
                f"--bt-tracker={trackers}",
                "-d", str(TORRENT_DOWNLOAD_DIR),
                magnet_link
            ]
            if debug_mode:
                print(f"\n{BLUE}🔧 Starting aria2c...{RESET}")
                print(f"{CYAN}   Download dir: {TORRENT_DOWNLOAD_DIR}{RESET}")
            subprocess.run(cmd, check=True)
            return True, "Download Complete."
        except subprocess.CalledProcessError as e:
            return False, f"aria2c failed with code {e.returncode}"
        except Exception as e:
            return False, str(e)
    
    def download_movie(self, search_query: str, debug_mode: bool = False, auto_scan: bool = True):
        """Interactive movie search and download."""
        try:
            self._print_banner()
            results = self.search(search_query, debug_mode=debug_mode)
            
            if not results:
                print(f"\n{RED}❌ No results found.{RESET}")
                return
            
            w = min(get_term_width() - 2, 60)
            print(f"\n{GREEN}{'═'*w}{RESET}")
            print(f"{GREEN}📺 TOP RESULTS:{RESET}")
            print(f"{GREEN}{'═'*w}{RESET}\n")
            
            # Get terminal width for proper truncation
            try:
                term_width = os.get_terminal_size().columns
            except:
                term_width = 80
            
            # Name gets: width - 40 (for size/seeds/source display)
            max_name_len = max(30, term_width - 45)
            
            for i, r in enumerate(results[:10]):
                size_display = r.get('size_str', 'Unknown')
                source = r.get('source', 'Unknown')
                name = r['name'][:max_name_len]
                print(f"{CYAN}[{i+1}]{RESET} {YELLOW}{name}{RESET}")
                print(f"    {MAGENTA}💾{RESET} {size_display}  {GREEN}🌱{RESET} {r['seeders']} seeds  [{source}]")
                print()
            
            w = min(get_term_width() - 2, 60)
            print(f"{GREEN}{'─'*w}{RESET}")
            choice = input(f"\n{CYAN}🔢 Enter number (or 'q' to quit): {RESET}")
            
            if choice.lower() == 'q':
                print(f"{YELLOW}👋 Goodbye!{RESET}")
                return
            
            if not choice.isdigit() or not (0 < int(choice) <= len(results)):
                print(f"{RED}Invalid choice!{RESET}")
                return
            
            selected = results[int(choice)-1]
            reputation = self.check_reputation(selected, debug_mode=True)
            
            if not reputation['safe']:
                print(f"\n{RED}🛑 DOWNLOAD BLOCKED FOR SAFETY{RESET}")
                proceed = input(f"{RED}Type 'DANGER' to proceed anyway: {RESET}")
                if proceed != 'DANGER':
                    print(f"{GREEN}✓ Wise choice. Cancelled.{RESET}")
                    return
            
            # Resolve magnet
            magnet = None
            source = selected.get('source', '')
            
            if 'magnet' in selected and selected['magnet']:
                magnet = selected['magnet']
            elif source == '1337x':
                print(f"{CYAN}Resolving magnet from 1337x...{RESET}")
                magnet = self.scraper_1337x.get_magnet(selected['link'])
                if not magnet:
                    print(f"{RED}❌ Failed to extract magnet.{RESET}")
                    return
            elif 'info_hash' in selected:
                magnet = f"magnet:?xt=urn:btih:{selected['info_hash']}&dn={urllib.parse.quote(selected['name'])}"
            else:
                print(f"{RED}❌ Could not resolve magnet.{RESET}")
                return
            
            print(f"\n{GREEN}🚀 Starting download...{RESET}")
            success, msg = self.download_magnet(magnet, debug_mode=debug_mode)
            
            if success:
                w = min(get_term_width() - 2, 60)
                print(f"\n{GREEN}{'═'*w}{RESET}")
                print(f"{GREEN}✅ {msg}{RESET}")
                print(f"{GREEN}📁 Saved to: {TORRENT_DOWNLOAD_DIR.resolve()}{RESET}")
                print(f"{GREEN}{'═'*w}{RESET}")
                
                if auto_scan:
                    print(f"\n{BLUE}🛡️ Initiating automatic malware scan...{RESET}")
                    self.scan_downloads(debug_mode=True)
            else:
                print(f"\n{RED}❌ Download Failed: {msg}{RESET}")
                
        except KeyboardInterrupt:
            print(f"\n{YELLOW}⚠️ Interrupted{RESET}")
        except Exception as e:
            if debug_mode:
                traceback.print_exc()
            print(f"\n{RED}❌ Error: {str(e)}{RESET}")
    
    def scan_downloads(self, debug_mode: bool = False):
        """Scan downloaded files for malware."""
        if debug_mode:
            w = min(get_term_width() - 2, 60)
            print(f"\n{BLUE}{'═'*w}{RESET}")
            print(f"{BLUE}🛡️ SCANNING DOWNLOADS{RESET}")
            print(f"{BLUE}{'═'*w}{RESET}")
        
        files = [f for f in TORRENT_DOWNLOAD_DIR.glob('*') if f.is_file() and not f.name.endswith('.aria2')]
        
        if not files:
            if debug_mode:
                print(f"{YELLOW}No files to scan{RESET}")
            return
        
        for file_path in files:
            if debug_mode:
                print(f"\n{CYAN}📄 {file_path.name}{RESET}")
            
            if self.virus_scanner:
                result = self.virus_scanner.full_scan(str(file_path), debug_mode=debug_mode)
                if not result['overall_safe']:
                    delete = input(f"{RED}DELETE this file? (yes/no): {RESET}")
                    if delete.lower() == 'yes':
                        file_path.unlink()
                        print(f"{GREEN}✓ Deleted{RESET}")
            else:
                print(f"{YELLOW}   Scanner not available{RESET}")
    
    def scan_downloads_quiet(self) -> dict:
        """Non-interactive scan - returns structured results for GUI.
        
        Returns dict with:
            - files_scanned: int
            - total_risk_score: int
            - risk_level: str (LOW/MEDIUM/HIGH)
            - results: list of file scan results
        """
        files = [f for f in TORRENT_DOWNLOAD_DIR.glob('*') 
                 if f.is_file() and not f.name.endswith('.aria2')]
        
        if not files:
            return {
                "files_scanned": 0,
                "total_risk_score": 0,
                "risk_level": "LOW",
                "results": [],
                "message": "No files to scan"
            }
        
        results = []
        total_score = 0
        
        for file_path in files:
            file_result = {
                "name": file_path.name,
                "path": str(file_path),
                "risk_score": 0,
                "safe": True,
                "warnings": []
            }
            
            if self.virus_scanner:
                scan = self.virus_scanner.full_scan(str(file_path), debug_mode=False)
                file_result["risk_score"] = scan.get("risk_score", 0)
                file_result["safe"] = scan.get("overall_safe", True)
                file_result["warnings"] = scan.get("warnings", [])
            else:
                # Basic checks without scanner
                name_lower = file_path.name.lower()
                for ext in self.BLOCK_LIST:
                    if name_lower.endswith(ext):
                        file_result["risk_score"] = 100
                        file_result["safe"] = False
                        file_result["warnings"].append(f"Executable file ({ext})")
                        break
            
            total_score += file_result["risk_score"]
            results.append(file_result)
        
        # Calculate average risk and level
        avg_score = total_score / len(files) if files else 0
        
        if avg_score < 20:
            risk_level = "LOW"
        elif avg_score < 50:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
        
        return {
            "files_scanned": len(files),
            "total_risk_score": int(avg_score),
            "risk_level": risk_level,
            "results": results,
            "message": f"Scanned {len(files)} file(s)"
        }
    
    def _print_banner(self):
        w = min(get_term_width() - 4, 60)
        def gothic(text):
            normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
            goth = "𝕬𝕭𝕮𝕯𝕰𝕱𝕲𝕳𝕴𝕵𝕶𝕷𝕸𝕹𝕺𝕻𝕼𝕽𝕾𝕿𝖀𝖁𝖂𝖃𝖄𝖅𝖆𝖇𝖈𝖉𝖊𝖋𝖌𝖍𝖎𝖏𝖐𝖑𝖒𝖓𝖔𝖕𝖖𝖗𝖘𝖙𝖚𝖛𝖜𝖝𝖞𝖟"
            return text.translate(str.maketrans(normal, goth))
        title = gothic("Movie Newspaper")
        print(f'\n{RED}{"▄"*w}{RESET}')
        print(f'{YELLOW}📢 {title} 📢{RESET}')
        print(f'{RED}{"▀"*w}{RESET}\n')
    
    def unload(self):
        gc.collect()
        print(f"{GREEN}[Clean] Torrent downloader unloaded{RESET}")


@register_pipeline(
    name="torrent",
    keywords=["torrent", "magnet", "piratebay", "tpb", "movie", "film"],
    description="Download movies via torrent with security scanning",
    category="video",
    supported_sites=["thepiratebay.org", "apibay.org", "1337x.to"]
)
def get_config(query: str, debug_mode: bool = False, auto_scan: bool = True, **kwargs) -> DownloadConfig:
    return DownloadConfig(pipeline="torrent", source=query, debug_mode=debug_mode, auto_scan=auto_scan, **kwargs)
