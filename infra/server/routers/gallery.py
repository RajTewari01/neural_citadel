from fastapi import APIRouter
from pathlib import Path
import os
import datetime
from configs.paths import ASSETS_DIR

router = APIRouter(prefix="/gallery", tags=["gallery"])

# Define Asset Roots to Scan and their Web Prefixes
# These MUST match the mounts in main.py
SCAN_CONFIGS = [
    {
        "root": ASSETS_DIR / "generated",
        "url_prefix": "/static/generated"
    },
    {
        "root": ASSETS_DIR / "downloaded",
        "url_prefix": "/static/downloaded"
    },
    {
        "root": ASSETS_DIR / "qr_code",
        "url_prefix": "/static/qr_code"
    },
    {
        "root": ASSETS_DIR / "outputs", 
        "url_prefix": "/static/assets"
    }
]

def get_file_type(path: Path):
    ext = path.suffix.lower()
    if ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp']: return 'image'
    if ext in ['.mp4', '.avi', '.mqv', '.mkv', '.mov', '.webm']: return 'video'
    if ext in ['.mp3', '.wav', '.flac', '.m4a', '.aac']: return 'audio' # Added Audio
    if ext in ['.pdf']: return 'pdf'
    if ext in ['.svg']: return 'svg'
    return 'unknown'

@router.get("/items")
async def get_gallery_items():
    items = []
    
    for config in SCAN_CONFIGS:
        root_dir = config["root"]
        url_prefix = config["url_prefix"]
        
        if not root_dir.exists():
            continue
            
        # helper to process a directory
        for root, _, files in os.walk(root_dir):
            for file in files:
                file_path = Path(root) / file
                f_type = get_file_type(file_path)
                if f_type == 'unknown': continue
                
                try:
                    # Create relative path from the specific root
                    rel_path = file_path.relative_to(root_dir)
                    # Join with the specific URL prefix for this root
                    # ensure forward slashes
                    web_path = f"{url_prefix}/{rel_path.as_posix()}"
                    
                    stats = file_path.stat()
                    mod_time = datetime.datetime.fromtimestamp(stats.st_mtime)
                    
                    items.append({
                        "name": file,
                        "type": f_type,
                        "url": web_path,
                        "date": mod_time.isoformat(),
                        "timestamp": stats.st_mtime,
                        "size": stats.st_size, # Added size in bytes
                        "source": root_dir.name 
                    })
                except Exception as e:
                    print(f"Skipping {file}: {e}")
                    continue

    # Sort by date descending
    items.sort(key=lambda x: x["timestamp"], reverse=True)
    return {"items": items}
