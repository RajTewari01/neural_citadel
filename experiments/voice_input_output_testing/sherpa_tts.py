"""
Sherpa ONNX TTS - Hindi-English Voice Synthesis
================================================

Wrapper for Sherpa ONNX TTS with support for Hindi and English voices.
Uses piper VITS models for offline, fast TTS.
"""
from sherpa_onnx import OfflineTts, OfflineTtsConfig, OfflineTtsModelConfig, OfflineTtsVitsModelConfig
from pathlib import Path
import tempfile
import struct
import wave
import os

# Model paths
LANG_DIR = Path("D:/neural_citadel/assets/models/voice/Language")

# Available models
MODELS = {
    "hi_male": ("vits-piper-hi_IN-pratham-medium", "hi_IN-pratham-medium.onnx"),
    "hi_female": ("vits-piper-hi_IN-priyamvada-medium", "hi_IN-priyamvada-medium.onnx"),
    "en_male": ("vits-piper-en_US-hfc_male-medium", "en_US-hfc_male-medium.onnx"),
    "en_female": ("vits-piper-en_US-libritts_r-medium", "en_US-libritts_r-medium.onnx"),
}

# Global model cache
TTS_CACHE = {}


def _init_engine(model_name: str) -> OfflineTts:
    """Initialize a Sherpa TTS engine."""
    model_dir, model_file = MODELS[model_name]
    model_path = LANG_DIR / model_dir
    
    vits_model = OfflineTtsVitsModelConfig(
        model=str(model_path / model_file),
        tokens=str(model_path / "tokens.txt"),
        lexicon=str(model_path / "lexicon.txt"),
        data_dir=str(model_path / "espeak-ng-data")
    )
    config = OfflineTtsConfig(model=OfflineTtsModelConfig(vits=vits_model))
    return OfflineTts(config)


def load_voice(voice: str = "hi_female"):
    """Pre-load a voice model."""
    global TTS_CACHE
    if voice not in TTS_CACHE:
        print(f"[TTS] Loading {voice}...")
        TTS_CACHE[voice] = _init_engine(voice)
        print(f"[TTS] {voice} ready!")
    return TTS_CACHE[voice]


def speak(text: str, voice: str = "hi_female", play_audio: bool = True):
    """Generate and play speech."""
    import sounddevice as sd
    import numpy as np
    
    # Load model if not cached
    engine = load_voice(voice)
    
    # Generate audio
    audio = engine.generate(text, speed=1.0, sid=0)
    
    # Convert to numpy array
    samples = np.array([s for s in audio.samples], dtype=np.float32)
    
    if play_audio:
        sd.play(samples, samplerate=audio.sample_rate)
        sd.wait()
    
    return samples, audio.sample_rate


def speak_to_file(text: str, voice: str = "hi_female") -> str:
    """Generate speech and save to temp file."""
    engine = load_voice(voice)
    audio = engine.generate(text, speed=1.0, sid=0)
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        output_file = f.name
    
    with wave.open(output_file, 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(audio.sample_rate)
        samples_bytes = struct.pack(f'{len(audio.samples)}h', 
                                    *[int(s * 32767) for s in audio.samples])
        f.writeframes(samples_bytes)
    
    return output_file


if __name__ == "__main__":
    print("Testing Sherpa TTS...")
    speak("Hello, my name is Raj", voice="en_male")
    speak("नमस्ते, मेरा नाम राज है", voice="hi_female")
