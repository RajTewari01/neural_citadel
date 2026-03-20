"""
Voice Pipeline - VAD + Whisper + TinyLlama + MeloTTS
=====================================================

Main orchestrator for voice input/output testing.
- Listens until user STOPS speaking (VAD silence detection) OR 25 sec max
- Transcribes with Faster Whisper (translates to English if Hindi)
- Generates response via TinyLlama subprocess (coreagentvenv)
- Speaks response with MeloTTS (English)

Usage: python voice_pipeline.py [--device N]
"""
import sys
import os
import time
import subprocess
import threading
import numpy as np
from pathlib import Path
from collections import deque

# Fix Windows console encoding for Hindi/Unicode
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Audio settings
SAMPLE_RATE = 16000
MAX_RECORD_SECONDS = 25
SILENCE_THRESHOLD_MS = 800  # Stop recording after 800ms of silence

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
COREAGENT_PYTHON = PROJECT_ROOT / "venvs" / "env" / "coreagentvenv" / "Scripts" / "python.exe"
TINYLLAMA_SERVER = Path(__file__).parent / "tinyllama_server.py"
WHISPER_CACHE = PROJECT_ROOT / "assets" / "models" / "speech" / "faster_whisper_cache"

# Global LLM process
llm_process = None

# Global TTS model (pre-loaded)
tts_model = None
tts_speaker_id = None

# Global audio buffer
audio_buffer = []
is_recording = False
voice_ended = threading.Event()


def setup_vad():
    """Initialize Silero VAD."""
    from silero_vad import load_silero_vad
    model = load_silero_vad()
    return model


def setup_whisper():
    """Initialize Faster Whisper (CPU mode to save VRAM for other models)."""
    from faster_whisper import WhisperModel
    model = WhisperModel(
        "small",  # Use small for speed
        device="cpu",  # CPU mode - no CUDA dependency issues
        compute_type="int8",  # Efficient on CPU
        download_root=str(WHISPER_CACHE)
    )
    return model


def record_until_silence(vad_model, device=None):
    """
    Record audio until:
    1. User STARTS speaking, then STOPS (silence detected for SILENCE_THRESHOLD_MS)
    2. OR max recording time reached (MAX_RECORD_SECONDS)
    """
    import sounddevice as sd
    import torch
    
    global audio_buffer, is_recording, voice_ended
    
    audio_buffer = []
    is_recording = True
    voice_ended.clear()
    
    silence_start = None
    recording_start = time.time()
    speech_detected = False  # Must detect speech first before triggering end
    
    print("\n[Listening...] Speak now (max 25 sec)")
    
    def audio_callback(indata, frames, time_info, status):
        nonlocal silence_start, speech_detected
        
        if not is_recording:
            return
        
        # Add to buffer
        audio_buffer.append(indata.copy())
        
        # Check VAD
        audio_chunk = indata[:, 0].astype(np.float32)
        tensor = torch.from_numpy(audio_chunk)
        
        # Silero VAD expects 512 samples at 16kHz
        if len(tensor) >= 512:
            speech_prob = vad_model(tensor[:512], SAMPLE_RATE).item()
            
            # Lower threshold for better sensitivity
            if speech_prob > 0.3:
                # Voice detected!
                speech_detected = True
                silence_start = None
                print(".", end="", flush=True)
            else:
                # Silence - only trigger end if we already detected speech
                if speech_detected:
                    if silence_start is None:
                        silence_start = time.time()
                    elif (time.time() - silence_start) * 1000 > SILENCE_THRESHOLD_MS:
                        # Enough silence after speech - stop recording
                        voice_ended.set()
    
    # Start recording
    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype=np.float32,
        device=device,
        blocksize=512,
        callback=audio_callback
    ):
        while is_recording:
            # Check timeout
            if time.time() - recording_start > MAX_RECORD_SECONDS:
                print("\n[Max time reached]")
                break
            
            # Check if voice ended (only after speech was detected)
            if voice_ended.wait(timeout=0.1):
                print("\n[Speech ended - silence detected]")
                break
    
    is_recording = False

    
    if audio_buffer:
        return np.concatenate(audio_buffer, axis=0)
    return None


