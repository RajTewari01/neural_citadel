"""
Movie Downloader - Virus Scanner
=================================

VirusTotal API integration and heuristic malware scanning.
"""

import os
import sys
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any

import requests
from dotenv import load_dotenv, set_key

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from configs.paths import SOCIALS_ENV_FILE, DEBUG_LOG_DIR

YELLOW = '\033[1;33m'
RESET = '\033[0m'
GREEN = '\033[1;32m'
RED = '\033[1;31m'
CYAN = '\033[1;36m'
BLUE = '\033[1;34m'

def get_term_width():
    try:
        return os.get_terminal_size().columns
    except:
        return 80

DEBUG_LOG_DIR.mkdir(parents=True, exist_ok=True)

EXTENSION_CATEGORIES = {
    'safe': ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.srt', '.sub', '.nfo', '.txt', '.jpg', '.png', '.mp3', '.flac'],
    'critical': ['.exe', '.bat', '.cmd', '.scr', '.vbs', '.vbe', '.js', '.jar', '.msi', '.dll', '.com', '.pif', '.ps1', '.reg', '.lnk', '.hta'],
    'warning': ['.zip', '.rar', '.7z', '.tar', '.gz', '.iso', '.img']
}

FILE_SIGNATURES = {
    b'MZ': 'Windows Executable (PE)',
    b'\x7fELF': 'Linux Executable (ELF)',
    b'PK\x03\x04': 'ZIP Archive',
    b'Rar!\x1a\x07': 'RAR Archive',
    b'\x00\x00\x00\x1c\x66\x74\x79\x70': 'MP4 Video',
    b'\x1a\x45\xdf\xa3': 'MKV/WebM Video',
}


