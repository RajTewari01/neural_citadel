"""
VAD Listener - Non-blocking Voice Activity Detection
=====================================================

Background thread that continuously monitors microphone for voice activity
using Silero VAD. Fires callbacks when voice is detected/lost.

Usage:
    from vad_listener import VADListener
    
    def on_voice_start():
        print("User started speaking!")
    
    def on_voice_end():
        print("User stopped speaking")
    
    listener = VADListener(device=2)
    listener.on_voice_start = on_voice_start
    listener.on_voice_end = on_voice_end
    listener.start()
"""

import sys
import threading
import numpy as np
from pathlib import Path
from typing import Callable, Optional
from collections import deque

# Force UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    import sounddevice as sd
    from silero_vad import load_silero_vad, read_audio, get_speech_timestamps
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("   Run: pip install silero-vad sounddevice")
    sys.exit(1)


class VADListener:
    """
    Non-blocking Voice Activity Detection listener.
    
    Runs in a background thread, monitoring microphone input for speech.
    Fires callbacks when voice starts/ends.
    
    Attributes:
        on_voice_start: Callback when user starts speaking
        on_voice_end: Callback when user stops speaking
        is_speaking: Property indicating current voice status
    """
    
    def __init__(
        self,
        device: Optional[int] = None,
        sample_rate: int = 16000,
        threshold: float = 0.5,
        min_silence_duration_ms: int = 300,
        min_speech_duration_ms: int = 100,
    ):
        """
        Initialize VAD Listener.
        
        Args:
            device: Audio input device index (None for default)
            sample_rate: Audio sample rate (16000 for Silero)
            threshold: Voice detection threshold (0.0-1.0)
            min_silence_duration_ms: Minimum silence before voice_end fires
            min_speech_duration_ms: Minimum speech before voice_start fires
        """
        self.device = device
        self.sample_rate = sample_rate
        
        # Silero VAD requires EXACTLY 512 samples for 16kHz (32ms) or 256 for 8kHz
        self.chunk_samples = 512 if sample_rate == 16000 else 256
        self.chunk_duration_ms = 32 if sample_rate == 16000 else 32  # Always 32ms
        
        self.threshold = threshold
        self.min_silence_chunks = int(min_silence_duration_ms / self.chunk_duration_ms)
        self.min_speech_chunks = int(min_speech_duration_ms / self.chunk_duration_ms)
        
        # State
        self._running = False
        self._paused = False  # Pause detection (for echo cancellation)
        self._thread: Optional[threading.Thread] = None
        self._is_speaking = False
        self._speech_counter = 0
        self._silence_counter = 0
        
        # Thread-safe interrupt event
        self._stop_event = threading.Event()
        self._voice_detected_event = threading.Event()
        
        # Callbacks
        self.on_voice_start: Optional[Callable[[], None]] = None
        self.on_voice_end: Optional[Callable[[], None]] = None
        
        # Load Silero VAD model
        print("⏳ Loading Silero VAD model...")
        self.model = load_silero_vad()
        print("✅ VAD model loaded")
    
    @property
    def is_speaking(self) -> bool:
        """Returns True if voice is currently detected."""
        return self._is_speaking
    
    @property
    def voice_detected_event(self) -> threading.Event:
        """Event that is set when voice is detected. Use for interrupt signaling."""
        return self._voice_detected_event
    
    def start(self) -> None:
        """Start the VAD listener in a background thread."""
        if self._running:
            print("⚠️ VAD listener already running")
            return
        
        self._stop_event.clear()
        self._voice_detected_event.clear()
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        print(f"🎙️ VAD listener started (device={self.device}, threshold={self.threshold})")
    
    def stop(self) -> None:
        """Stop the VAD listener gracefully."""
        if not self._running:
            return
        
        self._stop_event.set()
        self._running = False
        
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        
        print("🛑 VAD listener stopped")
    
    def _listen_loop(self) -> None:
        """Main listening loop running in background thread."""
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32,
                device=self.device,
                blocksize=self.chunk_samples
            ) as stream:
                while not self._stop_event.is_set():
                    # Read audio chunk
                    audio_chunk, overflowed = stream.read(self.chunk_samples)
                    if overflowed:
                        continue
                    
                    # Skip detection if paused (for echo cancellation)
                    if self._paused:
                        continue
                    
                    # Flatten and convert
                    audio_data = audio_chunk.flatten()
                    
                    # Get VAD probability
                    import torch
                    audio_tensor = torch.from_numpy(audio_data)
                    speech_prob = self.model(audio_tensor, self.sample_rate).item()
                    
                    # Update state machine
                    self._update_state(speech_prob >= self.threshold)
                    
        except Exception as e:
            print(f"❌ VAD listener error: {e}")
            self._running = False
    
    def _update_state(self, is_speech: bool) -> None:
        """Update the speech state machine based on current detection."""
        if is_speech:
            self._speech_counter += 1
            self._silence_counter = 0
            
            # Trigger voice start after minimum speech duration
            if not self._is_speaking and self._speech_counter >= self.min_speech_chunks:
                self._is_speaking = True
                self._voice_detected_event.set()
                if self.on_voice_start:
                    self.on_voice_start()
        else:
            self._silence_counter += 1
            self._speech_counter = 0
            
            # Trigger voice end after minimum silence duration
            if self._is_speaking and self._silence_counter >= self.min_silence_chunks:
                self._is_speaking = False
                self._voice_detected_event.clear()
                if self.on_voice_end:
                    self.on_voice_end()
    
    def wait_for_voice(self, timeout: Optional[float] = None) -> bool:
        """
        Block until voice is detected.
        
        Args:
            timeout: Maximum seconds to wait (None for indefinite)
            
        Returns:
            True if voice detected, False if timeout
        """
        return self._voice_detected_event.wait(timeout=timeout)
    
    def reset(self) -> None:
        """Reset the state machine (useful after interrupt)."""
        self._is_speaking = False
        self._speech_counter = 0
        self._silence_counter = 0
        self._voice_detected_event.clear()


def list_audio_devices() -> None:
    """Print available audio input devices."""
    print("\n📋 Available Audio Input Devices:")
    print("-" * 60)
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            marker = " ← default" if i == sd.default.device[0] else ""
            print(f"  [{i:2}] {device['name'][:45]}{marker}")
    print()


# =============================================================================
# STANDALONE TEST
# =============================================================================
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="VAD Listener Test")
    parser.add_argument("--device", "-d", type=int, default=None, help="Audio device index")
    parser.add_argument("--threshold", "-t", type=float, default=0.5, help="VAD threshold (0-1)")
    parser.add_argument("--list-devices", "-l", action="store_true", help="List audio devices")
    args = parser.parse_args()
    
    if args.list_devices:
        list_audio_devices()
        sys.exit(0)
    
    list_audio_devices()
    
    print("=" * 60)
    print("  VAD LISTENER TEST")
    print("  Speak into the microphone to see voice detection")
    print("  Press Ctrl+C to exit")
    print("=" * 60)
    
    # Create listener with callbacks
    listener = VADListener(device=args.device, threshold=args.threshold)
    
    def on_start():
        print("\n🟢 VOICE DETECTED - Speaking...")
    
    def on_end():
        print("🔴 VOICE ENDED - Silence\n")
    
    listener.on_voice_start = on_start
    listener.on_voice_end = on_end
    
    try:
        listener.start()
        
        # Keep main thread alive
        while True:
            import time
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\n👋 Exiting...")
    finally:
        listener.stop()
