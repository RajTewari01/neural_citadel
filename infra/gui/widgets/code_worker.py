"""
Code Worker - QThread for Code Engine Subprocess
=================================================

Manages the code engine subprocess and emits signals for PyQt UI.
"""

import subprocess
import json
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal


class CodeWorker(QThread):
    """
    Worker thread for running code engine subprocess.
    
    Signals:
        loaded: Model loaded successfully
        token: New token received (str)
        finished: Generation complete with full response (str)
        error: Error occurred (str)
    """
    
    loaded = pyqtSignal()
    token = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, prompt: str, model: str = "deepseek"):
        super().__init__()
        self.prompt = prompt
        self.model = model  # "deepseek" or "qwen"
        self._cancelled = False
        self._process = None
        self._full_response = ""
    
    def run(self):
        """Run the code engine subprocess."""
        # Get paths
        root = Path(__file__).resolve().parents[3]
        python_exe = root / "venvs" / "env" / "coreagentvenv" / "Scripts" / "python.exe"
        engine_script = root / "infra" / "standalone" / "code_engine.py"
        
        if not python_exe.exists():
            self.error.emit(f"Python not found: {python_exe}")
            return
        
        if not engine_script.exists():
            self.error.emit(f"Engine script not found: {engine_script}")
            return
        
        cmd = [
            str(python_exe),
            str(engine_script),
            "--prompt", self.prompt,
            "--model", self.model
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
                        # Decode JSON token to safely handle newlines/special chars
                        raw_token = line[6:]
                        tok = json.loads(raw_token)
                        self._full_response += tok
                        self.token.emit(tok)
                    except json.JSONDecodeError:
                        # Fallback for legacy/error cases
                        pass
                elif line == "DONE":
                    self.finished.emit(self._full_response)
                elif line.startswith("ERROR:"):
                    self.error.emit(line[6:])
            
            self._process.wait()
            
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
            # race condition fix


class CodeManager:
    """
    Manages code workers and model state.
    Only one model loads at a time.
    """
    
    def __init__(self):
        self._current_worker = None
        self._current_model = None
        self.is_active = False
    
    def start_coding(self, prompt: str, model: str = "deepseek") -> CodeWorker:
        """Start a new coding task."""
        # Terminate any existing worker
        self.terminate()
        
        self._current_model = model
        self._current_worker = CodeWorker(prompt, model)
        self.is_active = True
        
        return self._current_worker
    
    def terminate(self):
        """Terminate current worker."""
        if self._current_worker:
            self._current_worker.cancel()
            self._current_worker.wait(1000)
        self._current_worker = None
        self._current_model = None
        self.is_active = False
    
    @property
    def current_model(self):
        return self._current_model
