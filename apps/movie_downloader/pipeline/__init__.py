"""
Movie Downloader Pipelines
===========================

Download pipelines for different sources.
"""

from .registry import (
    DownloadConfig,
    register_pipeline,
    get_all_pipelines,
    get_pipeline_names,
    get_pipeline,
    find_pipeline_by_keyword,
    format_help_text,
    discover_pipelines
)

from .youtube import YouTubeDownloader
from .torrent import TorrentDownloader, APIMirrorManager
from .trending import TrendingMovies
from .sources.yts import YTSClient

__all__ = [
    "DownloadConfig",
    "register_pipeline",
    "get_all_pipelines",
    "get_pipeline_names",
    "get_pipeline",
    "find_pipeline_by_keyword",
    "format_help_text",
    "discover_pipelines",
    "YouTubeDownloader",
    "TorrentDownloader",
    "APIMirrorManager",
    "TrendingMovies",
    "YTSClient",
]
