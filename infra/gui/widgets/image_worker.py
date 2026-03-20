"""
Image Generation Worker
=======================

Background worker for running image generation via subprocess.
Uses image_venv Python to call apps.image_gen.runner.
"""

import sys
import subprocess
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

# Import paths from centralized config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from configs.paths import IMAGE_VENV_PYTHON, ROOT_DIR as PROJECT_ROOT, IMAGE_GEN_MODULE


class ImageWorker(QThread):
    """
    Background worker for image generation via subprocess.
    
    Signals:
        started: Emitted when generation starts
        progress: Emitted with output lines from the subprocess
        finished: Emitted with the output image path on success
        error: Emitted with error message on failure
    """
    
    started = pyqtSignal()
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)  # Output image path
    error = pyqtSignal(str)
    
    def __init__(self, prompt: str, pipeline: str, type_name: str = None, aspect: str = None, seed: int = None):
        super().__init__()
        self.prompt = prompt
        self.pipeline = pipeline
        self.type_name = type_name
        self.aspect = aspect
        self.seed = seed
        self._running = True
    
    def run(self):
        """Execute image generation in subprocess."""
        self.started.emit()
        
        # Build command - use image_venv python with -m module format
        python_exe = str(IMAGE_VENV_PYTHON)
        
        cmd = [
            python_exe,
            "-m", IMAGE_GEN_MODULE,
            self.prompt,
            "--style", self.pipeline,
        ]
        
        # Add optional arguments
        if self.type_name:
            cmd.extend(["--type", self.type_name])
        
        if self.aspect:
            cmd.extend(["--aspect", self.aspect])
        
        if self.seed is not None:
            cmd.extend(["--seed", str(self.seed)])
        
        # Always add details for better quality (no --open, will use popup)
        cmd.append("--add_details")
        
        self.progress.emit(f"Using: {python_exe}")
        self.progress.emit(f"Starting: {self.pipeline}" + (f" ({self.type_name})" if self.type_name else ""))
        
        try:
            # Set environment for proper Unicode handling
            import os
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUTF8'] = '1'
            
            # Run subprocess with explicit UTF-8 encoding
            process = subprocess.Popen(
                cmd,
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            output_path = None
            all_output = []
            
            # Stream stdout
            for line in iter(process.stdout.readline, ''):
                if not self._running:
                    process.terminate()
                    break
                
                line = line.strip()
                if line:
                    all_output.append(line)
                    self.progress.emit(line)
                    
                    # Look for the output path in the output
                    if "Image saved at:" in line:
                        output_path = line.split("Image saved at:")[-1].strip()
                    elif "📁 Image saved at:" in line:
                        output_path = line.split("📁 Image saved at:")[-1].strip()
                    elif "Saved to:" in line:
                        output_path = line.split("Saved to:")[-1].strip()
                    elif "saved at:" in line.lower():
                        output_path = line.split(":")[-1].strip()
                    # Also check for direct path in line (ends with .png or .jpg)
                    elif line.endswith('.png') or line.endswith('.jpg'):
                        if '\\' in line or '/' in line:
                            output_path = line
            
            # Wait for process and get return code
            process.wait()
            
            # Capture any stderr
            stderr_output = process.stderr.read()
            
            if process.returncode == 0 and output_path:
                self.finished.emit(output_path)
            elif process.returncode == 0:
                self.finished.emit("Generation complete")
            else:
                # Report the actual error
                error_msg = stderr_output.strip() if stderr_output else "Unknown error"
                if not error_msg and all_output:
                    error_msg = all_output[-1]  # Use last output line
                self.error.emit(f"Code {process.returncode}: {error_msg[:200]}")
                
        except Exception as e:
            self.error.emit(str(e))
    
    def stop(self):
        """Stop the worker."""
        self._running = False
