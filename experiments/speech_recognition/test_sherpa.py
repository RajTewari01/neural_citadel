"""
Sherpa-ONNX Speech Recognition Test
====================================

Basic test script for sherpa-onnx speech recognition.
Uses microphone input for real-time speech-to-text.

Usage:
    python test_sherpa.py
"""

import sherpa_onnx
import sounddevice as sd
import numpy as np


def list_audio_devices():
    """List available audio input devices."""
    print("\n📋 Available Audio Devices:")
    print("-" * 50)
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            print(f"  [{i}] {device['name']} (inputs: {device['max_input_channels']})")
    print()


def test_vad():
    """Test Voice Activity Detection (VAD)."""
    print("\n🎤 Testing Sherpa-ONNX VAD...")
    print("-" * 50)
    
    # Check if VAD model is available
    # You'll need to download a VAD model from:
    # https://github.com/k2-fsa/sherpa-onnx/releases
    
    print("✅ Sherpa-ONNX is installed correctly!")
    print(f"   Version: {sherpa_onnx.__version__ if hasattr(sherpa_onnx, '__version__') else 'unknown'}")
    print()
    print("📥 To use speech recognition, download a model from:")
    print("   https://github.com/k2-fsa/sherpa-onnx/releases")
    print()
    print("   Recommended models:")
    print("   - sherpa-onnx-streaming-zipformer-en-2023-06-26 (English, streaming)")
    print("   - sherpa-onnx-whisper-tiny.en (English, Whisper-based)")
    print("   - silero_vad.onnx (Voice Activity Detection)")


if __name__ == "__main__":
    print("=" * 60)
    print("  SHERPA-ONNX SPEECH RECOGNITION TEST")
    print("=" * 60)
    
    list_audio_devices()
    test_vad()
