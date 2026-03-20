# Download Pipelines

> `apps/movie_downloader/pipeline/`

Download source integrations for various platforms.

---

## 📁 Structure

```
pipeline/
├── __init__.py     # Package exports
├── registry.py     # Source registration
├── youtube.py      # yt-dlp integration
├── torrent.py      # Multi-source torrent search
├── trending.py     # TMDB trending movies
└── sources/        # Additional source modules
```

---

## 1. YouTube Pipeline (`youtube.py`)

YouTube downloading using yt-dlp.

```python
def download_youtube(
    url: str,
    output_dir: Path = None,
    quality: str = "best",
    audio_only: bool = False
) -> Path:
    """
    Download video from YouTube.
    
    Args:
        url: YouTube video or playlist URL
        output_dir: Download directory
        quality: "best", "1080p", "720p", "480p", "360p"
        audio_only: Extract audio only (MP3)
        
    Returns:
        Path to downloaded file
    """
```

**Quality Options:**

| Quality | Description |
|---------|-------------|
| `best` | Highest available |
| `1080p` | Full HD |
| `720p` | HD |
| `480p` | SD |
| `audio` | Audio only (MP3) |

**CLI Usage:**
```bash
python runner.py youtube --url "https://youtube.com/watch?v=..."
python runner.py youtube --url URL --quality 720p
python runner.py youtube --url URL --audio-only
```

---

## 2. Torrent Pipeline (`torrent.py`)

Multi-source torrent search and download.

```python
def search_torrents(
    query: str,
    source: str = "1337x",
    limit: int = 25
) -> List[Dict]:
    """
    Search for torrents across multiple sources.
    
    Args:
        query: Search query (e.g., "movie name 2024")
        source: "1337x", "piratebay", "rarbg"
        limit: Max results
        
    Returns:
        List of torrent dicts with keys:
        - name: str
        - magnet: str
        - size: str
        - seeders: int
        - leechers: int
    """

def download_torrent(magnet_link: str, output_dir: Path = None) -> Path:
    """
    Download torrent using system torrent client.
    
    Returns:
        Path to download directory
    """
```

**Supported Sources:**

| Source | File | Status |
|--------|------|--------|
| 1337x | `sources/1337x.py` | Active |
| PirateBay | `sources/piratebay.py` | Active |
| RARBG | `sources/rarbg.py` | Proxy |

**CLI Usage:**
```bash
python runner.py torrent --query "movie name"
python runner.py torrent --query "..." --source piratebay
python runner.py torrent --magnet "magnet:?xt=..."
```

---

## 3. Trending Pipeline (`trending.py`)

Browse trending movies using TMDB API.

```python
def get_trending_movies(
    time_window: str = "week",
    limit: int = 20
) -> List[Dict]:
    """
    Get trending movies from TMDB.
    
    Args:
        time_window: "day" or "week"
        limit: Max results
        
    Returns:
        List of movie dicts with keys:
        - title: str
        - year: int
        - rating: float
        - overview: str
        - poster_url: str
        - trailer_url: str (if available)
    """

def search_movie_torrent(movie_title: str, year: int) -> Optional[str]:
    """
    Search for torrent of specific movie.
    
    Returns:
        Magnet link if found, None otherwise
    """
```

**CLI Usage:**
```bash
python runner.py trending
```

Displays interactive list with poster, rating, and download options.

---

## 4. Registry (`registry.py`)

Source registration and management.

```python
SOURCES = {
    "youtube": YouTubePipeline,
    "torrent": TorrentPipeline,
    "trending": TrendingPipeline,
}

def get_source(name: str) -> BasePipeline:
    """Get pipeline by name"""

def list_sources() -> List[str]:
    """List available source names"""
```

---

## Output Directories

Configured in `configs/paths.py`:

| Type | Path |
|------|------|
| YouTube | `MOVIE_DOWNLOAD_DIR / "youtube/"` |
| Torrents | `TORRENT_DOWNLOAD_DIR` |
| Movies | `MOVIE_DOWNLOAD_DIR` |
