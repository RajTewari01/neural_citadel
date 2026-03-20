"""
Voice Assistant with Barge-In Support
======================================

Main orchestrator that combines VAD, TTS, and STT for a natural
voice conversation with instant barge-in capability.

When the assistant is speaking and the user starts talking,
the TTS immediately stops and switches to listening mode.

Usage:
    # Run with default settings
    python voice_assistant.py
    
    # Specify microphone device
    python voice_assistant.py --device 2
    
    # Test VAD only
    python voice_assistant.py --test-vad
    
    # Test TTS only
    python voice_assistant.py --test-tts
"""

import sys
import time
import argparse
import threading
from pathlib import Path
from typing import Optional, Callable
from enum import Enum, auto

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Force UTF-8 for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

try:
    import numpy as np
    import sounddevice as sd
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    sys.exit(1)

# Local imports
from vad_listener import VADListener, list_audio_devices
from interruptible_tts import InterruptibleTTS

# Optional: Faster-Whisper for STT
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("⚠️ faster-whisper not available, STT disabled")


class AssistantState(Enum):
    """Voice assistant state machine states."""
    IDLE = auto()
    LISTENING = auto()
    PROCESSING = auto()
    SPEAKING = auto()


class VoiceAssistant:
    """
    Voice assistant with automatic barge-in support.
    
    The assistant continuously listens for voice. When the user speaks,
    if the assistant is currently speaking, it immediately stops (barge-in).
    The user's speech is then transcribed and processed.
    """
    
    def __init__(
        self,
        device: Optional[int] = None,
        voice: str = "en_male",
        whisper_model: str = "medium",
        vad_threshold: float = 0.5,
        on_transcription: Optional[Callable[[str], str]] = None,
    ):
        """
        Initialize Voice Assistant.
        
        Args:
            device: Audio input device index
            voice: TTS voice to use
            whisper_model: Whisper model size for STT
            vad_threshold: VAD sensitivity (0-1)
            on_transcription: Callback when transcription is ready. 
                              Should return response text to speak.
        """
        self.device = device
        self.voice = voice
        self.sample_rate = 16000
        
        # State
        self.state = AssistantState.IDLE
        self._running = False
        self._audio_buffer: list = []
        self._buffer_lock = threading.Lock()
        
        # Callbacks
        self.on_transcription = on_transcription or self._default_response
        
        # Initialize VAD
        print("\n" + "=" * 60)
        print("  INITIALIZING VOICE ASSISTANT")
        print("=" * 60)
        
        self.vad = VADListener(
            device=device,
            threshold=vad_threshold,
            min_silence_duration_ms=500,  # Wait a bit before processing
            min_speech_duration_ms=150,
        )
        self.vad.on_voice_start = self._on_voice_start
        self.vad.on_voice_end = self._on_voice_end
        
        # Initialize TTS
        self.tts = InterruptibleTTS(voice=voice)
        
        # Initialize STT (if available)
        self.whisper: Optional[WhisperModel] = None
        if WHISPER_AVAILABLE:
            print(f"⏳ Loading Whisper model '{whisper_model}'...")
            try:
                from configs.paths import SPEECH_MODELS_DIR
                cache_dir = SPEECH_MODELS_DIR / "faster_whisper_cache"
                cache_dir.mkdir(parents=True, exist_ok=True)
                
                self.whisper = WhisperModel(
                    whisper_model,
                    device="auto",
                    compute_type="int8",
                    download_root=str(cache_dir)
                )
                print("✅ Whisper loaded")
            except Exception as e:
                print(f"⚠️ Could not load Whisper: {e}")
                self.whisper = None
        
        print("✅ Voice Assistant ready!\n")
    
    def _default_response(self, text: str) -> str:
        """Default response handler - just echoes back."""
        return f"You said: {text}"
    
    def _on_voice_start(self) -> None:
        """Called when VAD detects user started speaking."""
        print("🎤 Voice detected...")
        
        # BARGE-IN: If we're speaking, interrupt immediately
        if self.state == AssistantState.SPEAKING:
            print("⚡ BARGE-IN! Interrupting speech...")
            self.tts.interrupt()
        
        # Start recording
        self.state = AssistantState.LISTENING
        with self._buffer_lock:
            self._audio_buffer.clear()
    
    def _on_voice_end(self) -> None:
        """Called when VAD detects user stopped speaking."""
        if self.state != AssistantState.LISTENING:
            return
        
        print("🔇 Voice ended, processing...")
        self.state = AssistantState.PROCESSING
        
        # Process the recorded audio
        threading.Thread(target=self._process_speech, daemon=True).start()
    
    def _process_speech(self) -> None:
        """Process recorded speech: transcribe and respond."""
        # Get recorded audio
        with self._buffer_lock:
            if not self._audio_buffer:
                print("   (No audio recorded)")
                self.state = AssistantState.IDLE
                return
            audio = np.concatenate(self._audio_buffer).flatten()
            self._audio_buffer.clear()
        
        # Transcribe
        text = self._transcribe(audio)
        
        if not text or len(text.strip()) < 2:
            print("   (No speech detected)")
            self.state = AssistantState.IDLE
            return
        
        print(f"📝 Transcribed: \"{text}\"")
        
        # Get response
        response = self.on_transcription(text)
        
        if response:
            # Speak response
            self.state = AssistantState.SPEAKING
            print(f"🔊 Speaking: \"{response[:50]}...\"" if len(response) > 50 else f"🔊 Speaking: \"{response}\"")
            self.tts.speak(response, blocking=True)
        
        # Return to idle
        self.state = AssistantState.IDLE
        print("💤 Ready for next input...")
    
    def _transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio to text using Whisper."""
        if not self.whisper:
            return ""
        
        try:
            segments, info = self.whisper.transcribe(
                audio,
                beam_size=5,
                task="transcribe",
                language=None,  # Auto-detect
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
            )
            return " ".join([seg.text for seg in segments]).strip()
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return ""
    
    def _recording_loop(self) -> None:
        """Background loop that records audio when listening."""
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
                    
                    # Only buffer when listening
                    if self.state == AssistantState.LISTENING:
                        with self._buffer_lock:
                            self._audio_buffer.append(audio.copy())
                    
                    time.sleep(0.01)  # Prevent busy loop
                    
        except Exception as e:
            print(f"❌ Recording error: {e}")
    
    def run(self) -> None:
        """Run the voice assistant main loop."""
        print("\n" + "=" * 60)
        print("  VOICE ASSISTANT RUNNING")
        print("  Speak to interact. Press Ctrl+C to exit.")
        print("  The assistant will stop talking when you interrupt!")
        print("=" * 60 + "\n")
        
        self._running = True
        self.state = AssistantState.IDLE
        
        # Start VAD listener
        self.vad.start()
        
        # Start recording thread
        record_thread = threading.Thread(target=self._recording_loop, daemon=True)
        record_thread.start()
        
        try:
            # Keep main thread alive
            while self._running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\n👋 Shutting down...")
        finally:
            self._running = False
            self.vad.stop()
            self.tts.interrupt()
    
    def speak(self, text: str, blocking: bool = True) -> None:
        """Manually trigger speech (can be interrupted by user voice)."""
        self.state = AssistantState.SPEAKING
        self.tts.speak(text, blocking=blocking)
        if blocking:
            self.state = AssistantState.IDLE


# =============================================================================
# CLI ENTRY POINT
# =============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Voice Assistant with Barge-In Support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run assistant with device 2
    python voice_assistant.py --device 2
    
    # Test VAD detection only
    python voice_assistant.py --test-vad
    
    # Test TTS with interrupt simulation
    python voice_assistant.py --test-tts
        """
    )
    parser.add_argument("--device", "-d", type=int, default=None, help="Audio device index")
    parser.add_argument("--voice", "-v", default="en_male", help="TTS voice")
    parser.add_argument("--model", "-m", default="medium", help="Whisper model size")
    parser.add_argument("--threshold", "-t", type=float, default=0.5, help="VAD threshold")
    parser.add_argument("--list-devices", "-l", action="store_true", help="List devices")
    parser.add_argument("--test-vad", action="store_true", help="Test VAD only")
    parser.add_argument("--test-tts", action="store_true", help="Test TTS only")
    
    args = parser.parse_args()
    
    if args.list_devices:
        list_audio_devices()
        return
    
    list_audio_devices()
    
    # Test modes
    if args.test_vad:
        print("\n🧪 Testing VAD (press Ctrl+C to exit)...")
        vad = VADListener(device=args.device, threshold=args.threshold)
        vad.on_voice_start = lambda: print("🟢 Voice START")
        vad.on_voice_end = lambda: print("🔴 Voice END")
        vad.start()
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            vad.stop()
        return
    
    if args.test_tts:
        print("\n🧪 Testing TTS interrupt...")
        tts = InterruptibleTTS(voice=args.voice)
        text = "This is a long test sentence that demonstrates the interruptible text to speech capability. I will keep talking until you interrupt me or I finish."
        print(f"🔊 Speaking: \"{text[:50]}...\"")
        tts.speak(text)
        time.sleep(2)
        print("⚡ Interrupting...")
        tts.interrupt()
        print("✅ Test complete")
        return
    
    # Run full assistant
    def simple_response(text: str) -> str:
        """Simple echo response for demo."""
        return f"I heard you say: {text}. How can I help you further?"
    
    assistant = VoiceAssistant(
        device=args.device,
        voice=args.voice,
        whisper_model=args.model,
        vad_threshold=args.threshold,
        on_transcription=simple_response,
    )
    assistant.run()


if __name__ == "__main__":
    main()
