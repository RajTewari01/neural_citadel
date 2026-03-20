"""
Movie Downloader App
====================

Download movies from YouTube, torrents, and generate subtitles.
"""

from .pipeline import YouTubeDownloader, TorrentDownloader, TrendingMovies
from .tools import VirusScanner
from .transcriber import SubtitleGenerator

__all__ = [
    'YouTubeDownloader',
    'TorrentDownloader', 
    'TrendingMovies',
    'VirusScanner',
    'SubtitleGenerator',
]
