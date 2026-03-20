"""
Voice Worker - PyQt Manager for Voice Engine
=============================================

Manages the voice_engine.py subprocess from speech_venv.
Provides Qt signals for GUI integration.
"""
from PyQt6.QtCore import QObject, QProcess, pyqtSignal, QTimer
from pathlib import Path
import json


# Paths
SPEECH_VENV_PYTHON = Path("d:/neural_citadel/venvs/env/speech_venv/Scripts/python.exe")
VOICE_ENGINE_SCRIPT = Path("d:/neural_citadel/infra/standalone/voice_engine.py")


class VoiceManager(QObject):
    """Manages voice engine subprocess for STT."""
    
    # Signals
    ready = pyqtSignal()           # Model loaded, ready for commands
    listening = pyqtSignal()       # Recording started
    processing = pyqtSignal()      # Transcribing
    transcription = pyqtSignal(str)  # Got text result
    stopped = pyqtSignal()         # Recording stopped
    error = pyqtSignal(str)        # Error message
    status_changed = pyqtSignal(str)  # General status updates
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = None
        self._is_loaded = False
        self._is_listening = False
    
    @property
    def is_loaded(self) -> bool:
        """Check if voice engine is loaded."""
        return self._is_loaded and self.process and self.process.state() == QProcess.ProcessState.Running
    
    @property
    def is_listening(self) -> bool:
        """Check if currently recording."""
        return self._is_listening
    
    def load_model(self):
        """Start the voice engine subprocess."""
        if self.is_loaded:
            return
        
        # Parent to self (VoiceManager singleton) to prevent garbage collection
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._on_output)
        self.process.finished.connect(self._on_finished)
        self.process.errorOccurred.connect(self._on_error)
        
        self.status_changed.emit("Loading voice model...")
        
        self.process.start(
            str(SPEECH_VENV_PYTHON),
            [str(VOICE_ENGINE_SCRIPT)]
        )
    
    def unload_model(self):
        """Stop the voice engine subprocess."""
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            self.process.write(b"QUIT\n")
            self.process.waitForFinished(3000)
            if self.process.state() == QProcess.ProcessState.Running:
                self.process.kill()
        
        self._is_loaded = False
        self._is_listening = False
        self.status_changed.emit("Voice model unloaded")
    
    def start_listening(self):
        """Start voice recording."""
        if not self.is_loaded:
            self.error.emit("Voice model not loaded")
            return
        
        if self._is_listening:
            return
        
        self._is_listening = True
        self.process.write(b"START\n")
    
    def stop_listening(self):
        """Stop voice recording manually."""
        if not self.is_loaded or not self._is_listening:
            return
        
        self.process.write(b"STOP\n")
    
    def cancel_listening(self):
        """Cancel voice recording without processing."""
        if not self.is_loaded or not self._is_listening:
            return
        
        self._is_listening = False
        self.process.write(b"CANCEL\n")
    
    def _on_output(self):
        """Handle output from voice engine."""
        while self.process.canReadLine():
            line = bytes(self.process.readLine()).decode('utf-8', errors='replace').strip()
            
            if line == "READY":
                self._is_loaded = True
                self.ready.emit()
                self.status_changed.emit("Voice model ready")
            
            elif line == "LISTENING":
                self.listening.emit()
                self.status_changed.emit("Listening...")
            
            elif line == "PROCESSING":
                self.processing.emit()
                self.status_changed.emit("Processing...")
            
            elif line.startswith("TEXT:"):
                text = line[5:]  # Remove "TEXT:" prefix
                self._is_listening = False
                self.transcription.emit(text)
            
            elif line == "STOPPED":
                self._is_listening = False
                self.stopped.emit()
                self.status_changed.emit("Ready")
            
            elif line.startswith("ERROR:"):
                error_msg = line[6:]
                self._is_listening = False
                self.error.emit(error_msg)
    
    def _on_finished(self, exit_code, exit_status):
        """Handle process finished."""
        self._is_loaded = False
        self._is_listening = False
        self.status_changed.emit("Voice engine stopped")
    
    def _on_error(self, error):
        """Handle process error."""
        self._is_loaded = False
        self._is_listening = False
        self.error.emit(f"Process error: {error}")


# Singleton instance for shared access
_voice_manager_instance = None


def get_voice_manager() -> VoiceManager:
    """Get the shared VoiceManager instance."""
    global _voice_manager_instance
    if _voice_manager_instance is None:
        _voice_manager_instance = VoiceManager()
    return _voice_manager_instance
