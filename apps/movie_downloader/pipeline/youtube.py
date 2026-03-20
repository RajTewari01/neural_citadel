"""
YouTube Download Pipeline
==========================

Download videos from YouTube and social media using yt-dlp.
Supports highest quality downloads with aria2c acceleration.
"""

import gc
import sys
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import yt_dlp
    HAS_YTDLP = True
except ImportError:
    HAS_YTDLP = False

try:
    from moviepy.editor import VideoFileClip
    HAS_MOVIEPY = True
except ImportError:
    HAS_MOVIEPY = False

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from configs.paths import MOVIE_DOWNLOAD_DIR, ARIA2_EXE, DEBUG_LOG_DIR
from .registry import register_pipeline, DownloadConfig

# Colors
YELLOW = '\033[1;33m'
RESET = '\033[0m'
GREEN = '\033[1;32m'
RED = '\033[1;31m'
CYAN = '\033[1;36m'
BLUE = '\033[1;34m'

DEBUG_LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = DEBUG_LOG_DIR / "youtube.log"

logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)-8s - %(message)s')


def _check_ffmpeg() -> bool:
    """Check if FFmpeg is installed and available."""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


class YouTubeDownloader:
    """
    YouTube and social media downloader using yt-dlp.
    
    Supports: YouTube, Twitter, Instagram, TikTok, Vimeo, and 1000+ sites.
    """
    
    QUALITY_PRESETS = {
        # Best: Prioritize H.264 codec for compatibility, highest resolution
        # [vcodec^=avc] = H.264 only (widely supported, avoids AV1/VP9 codec issues)
        'best': 'bestvideo[vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/bestvideo[vcodec^=avc]+bestaudio/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
        # 4K with H.264 preference (H.264 4K may not always be available)
        '4k': 'bestvideo[height<=2160][vcodec^=avc1]+bestaudio[ext=m4a]/bestvideo[height<=2160][ext=mp4]+bestaudio/best[height<=2160]',
        '1080p': 'bestvideo[height<=1080][vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080][ext=mp4]+bestaudio/best[height<=1080]',
        '720p': 'bestvideo[height<=720][vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720][ext=mp4]+bestaudio/best[height<=720]',
        '480p': 'bestvideo[height<=480][vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=480][ext=mp4]+bestaudio/best[height<=480]',
        'audio': 'bestaudio[ext=m4a]/bestaudio',
        # Maximum: Best quality regardless of codec (may get AV1/VP9)
        'max': 'bestvideo*+bestaudio*/best*',
    }
    
    def __init__(self):
        if not HAS_YTDLP:
            raise ImportError("yt-dlp not installed. Run: pip install yt-dlp")
        
        gc.collect()
        self.logger = logging.getLogger(__name__)
        self.has_ffmpeg = _check_ffmpeg()
        MOVIE_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        if self.has_ffmpeg:
            print(f'{GREEN}{"YouTube Downloader Ready".center(50, "-")}{RESET}')
        elif HAS_MOVIEPY:
            print(f'{YELLOW}{"YouTube Downloader Ready (MoviePy fallback)".center(50, "-")}{RESET}')
        else:
            print(f'{RED}{"WARNING: No FFmpeg or MoviePy available!".center(50, "-")}{RESET}')
    
    def _get_ydl_opts(self, quality: str = "best", output_dir: Path = None) -> Dict:
        """Build yt-dlp options for maximum quality."""
        out_dir = output_dir or MOVIE_DOWNLOAD_DIR
        
        opts = {
            'format': self.QUALITY_PRESETS.get(quality, self.QUALITY_PRESETS['best']),
            'outtmpl': str(out_dir / '%(title)s.%(ext)s'),
            'prefer_free_formats': False,
            # General options
            'quiet': False,
            'no_warnings': False,
            'ignoreerrors': True,
            'nocheckcertificate': True,
            'geo_bypass': True,
            'noplaylist': True,  # Only download single video, not entire playlist
            'socket_timeout': 30,
            'retries': 10,
            'fragment_retries': 10,
            # Enable remote components to solve YouTube challenges
            'remote_components': {'ejs:github'},
        }
        
        # Only configure FFmpeg options if available
        if self.has_ffmpeg:
            opts['merge_output_format'] = 'mp4'
            opts['postprocessors'] = [{
                'key': 'FFmpegVideoRemuxer',
                'preferedformat': 'mp4',
            }]
            # Prioritize highest resolution, then codec compatibility
            opts['format_sort'] = ['res', 'fps', 'codec:h264:aac', 'ext:mp4:m4a']
            # Delete temporary files after merging
            opts['keepvideo'] = False
        
        # Use aria2c if available for faster downloads
        if ARIA2_EXE.exists():
            opts['external_downloader'] = str(ARIA2_EXE)
            opts['external_downloader_args'] = {
                'default': ['-x', '16', '-s', '16', '-k', '1M']
            }
        
        return opts
    
    def _verify_and_fix_video(self, video_path: Path, debug_mode: bool = False) -> Optional[Path]:
        """
        Re-encode video with MoviePy to fix compatibility issues.
        
        Args:
            video_path: Path to video file
            debug_mode: Enable verbose output
            
        Returns:
            Path to fixed video or original if no fix needed
        """
        if not HAS_MOVIEPY:
            self.logger.warning("MoviePy not available for video verification")
            return video_path
        
        try:
            if debug_mode:
                print(f"{CYAN}🔧 Re-encoding with MoviePy...{RESET}")
            
            clip = VideoFileClip(str(video_path), audio=True, fps_source='fps')
            
            if debug_mode:
                print(f"{CYAN}📹 Video: {clip.duration:.1f}s, {clip.size[0]}x{clip.size[1]}px{RESET}")
            
            # Re-encode using MoviePy
            fixed_path = video_path.with_stem(f"{video_path.stem}_fixed")
            
            clip.write_videofile(
                str(fixed_path),
                codec='libx264',
                audio_codec='aac',
                preset='medium',
                ffmpeg_params=['-pix_fmt', 'yuv420p'],
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                logger='bar' if debug_mode else None
            )
            clip.close()
            
            # Replace original with fixed version
            if fixed_path.exists():
                video_path.unlink()
                fixed_path.rename(video_path)
                
                if debug_mode:
                    print(f"{GREEN}✅ Video fixed successfully with MoviePy{RESET}")
                
                self.logger.info(f"Video fixed with MoviePy: {video_path}")
                return video_path
            
        except Exception as e:
            self.logger.error(f"Video verification/fix failed: {e}")
            if debug_mode:
                print(f"{RED}❌ MoviePy failed: {e}{RESET}")
                print(f"{YELLOW}⚠️  File may only contain audio or be corrupted{RESET}")
        
        return video_path
    
    def download(
        self, 
        url: str, 
        quality: str = "best",
        output_dir: Path = None,
        debug_mode: bool = False,
        download_playlist: bool = False,
        force_moviepy: bool = False
    ) -> Optional[Path]:
        """
        Download video from URL.
        
        Args:
            url: Video URL
            quality: Quality preset (best, 4k, 1080p, 720p, 480p, audio)
            output_dir: Custom output directory
            debug_mode: Enable verbose output
            download_playlist: If True, download entire playlist; if False, only single video
            force_moviepy: Force MoviePy re-encoding even if FFmpeg is available
            
        Returns:
            Path to downloaded file or None on error
        """
        if debug_mode:
            playlist_msg = " (Playlist)" if download_playlist else ""
            print(f"\n{GREEN}{'='*60}{RESET}")
            print(f"{GREEN}📺 YOUTUBE DOWNLOADER{playlist_msg}{RESET}")
            print(f"{GREEN}{'='*60}{RESET}")
            print(f"{CYAN}URL: {url}{RESET}")
            print(f"{CYAN}Quality: {quality}{RESET}")
        
        try:
            opts = self._get_ydl_opts(quality, output_dir)
            # Override noplaylist based on user choice
            opts['noplaylist'] = not download_playlist
            
            if debug_mode:
                opts['quiet'] = False
                opts['verbose'] = True
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if info:
                    filename = ydl.prepare_filename(info)
                    # Handle format conversion
                    final_path = Path(filename).with_suffix('.mp4')
                    
                    if debug_mode:
                        print(f"\n{GREEN}✅ Download complete!{RESET}")
                        print(f"{GREEN}📁 Saved to: {final_path}{RESET}")
                    
                    # Use MoviePy if: 1) FFmpeg not available, OR 2) force_moviepy is True
                    if final_path.exists() and quality != 'audio':
                        if force_moviepy:
                            if debug_mode:
                                print(f"{CYAN}🔧 Force re-encoding with MoviePy...{RESET}")
                            final_path = self._verify_and_fix_video(final_path, debug_mode)
                        elif not self.has_ffmpeg:
                            if debug_mode:
                                print(f"{YELLOW}⚠️  FFmpeg not found, using MoviePy fallback{RESET}")
                            final_path = self._verify_and_fix_video(final_path, debug_mode)
                    
                    self.logger.info(f"Downloaded: {final_path}")
                    return final_path
                    
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            if debug_mode:
                print(f"{RED}❌ Error: {e}{RESET}")
            return None
    
    def get_info(self, url: str) -> Optional[Dict]:
        """Get video info without downloading."""
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                return ydl.extract_info(url, download=False)
        except:
            return None
    
    def unload(self):
        """Clean up resources."""
        gc.collect()
        print(f"{GREEN}[Clean] YouTube downloader unloaded{RESET}")


@register_pipeline(
    name="youtube",
    keywords=["youtube", "youtu.be", "twitter", "x.com", "instagram", "tiktok", "vimeo"],
    description="Download from YouTube and social media",
    category="video",
    supported_sites=["youtube.com", "youtu.be", "twitter.com", "x.com", "instagram.com", "tiktok.com"]
)
def get_config(url: str, quality: str = "best", **kwargs) -> DownloadConfig:
    return DownloadConfig(pipeline="youtube", source=url, quality=quality, **kwargs)