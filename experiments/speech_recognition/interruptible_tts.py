"""
Interruptible TTS - Text-to-Speech with Barge-In Support
=========================================================

TTS wrapper that plays audio smoothly using simpleaudio, with 
instant interrupt capability when the user starts speaking.

Usage:
    from interruptible_tts import InterruptibleTTS
    
    tts = InterruptibleTTS(voice="en_male")
    tts.speak("Hello, how can I help you today?")
    
    # Interrupt from another thread/callback
    tts.interrupt()
"""

import sys
import os
import struct
import tempfile
import threading
import time
import wave
from pathlib import Path
from typing import Optional

# Force UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    import numpy as np
    import simpleaudio as sa
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("   Run: pip install numpy simpleaudio")
    sys.exit(1)

# Import Sherpa TTS
try:
    from sherpa_onnx import OfflineTts, OfflineTtsConfig, OfflineTtsModelConfig, OfflineTtsVitsModelConfig
except ImportError:
    print("❌ sherpa-onnx not installed. Run: pip install sherpa-onnx")
    sys.exit(1)


# =============================================================================
# PATHS AND CONFIGURATION
# =============================================================================
BASE_DIR = Path(__file__).parent.parent.parent
LANG_DIR = BASE_DIR / "assets" / "models" / "voice" / "Language"

# Voice model configurations
VOICE_MODELS = {
    "hi_male": ("vits-piper-hi_IN-pratham-medium", "hi_IN-pratham-medium.onnx"),
    "hi_female": ("vits-piper-hi_IN-priyamvada-medium", "hi_IN-priyamvada-medium.onnx"),
    "en_male": ("vits-piper-en_US-hfc_male-medium", "en_US-hfc_male-medium.onnx"),
    "en_female": ("vits-piper-en_US-libritts_r-medium", "en_US-libritts_r-medium.onnx"),
    "ru_female": ("vits-piper-ru_RU-irina-medium", "ru_RU-irina-medium.onnx"),
    "es_male": ("vits-piper-es_ES-carlfm-x_low", "es_ES-carlfm-x_low.onnx"),
}

# Global TTS model cache
_TTS_CACHE: dict = {}


def _init_tts_engine(model_name: str) -> OfflineTts:
    """Initialize a TTS engine for the given voice."""
    if model_name not in VOICE_MODELS:
        raise ValueError(f"Unknown voice: {model_name}. Available: {list(VOICE_MODELS.keys())}")
    
    model_dir, model_file = VOICE_MODELS[model_name]
    model_path = LANG_DIR / model_dir
    
    if not model_path.exists():
        raise FileNotFoundError(f"Voice model not found: {model_path}")
    
    vits_model = OfflineTtsVitsModelConfig(
        model=str(model_path / model_file),
        tokens=str(model_path / "tokens.txt"),
        lexicon=str(model_path / "lexicon.txt"),
        data_dir=str(model_path / "espeak-ng-data")
    )
    config = OfflineTtsConfig(model=OfflineTtsModelConfig(vits=vits_model))
    return OfflineTts(config)


def get_tts_engine(voice: str) -> OfflineTts:
    """Get or create a cached TTS engine."""
    if voice not in _TTS_CACHE:
        print(f"⏳ Loading TTS voice: {voice}")
        _TTS_CACHE[voice] = _init_tts_engine(voice)
        print(f"✅ Voice '{voice}' loaded")
    return _TTS_CACHE[voice]


class InterruptibleTTS:
    """
    Text-to-Speech engine with barge-in interrupt support.
    
    Plays audio smoothly using simpleaudio with instant stop capability.
    """
    
    def __init__(self, voice: str = "en_male"):
        """
        Initialize InterruptibleTTS.
        
        Args:
            voice: Voice to use (en_male, en_female, hi_male, hi_female, etc.)
        """
        self.voice = voice
        
        # State
        self._speaking = False
        self._playback_thread: Optional[threading.Thread] = None
        self._current_play_obj = None  # simpleaudio PlayObject
        self._lock = threading.Lock()
        
        # Pre-load the TTS engine
        self._engine = get_tts_engine(voice)
    
    @property
    def is_speaking(self) -> bool:
        """Returns True if currently speaking."""
        return self._speaking
    
    def speak(self, text: str, blocking: bool = False) -> None:
        """
        Speak the given text.
        
        Args:
            text: Text to speak
            blocking: If True, wait until speech completes or is interrupted
        """
        if self._speaking:
            self.interrupt()  # Stop any current speech first
        
        self._speaking = True
        
        if blocking:
            self._speak_internal(text)
        else:
            self._playback_thread = threading.Thread(
                target=self._speak_internal,
                args=(text,),
                daemon=True
            )
            self._playback_thread.start()
    
    def _speak_internal(self, text: str) -> None:
        """Internal method that handles TTS generation and playback."""
        try:
            # Generate audio using sherpa-onnx
            audio = self._engine.generate(text, speed=1.0, sid=0)
            sample_rate = audio.sample_rate
            
            # Convert float samples to int16
            samples_int16 = np.array(
                [int(s * 32767) for s in audio.samples], 
                dtype=np.int16
            )
            
            # Play using simpleaudio (smooth, non-chunked playback)
            with self._lock:
                self._current_play_obj = sa.play_buffer(
                    samples_int16,
                    num_channels=1,
                    bytes_per_sample=2,
                    sample_rate=sample_rate
                )
            
            # Wait for playback to complete (or be interrupted)
            if self._current_play_obj:
                self._current_play_obj.wait_done()
            
        except Exception as e:
            import traceback
            print(f"❌ TTS error: {e}")
            traceback.print_exc()
        
        finally:
            self._speaking = False
            with self._lock:
                self._current_play_obj = None
    
    def interrupt(self) -> None:
        """Interrupt current speech immediately."""
        with self._lock:
            if self._current_play_obj:
                try:
                    self._current_play_obj.stop()
                except:
                    pass
                self._current_play_obj = None
        self._speaking = False
    
    def wait_complete(self, timeout: Optional[float] = None) -> bool:
        """Wait for speech to complete."""
        if self._playback_thread:
            self._playback_thread.join(timeout=timeout)
            return not self._speaking
        return True
    
    def set_voice(self, voice: str) -> None:
        """Change the current voice."""
        if voice != self.voice:
            self.voice = voice
            self._engine = get_tts_engine(voice)


# =============================================================================
# STANDALONE TEST
# =============================================================================
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Interruptible TTS Test")
    parser.add_argument("--voice", "-v", default="en_male", help="Voice to use")
    parser.add_argument("--text", "-t", default="Hello! Testing one two three. This is a longer sentence to test smooth playback.", help="Text to speak")
    parser.add_argument("--list-voices", "-l", action="store_true", help="List available voices")
    parser.add_argument("--interrupt-test", "-i", action="store_true", help="Test interrupt after 2 seconds")
    args = parser.parse_args()
    
    if args.list_voices:
        print("\n📢 Available Voices:")
        for voice in VOICE_MODELS:
            print(f"  - {voice}")
        sys.exit(0)
    
    print("=" * 60)
    print("  INTERRUPTIBLE TTS TEST")
    print(f"  Voice: {args.voice}")
    print("=" * 60)
    
    tts = InterruptibleTTS(voice=args.voice)
    
    print(f"\n🔊 Speaking: \"{args.text}\"")
    
    if args.interrupt_test:
        tts.speak(args.text, blocking=False)
        time.sleep(2)
        print("\n⚡ Interrupting...")
        tts.interrupt()
    else:
        tts.speak(args.text, blocking=True)
    
    print("\n✅ Test complete")
