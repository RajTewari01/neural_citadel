"""
Reasoning Worker - QThread for DeepSeek R1 Subprocess
======================================================

Manages subprocess lifecycle for the reasoning engine.
Handles 3-chat LIFO history and signal emission for UI updates.
"""

import json
import subprocess
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal, QProcess

# Import paths - these are safe as they're just Path objects
try:
    from configs.paths import COREAGENT_VENV_PYTHON, REASONING_ENGINE
except ImportError:
    # Fallback paths
    ROOT = Path(__file__).resolve().parents[3]
    COREAGENT_VENV_PYTHON = ROOT / "venvs" / "env" / "coreagentvenv" / "Scripts" / "python.exe"
    REASONING_ENGINE = ROOT / "infra" / "standalone" / "reasoning_engine.py"


class ReasoningWorker(QThread):
    """
    Worker thread for running reasoning engine subprocess.
    
    Signals:
        loaded: Model loaded successfully
        think_start: Entering <think> block
        token: Individual token received
        think_end: Exiting </think> block
        finished: Generation complete with full response
        error: Error occurred
    """
    
    loaded = pyqtSignal()
    think_start = pyqtSignal()
    token = pyqtSignal(str)
    think_end = pyqtSignal()
    finished = pyqtSignal(str)  # Full response text
    error = pyqtSignal(str)
    
    def __init__(self, prompt: str, history: list = None, parent=None):
        super().__init__(parent)
        self.prompt = prompt
        self.history = history or []
        self.process = None
        self._full_response = ""
        self._cancelled = False
    
    def run(self):
        """Execute reasoning engine subprocess."""
        
        # Validate paths
        if not COREAGENT_VENV_PYTHON.exists():
            self.error.emit(f"Python not found: {COREAGENT_VENV_PYTHON}")
            return
        
        if not REASONING_ENGINE.exists():
            self.error.emit(f"Engine not found: {REASONING_ENGINE}")
            return
        
        # Build command
        cmd = [
            str(COREAGENT_VENV_PYTHON),
            "-u",  # Unbuffered output
            str(REASONING_ENGINE),
            "--prompt", self.prompt,
            "--history", json.dumps(self.history)
        ]
        
        try:
            # Start subprocess
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
                encoding='utf-8',
                errors='replace'
            )
            
            # Read output line by line
            for line in iter(self.process.stdout.readline, ''):
                if self._cancelled:
                    self.process.terminate()
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                self._process_line(line)
            
            # Wait for process to complete
            self.process.wait()
            
            # Check for errors
            if self.process.returncode != 0 and not self._cancelled:
                stderr = self.process.stderr.read()
                if stderr:
                    self.error.emit(f"Process error: {stderr[:200]}")
            
        except Exception as e:
            self.error.emit(f"Failed to run: {e}")
        
        finally:
            if self.process:
                try:
                    self.process.kill()
                except:
                    pass
                self.process = None
    
    def _process_line(self, line: str):
        """Process a single line from subprocess output."""
        
        if line == "LOADED":
            self.loaded.emit()
        
        elif line == "THINK_START":
            self.think_start.emit()
        
        elif line == "THINK_END":
            self.think_end.emit()
        
        elif line.startswith("TOKEN:"):
            token_text = line[6:]  # Remove "TOKEN:" prefix
            self._full_response += token_text
            self.token.emit(token_text)
        
        elif line == "DONE":
            self.finished.emit(self._full_response)
        
        elif line.startswith("ERROR:"):
            self.error.emit(line[6:])
    
    def cancel(self):
        """Cancel the current generation."""
        self._cancelled = True
        if self.process:
            try:
                self.process.kill()  # Force kill to release VRAM immediately
            except:
                pass
            # Do NOT set self.process = None here to avoid race condition in run()


class ReasoningManager:
    """
    Manages reasoning worker lifecycle and history.
    
    Features:
    - 3-chat LIFO history
    - Lazy subprocess management
    - Clean termination on mode switch
    """
    
    MAX_HISTORY_PAIRS = 3  # Keep last 3 Q&A pairs
    
    def __init__(self):
        self.history = []
        self.current_worker = None
        self._is_active = False
    
    def start_reasoning(self, prompt: str) -> ReasoningWorker:
        """Start a new reasoning task."""
        
        # Cancel any existing worker
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.cancel()
            self.current_worker.wait(1000)
        
        # Create new worker with history
        self.current_worker = ReasoningWorker(prompt, self.history.copy())
        self._is_active = True
        
        return self.current_worker
    
    def add_to_history(self, user_msg: str, assistant_msg: str):
        """Add Q&A pair to history (LIFO, max 3 pairs)."""
        
        self.history.append({"role": "user", "content": user_msg})
        self.history.append({"role": "assistant", "content": assistant_msg})
        
        # Keep only last 3 pairs (6 messages)
        max_msgs = self.MAX_HISTORY_PAIRS * 2
        if len(self.history) > max_msgs:
            self.history = self.history[-max_msgs:]
    
    def clear_history(self):
        """Clear conversation history."""
        self.history = []
    
    def has_history(self) -> bool:
        """Check if there's any history."""
        return len(self.history) > 0
    
    def terminate(self):
        """Terminate subprocess and clear state."""
        
        if self.current_worker:
            self.current_worker.cancel()
            self.current_worker.wait(1000)  # Wait for thread
            self.current_worker = None
        
        self._is_active = False
    
    @property
    def is_active(self) -> bool:
        return self._is_active
