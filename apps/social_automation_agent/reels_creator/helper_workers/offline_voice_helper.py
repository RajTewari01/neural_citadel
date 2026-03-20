"""
offline_voice_helper.py - Helper functions for voiceover generation.
============================================================
"""
import sys
from pathlib import Path
from typing import Optional
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from configs.paths import VITS_PIPER_MODELS, get_piper_model
from sherpa_onnx import OfflineTts, OfflineTtsConfig, OfflineTtsModelConfig, OfflineTtsVitsModelConfig
from pydub.playback import play
from pydub import AudioSegment
import tempfile
import struct
import wave
import os
import gc

TTS_CACHE = {}


# =====================================================
# INITIALIZING ENGINE (INTERNAL)
# =====================================================

def _init_tts_engine(model_name: str) -> OfflineTts:
    """Initializes and returns a single OfflineTts engine (internal use)."""
    model_config = get_piper_model(model_name)
    
    vits_model = OfflineTtsVitsModelConfig(
        model=str(model_config["model"]),
        tokens=str(model_config["tokens"]),
        lexicon=model_config["lexicon"],
        data_dir=str(model_config["data_dir"])
    )
    config = OfflineTtsConfig(model=OfflineTtsModelConfig(vits=vits_model))
    return OfflineTts(config)


# =====================================================
# LOADING ALL VITS_PIPER_MODELS {FAST BUT HEAVY}
# =====================================================

def fast_preload_all_engines() -> dict:
    """
    Pre-load ALL models into the cache at startup.
    Fast switching but uses more memory.
    """
    print("[INFO] Pre-loading ALL TTS models (this may take a moment)...")
    loaded_count = 0
    
    for key in VITS_PIPER_MODELS:
        try:
            TTS_CACHE[key] = _init_tts_engine(key)
            print(f"  [OK] Loaded {key}")
            loaded_count += 1
        except Exception as e:
            print(f"  [ERROR] Failed to load {key}: {e}")
    
    print(f"[INFO] Preloaded {loaded_count}/{len(VITS_PIPER_MODELS)} models")
    return TTS_CACHE


# =====================================================
# LOADING ONLY ONE VITS_PIPER_MODEL {SLOW BUT LIGHT}
# =====================================================

def slow_load_single_engine(model_name: str) -> OfflineTts:
    """
    Load only ONE model on demand.
    Low memory but slower when switching voices.
    """
    # Clear old cache to free memory
    if TTS_CACHE and model_name not in TTS_CACHE:
        print(f"[INFO] Unloading previous models, loading {model_name}...")
        TTS_CACHE.clear()
        gc.collect()
    
    if model_name in TTS_CACHE:
        return TTS_CACHE[model_name]
    
    try:
        TTS_CACHE[model_name] = _init_tts_engine(model_name)
        model_config = get_piper_model(model_name)
        print(f"[OK] Loaded: {model_config['description']}")
        return TTS_CACHE[model_name]
    except Exception as e:
        print(f"[ERROR] Failed to load {model_name}: {e}")
        raise


# =====================================================
# GET ENGINE (AUTO-LOADS IF NEEDED)
# =====================================================

def get_engine(model_name: str) -> OfflineTts:
    """Get engine from cache or load it if not available."""
    if model_name in TTS_CACHE:
        return TTS_CACHE[model_name]
    return slow_load_single_engine(model_name)


# =====================================================
# VOICE HELPER CLASS
# =====================================================