class VirusScanner:
    """Comprehensive malware scanner."""
    
    def __init__(self, api_key: str = None):
        load_dotenv(SOCIALS_ENV_FILE)
        self.api_key = api_key or os.getenv("VIRUSTOTAL_API_KEY")
        self.logger = logging.getLogger(__name__)
        self.vt_api_url = "https://www.virustotal.com/api/v3"
    
    @staticmethod
    def set_api_key() -> str:
        load_dotenv(SOCIALS_ENV_FILE)
        new_key = input("Enter your VirusTotal API key:\n>>> ")
        set_key(SOCIALS_ENV_FILE, "VIRUSTOTAL_API_KEY", new_key)
        print(f"{GREEN}API key saved{RESET}")
        return new_key
    
    def calculate_hash(self, filepath: str, algorithm: str = "sha256") -> Optional[str]:
        try:
            hash_func = hashlib.new(algorithm)
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except Exception as e:
            self.logger.error(f"Hash calculation failed: {e}")
            return None
    
    def analyze_file_signature(self, filepath: str) -> Dict[str, Any]:
        try:
            with open(filepath, 'rb') as f:
                header = f.read(64)
            detected_type = None
            for sig, ftype in FILE_SIGNATURES.items():
                if header.startswith(sig):
                    detected_type = ftype
                    break
            file_ext = Path(filepath).suffix.lower()
            is_disguised = False
            if detected_type and 'Executable' in detected_type and file_ext in EXTENSION_CATEGORIES['safe']:
                is_disguised = True
            return {'detected_type': detected_type or 'Unknown', 'is_disguised': is_disguised, 'extension': file_ext}
        except Exception as e:
            return {'detected_type': 'Error', 'is_disguised': False, 'error': str(e)}
    
    def heuristic_scan(self, filepath: str, debug_mode: bool = False) -> Dict[str, Any]:
        warnings = []
        risk_score = 0
        file_path = Path(filepath)
        
        try:
            if debug_mode:
                print(f"\n{BLUE}🔬 Running heuristic analysis...{RESET}")
            
            file_ext = file_path.suffix.lower()
            file_size_mb = file_path.stat().st_size / (1024**2)
            
            if file_ext in EXTENSION_CATEGORIES['critical']:
                warnings.append(f"🚨 CRITICAL: Executable file type ({file_ext})")
                risk_score += 100
            
            suffixes = file_path.suffixes
            if len(suffixes) >= 2 and suffixes[-1].lower() in EXTENSION_CATEGORIES['critical']:
                warnings.append(f"🚨 CRITICAL: Double extension ({'.'.join(suffixes)})")
                risk_score += 100
            
            sig_result = self.analyze_file_signature(filepath)
            if sig_result['is_disguised']:
                warnings.append(f"🚨 CRITICAL: {sig_result['detected_type']} disguised as {file_ext}")
                risk_score += 100
            
            video_exts = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.webm']
            if file_ext in video_exts and file_size_mb < 10:
                warnings.append(f"⚠️ Video suspiciously small ({file_size_mb:.2f} MB)")
                risk_score += 50
            
            if risk_score >= 100:
                severity = 'critical'
            elif risk_score >= 50:
                severity = 'high'
            elif risk_score >= 20:
                severity = 'warning'
            else:
                severity = 'safe'
            
            result = {'suspicious': len(warnings) > 0, 'severity': severity, 'risk_score': min(risk_score, 100),
                     'reasons': warnings, 'file_size_mb': file_size_mb, 'signature': sig_result}
            
            if debug_mode:
                if severity == 'safe':
                    print(f"{GREEN}   ✓ No threats detected{RESET}")
                else:
                    for w in warnings:
                        color = RED if '🚨' in w else YELLOW
                        print(f"{color}   {w}{RESET}")
            
            return result
        except Exception as e:
            return {'suspicious': False, 'severity': 'safe', 'risk_score': 0, 'reasons': [], 'error': str(e)}
    
    def inspect_archive(self, filepath: str, debug_mode: bool = False) -> Dict[str, Any]:
        """Inspect archive contents for dangerous files."""
        result = {'scanned': False, 'file_count': 0, 'dangerous_files': [], 'warnings': []}
        file_ext = Path(filepath).suffix.lower()
        
        if file_ext not in ['.zip', '.rar', '.7z']:
            return result
        
        if debug_mode:
            print(f"\n{BLUE}📦 Inspecting archive contents...{RESET}")
        
        try:
            if file_ext == '.zip':
                import zipfile
                with zipfile.ZipFile(filepath, 'r') as zf:
                    result['file_count'] = len(zf.namelist())
                    for name in zf.namelist():
                        ext = Path(name).suffix.lower()
                        if ext in EXTENSION_CATEGORIES['critical']:
                            result['dangerous_files'].append(name)
                            result['warnings'].append(f"🚨 Executable inside archive: {name}")
            result['scanned'] = True
            if debug_mode:
                if result['dangerous_files']:
                    print(f"{RED}   Found {len(result['dangerous_files'])} dangerous files{RESET}")
                else:
                    print(f"{GREEN}   Archive contents appear safe ({result['file_count']} files){RESET}")
        except Exception as e:
            result['warnings'].append(f"⚠️ Could not inspect archive: {e}")
        return result
    
    def scan_with_virustotal(self, filepath: str, debug_mode: bool = False) -> Dict[str, Any]:
        if not self.api_key:
            if debug_mode:
                print(f"{YELLOW}⚠️ VirusTotal API key not configured{RESET}")
            return {'safe': None, 'error': 'No API key'}
        
        try:
            if debug_mode:
                print(f"\n{BLUE}🔍 Calculating file hash...{RESET}")
            file_hash = self.calculate_hash(filepath, "sha256")
            if not file_hash:
                return {'safe': None, 'error': 'Hash failed'}
            
            if debug_mode:
                print(f"{CYAN}   SHA256: {file_hash}{RESET}")
                print(f"{BLUE}🌐 Querying VirusTotal...{RESET}")
            
            headers = {"x-apikey": self.api_key}
            response = requests.get(f"{self.vt_api_url}/files/{file_hash}", headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                stats = data['data']['attributes']['last_analysis_stats']
                malicious = stats.get('malicious', 0)
                suspicious = stats.get('suspicious', 0)
                total = sum(stats.values())
                
                result = {'safe': malicious == 0 and suspicious == 0, 'detections': malicious + suspicious,
                         'total_engines': total, 'report_url': f"https://www.virustotal.com/gui/file/{file_hash}"}
                
                if debug_mode:
                    if result['safe']:
                        print(f"\n{GREEN}✅ FILE IS CLEAN ({total} engines){RESET}")
                    else:
                        print(f"\n{RED}⚠️ THREAT DETECTED: {result['detections']}/{total} engines{RESET}")
                return result
            elif response.status_code == 404:
                if debug_mode:
                    print(f"{YELLOW}   File not in database{RESET}")
                return {'safe': None, 'error': 'File not in VT database'}
            else:
                return {'safe': None, 'error': f'API error: {response.status_code}'}
        except Exception as e:
            return {'safe': None, 'error': str(e)}
    
    def full_scan(self, filepath: str, debug_mode: bool = False, use_virustotal: bool = True) -> Dict[str, Any]:
        if debug_mode:
            w = min(get_term_width() - 2, 60)
            print(f"\n{BLUE}{'═'*w}{RESET}")
            print(f"{BLUE}🛡️ COMPREHENSIVE FILE SCAN{RESET}")
            print(f"{BLUE}   File: {Path(filepath).name}{RESET}")
            print(f"{BLUE}{'═'*w}{RESET}")
        
        heuristic_result = self.heuristic_scan(filepath, debug_mode)
        
        archive_result = self.inspect_archive(filepath, debug_mode)
        if archive_result['dangerous_files']:
            heuristic_result['risk_score'] += 100
            heuristic_result['severity'] = 'critical'
            heuristic_result['reasons'].extend(archive_result['warnings'])
        
        vt_result = {}
        if use_virustotal and self.api_key:
            vt_result = self.scan_with_virustotal(filepath, debug_mode)
        
        heuristic_unsafe = heuristic_result['severity'] in ['critical', 'high']
        vt_unsafe = vt_result.get('safe') is False
        
        if heuristic_unsafe or vt_unsafe:
            overall_safe = False
            overall_severity = 'critical'
            recommendation = 'DELETE this file immediately!'
        elif heuristic_result['severity'] == 'warning':
            overall_safe = True
            overall_severity = 'warning'
            recommendation = 'Proceed with caution.'
        else:
            overall_safe = True
            overall_severity = 'safe'
            recommendation = 'File appears safe.'
        
        return {'overall_safe': overall_safe, 'overall_severity': overall_severity, 'heuristic': heuristic_result,
                'archive': archive_result, 'virustotal': vt_result, 'recommendation': recommendation}


def quick_scan(filepath: str, debug_mode: bool = True) -> bool:
    scanner = VirusScanner()
    result = scanner.full_scan(filepath, debug_mode=debug_mode)
    return result['overall_safe']
