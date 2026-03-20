"""
Voice Engine - Faster Whisper STT
==================================

Standalone CLI for voice-to-text using Faster Whisper.
Runs in speech_venv via subprocess from PyQt GUI.

Protocol (stdout):
    READY           - Engine ready for commands
    LISTENING       - Recording started
    PROCESSING      - Transcribing audio
    TEXT:<text>     - Final transcription (English)
    ERROR:<msg>     - Error occurred
    STOPPED         - Recording stopped

Commands (stdin):
    START           - Begin recording
    STOP            - Manual stop
    QUIT            - Exit process

Features:
    - VAD: Auto-stop after 10s silence
    - Any language → English translation
"""
import sys
import os
import io
import time
import threading
import queue
import numpy as np
from pathlib import Path

# Ensure UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configuration
SAMPLE_RATE = 16000
SILENCE_TIMEOUT = 10  # seconds of silence to auto-stop
VAD_THRESHOLD = 0.3   # VAD sensitivity (0.0-1.0)
MAX_RECORD_SECONDS = 60  # absolute max recording time


def flush_print(msg: str):
    """Print with immediate flush for real-time IPC."""
    print(msg, flush=True)


class VoiceEngine:
    """Main voice engine with threaded stdin handling."""
    
    def __init__(self):
        self.whisper_model = None
        self.vad_model = None
        self.stop_event = threading.Event()
        self.cancel_event = threading.Event()  # Cancel without processing
        self.command_queue = queue.Queue()
        self.running = True
    
    def load_whisper(self):
        """Load Faster Whisper model."""
        try:
            from faster_whisper import WhisperModel
            self.whisper_model = WhisperModel(
                "medium",  # Using medium for better accuracy
                device="cpu",
                compute_type="int8"
            )
            return True
        except Exception as e:
            flush_print(f"ERROR:Failed to load Whisper: {e}")
            return False
    
    def load_vad(self):
        """Load Silero VAD model."""
        try:
            import torch
            model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=True
            )
            self.vad_model = model
            return True
        except Exception as e:
            flush_print(f"ERROR:Failed to load VAD: {e}")
            return False
    
    def stdin_reader_thread(self):
        """Background thread that reads stdin commands."""
        while self.running:
            try:
                line = sys.stdin.readline()
                if not line:  # EOF
                    self.running = False
                    self.stop_event.set()
                    break
                cmd = line.strip().upper()
                if cmd:
                    self.command_queue.put(cmd)
                    # Immediately set stop if STOP or CANCEL command
                    if cmd == "STOP":
                        self.stop_event.set()
                    elif cmd == "CANCEL":
                        self.cancel_event.set()  # Cancel without processing
                        self.stop_event.set()
                    elif cmd == "QUIT":
                        self.running = False
                        self.stop_event.set()
            except:
                break
    
    def record_audio(self) -> np.ndarray:
        """Record audio until silence detected or manual stop."""
        import sounddevice as sd
        import torch
        
        audio_buffer = []
        silence_start = None
        speech_detected = False
        
        flush_print("LISTENING")
        
        def callback(indata, frames, time_info, status):
            nonlocal silence_start, speech_detected
            
            if self.stop_event.is_set():
                raise sd.CallbackAbort()
            
            audio_chunk = indata[:, 0].copy()
            audio_buffer.append(audio_chunk)
            
            # VAD check
            chunk_tensor = torch.from_numpy(audio_chunk).float()
            speech_prob = self.vad_model(chunk_tensor, SAMPLE_RATE).item()
            
            if speech_prob > VAD_THRESHOLD:
                speech_detected = True
                silence_start = None
            elif speech_detected:
                if silence_start is None:
                    silence_start = time.time()
                elif time.time() - silence_start > SILENCE_TIMEOUT:
                    raise sd.CallbackAbort()
        
        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype='float32',
                blocksize=512,
                device=2,  # User's preferred microphone index
                callback=callback
            ):
                start_time = time.time()
                while not self.stop_event.is_set():
                    time.sleep(0.05)  # Faster response to stop
                    if time.time() - start_time > MAX_RECORD_SECONDS:
                        break
        except sd.CallbackAbort:
            pass
        except Exception as e:
            flush_print(f"ERROR:Recording failed: {e}")
            return None
        
        if audio_buffer:
            return np.concatenate(audio_buffer, axis=0)
        return None
    
    def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio to English text with translation."""
        flush_print("PROCESSING")
        
        try:
            segments, info = self.whisper_model.transcribe(
                audio.flatten(),
                beam_size=8,  # Increased for better accuracy
                task='translate',  # Translate any language to English
                language=None,  # Auto-detect source language
                word_timestamps=False,
                condition_on_previous_text=True,
                no_speech_threshold=0.5,
                log_prob_threshold=-1.0,
                compression_ratio_threshold=2.4,
            )
            
            text = " ".join(seg.text for seg in segments).strip()
            return text
        except Exception as e:
            flush_print(f"ERROR:Transcription failed: {e}")
            return ""
    
    def run(self):
        """Main loop."""
        # Load models
        if not self.load_whisper():
            return
        if not self.load_vad():
            return
        
        flush_print("READY")
        
        # Start stdin reader thread
        stdin_thread = threading.Thread(target=self.stdin_reader_thread, daemon=True)
        stdin_thread.start()
        
        while self.running:
            try:
                # Wait for command with timeout
                try:
                    cmd = self.command_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                if cmd == "QUIT":
                    break
                
                elif cmd == "START":
                    self.stop_event.clear()
                    self.cancel_event.clear()
                    
                    # Record audio
                    audio = self.record_audio()
                    
                    # Check if cancelled - skip processing
                    if self.cancel_event.is_set():
                        flush_print("CANCELLED")
                        continue
                    
                    if audio is not None and len(audio) > 0:
                        text = self.transcribe(audio)
                        flush_print(f"TEXT:{text}" if text else "TEXT:")
                    else:
                        flush_print("TEXT:")
                    
                    flush_print("STOPPED")
                
            except Exception as e:
                flush_print(f"ERROR:{e}")
        
        # Cleanup
        del self.whisper_model
        del self.vad_model
        
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except:
            pass


def main():
    engine = VoiceEngine()
    engine.run()


if __name__ == "__main__":
    main()
