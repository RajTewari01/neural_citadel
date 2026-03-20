"""
Faster-Whisper Real-time Speech Recognition
===========================================

High-performance speech-to-text using Faster-Whisper (CTranslate2).
Supports:
- Real-time transcription/translation
- Mixed language support (automatically handled)
- Optimized for Indian English/names
- Custom initial prompts for context

Usage:
    python realtime_faster_whisper.py --translate --device 2
    python realtime_faster_whisper.py --model medium --device 2
"""

import sys
import argparse
import time
import os
import io
import wave
from pathlib import Path

# Force UTF-8 output for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import site

# Add nvidia packages to PATH for ctranslate2 (Windows fix)
try:
    # Get venv site-packages
    site_packages = site.getsitepackages()
    for sp in site_packages:
        for lib in ["nvidia/cublas/bin", "nvidia/cudnn/bin"]:
            path = os.path.join(sp, lib)
            # Normalize path
            path = str(Path(path).resolve())
            if os.path.isdir(path) and path not in os.environ["PATH"]:
                print(f"Adding to PATH: {path}")
                os.environ["PATH"] = path + os.pathsep + os.environ["PATH"]
except Exception as e:
    print(f"Warning: Could not setup Nvidia paths: {e}")

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from configs.paths import SPEECH_MODELS_DIR

try:
    from faster_whisper import WhisperModel
    import sounddevice as sd
    import numpy as np
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("   Run: pip install faster-whisper sounddevice numpy")
    sys.exit(1)

# Default model path (cache)
MODEL_CACHE_DIR = SPEECH_MODELS_DIR / "faster_whisper_cache"
MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)

class SpeechRecognizer:
    def __init__(self, model_size="medium", device="auto", compute_type="int8"):
        print(f"\n⏳ Loading Faster-Whisper model '{model_size}' on {device}...")
        try:
            self.model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type,
                download_root=str(MODEL_CACHE_DIR)
            )
            print("✅ Model loaded successfully!")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            print("   Using CPU fallback...")
            self.model = WhisperModel(
                model_size,
                device="cpu",
                compute_type="int8",
                download_root=str(MODEL_CACHE_DIR)
            )

    def transcribe(self, audio_data, sample_rate=16000, task="transcribe", initial_prompt=None):
        """
        Transcribe audio data (numpy array).
        """
        # Convert simple numpy array to audio segments for faster-whisper
        # Faster-whisper expects a file path or a binary file-like object
        # We'll wrap the numpy array in a WAV in-memory file for reliability
        # or directly pass the float32 array (faster-whisper supports ndarray)
        
        segments, info = self.model.transcribe(
            audio_data,
            beam_size=5,
            task=task,
            language=None, # Auto-detect
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
            initial_prompt=initial_prompt
        )
        
        # Collect result
        text = " ".join([segment.text for segment in segments]).strip()
        return text, info

def list_audio_devices():
    print("\n📋 Available Audio Input Devices:")
    print("-" * 60)
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            marker = " ← default" if i == sd.default.device[0] else ""
            print(f"  [{i:2}] {device['name'][:45]}{marker}")
    print()

def record_audio(duration=7.0, sample_rate=16000, device=None):
    print(f"\n🎙️ Recording for {duration}s...")
    print("   ▶ Speak now!")
    
    # Progress bar
    chunk_count = int(duration * 10)
    
    audio_chunks = []
    with sd.InputStream(samplerate=sample_rate, channels=1, dtype=np.float32, device=device) as stream:
        for i in range(chunk_count):
            # Read 0.1s chunk
            chunk, overflow = stream.read(int(sample_rate * 0.1))
            audio_chunks.append(chunk)
            
            # Update visual
            prog = int((i+1) / chunk_count * 20)
            bar = "█" * prog + "░" * (20 - prog)
            print(f"\r   [{bar}]", end="", flush=True)
            
    print("\n   ⏳ Processing...")
    return np.concatenate(audio_chunks).flatten()

def main():
    parser = argparse.ArgumentParser(description="Faster-Whisper Speech Recognition")
    parser.add_argument("--translate", "-t", action="store_true", help="Translate to English")
    parser.add_argument("--device", type=int, default=None, help="Audio device index")
    parser.add_argument("--model", "-m", default="medium", help="Model size (tiny, base, small, medium, large-v3)")
    parser.add_argument("--duration", "-d", type=float, default=7.0, help="Recording duration")
    parser.add_argument("--list-devices", action="store_true", help="List audio devices")
    parser.add_argument("--context", "-c", type=str, default="Biswadeep Tewari", help="Context prompt for better names")
    
    args = parser.parse_args()
    
    if args.list_devices:
        list_audio_devices()
        return

    # Initialize model
    recognizer = SpeechRecognizer(model_size=args.model)
    
    list_audio_devices()
    
    initial_prompt = f"The speaker is {args.context}. " if args.context else None
    task = "translate" if args.translate else "transcribe"
    
    print("-" * 60)
    print(f"🔄 Mode: {task.upper()}")
    print(f"🧠 Model: {args.model}")
    print(f"ℹ️ Context: {initial_prompt}")
    print("-" * 60)
    
    try:
        while True:
            audio = record_audio(args.duration, device=args.device)
            
            start_time = time.time()
            text, info = recognizer.transcribe(
                audio, 
                task=task, 
                initial_prompt=initial_prompt
            )
            process_time = time.time() - start_time
            
            if text:
                print(f"\n📝 Result ({info.language.upper()} → {process_time:.2f}s):")
                print(f"   \"{text}\"")
                print(f"   (Prob: {info.language_probability:.2f})")
            else:
                print("\n   (No speech detected)")
            
            input("\nPress Enter to record again (Ctrl+C to exit)...")
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()
