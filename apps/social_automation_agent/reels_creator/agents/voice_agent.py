"""
Voice Agent - Automated voice generation pipeline.
==================================================

Features:
    - Local/APIs integration
    - AI-generated voiceovers
    - Customizable voice, language, accent, tone
    - Text-to-speech conversion
    - Multi-platform export
"""

from pathlib import Path
import sys
_ROOT = Path(__file__).resolve().parents[4]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from apps.social_automation_agent.reels_creator.agents.base import ConfigPlatform
from typing import Optional,Literal,List,Union,Dict,Tuple
import subprocess
import requests
import tempfile
import os


class VoiceOverAgent:
    """Generate voiceovers with customizable voice, language, accent, tone."""
    def __init__(self):
        self._ROOT = Path(__file__).resolve().parents[4]
        self._VENV = ConfigPlatform.config_venv("speech_venv")
        self._SCRIPTS = self._ROOT / 'apps/social_automation_agent/reels_creator/helper_workers/offline_voice_helper.py'
    
    def generate_audio_locally(
        self,
        text: str,
        audio_speed: float = 1.0,
        model: Literal['en_US_male','en_US_libritts','es_ES_carlfm','hi_IN_pratham','hi_IN_priyamvada','ru_RU_irina'] = 'en_US_male',
        preload_all_models: bool = False,
        )->Optional[Path]:
        """Generate audio locally by using sherpa_onnx"""
        if not self._VENV.exists():raise FileNotFoundError("Cannot find the venv file path.")
        if not self._SCRIPTS.exists():raise FileNotFoundError("Cannot find the helper/bridge file path.")
        if not text:
            raise ValueError("Text cannot be empty.")

        command = [
            str(self._VENV),
            str(self._SCRIPTS),
            '--generate',
            '--text', text,
            '--speed', str(audio_speed),
            '--model', model,
        ]

        if preload_all_models:
            command.append('--preload')

        try:
            run_command = subprocess.run(
                command, 
                check=True,
                text=True,
                capture_output=True
                )
        
        except subprocess.CalledProcessError as e:
            print(f"Failed to generate audio: {e.stderr}")
            return None
        
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return None
        
        else:
            lines = run_command.stdout.strip().split('\n')

        for line in reversed(lines):
            cleaned_line = line.strip()
            if cleaned_line.endswith('.wav'):
                potential_output_path = Path(cleaned_line)
                if potential_output_path.exists():
                    return potential_output_path
        
        return None

    def generate_audio_online(self,
                            text: str, 
                            provider: str = 'voicerss',
                            voice: str = None,
                            speed: float = 1.0) -> Optional[Path]:
        """
        Generate audio using online TTS APIs.
        
        Args:
            text: Text to synthesize
            provider: 'google', 'azure', or 'voicerss'
            voice: Voice name (provider-specific)
            speed: Speech speed (1.0 = normal)
            
        Returns:
            Path to generated audio file
        """
        from dotenv import dotenv_values
        
        # Load API keys from env file
        env_path = self._ROOT / "configs/secrets/socials.env"
        secrets = dotenv_values(env_path)
        
        output_path = Path(tempfile.gettempdir()) / f"tts_online_{secrets.get(provider, 'unknown')}_{os.getpid()}.wav"
        
        if provider == 'voicerss':
            api_key = secrets.get('VOICERSS_API_KEY', '')
            if not api_key:
                raise ValueError("VOICERSS_API_KEY not set in socials.env")
            
            # VoiceRSS API - simple and free (350 req/day)
            voice = voice or 'en-us'
            url = f"http://api.voicerss.org/"
            params = {
                'key': api_key,
                'hl': voice,
                'src': text,
                'r': str(int((speed - 1) * 10)),  # -10 to 10 range
                'c': 'WAV',
                'f': '16khz_16bit_mono'
            }
            response = requests.get(url, params=params)
            
            if response.status_code == 200 and not response.content.startswith(b'ERROR'):
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print(f"[AUDIO] Generated (VoiceRSS): {output_path}")
                return output_path
            else:
                raise RuntimeError(f"VoiceRSS error: {response.content[:100]}")
                
        elif provider == 'azure':
            api_key = secrets.get('AZURE_SPEECH_API_KEY', '')
            region = secrets.get('AZURE_SPEECH_REGION', 'eastus')
            if not api_key:
                raise ValueError("AZURE_SPEECH_API_KEY not set in socials.env")
            
            # Azure Speech API
            voice = voice or 'en-US-AriaNeural'
            url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
            headers = {
                'Ocp-Apim-Subscription-Key': api_key,
                'Content-Type': 'application/ssml+xml',
                'X-Microsoft-OutputFormat': 'riff-16khz-16bit-mono-pcm'
            }
            ssml = f"""
            <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
                <voice name='{voice}'>
                    <prosody rate='{speed}'>{text}</prosody>
                </voice>
            </speak>
            """
            response = requests.post(url, headers=headers, data=ssml.encode('utf-8'))
            
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print(f"[AUDIO] Generated (Azure): {output_path}")
                return output_path
            else:
                raise RuntimeError(f"Azure error: {response.status_code} - {response.text[:100]}")
                
        elif provider == 'google':
            api_key = secrets.get('GOOGLE_CLOUD_TTS_API_KEY', '')
            if not api_key:
                raise ValueError("GOOGLE_CLOUD_TTS_API_KEY not set in socials.env")
            
            # Google Cloud TTS API
            voice = voice or 'en-US-Wavenet-D'
            url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"
            payload = {
                "input": {"text": text},
                "voice": {"languageCode": voice[:5], "name": voice},
                "audioConfig": {"audioEncoding": "LINEAR16", "speakingRate": speed}
            }
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                import base64
                audio_content = base64.b64decode(response.json()['audioContent'])
                with open(output_path, 'wb') as f:
                    f.write(audio_content)
                print(f"[AUDIO] Generated (Google): {output_path}")
                return output_path
            else:
                raise RuntimeError(f"Google error: {response.status_code} - {response.text[:100]}")
        else:
            raise ValueError(f"Unknown provider: {provider}. Use 'voicerss', 'azure', or 'google'")

if __name__ == "__main__":
    print(VoiceOverAgent().generate_audio_locally("Hello, how are you?"))

