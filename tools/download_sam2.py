"""
SAM2 Model Downloader
=====================
Downloads SAM2 model checkpoints from Meta's repository.

Run this script to download the small model (recommended for 4GB VRAM):
    python download_sam2.py small

Available models:
    - tiny:      ~150MB, fastest, less accurate
    - small:     ~185MB, balanced (RECOMMENDED)
    - base_plus: ~320MB, more accurate
    - large:     ~890MB, most accurate, needs more VRAM
"""

import sys
import urllib.request
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from configs.paths import SAM2_MODELS, IMAGE_SURGEON_MODELS_DIR

# SAM2 download URLs (from Meta's repository)
SAM2_URLS = {
    "tiny": "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_tiny.pt",
    "small": "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_small.pt",
    "base_plus": "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_base_plus.pt",
    "large": "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_large.pt",
}


def download_with_progress(url: str, dest_path: Path):
    """Download a file with progress bar."""
    
    def report_progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(100, downloaded * 100 // total_size)
        bar_len = 40
        filled = int(bar_len * percent // 100)
        bar = '█' * filled + '░' * (bar_len - filled)
        mb_downloaded = downloaded / (1024 * 1024)
        mb_total = total_size / (1024 * 1024)
        print(f'\r   [{bar}] {percent}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)', end='', flush=True)
    
    print(f"📥 Downloading: {url.split('/')[-1]}")
    print(f"   To: {dest_path}")
    
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest_path, report_progress)
    print()  # New line after progress
    print(f"✅ Download complete!")


def main():
    print("=" * 60)
    print("SAM2 Model Downloader")
    print("=" * 60)
    
    # Parse model argument
    if len(sys.argv) < 2:
        model_name = "small"  # Default
        print(f"No model specified, using default: {model_name}")
    else:
        model_name = sys.argv[1].lower()
    
    if model_name not in SAM2_URLS:
        print(f"❌ Unknown model: {model_name}")
        print(f"   Available: {list(SAM2_URLS.keys())}")
        sys.exit(1)
    
    # Check if already exists
    dest_path = SAM2_MODELS[model_name]
    if dest_path.exists():
        print(f"⚠️  Model already exists: {dest_path}")
        response = input("   Download anyway? [y/N]: ").strip().lower()
        if response != 'y':
            print("   Skipped.")
            return
    
    # Download
    url = SAM2_URLS[model_name]
    try:
        download_with_progress(url, dest_path)
        print(f"\n✅ SAM2 {model_name} model ready!")
        print(f"   Path: {dest_path}")
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
