# Movie Downloader

> `apps/movie_downloader/`

Unified video/movie download system supporting YouTube, torrents, and trending content.

---

## 📁 Structure

```
movie_downloader/
├── runner.py              # CLI interface & interactive mode
├── transcriber.py         # Audio transcription (Whisper)
├── pipeline/              # Download pipelines
│   ├── __init__.py        # Package exports
│   ├── registry.py        # Source registration
│   ├── youtube.py         # yt-dlp integration
│   ├── torrent.py         # Torrent search & download
│   ├── trending.py        # Trending movies discovery
│   └── sources/           # Additional source modules
└── tools/                 # Utility tools
    ├── __init__.py        # Package exports
    └── virus_scanner.py   # Downloaded file security scan
```

---

## 🔧 Components

### 1. Runner (`runner.py`)

CLI interface with interactive menu support.

**Interactive Mode:**
```bash
python runner.py
```

Displays menu:
```
╔═══════════════════════════════════════╗
║        MOVIE DOWNLOADER               ║
╠═══════════════════════════════════════╣
║  [1] YouTube Download                 ║
║  [2] Torrent Search                   ║
║  [3] Trending Movies                  ║
║  [4] Fetch Subtitles                  ║
║  [5] Virus Scan                       ║
║  [0] Exit                             ║
╚═══════════════════════════════════════╝
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `youtube` | Download from YouTube |
| `torrent` | Search & download torrents |
| `trending` | Browse trending movies |
| `subtitle` | Fetch subtitles for video |
| `scan` | Virus scan downloaded files |

---

### 2. Transcriber (`transcriber.py`)

Audio transcription using OpenAI Whisper.

```python
class Transcriber:
    """
    Audio/video transcription using Whisper.
    
    Args:
        model_size: "tiny", "base", "small", "medium", "large"
    """
    
    def transcribe(self, audio_path: str, output_format: str = "srt") -> str:
        """
        Transcribe audio/video file.
        
        Args:
            audio_path: Path to audio/video file
            output_format: "srt", "txt", "vtt", or "json"
            
        Returns:
            Path to generated transcript
        """
```

**Model Sizes:**

| Model | VRAM | Speed | Quality |
|-------|------|-------|---------|
| `tiny` | ~1GB | Fastest | Basic |
| `base` | ~1GB | Fast | Good |
| `small` | ~2GB | Medium | Better |
| `medium` | ~5GB | Slow | Great |
| `large` | ~10GB | Slowest | Best |

---

*See subdirectory docs for detailed API reference:*
- [pipeline/](pipeline/) - Download pipelines
- [tools/](tools/) - Utility tools
