import logging
import asyncio
import contextlib
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import sys
from pathlib import Path
# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from infra.server.routers import chat, image, newspaper, movie, surgeon, admin, support, system, caption, gallery, stats, users, qr
from infra.server import database

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB
    database.init_db()
    yield
    # Shutdown: (Cleanup if needed)

app = FastAPI(title="Neural Citadel API", version="2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(chat.router)
app.include_router(image.router)
app.include_router(newspaper.router)
app.include_router(movie.router)
app.include_router(surgeon.router)
app.include_router(admin.router)
app.include_router(support.router)
app.include_router(system.router)
app.include_router(caption.router)
app.include_router(gallery.router)
app.include_router(stats.router)
app.include_router(users.router)
app.include_router(qr.router)
# app.include_router(admin.router) # Removed duplicate inclusion

# ... existing code ...

# Import path configs
from configs.paths import ASSETS_DIR, ROOT_DIR

# Mount Static Assets (Outputs)
# /static/assets maps to assets/outputs
ASSETS_OUTPUTS_DIR = ASSETS_DIR / "outputs"
ASSETS_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static/assets", StaticFiles(directory=str(ASSETS_OUTPUTS_DIR)), name="assets")

# Mount Generated Content (Images, Newspapers)
# /static/generated maps to assets/generated
GENERATED_DIR = ASSETS_DIR / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static/generated", StaticFiles(directory=str(GENERATED_DIR)), name="generated")

# Mount Downloaded Content (Movies, Torrents)
# /static/downloaded maps to assets/downloaded
DOWNLOADED_DIR = ASSETS_DIR / "downloaded"
DOWNLOADED_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static/downloaded", StaticFiles(directory=str(DOWNLOADED_DIR)), name="downloaded")

# Mount QR Codes
# /static/qr_code maps to assets/qr_code
QR_CODE_DIR = ASSETS_DIR / "qr_code"
QR_CODE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static/qr_code", StaticFiles(directory=str(QR_CODE_DIR)), name="qr_code")

# Mount Temp
# /static/temp maps to assets/temp
TEMP_DIR = ASSETS_DIR / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static/temp", StaticFiles(directory=str(TEMP_DIR)), name="temp")

# Mount Legacy Gallery
# /static/gallery maps to assets/gallery
GALLERY_DIR = ASSETS_DIR / "gallery"
GALLERY_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static/gallery", StaticFiles(directory=str(GALLERY_DIR)), name="gallery")

@app.get("/")
async def root():
    return {
        "status": "online", 
        "system": "Neural Citadel",
        "version": "1.0.0"
    }

@app.get("/status")
async def system_status():
    """Check health of all subsystems."""
    return {
        "gateway": "operational",
        "nsfw_engine": "unknown",  # TODO: Check subprocess
        "code_engine": "unknown",
        "voice_engine": "unknown"
    }

if __name__ == "__main__":
    import uvicorn
    # Run on 0.0.0.0 to enable Mobile access
    uvicorn.run(app, host="0.0.0.0", port=8000)
