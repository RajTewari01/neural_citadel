import asyncio
import logging
import json
import io
import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

# Logger
logger = logging.getLogger("CAPTION_API")

router = APIRouter(prefix="/caption", tags=["Image Captioner"])

# Paths
ROOT_DIR = Path(r"d:\neural_citadel")
# Captioner uses its own lightweight venv usually, or image_venv?
# Runner says: "Uses image_captioner venv with PyTorch CPU"
# Let's verify python path for that. 
# "venvs/env/image_captioner/Scripts/python.exe" (Assuming standard naming) or "photo-recognizer" logic?
# Runner says: "venvs/env/image_captioner" (lines 6 of runner.py)
# Actually runner validation says "Uses image_captioner venv".
CAPTION_VENV_PYTHON = r"d:\neural_citadel\venvs\env\image_captioner\Scripts\python.exe"
CAPTION_RUNNER = "apps.image_captioner.runner"

class CaptionState:
    process: asyncio.subprocess.Process = None
    lock = asyncio.Lock()

state = CaptionState()

async def get_caption_service():
    """Get or start persistent caption service."""
    async with state.lock:
        if state.process is None or state.process.returncode is not None:
            logger.info("Starting Caption Service...")
            try:
                # Need PYTHONUTF8 for reliable I/O
                env = {"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
                import os
                full_env = os.environ.copy()
                full_env.update(env)
                
                # Check if venv exists, otherwise fallback?
                python_exe = CAPTION_VENV_PYTHON
                if not Path(python_exe).exists():
                     logger.warning(f"Caption venv not found at {python_exe}, falling back to server_venv")
                     python_exe = r"d:\neural_citadel\venvs\env\server_venv\Scripts\python.exe"

                state.process = await asyncio.create_subprocess_exec(
                    python_exe, "-m", CAPTION_RUNNER, "--service",
                    cwd=str(ROOT_DIR),
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=full_env
                )
                
                # Wait for READY signal
                while True:
                    line = await state.process.stdout.readline()
                    if not line: break
                    decoded = line.decode().strip()
                    if decoded == "READY":
                        logger.info("Caption Service READY")
                        break
            except Exception as e:
                logger.error(f"Failed to start caption service: {e}")
                return None
        return state.process

@router.post("/process")
async def caption_image(
    image: UploadFile = File(...),
    mode: str = Form("caption") # caption or detailed
):
    """
    Generate caption for uploaded image.
    PROD: Uses persistent service mode.
    """
    process = await get_caption_service()
    if not process:
         # Fallback to oneshot if service fails?
         raise HTTPException(status_code=503, detail="Caption service unavailable")
         
    # Save temp file
    temp_dir = ROOT_DIR / "assets" / "temp" / "caption_uploads"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / f"{uuid.uuid4()}_{image.filename}"
    
    try:
        with open(temp_path, "wb") as f:
            f.write(await image.read())
            
        # Send to service: "path|task"
        cmd = f"{str(temp_path)}|{mode}\n"
        process.stdin.write(cmd.encode())
        await process.stdin.drain()
        
        # Read response
        while True:
            line = await process.stdout.readline()
            if not line: break
            decoded = line.decode('utf-8', errors='replace').strip()
            
            if decoded.startswith("CAPTION:"):
                # Clean up
                try: os.unlink(temp_path) 
                except: pass
                
                return {"caption": decoded[8:]}
            elif decoded.startswith("[BLIP]"):
                 # Log internal logs
                 logger.info(f"Service Log: {decoded}")
            
    except Exception as e:
        logger.error(f"Captioning Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup in case of error
        if temp_path.exists():
            try: os.unlink(temp_path)
            except: pass
