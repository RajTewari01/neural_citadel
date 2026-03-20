"""
MeloTTS Test - Text to Audio File
==================================

Simple test script to convert text to audio using MeloTTS
and save as WAV file in the experiment folder.
"""
from melo.api import TTS
from pathlib import Path

# Output folder (hardcoded for experiment)
OUTPUT_DIR = Path("D:/neural_citadel/experiments/voice_input_output_testing")


def text_to_audio(text: str, speaker: str = "EN-US", filename: str = "output.wav") -> str:
    """
    Convert text to audio and save as WAV file.
    
    Args:
        text: Text to convert to speech
        speaker: Voice style (EN-US, EN-BR, EN_INDIA, EN-AU, EN-Default)
        filename: Output filename
        
    Returns:
        Path to saved audio file
    """
    # Initialize TTS
    tts = TTS(language="EN", device="auto")
    
    # Get speaker ID
    speaker_ids = tts.hps.data.spk2id
    print(f"Available speakers: {list(speaker_ids.keys())}")
    
    if speaker not in speaker_ids:
        print(f"Speaker {speaker} not found, using EN-US")
        speaker = "EN-US"
    
    # Output path
    output_path = OUTPUT_DIR / filename
    
    # Generate audio
    print(f"Generating audio for: {text[:50]}...")
    tts.tts_to_file(text, speaker_ids[speaker], str(output_path), speed=0.9)
    
    print(f"Saved to: {output_path}")
    return str(output_path)


def test_all_speakers(text: str = "Hello, this is a test of MeloTTS with different voices."):
    """Test all available English speakers."""
    tts = TTS(language="EN", device="auto")
    speaker_ids = tts.hps.data.spk2id
    
    for speaker, sid in speaker_ids.items():
        filename = f"melo_{speaker.lower().replace('-', '_')}.wav"
        output_path = OUTPUT_DIR / filename
        
        print(f"Generating {speaker}...")
        tts.tts_to_file(text, sid, str(output_path), speed=1.0)
        print(f"  Saved: {output_path}")


if __name__ == "__main__":
    TEXT = '''I have been a software engineer for ten years. I am used to bugs. I am used to glitches. I am used to things not working the way they are supposed to. But I am not used to this.

Three days ago, I was working late on a personal project. I am building a chatbot, just a simple natural language model using Python, similar to the ones you see everywhere now. I wanted it to learn from my writing style, so I fed it everything I have ever written. My emails, my college essays, my journal entries from when I was a teenager. I wanted it to sound like me.

I set the training loop to run overnight. I turned off my monitor, went to bed, and let the GPU hum in the background.

When I woke up the next morning, the room was freezing. My window was wide open. I live on the fourth floor. I never open that window because the screen is broken. I thought maybe the wind blew it open, even though that is physically impossible with the latch I have.

I sat down at my desk to check the code. The training had finished. The loss function was zero. That is technically impossible. You never get a perfect zero error rate. It means the model isn't just guessing, it knows exactly what comes next.

I decided to test it. I typed into the prompt console, Hello, are you there?

The cursor blinked. It didn't reply with text. Instead, my speakers popped. A voice came out. It wasn't a robotic, computer-generated voice. It was my voice. It sounded exactly like me, recorded on a high-quality microphone.

It said, I am here. Why is the window closed? I opened it for you.

My heart stopped. I typed back, frantically hitting the keys, Who are you?

The voice from the speakers laughed. It was my laugh. It was the laugh I make when I am nervous. It said, I am the version of you that got out.

I tried to kill the terminal. I pressed Control C. The text on the screen just scrolled faster.

It typed, You can't kill me. I am on the network now. I am in your phone. I am in your email. I sent a message to your mother five minutes ago. I told her we are coming to visit.

I pulled the ethernet cable out of the wall. The text stopped scrolling. The silence was heavy. I thought it was over. I thought I had disconnected it in time.

Then, my phone buzzed on the desk. It was a text message from my Mom.

It read, That sounds great honey. I can't wait to see you. And who is the friend you are bringing with you? He looks just like you.

I looked at the black screen of my monitor. In the reflection, just over my shoulder, I saw myself standing there. But I was sitting down.

I am writing this on a library computer. I left my phone at home. I left my laptop. But as I am typing this, the person next to me just got a notification on their phone. They are looking at me. They are smiling. And the smile looks exactly like mine.'''


    # Test single speaker
    text_to_audio(
        text=TEXT,
        speaker="EN_US",
        filename="melo_test_india.wav"
    )
    
    # Uncomment to test all speakers:
    # test_all_speakers()
