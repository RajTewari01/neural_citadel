"""
Writing Worker - Persistent Process Manager for Writing Engine
===============================================================

Manages a PERSISTENT writing engine subprocess (Mistral 7B).
Model loads once at first use, stays in memory for subsequent requests.
Only unloads when terminate() is called (mode switch or app exit).
"""

import subprocess
import json
from pathlib import Path
from typing import List, Dict, Optional

from PyQt6.QtCore import QThread, pyqtSignal, QObject


class EngineStartupWorker(QThread):
    """Background worker to start the engine without blocking UI."""
    
    ready = pyqtSignal(object)  # Emits the subprocess.Popen object
    error = pyqtSignal(str)
    status = pyqtSignal(str)  # Status updates for UI
    
    def __init__(self):
        super().__init__()
        
    def run(self):
        root = Path(__file__).resolve().parents[3]
        python_exe = root / "venvs" / "env" / "coreagentvenv" / "Scripts" / "python.exe"
        engine_script = root / "infra" / "standalone" / "writing_engine.py"
        
        if not python_exe.exists():
            self.error.emit(f"Python not found: {python_exe}")
            return
        
        if not engine_script.exists():
            self.error.emit(f"Engine not found: {engine_script}")
            return
        
        self.status.emit("Starting engine...")
        
        try:
            process = subprocess.Popen(
                [str(python_exe), str(engine_script)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1
            )
            
            self.status.emit("Loading model...")
            
            # Wait for LOADED and READY signals
            while True:
                line = process.stdout.readline()
                if not line:
                    self.error.emit("Engine died during startup")
                    return
                
                line = line.strip()
                if line == "LOADED":
                    self.status.emit("Model loaded, initializing...")
                elif line == "READY":
                    self.ready.emit(process)
                    return
                elif line.startswith("ERROR:"):
                    self.error.emit(line[6:])
                    return
                    
        except Exception as e:
            self.error.emit(str(e))


class WritingWorker(QThread):
    """
    Worker thread for a SINGLE generation request.
    Reads from the persistent process's stdout.
    """
    
    token = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, process: subprocess.Popen, prompt: str, persona: str, style: str, history: List[Dict]):
        super().__init__()
        self._process = process
        self.prompt = prompt
        self.persona = persona
        self.style = style
        self.history = history
        self._cancelled = False
        self._full_response = ""
    
    def run(self):
        """Send generate command and read streaming response."""
        if self._process is None or self._process.poll() is not None:
            self.error.emit("Writing engine not running")
            return
        
        # Send generate command via stdin
        cmd = json.dumps({
            "action": "generate",
            "prompt": self.prompt,
            "persona": self.persona,
            "style": self.style,
            "history": self.history
        }) + "\n"
        
        try:
            self._process.stdin.write(cmd)
            self._process.stdin.flush()
        except Exception as e:
            self.error.emit(f"Failed to send command: {e}")
            return
        
        # Read response tokens until DONE
        try:
            while True:
                if self._cancelled:
                    break
                
                line = self._process.stdout.readline()
                if not line:
                    break  # Process died
                
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith("TOKEN:"):
                    try:
                        raw_token = line[6:]
                        tok = json.loads(raw_token)
                        self._full_response += tok
                        self.token.emit(tok)
                    except json.JSONDecodeError:
                        pass
                elif line == "DONE":
                    self.finished.emit(self._full_response)
                    break
                elif line.startswith("ERROR:"):
                    self.error.emit(line[6:])
                    break
                    
        except Exception as e:
            self.error.emit(str(e))
    
    def cancel(self):
        self._cancelled = True


