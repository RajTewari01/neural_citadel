"""
Barge-In Test Demo
==================

Continuously speaks "testing" until user interrupts.
When user speaks, it stops and transcribes what they said.

Usage:
    python barge_in_test.py --device 2
"""

import sys
import time
import argparse
import threading
import numpy as np
from pathlib import Path

# Force UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    import sounddevice as sd
    from faster_whisper import WhisperModel
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    sys.exit(1)

# Local imports
from vad_listener import VADListener, list_audio_devices
from interruptible_tts import InterruptibleTTS


class BargeInTest:
    """Simple test for barge-in functionality."""
    
    def __init__(self, device: int = None, voice: str = "en_male"):
        self.device = device
        self.sample_rate = 16000
        
        # Audio buffer for recording
        self._audio_buffer = []
        self._buffer_lock = threading.Lock()
        self._recording = False
        
        print("\n" + "=" * 60)
        print("  BARGE-IN TEST DEMO")
        print("=" * 60)
        
        # Initialize VAD (threshold 0.85 to ignore background noise, 300ms min speech)
        self.vad = VADListener(device=device, threshold=0.85, min_speech_duration_ms=300)
        self.vad.on_voice_start = self._on_voice_start
        self.vad.on_voice_end = self._on_voice_end
        
        # Initialize TTS
        self.tts = InterruptibleTTS(voice=voice)
        
        # Initialize Whisper
        print("⏳ Loading Whisper model...")
        from configs.paths import SPEECH_MODELS_DIR
        cache_dir = SPEECH_MODELS_DIR / "faster_whisper_cache"
        # Use CPU to avoid cublas64_12.dll error
        self.whisper = WhisperModel(
            "medium",
            device="cpu",
            compute_type="int8",
            download_root=str(cache_dir)
        )
        print("✅ Whisper loaded")
        
        self._running = False
        self._speak_loop_active = False
    
    def _on_voice_start(self):
        """Called when VAD detects voice."""
        print("\n⚡ BARGE-IN! Stopping TTS...")
        self.tts.interrupt()
        self._speak_loop_active = False  # Stop the speaking loop
        
        # Start recording
        self._recording = True
        with self._buffer_lock:
            self._audio_buffer.clear()
    
    def _on_voice_end(self):
        """Called when VAD detects silence."""
        if not self._recording:
            return
        
        self._recording = False
        print("🔇 Voice ended, transcribing...")
        
        # Get recorded audio
        with self._buffer_lock:
            if not self._audio_buffer:
                print("   (No audio recorded)")
                self._resume_speaking()
                return
            audio = np.concatenate(self._audio_buffer).flatten()
            self._audio_buffer.clear()
        
        # Transcribe
        try:
            segments, info = self.whisper.transcribe(
                audio,
                beam_size=5,
                task="transcribe",
                language=None,
                vad_filter=True,
            )
            text = " ".join([seg.text for seg in segments]).strip()
            
            if text:
                print(f"\n📝 You said: \"{text}\"\n")
            else:
                print("   (No speech detected)")
        except Exception as e:
            print(f"❌ Transcription error: {e}")
        
        # Resume speaking after a short pause
        time.sleep(0.5)
        self._resume_speaking()
    
    def _resume_speaking(self):
        """Resume the continuous speaking loop."""
        if self._running:
            self._speak_loop_active = True
    
    def _recording_loop(self):
        """Background loop that records audio when VAD detects voice."""
        chunk_samples = int(self.sample_rate * 0.1)  # 100ms chunks
        
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32,
                device=self.device,
                blocksize=chunk_samples
            ) as stream:
                while self._running:
                    audio, _ = stream.read(chunk_samples)
                    
                    if self._recording:
                        with self._buffer_lock:
                            self._audio_buffer.append(audio.copy())
                    
                    time.sleep(0.01)
        except Exception as e:
            print(f"❌ Recording error: {e}")
    
    def _speaking_loop(self):
        """Continuously speak 'testing' until interrupted."""
        test_phrases = [
            "Testing, testing, one two three. This is a long test sentence for barge-in.",
            "This is a test of the barge-in system. You can interrupt me at any time.",
            "Speak now to interrupt me. I will keep talking until you say something.",
            "The quick brown fox jumps over the lazy dog. Speak to stop me talking.",
        ]
        phrase_idx = 0
        
        while self._running:
            if self._speak_loop_active and not self._recording:
                phrase = test_phrases[phrase_idx % len(test_phrases)]
                print(f"🔊 Speaking: \"{phrase[:50]}...\"")
                
                # Brief pause during TTS start to avoid self-trigger (0.5s)
                self.vad._paused = True
                self.tts.speak(phrase, blocking=False)  # Start non-blocking
                
                time.sleep(0.5)  # Short lockout
                self.vad._paused = False
                print("👂 Listening for barge-in...")
                
                # Wait for TTS to finish (or be interrupted)
                self.tts.wait_complete()
                
                phrase_idx += 1
                time.sleep(0.3)  # Small gap between phrases
            else:
                time.sleep(0.1)
    
    def run(self):
        """Run the test."""
        print("\n" + "-" * 60)
        print("  Speak at any time to interrupt!")
        print("  Your speech will be transcribed.")
        print("  Press Ctrl+C to exit.")
        print("-" * 60 + "\n")
        
        self._running = True
        self._speak_loop_active = True
        
        # Start VAD
        self.vad.start()
        
        # Start recording thread
        record_thread = threading.Thread(target=self._recording_loop, daemon=True)
        record_thread.start()
        
        # Run speaking loop in main thread
        try:
            self._speaking_loop()
        except KeyboardInterrupt:
            print("\n\n👋 Exiting...")
        finally:
            self._running = False
            self._speak_loop_active = False
            self.vad.stop()
            self.tts.interrupt()


def main():
    parser = argparse.ArgumentParser(description="Barge-In Test Demo")
    parser.add_argument("--device", "-d", type=int, default=25, help="Audio device index (25=AI Noise-cancelling)")
    parser.add_argument("--voice", "-v", default="en_male", help="TTS voice")
    parser.add_argument("--list-devices", "-l", action="store_true", help="List devices")
    args = parser.parse_args()
    
    if args.list_devices:
        list_audio_devices()
        return
    
    list_audio_devices()
    
    test = BargeInTest(device=args.device, voice=args.voice)
    test.run()


if __name__ == "__main__":
    main()
