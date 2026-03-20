"""
QR Studio Worker
=================

Background worker for running QR Studio commands in isolated GLOBAL Python.
Uses subprocess to call GLOBAL_PYTHON (NOT pyqt_venv!) to avoid dependency conflicts.

CRITICAL: QR Studio runs in global Python, NOT in pyqt_venv!
"""

from PyQt6.QtCore import QThread, pyqtSignal
import subprocess
import json
import sys
import re
from pathlib import Path

# =============================================================================
# PATH SETUP - Import from configs/paths.py
# =============================================================================

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from configs.paths import GLOBAL_PYTHON, QR_STUDIO_RUNNER, ROOT_DIR

# Debug: Print paths at import time
print(f"[QRWorker] GLOBAL_PYTHON: {GLOBAL_PYTHON}")
print(f"[QRWorker] Exists: {GLOBAL_PYTHON.exists()}")
print(f"[QRWorker] QR_STUDIO_RUNNER: {QR_STUDIO_RUNNER}")


class QRWorker(QThread):
    """
    Background worker for QR code generation.
    
    CRITICAL: Uses GLOBAL_PYTHON, NOT pyqt_venv Python!
    This ensures qr_studio dependencies are available.
    
    Supports:
    - SVG mode: Pure vector QR codes
    - Gradient mode: PNG with gradient colors (auto/manual)
    - Creative mode: AI artistic QR using Stable Diffusion + ControlNet
    - Logo embedding
    """
    
    progress = pyqtSignal(str)      # Status messages
    finished = pyqtSignal(str)      # Output path on success
    error = pyqtSignal(str)         # Error message
    
    def __init__(
        self,
        handler: str,
        data: dict,
        mode: str = "svg",
        auto_mode: bool = True,
        colors: list = None,
        mask: str = "radial",
        drawer: str = "rounded",
        logo_path: str = "",
        prompt: str = "",
    ):
        """
        Initialize QR worker.
        
        Args:
            handler: Handler type (url, wifi, vcard, etc.)
            data: Dictionary of data fields for the handler
            mode: "svg", "gradient", or "creative"
            auto_mode: If True, use random colors/mask/drawer
            colors: List of 3 colors [back, center, edge] for manual mode
            mask: Gradient mask (radial, horizontal, vertical, diagonal)
            drawer: Module drawer (rounded, square, circle, gapped)
            logo_path: Optional path to logo image
            prompt: AI prompt for creative mode
        """
        super().__init__()
        self.handler = handler
        self.data = data
        self.mode = mode
        self.auto_mode = auto_mode
        self.colors = colors or ["#ffffff", "#ff5500", "#0055ff"]
        self.mask = mask
        self.drawer = drawer
        self.logo_path = logo_path
        self.prompt = prompt
        self._process = None
        self._should_stop = False
    
    def stop(self):
        """Request to stop the worker and kill the subprocess."""
        self._should_stop = True
        if self._process:
            try:
                import psutil
                parent = psutil.Process(self._process.pid)
                for child in parent.children(recursive=True):
                    child.terminate()
                parent.terminate()
            except Exception:
                pass
    
    def run(self):
        """Execute the QR generation command."""
        if not GLOBAL_PYTHON.exists():
            self.error.emit(f"Global Python not found: {GLOBAL_PYTHON}")
            return
        
        if not QR_STUDIO_RUNNER.exists():
            self.error.emit(f"QR Studio runner not found: {QR_STUDIO_RUNNER}")
            return
        
        self.progress.emit(f"Generating {self.mode.upper()} QR ({self.handler})...")
        
        try:
            # Build command
            cmd = self._build_command()
            print(f"[QRWorker] Command: {' '.join(cmd)}")
            
            # Run subprocess with proper settings for long-running diffusion
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(ROOT_DIR),
                bufsize=1,
            )
            
            output_path = None
            
            # Stream output with error handling
            try:
                for line in iter(self._process.stdout.readline, ''):
                    if self._should_stop:
                        self._process.terminate()
                        self.error.emit("Generation canceled")
                        return
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    print(f"[QRWorker] {line}")
                    
                    # Look for output path
                    if "[OK] QR Code saved:" in line:
                        output_path = line.split("saved:")[-1].strip()
                    elif "[OK] Diffusion complete:" in line:
                        output_path = line.split("complete:")[-1].strip()
                    elif "[OUTPUT]" in line:
                        output_path = line.split("[OUTPUT]")[-1].strip()
                    elif "OUTPUT_PATH:" in line:
                        # Diffusion worker output format
                        output_path = line.split("OUTPUT_PATH:")[-1].strip()
                    elif line.endswith(".png") or line.endswith(".svg"):
                        # Try to extract path
                        path_match = re.search(r'([A-Za-z]:[\\\/].*?\.(png|svg))', line)
                        if path_match:
                            output_path = path_match.group(1)
                    
                    # Progress updates
                    if "[AUTO]" in line or "[GRADIENT]" in line or "[SVG]" in line or "[DIFFUSION]" in line or "[STEP" in line or "[WORKER]" in line:
                        try:
                            self.progress.emit(line.split("]", 1)[-1].strip()[:50])
                        except RuntimeError:
                            # Qt object might be deleted
                            pass
            except Exception as read_error:
                print(f"[QRWorker] Error reading output: {read_error}")
            
            # Wait for process to complete
            try:
                self._process.wait(timeout=900)  # 15 minute timeout for diffusion
            except subprocess.TimeoutExpired:
                print("[QRWorker] Process timed out after 15 minutes")
                self._process.kill()
                self.error.emit("Generation timed out (15 minutes)")
                return
            
            # If we captured an output path, consider it success even if runner crashed later
            # (e.g., print_ascii fails on Windows due to encoding but QR was already saved)
            if output_path:
                try:
                    self.finished.emit(output_path)
                except RuntimeError:
                    print(f"[QRWorker] Result: {output_path}")
            elif self._process.returncode == 0:
                try:
                    self.finished.emit("QR generated (path not captured)")
                except RuntimeError:
                    print("[QRWorker] Complete but path not captured")
            else:
                try:
                    self.error.emit(f"QR generation failed (code {self._process.returncode})")
                except RuntimeError:
                    print(f"[QRWorker] Failed with code {self._process.returncode}")
        
        except Exception as e:
            import traceback
            print(f"[QRWorker] Exception: {e}")
            traceback.print_exc()
            try:
                self.error.emit(f"Error: {str(e)}")
            except RuntimeError:
                # Qt object deleted, can't emit signal
                pass
    
    def _build_command(self) -> list:
        """Build the subprocess command list."""
        # Determine how to pass data based on number of fields
        # Single-field handlers: pass value directly (runner.py wraps it)
        # Multi-field handlers: pass as JSON
        if len(self.data) == 1:
            # Single field - pass value directly
            data_value = list(self.data.values())[0]
        else:
            # Multiple fields - pass as JSON
            data_value = json.dumps(self.data)
        
        cmd = [
            str(GLOBAL_PYTHON),
            str(QR_STUDIO_RUNNER),
            "--handler", self.handler,
            "--data", data_value,
        ]
        
        # Mode-specific arguments
        if self.mode == "svg":
            cmd.append("--svg")
        elif self.mode == "creative":
            # Creative/Diffusion mode - uses AI to generate artistic QR
            cmd.append("--diffusion")
            if self.prompt:
                cmd.extend(["--prompt", self.prompt])
        else:
            # Gradient mode
            if self.auto_mode:
                cmd.extend(["--gradient", "auto"])
            else:
                cmd.extend([
                    "--gradient", "manual",
                    "--colors", self.colors[0], self.colors[1], self.colors[2],
                    "--mask", self.mask,
                    "--drawer", self.drawer,
                ])
        
        # Add logo if provided (only for gradient mode)
        if self.logo_path and self.mode == "gradient":
            cmd.extend(["--logo", self.logo_path])
        
        # Don't print QR (avoids Windows encoding crash)
        cmd.append("--no-print")
        
        return cmd