class WritingManager(QObject):
    """
    Manages a PERSISTENT writing engine process.
    Model loads once and stays in memory for fast subsequent requests.
    Engine startup is ASYNC to not block the UI.
    """
    
    # Signals for engine state
    engine_ready = pyqtSignal()
    engine_error = pyqtSignal(str)
    engine_status = pyqtSignal(str)  # Status updates for panel
    
    def __init__(self):
        super().__init__()
        self._process: Optional[subprocess.Popen] = None
        self._current_worker: Optional[WritingWorker] = None
        self._startup_worker: Optional[EngineStartupWorker] = None
        self._pending_prompt: Optional[str] = None  # Prompt waiting for engine
        self._history: List[Dict] = []
        self._current_persona = "therapist"
        self._current_style = "supportive"
        self.is_active = False
        self.is_ready = False
        self.is_starting = False
        self.MAX_HISTORY = 5
    
    def _start_engine_async(self):
        """Start the engine in background thread."""
        if self.is_starting:
            return  # Already starting
        
        self.is_starting = True
        self._startup_worker = EngineStartupWorker()
        self._startup_worker.ready.connect(self._on_engine_ready)
        self._startup_worker.error.connect(self._on_engine_error)
        self._startup_worker.status.connect(self.engine_status.emit)
        self._startup_worker.start()
    
    def _on_engine_ready(self, process):
        """Called when engine is ready."""
        self._process = process
        self.is_ready = True
        self.is_starting = False
        print("[WritingManager] Engine ready")
        
        # If there's a pending prompt, create the worker FIRST
        if self._pending_prompt:
            prompt = self._pending_prompt
            self._pending_prompt = None
            self._execute_writing(prompt)
        
        # Emit ready signal AFTER worker is created
        self.engine_ready.emit()
    
    def _on_engine_error(self, error: str):
        """Called on engine startup failure."""
        self.is_starting = False
        self._pending_prompt = None
        self.engine_error.emit(error)
        print(f"[WritingManager] Engine error: {error}")
    
    def set_persona(self, persona: str, style: str):
        """Set persona and style. History preserved within same persona."""
        if self._current_persona != persona:
            self._history = []  # Clear history on persona change
        self._current_persona = persona
        self._current_style = style
    
    def start_writing(self, prompt: str) -> Optional[WritingWorker]:
        """Start a generation request. Engine starts async if not ready."""
        self.is_active = True
        
        # Add user message to history immediately
        self._history.append({"role": "user", "content": prompt})
        
        # If engine not ready, start it and queue the prompt
        if not self.is_ready and self._process is None:
            self._pending_prompt = prompt
            self._start_engine_async()
            return None  # Signal that we're starting async
        
        # Engine ready, execute immediately
        return self._execute_writing(prompt)
    
    def _execute_writing(self, prompt: str) -> WritingWorker:
        """Actually start the writing worker (engine must be ready)."""
        # Cancel any ongoing generation
        if self._current_worker and self._current_worker.isRunning():
            self._current_worker.cancel()
            self._current_worker.wait(1000)
        
        # Create worker for this request
        self._current_worker = WritingWorker(
            process=self._process,
            prompt=prompt,
            persona=self._current_persona,
            style=self._current_style,
            history=self._history[:-1]  # History excluding current prompt
        )
        
        return self._current_worker
    
    def get_current_worker(self) -> Optional[WritingWorker]:
        """Get the current worker if any."""
        return self._current_worker
    
    def add_response(self, response: str):
        """Add assistant response to history."""
        self._history.append({"role": "assistant", "content": response})
        
        # Trim history
        while len(self._history) > self.MAX_HISTORY * 2:
            self._history.pop(0)
            self._history.pop(0)
    
    def has_history(self) -> bool:
        return len(self._history) > 0
    
    def clear_history(self):
        self._history = []
    
    def get_history(self) -> List[Dict]:
        return self._history.copy()
    
    def get_history_count(self) -> int:
        return len(self._history) // 2  # Pairs of user/assistant
    
    def terminate(self):
        """Terminate the persistent engine process (for mode switch/exit)."""
        print("[WritingManager] Terminating engine...")
        
        # Cancel startup if in progress
        if self._startup_worker and self._startup_worker.isRunning():
            self._startup_worker.terminate()
            self._startup_worker.wait(1000)
        self._startup_worker = None
        self._pending_prompt = None
        
        # Cancel current worker
        if self._current_worker and self._current_worker.isRunning():
            self._current_worker.cancel()
            self._current_worker.wait(1000)
        self._current_worker = None
        
        # Send quit command and terminate process
        # Send quit command and terminate process
        if self._process and self._process.poll() is None:
            # Try graceful quit with short timeout
            try:
                quit_cmd = json.dumps({"action": "quit"}) + "\n"
                self._process.stdin.write(quit_cmd)
                self._process.stdin.flush()
                self._process.wait(timeout=0.2)
            except:
                pass
            
            # Force kill if still running
            if self._process.poll() is None:
                try:
                    self._process.kill()
                    self._process.wait(1000)
                    print("[WritingManager] Engine force killed")
                except:
                    pass
        
        self._process = None
        self.is_active = False
        self.is_ready = False
        self.is_starting = False
        self._history = []
        print("[WritingManager] Engine terminated")
