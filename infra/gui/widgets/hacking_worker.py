"""
Hacking Worker - QThread for Hacking Engine Subprocess
======================================================
Manages the hacking engine subprocess for offensive security tasks.
"""
from __future__ import annotations

import subprocess
import json
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal


class HackingWorker(QThread):
    """
    Worker thread for running hacking engine subprocess.
    """
    
    loaded = pyqtSignal()
    token = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, prompt: str):
        super().__init__()
        self.prompt = prompt
        self._cancelled = False
        self._process: Optional[subprocess.Popen] = None
        self._full_response = ""
    
    def run(self):
        """Run the hacking engine subprocess."""
        # Get paths
        root = Path(__file__).resolve().parents[3]
        python_exe = root / "venvs" / "env" / "coreagentvenv" / "Scripts" / "python.exe"
        engine_script = root / "infra" / "standalone" / "hacking_engine.py"
        
        if not python_exe.exists():
            self.error.emit(f"Python not found: {python_exe}")
            return
        
        if not engine_script.exists():
            self.error.emit(f"Engine script not found: {engine_script}")
            return
        
        # Debug info
        print(f"[HackingWorker] DEBUG: CMD = {[str(python_exe), str(engine_script), '--prompt', self.prompt]}")
        
        cmd = [
            str(python_exe),
            str(engine_script),
            "--prompt", self.prompt
        ]
        
        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1
            )
            
            print("[HackingWorker] DEBUG: Starting run()")
            
            # Read output line by line
            for line in iter(self._process.stdout.readline, ''):
                if self._cancelled:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                if line == "LOADED":
                    self.loaded.emit()
                elif line.startswith("TOKEN:"):
                    try:
                        token_json = line[6:]
                        # Decode JSON-encoded token from engine
                        token = json.loads(token_json)
                        self._full_response += token
                        self.token.emit(token)
                    except Exception:
                        # Fallback: use raw if JSON decode fails
                        token = line[6:]
                        self._full_response += token
                        self.token.emit(token)
                elif line == "DONE":
                    self.finished.emit(self._full_response)
                elif line.startswith("ERROR:"):
                    self.error.emit(line[6:])
            
            self._process.wait()
            print(f"[HackingWorker] Process exited with code: {self._process.returncode}")
            
        except Exception as e:
            self.error.emit(str(e))
    
    def cancel(self):
        """Cancel the generation."""
        self._cancelled = True
        if self._process:
            try:
                self._process.kill()  # Force kill
            except:
                pass
            # race condition fix: do NOT set self._process = None


class HackingManager:
    """
    Manages hacking workers.
    """
    
    def __init__(self):
        self._current_worker: Optional[HackingWorker] = None
        self.is_active = False
    
    def start_hacking(self, prompt: str) -> HackingWorker:
        """Start a new hacking task."""
        # Terminate any existing worker
        self.terminate()
        
        self._current_worker = HackingWorker(prompt)
        self.is_active = True
        
        return self._current_worker
    
    def terminate(self):
        """Terminate current worker."""
        if self._current_worker:
            self._current_worker.cancel()
            self._current_worker.wait(1000)
        self._current_worker = None
        self.is_active = False
