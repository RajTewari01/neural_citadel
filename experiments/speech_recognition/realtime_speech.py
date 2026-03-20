"""
Sherpa-ONNX Multilingual Speech Recognition + Translation
==========================================================

Real-time speech-to-text with:
- Mixed language support (code-switching: English + Bengali + Hindi, etc.)
- Auto-translation to English
- Custom microphone selection
- Improved accuracy settings

Usage:
    # Translate mixed languages to English, using mic 2
    python realtime_speech.py --translate --device 2
    
    # Longer recording for better accuracy
    python realtime_speech.py --translate --device 2 -d 8
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from configs.paths import SPEECH_MODELS_DIR

try:
    import sherpa_onnx
    import sounddevice as sd
    import numpy as np
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("   Run: pip install sherpa-onnx sounddevice numpy")
    sys.exit(1)

# Model paths
WHISPER_MODEL_DIR = SPEECH_MODELS_DIR / "sherpa-onnx-whisper-small"
VAD_MODEL = SPEECH_MODELS_DIR / "silero_vad.onnx"

# Supported languages
LANGUAGES = {
    "auto": "Auto-detect",
    "en": "English",
    "bn": "Bengali",
    "hi": "Hindi",
    "ru": "Russian",
    "es": "Spanish",
    "ja": "Japanese",
}


def create_recognizer(language: str = "auto", translate: bool = False):
    """
    Create Whisper recognizer with optimized settings.
    """
    
    # Use regular ONNX for better accuracy (not int8)
    encoder = str(WHISPER_MODEL_DIR / "small-encoder.onnx")
    decoder = str(WHISPER_MODEL_DIR / "small-decoder.onnx")
    tokens = str(WHISPER_MODEL_DIR / "small-tokens.txt")
    
    # Verify files exist
    for f in [encoder, decoder, tokens]:
        if not Path(f).exists():
            print(f"❌ Missing model file: {f}")
            sys.exit(1)
    
    # Task: "transcribe" or "translate" (translate always outputs English)
    task = "translate" if translate else "transcribe"
    
    # For auto-detect, don't specify language
    lang = "" if language == "auto" else language
    
    recognizer = sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=encoder,
        decoder=decoder,
        tokens=tokens,
        language=lang,
        task=task,
        num_threads=4,
        decoding_method="greedy_search",  # More accurate for names
    )
    
    return recognizer


def list_audio_devices():
    """List available audio input devices."""
    print("\n📋 Available Audio Input Devices:")
    print("-" * 60)
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            marker = " ← default" if i == sd.default.device[0] else ""
            print(f"  [{i:2}] {device['name'][:45]}{marker}")
    print()


def record_and_transcribe(recognizer, duration: float = 7.0, sample_rate: int = 16000, device: int = None):
    """Record audio and transcribe/translate with visual feedback."""
    
    print(f"\n🎙️ Recording for {duration} seconds...")
    print("   ▶ Speak clearly now!")
    
    # Record with progress indicator
    audio_chunks = []
    chunk_size = int(sample_rate * 0.5)  # 0.5 second chunks
    total_chunks = int(duration * 2)
    
    for i in range(total_chunks):
        chunk = sd.rec(chunk_size, samplerate=sample_rate, channels=1, dtype=np.float32, device=device)
        sd.wait()
        audio_chunks.append(chunk)
        # Progress bar
        progress = "█" * (i + 1) + "░" * (total_chunks - i - 1)
        print(f"\r   [{progress}]", end="", flush=True)
    
    print("\n   ⏳ Processing...")
    
    # Combine all chunks
    audio = np.concatenate(audio_chunks).flatten()
    
    # Normalize audio for better recognition
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val * 0.95
    
    # Create stream for recognition
    stream = recognizer.create_stream()
    stream.accept_waveform(sample_rate, audio)
    recognizer.decode_stream(stream)
    
    result = stream.result.text.strip()
    return result


def continuous_recognition(recognizer, sample_rate: int = 16000, device: int = None):
    """Continuous real-time recognition with VAD-like behavior."""
    print("\n🎙️ Continuous listening mode")
    print("   Speak naturally, mix languages!")
    print("   Press Ctrl+C to stop")
    print("-" * 60)
    
    chunk_duration = 3.0  # 3 second chunks for better context
    
    try:
        while True:
            # Record chunk
            audio = sd.rec(
                int(chunk_duration * sample_rate),
                samplerate=sample_rate,
                channels=1,
                dtype=np.float32,
                device=device
            )
            sd.wait()
            
            # Check if there's actual audio (not just silence)
            audio_flat = audio.flatten()
            rms = np.sqrt(np.mean(audio_flat**2))
            
            if rms > 0.01:  # Voice detected
                # Normalize
                max_val = np.max(np.abs(audio_flat))
                if max_val > 0:
                    audio_flat = audio_flat / max_val * 0.95
                
                # Recognize
                stream = recognizer.create_stream()
                stream.accept_waveform(sample_rate, audio_flat)
                recognizer.decode_stream(stream)
                
                result = stream.result.text.strip()
                if result and len(result) > 1:  # Ignore single chars
                    print(f"\n📝 {result}")
            else:
                print(".", end="", flush=True)  # Show we're listening
                    
    except KeyboardInterrupt:
        pass


def main():
    parser = argparse.ArgumentParser(
        description="Sherpa-ONNX Multilingual Speech Recognition + Translation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Mixed English+Bengali+Hindi → English, mic 2
  python realtime_speech.py --translate --device 2
  
  # Longer recording for names/accuracy
  python realtime_speech.py --translate --device 2 -d 8
  
  # Continuous mode
  python realtime_speech.py --translate --device 2 --continuous
        """
    )
    parser.add_argument("--language", "-l", default="auto", choices=LANGUAGES.keys(),
                        help="Language code (default: auto-detect)")
    parser.add_argument("--translate", "-t", action="store_true",
                        help="Translate to English (handles mixed languages!)")
    parser.add_argument("--duration", "-d", type=float, default=7.0,
                        help="Recording duration in seconds (default: 7)")
    parser.add_argument("--device", type=int, default=None,
                        help="Audio input device index")
    parser.add_argument("--continuous", "-c", action="store_true",
                        help="Continuous listening mode")
    parser.add_argument("--list-devices", action="store_true",
                        help="List audio devices and exit")
    args = parser.parse_args()
    
    print("=" * 60)
    print("  SHERPA-ONNX MULTILINGUAL SPEECH RECOGNITION")
    print("=" * 60)
    
    if args.list_devices:
        list_audio_devices()
        return
    
    # Verify model exists
    if not WHISPER_MODEL_DIR.exists():
        print(f"❌ Whisper model not found at: {WHISPER_MODEL_DIR}")
        sys.exit(1)
    
    # Show configuration
    lang_name = LANGUAGES.get(args.language, args.language)
    print(f"\n🌐 Language: {lang_name}")
    print(f"🔄 Mode: {'TRANSLATE to English' if args.translate else 'TRANSCRIBE (original)'}")
    if args.device is not None:
        print(f"🎤 Microphone: Device {args.device}")
    print(f"⏱️ Duration: {args.duration}s per recording")
    
    # Create recognizer
    print("\n⏳ Loading Whisper model...")
    recognizer = create_recognizer(args.language, args.translate)
    print("✅ Ready!")
    
    list_audio_devices()
    
    if args.continuous:
        continuous_recognition(recognizer, device=args.device)
    else:
        print("-" * 60)
        print("Tip: Speak clearly and wait for the full recording")
        print("-" * 60)
        
        try:
            while True:
                result = record_and_transcribe(recognizer, args.duration, device=args.device)
                if result:
                    print(f"\n✅ Result: {result}\n")
                else:
                    print("\n   (No speech detected)\n")
                
                input("Press Enter to record again (Ctrl+C to exit)...")
        except KeyboardInterrupt:
            pass
    
    print("\n\n👋 Goodbye!")


if __name__ == "__main__":
    main()
