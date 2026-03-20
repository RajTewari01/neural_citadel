"""
Movie Downloader Worker
========================

Background worker for running movie_downloader commands in isolated venv.
Uses subprocess to call movie_venv Python.
"""

from PyQt6.QtCore import QThread, pyqtSignal
import subprocess
import sys
from pathlib import Path

# Import paths from centralized config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from configs.paths import MOVIE_VENV_PYTHON, ROOT_DIR as PROJECT_ROOT

# Debug: Print path at import time
print(f"[MovieWorker] MOVIE_VENV_PYTHON: {MOVIE_VENV_PYTHON}")
print(f"[MovieWorker] Exists: {MOVIE_VENV_PYTHON.exists()}")


class MovieWorker(QThread):
    """
    Background worker for movie downloader operations.
    
    Supports:
    - youtube: Download from YouTube/URL
    - torrent-search: Non-interactive search (JSON output)
    - torrent-download: Download by magnet
    - scan: Scan downloads for malware
    - subtitle: Generate subtitles
    """
    
    progress = pyqtSignal(str)        # Progress messages
    finished = pyqtSignal(str)        # Completion message
    error = pyqtSignal(str)           # Error message
    search_results = pyqtSignal(list) # Torrent search results
    scan_complete = pyqtSignal(dict)  # Scan results with risk score
    
    def __init__(self, command: str, **kwargs):
        """
        Initialize movie worker.
        
        Args:
            command: One of 'youtube', 'torrent-search', 'torrent-download', 'scan', 'subtitle'
            **kwargs: Command-specific arguments
        """
        super().__init__()
        self.command = command
        self.kwargs = kwargs
        self._running = True
        self._process = None  # Store process reference for cancellation
    
    def stop(self):
        """Request to stop the worker and kill the subprocess tree."""
        self._running = False
        if self._process:
            try:
                import os
                import signal
                pid = self._process.pid
                
                # On Windows, use taskkill to kill the entire process tree
                if os.name == 'nt':
                    os.system(f'taskkill /F /T /PID {pid} >nul 2>&1')
                else:
                    # On Unix, kill the process group
                    os.killpg(os.getpgid(pid), signal.SIGTERM)
                
                self._process.terminate()
                self._process.kill()
            except:
                pass
    
    def run(self):
        """Execute the movie command."""
        import json
        
        try:
            cmd = self._build_command()
            if not cmd:
                self.error.emit("Invalid command")
                return
            
            self.progress.emit(f"🎬 Starting {self.command}...")
            
            # Debug: print command and emit to progress
            print(f"[MovieWorker] Command: {cmd}")
            print(f"[MovieWorker] CWD: {PROJECT_ROOT}")
            self.progress.emit(f"🐍 Python: {cmd[0]}")
            
            # Create environment with movie_venv paths to ensure isolation
            import os
            env = os.environ.copy()
            
            # Fix encoding issues - prevent cp1252 errors
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUTF8"] = "1"
            
            movie_venv_scripts = str(MOVIE_VENV_PYTHON.parent)
            movie_venv_root = str(MOVIE_VENV_PYTHON.parent.parent)
            env["PATH"] = f"{movie_venv_scripts};{movie_venv_root};{env.get('PATH', '')}"
            env["VIRTUAL_ENV"] = movie_venv_root
            # Remove any PYTHONHOME that might interfere
            env.pop("PYTHONHOME", None)
            
            # Run subprocess - merge stderr into stdout to capture all output
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Merge stderr into stdout for unified progress
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=str(PROJECT_ROOT),
                env=env
            )
            
            # Collect all output for JSON parsing
            all_output = []
            for line in iter(self._process.stdout.readline, ''):
                if not self._running:
                    self._process.terminate()
                    break
                
                line = line.strip()
                if line:
                    all_output.append(line)
                    
                    # Check for SCAN_RESULT JSON in download output
                    if line.startswith("SCAN_RESULT:"):
                        try:
                            scan_json = line.replace("SCAN_RESULT:", "")
                            scan_data = json.loads(scan_json)
                            self.scan_complete.emit(scan_data)
                        except:
                            pass
                    else:
                        self.progress.emit(line)
            
            self._process.wait()
            
            if self._process.returncode == 0:
                # For torrent-search, parse JSON and emit search_results
                if self.command == "torrent-search":
                    # Find JSON in output (last line usually)
                    for line in reversed(all_output):
                        if line.startswith("{"):
                            try:
                                data = json.loads(line)
                                results = data.get("results", [])
                                self.search_results.emit(results)
                                self.finished.emit(f"✅ Found {len(results)} results")
                                return
                            except:
                                pass
                    self.error.emit("Failed to parse search results")
                else:
                    self.finished.emit(f"✅ {self.command.capitalize()} completed!")
            else:
                # Get last few lines for error context (stderr is merged into stdout)
                error_context = '\n'.join(all_output[-5:]) if all_output else 'Unknown error'
                self.error.emit(f"Code {self._process.returncode}: {error_context[:200]}")
                
        except Exception as e:
            self.error.emit(str(e))
    
    def _build_command(self) -> list:
        """Build the subprocess command list."""
        # Use -u for unbuffered output to enable real-time progress streaming
        base = [str(MOVIE_VENV_PYTHON), "-u", "-m", "apps.movie_downloader.runner"]
        
        if self.command == "youtube":
            url = self.kwargs.get("url", "")
            quality = self.kwargs.get("quality", "best")
            playlist = self.kwargs.get("playlist", False)
            if not url:
                return None
            cmd = base + ["youtube", url, "--quality", quality, "--debug"]
            if playlist:
                cmd.append("--playlist")
            return cmd
        
        elif self.command == "torrent-search":
            # Non-interactive search - returns JSON
            query = self.kwargs.get("query", "")
            limit = self.kwargs.get("limit", 10)
            if not query:
                return None
            return base + ["torrent-search", query, "--limit", str(limit)]
        
        elif self.command == "torrent-download":
            # Download by magnet/hash
            magnet = self.kwargs.get("magnet", "")
            if not magnet:
                return None
            return base + ["torrent-download", magnet, "--debug"]
        
        elif self.command == "torrent":
            # Legacy interactive (for backwards compatibility)
            query = self.kwargs.get("query", "")
            if not query:
                return None
            return base + ["torrent", query, "--debug"]
        
        elif self.command == "scan":
            return base + ["scan", "--debug"]
        
        elif self.command == "subtitle":
            file_path = self.kwargs.get("file", "")
            lang = self.kwargs.get("lang", "en")
            task = self.kwargs.get("task", "transcribe")
            model = self.kwargs.get("model", "small")
            if not file_path:
                return None
            return base + ["subtitle", file_path, "--lang", lang, "--task", task, "--model", model]
        
        return None


# Movie operation types for the GUI
MOVIE_OPERATIONS = [
    ("📺 YouTube Download", "youtube", "Download from YouTube or social media URL"),
    ("🏴‍☠️ Torrent Search", "torrent", "Search and download movies via torrent"),
    ("🛡️ Scan Downloads", "scan", "Scan downloads folder for malware"),
    ("📝 Generate Subtitles", "subtitle", "Generate subtitles using Whisper AI"),
]

# Quality options for YouTube
YOUTUBE_QUALITIES = ["best", "4k", "1080p", "720p", "480p"]

# Subtitle languages
SUBTITLE_LANGS = ["en", "bn", "hi", "es", "fr", "de", "ja", "ko", "zh"]

# Whisper model sizes
WHISPER_MODELS = ["tiny", "base", "small", "medium"]