class VoiceHelper:
    """Helper class for voice synthesis with easy model switching."""
    
    def __init__(self, model_name: str = "en_US_male", preload_all: bool = False):
        """
        Initialize VoiceHelper.
        
        Args:
            model_name: Initial model to load
            preload_all: If True, preload ALL models for instant switching (uses more RAM)
        """
        self.model_name = model_name
        
        if preload_all:
            self.preload_all_models()
        
        self.engine = get_engine(model_name)
    
    def preload_all_models(self):
        """Preload ALL voice models into memory for instant switching."""
        fast_preload_all_engines()
        
    def load_model(self, model_name: str):
        """Switch to a different voice model (instant if preloaded)."""
        self.model_name = model_name
        self.engine = get_engine(model_name)
        
    def unload_model(self):
        """Unload current model to free memory."""
        if self.model_name in TTS_CACHE:
            del TTS_CACHE[self.model_name]
        self.engine = None
        gc.collect()
    
    def unload_all_models(self):
        """Unload ALL cached models to free memory."""
        TTS_CACHE.clear()
        self.engine = None
        gc.collect()
        print("[INFO] Unloaded all TTS models")

    def synthesize_audio(self, text: str = None, speed: float = 1.0, 
                         output_path: Path = None, debug: bool = False) -> Path:
        """
        Synthesize text to audio file.
        
        Args:
            text: Text to synthesize
            speed: Speech speed (1.0 = normal)
            output_path: Optional output path (auto-generates if None)
            debug: If True, use test text when text is None
            
        Returns:
            Path to generated audio file
        """
        if text is None and not debug:
            raise ValueError("Text cannot be None (use debug=True for test text)")
        if text is None and debug:
            text = "Hello everyone, this is Neural Citadel voice engine. Testing audio synthesis."
        
        # Generate audio
        audio = self.engine.generate(text, speed=speed)
        
        # Create output path
        if output_path is None:
            output_path = Path(tempfile.gettempdir()) / f"tts_{self.model_name}_{os.getpid()}.wav"
        
        # Write WAV file
        with wave.open(str(output_path), 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(audio.sample_rate)
            wf.writeframes(struct.pack(f'{len(audio.samples)}h', *[int(s * 32767) for s in audio.samples]))
        
        print(output_path)
        return output_path
    
    def synthesize_and_play(self, text: str, speed: float = 1.0, cleanup: bool = True) -> Optional[Path]:
        """
        Synthesize text and play it immediately.
        
        Args:
            text: Text to synthesize
            speed: Speech speed
            cleanup: If True, delete temp file after playing
        """
        audio_path = self.synthesize_audio(text, speed=speed)
        audio = AudioSegment.from_wav(str(audio_path))
        play(audio)
        if cleanup:
            os.remove(audio_path)
        else:
            return audio_path


# =====================================================
# AVAILABLE MODELS
# =====================================================

def list_available_models() -> list:
    """Return list of available model names."""
    return list(VITS_PIPER_MODELS.keys())


if __name__ == "__main__":
    import argparse
    
    EPILOG = """

EXAMPLES
========

  Basic Usage:
    python voice_helper.py --list
        Show all available voice models

    python voice_helper.py --generate --text "Hello world"
        Generate audio using default English (US) male voice

  Using Different Voices:
    python voice_helper.py --generate --model hi_IN_pratham --text "Namaste dost"
        Generate audio using Hindi male voice

    python voice_helper.py --generate --model ru_RU_irina --text "Privet"
        Generate audio using Russian female voice

  Speed Control:
    python voice_helper.py --generate --text "Fast speech" --speed 1.5
        Generate audio 50% faster than normal

    python voice_helper.py --generate --text "Slow speech" --speed 0.7
        Generate audio 30% slower than normal

  Save to File:
    python voice_helper.py --generate --text "Hello" --output "D:/audio/hello.wav"
        Save generated audio to specific path

  Preload Mode (Fast Switching):
    python voice_helper.py --preload --generate --model en_US_male --text "Hi"
        Load ALL voice models into memory first, then generate

AVAILABLE MODELS
================
  en_US_male       - English (US) Male
  en_US_libritts   - English (US) LibriTTS
  es_ES_carlfm     - Spanish (Spain) Male
  hi_IN_pratham    - Hindi Male
  hi_IN_priyamvada - Hindi Female
  ru_RU_irina      - Russian Female
"""
    
    parser = argparse.ArgumentParser(
        description="Voice Helper CLI - Text-to-Speech Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EPILOG
    )
    
    # Actions
    parser.add_argument("--list", action="store_true", 
                        help="List all available TTS voice models")
    parser.add_argument("--generate", action="store_true", 
                        help="Generate audio from text")
    parser.add_argument("--preload", action="store_true", 
                        help="Preload ALL models (uses more RAM, instant switching)")
    
    # Options
    parser.add_argument("--model", type=str, default="en_US_male", 
                        help="Voice model to use (default: en_US_male)")
    parser.add_argument("--text", type=str, default=None, 
                        help="Text to synthesize into speech")
    parser.add_argument("--speed", type=float, default=1.0, 
                        help="Speech speed multiplier (default: 1.0)")
    parser.add_argument("--output", type=str, default=None, 
                        help="Output .wav file path (default: temp file)")
    parser.add_argument("--debug", action="store_true", 
                        help="Use test text if --text not provided")

    # testing purpose
    parser.add_argument("--test", action="store_true", 
                        help="Test the voice helper")
    
    args = parser.parse_args()
    
    # Handle --list
    if args.list:
        print("Available models:", list_available_models())
    
    # Handle --generate
    if args.generate:
        if args.preload:
            voice_helper = VoiceHelper(args.model, preload_all=True)
        else:
            voice_helper = VoiceHelper(args.model)
        
        if args.text is None and not args.debug:
            raise ValueError("Text cannot be None (use --debug for test text)")
        
        output_path = voice_helper.synthesize_audio(args.text, args.speed, args.output, args.debug)
        print(output_path)  # Output path for subprocess capture

    # Handle --test
    if args.test:
        print("Voice Helper - Multi-Voice Narrative Test")
        print("=" * 50)
        
        # Preload all models for instant switching
        voice_helper = VoiceHelper("en_US_male", preload_all=True)
        
        # Narrative with different voices and character names
        print("\n[1/6] Alex - English (US) Male")
        voice_helper.load_model("en_US_male")
        voice_helper.synthesize_and_play("Hey there! I'm Alex. Welcome to Neural Citadel voice engine.", cleanup=True)
        
        print("\n[2/6] Emma - English (US) LibriTTS")
        voice_helper.load_model("en_US_libritts")
        voice_helper.synthesize_and_play("Hello! I'm Emma. I love narrating audiobooks.", cleanup=True)
        
        print("\n[3/6] Arjun - Hindi Pratham Male")
        voice_helper.load_model("hi_IN_pratham")
        voice_helper.synthesize_and_play("नमस्ते! मैं अर्जुन हूं।", cleanup=True)
        
        print("\n[4/6] Priya - Hindi Female")
        voice_helper.load_model("hi_IN_priyamvada")
        voice_helper.synthesize_and_play("नमस्ते! मेरा नाम प्रिया है।", cleanup=True)
        
        print("\n[5/6] Natasha - Russian Female")
        voice_helper.load_model("ru_RU_irina")
        voice_helper.synthesize_and_play("Privet! Menya zovut Natasha.", cleanup=True)
        
        print("\n[6/6] Carlos - Spanish Male")
        voice_helper.load_model("es_ES_carlfm")
        voice_helper.synthesize_and_play("Hola amigos! Me llamo Carlos.", cleanup=True)
        
        print("\n" + "=" * 50)
        print("All 6 voice tests completed successfully!")
        voice_helper.unload_all_models()