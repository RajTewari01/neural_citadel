"""
Subtitle Generator
==================

Generate subtitles from video using OpenAI Whisper.
Supports local model loading for offline use.
"""

import gc
import sys
import logging
from pathlib import Path
from typing import Optional, Literal

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from configs.paths import WHISPER_MODELS_DIR, MOVIE_SUBTITLES_DIR, MOVIE_TEMP_DIR, ASSETS_DIR

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

WHISPER_MODELS = {
    "tiny": "openai/whisper-tiny",
    "base": "openai/whisper-base",
    "small": "openai/whisper-small",
    "medium": "openai/whisper-medium",
}


class Colors:
    YELLOW = '\033[1;33m'
    RESET = '\033[0m'
    GREEN = '\033[1;32m'
    RED = '\033[1;31m'
    CYAN = '\033[1;36m'
    BLUE = '\033[1;34m'
    MAGENTA = '\033[1;35m'


class SubtitleGenerator:
    """Generate subtitles using Whisper model."""
    
    def __init__(self, model_size: Literal["tiny", "base", "small", "medium"] = "small"):
        if not HAS_TORCH:
            raise ImportError("PyTorch not installed. Run: pip install torch")
        
        self.model_size = model_size
        self.model_id = WHISPER_MODELS.get(model_size, WHISPER_MODELS["small"])
        self.pipe = None
        
        WHISPER_MODELS_DIR.mkdir(parents=True, exist_ok=True)
        MOVIE_SUBTITLES_DIR.mkdir(parents=True, exist_ok=True)
        MOVIE_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f'{Colors.MAGENTA}{"Subtitle Generator Ready".center(50, "-")}{Colors.RESET}')
        print(f"   Device: {self.device.upper()}")
        
        self.local_model_path = self._find_local_model()
        if self.local_model_path:
            print(f"   Model: Local ({self.local_model_path.name})")
        else:
            print(f"   Model: {self.model_id} (HuggingFace)")
    
    def _find_local_model(self) -> Optional[Path]:
        """Find local model in assets directories."""
        if WHISPER_MODELS_DIR.exists():
            for item in WHISPER_MODELS_DIR.iterdir():
                if item.is_dir() and self.model_size in item.name:
                    return item
        if ASSETS_DIR.exists():
            for item in ASSETS_DIR.iterdir():
                if item.is_dir() and "whisper" in item.name.lower() and self.model_size in item.name:
                    return item
        return None
    
    def _load_model(self):
        """Lazy load model."""
        if self.pipe is not None:
            return
        
        print(f"\n{Colors.CYAN}📦 Loading Whisper model...{Colors.RESET}")
        
        try:
            from transformers import pipeline
            
            model_path = str(self.local_model_path) if self.local_model_path else self.model_id
            
            self.pipe = pipeline(
                "automatic-speech-recognition",
                model=model_path,
                device=0 if self.device == "cuda" else -1,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                chunk_length_s=30,
            )
            print(f"{Colors.GREEN}✅ Model loaded{Colors.RESET}")
        except ImportError:
            print(f"{Colors.RED}❌ Missing: transformers, torch{Colors.RESET}")
            raise
        except Exception as e:
            print(f"{Colors.RED}❌ Failed to load model: {e}{Colors.RESET}")
            raise
    
    def _extract_audio(self, video_path: Path) -> Path:
        """Extract audio from video file."""
        audio_path = MOVIE_TEMP_DIR / f"{video_path.stem}.wav"
        
        print(f"{Colors.CYAN}🎵 Extracting audio...{Colors.RESET}")
        
        try:
            from moviepy.video.io.VideoFileClip import VideoFileClip
            clip = VideoFileClip(str(video_path))
            clip.audio.write_audiofile(str(audio_path), fps=16000, nbytes=2, codec='pcm_s16le', verbose=False, logger=None)
            clip.close()
            print(f"{Colors.GREEN}✅ Audio extracted{Colors.RESET}")
            return audio_path
        except Exception as e:
            print(f"{Colors.RED}❌ Audio extraction failed: {e}{Colors.RESET}")
            raise
    
    def _format_srt(self, result: dict) -> str:
        """Convert transcription to SRT format."""
        srt_content = []
        chunks = result.get('chunks', [])
        
        if not chunks:
            # Fallback: single chunk
            srt_content.append("1")
            srt_content.append("00:00:00,000 --> 00:05:00,000")
            srt_content.append(result.get('text', ''))
            srt_content.append("")
            return '\n'.join(srt_content)
        
        for i, chunk in enumerate(chunks, 1):
            start, end = chunk.get('timestamp', (0, 0))
            if end is None:
                end = start + 5
            
            start_time = self._seconds_to_srt_time(start)
            end_time = self._seconds_to_srt_time(end)
            
            srt_content.append(str(i))
            srt_content.append(f"{start_time} --> {end_time}")
            srt_content.append(chunk.get('text', '').strip())
            srt_content.append("")
        
        return '\n'.join(srt_content)
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def generate(
        self,
        video_path: Path,
        output_path: Path = None,
        lang: str = "en",
        task: str = "transcribe"
    ) -> Optional[Path]:
        """Generate subtitles from video."""
        video_path = Path(video_path)
        
        if not video_path.exists():
            print(f"{Colors.RED}❌ Video not found: {video_path}{Colors.RESET}")
            return None
        
        output_path = output_path or MOVIE_SUBTITLES_DIR / f"{video_path.stem}.srt"
        
        print(f"\n{Colors.GREEN}{'='*60}{Colors.RESET}")
        print(f"{Colors.GREEN}📝 SUBTITLE GENERATOR{Colors.RESET}")
        print(f"{Colors.GREEN}{'='*60}{Colors.RESET}")
        print(f"{Colors.CYAN}Video: {video_path.name}{Colors.RESET}")
        print(f"{Colors.CYAN}Task: {task} | Language: {lang}{Colors.RESET}")
        
        try:
            self._load_model()
            audio_path = self._extract_audio(video_path)
            
            print(f"\n{Colors.CYAN}🔊 Transcribing...{Colors.RESET}")
            
            result = self.pipe(
                str(audio_path),
                generate_kwargs={"language": lang, "task": task},
                return_timestamps=True
            )
            
            srt_content = self._format_srt(result)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            # Cleanup
            if audio_path.exists():
                audio_path.unlink()
            
            print(f"\n{Colors.GREEN}✅ Subtitles saved to: {output_path}{Colors.RESET}")
            return output_path
            
        except Exception as e:
            print(f"{Colors.RED}❌ Error: {e}{Colors.RESET}")
            return None
    
    def unload(self):
        """Clean up resources."""
        if self.pipe is not None:
            del self.pipe
            self.pipe = None
        gc.collect()
        if HAS_TORCH and torch.cuda.is_available():
            torch.cuda.empty_cache()
        print(f"{Colors.GREEN}[Clean] Subtitle generator unloaded{Colors.RESET}")