def transcribe(whisper_model, audio: np.ndarray) -> str:
    """Transcribe audio using Faster Whisper (translates to English)."""
    print("[Transcribing...]")
    
    # Use task='translate' to translate any language to English
    # This way TinyLlama and MeloTTS (English) can understand/speak
    segments, info = whisper_model.transcribe(
        audio.flatten(),
        beam_size=5,
        task='translate',  # Translate Hindi/any language to English
        vad_filter=True
    )
    
    text = " ".join(seg.text for seg in segments).strip()
    print(f"[You said (translated)]: {text}")
    return text


def setup_llm():
    """Start persistent TinyLlama server in background."""
    global llm_process
    
    print("[LLM] Starting TinyLlama server...")
    llm_process = subprocess.Popen(
        [str(COREAGENT_PYTHON), str(TINYLLAMA_SERVER)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    # Wait for READY signal
    for line in llm_process.stdout:
        line = line.strip()
        if line == "LOADING":
            print("[LLM] Loading model...")
        elif line == "READY":
            print("[LLM] Model loaded and ready!")
            break
    
    return llm_process


def generate_response(prompt: str) -> str:
    """Send prompt to persistent TinyLlama server."""
    global llm_process
    
    if llm_process is None:
        return "LLM not initialized"
    
    print("[Generating response...]")
    
    try:
        # Send prompt
        llm_process.stdin.write(prompt + "\n")
        llm_process.stdin.flush()
        
        # Read response
        for line in llm_process.stdout:
            line = line.strip()
            if line.startswith("RESPONSE:"):
                response = line[9:]
                print(f"[AI]: {response}")
                return response
        
        return "No response received"
        
    except Exception as e:
        return f"Error: {e}"


def shutdown_llm():
    """Shutdown TinyLlama server."""
    global llm_process
    if llm_process:
        llm_process.stdin.write("QUIT\n")
        llm_process.stdin.flush()
        llm_process.wait(timeout=5)
        llm_process = None


def setup_tts():
    """Pre-load Sherpa TTS at startup."""
    from sherpa_tts import load_voice
    
    print("[TTS] Loading Sherpa ONNX TTS (Hindi-English)...")
    load_voice("hi_female")  # Pre-load Hindi female voice
    load_voice("en_male")    # Pre-load English male voice
    print("[TTS] Ready! Voices: hi_female, en_male")


def speak(text: str, voice: str = "en_male"):
    """Speak text using Sherpa ONNX TTS."""
    from sherpa_tts import speak as sherpa_speak
    
    print(f"[Speaking ({voice})]: {text[:50]}..." if len(text) > 50 else f"[Speaking ({voice})]: {text}")
    
    try:
        sherpa_speak(text, voice=voice, play_audio=True)
    except Exception as e:
        print(f"[TTS Error]: {e}")
        print(f"[Would say]: {text}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Voice Pipeline")
    parser.add_argument("--device", type=int, default=None, help="Audio input device")
    args = parser.parse_args()
    
    print("=" * 60)
    print("Voice Pipeline - VAD + Whisper + TinyLlama")
    print("=" * 60)
    print("Initializing...")
    
    # Setup models
    setup_llm()      # TinyLlama LLM
    setup_tts()      # MeloTTS
    
    vad_model = setup_vad()
    whisper_model = setup_whisper()
    
    print("Ready! Press Ctrl+C to exit.\n")
    
    try:
        while True:
            # Record until silence
            audio = record_until_silence(vad_model, device=args.device)
            
            if audio is None or len(audio) < SAMPLE_RATE * 0.5:
                print("[Too short, ignored]")
                continue
            
            # Transcribe
            text = transcribe(whisper_model, audio)
            
            if not text or len(text) < 2:
                print("[No speech detected]")
                continue
            
            # Generate response
            response = generate_response(text)
            
            # Speak response
            speak(response)
            
            print()  # Blank line before next loop
            
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        shutdown_llm()
        print("Exiting...")


if __name__ == "__main__":
    main()
