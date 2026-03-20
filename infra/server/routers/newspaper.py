import asyncio
import logging
import json
import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List

# Logger
logger = logging.getLogger("NEWSPAPER_API")

router = APIRouter(prefix="/newspaper", tags=["Newspaper"])

# Paths -- Newspaper usually runs in 'enhanced' or 'server_venv' depending on dependencies
# Let's check imports. It imports `rss_sites`, `templates`. 
# It seems to rely on `BeautifulSoup`, `reportlab`, etc.
# The user's repo has `server_venv` for general things, but `newspaper` might use `enhanced`?
# Let's assume `server_venv` for now or check if it needs specific deps.
# Actually, checking `infra/gui/widgets/newspaper_panel.py` might reveal the venv.
# But generally `server_venv` is safe for basic logic.
# However, if it uses NLLB (offline translation), it might need a heavier venv.
# Let's use `server_venv` as it's the default "runner" venv for many tools.

ROOT_DIR = Path(r"d:\neural_citadel")
# Using server_venv as a safe bet for generic python apps
# Newspaper runs on Global Python due to legacy dependencies
NEWSPAPER_VENV_PYTHON = r"C:\Program Files\Python310\python.exe" 
NEWSPAPER_RUNNER = "apps.newspaper_publisher.runner"

class NewspaperRequest(BaseModel):
    category: str = "GLOBAL" # INDIA, USA, GLOBAL
    style: str = "Classic"   # Classic, Modern, Magazine
    substyle: Optional[str] = None
    language: str = "English"
    translation_mode: str = "online" # online, offline

class NewspaperState:
    process: asyncio.subprocess.Process = None
    lock = asyncio.Lock()

state = NewspaperState()

@router.get("/schema")
async def get_newspaper_schema():
    """
    Get dynamic schema for Newspaper Publisher UI.
    Hardcoded to avoid checking deps in server_venv.
    """
    try:
        # 1. Magazine Substyles (Extracted from magazine.py)
        msg_substyles = [
            'Neural Citadel', 'The Tech', 'The Times', 'The Minimal', 'The Bold', 'The Elegant', 
            'The Geo', 'The Star', 'The Noir', 'The Pop', 'The Corporate', 'The Future',
            'Vogue Classic', 'Vogue Paris', 'Vogue Noir', 'Elle Style', 'Harpers Bazaar', 'GQ Magazine'
        ]
        mag_substyles = sorted(msg_substyles)
        
        # 2. Feed Regions (Extracted from runner.py)
        regions = ["GLOBAL", "INDIA", "USA"]
        
        # 3. Languages
        languages = [
            "English", "Hindi", "Bengali", "Spanish", "French", "German",
            "Japanese", "Chinese", "Korean", "Russian", "Portuguese", "Arabic",
            "Tamil", "Telugu", "Gujarati", "Punjabi", "Filipino", "Vietnamese",
            "Thai", "Indonesian"
        ]
        
        return {
            "regions": regions,
            "styles": ["Classic", "Modern", "Magazine"],
            "magazine_substyles": mag_substyles,
            "languages": languages
        }
    except Exception as e:
        logger.error(f"Schema Error: {e}")
        return {
            "regions": ["GLOBAL", "USA", "INDIA"],
            "styles": ["Classic", "Modern", "Magazine"],
            "error": str(e)
        }

@router.post("/generate")
async def generate_newspaper(req: NewspaperRequest):
    """
    Generate a newspaper PDF.
    Stream logs.
    """
    if state.process and state.process.returncode is None:
         # Lock to single generation for now to avoid resource contention
         raise HTTPException(status_code=503, detail="Publisher is busy")
    
    await state.lock.acquire()
    
    async def event_generator():
        try:
             args = [
                NEWSPAPER_VENV_PYTHON,
                "-m", NEWSPAPER_RUNNER,
                "--category", req.category,
                "--style", req.style,
                "--language", req.language
            ]
             
             if req.substyle:
                 args.extend(["--substyle", req.substyle])
            
             # Translation Mode
             if req.translation_mode == "offline":
                 args.append("--offline")
             else:
                 args.append("--online")

             # Headless mode implied
             
             logger.info(f"Starting Publisher: {args}")
             
             # Env
             env = {"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
             import os
             full_env = os.environ.copy()
             full_env.update(env)

             state.process = await asyncio.create_subprocess_exec(
                *args,
                cwd=str(ROOT_DIR),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=full_env
            )
             
             # Read stdout
             while True:
                line = await state.process.stdout.readline()
                if not line:
                    break
                
                decoded = line.decode('utf-8', errors='replace').strip()
                if decoded:
                    if "[DONE] PDF Saved:" in decoded:
                         # Next line usually has path: "   Path: ..."
                         pass
                    elif "Path:" in decoded:
                        path = decoded.split("Path:", 1)[1].strip()
                        yield f"RESULT:{path}\n"
                    
                    yield f"{decoded}\n"
             
             await state.process.wait()
             
             if state.process.returncode != 0:
                 stderr = await state.process.stderr.read()
                 yield f"ERROR: {stderr.decode()}"
                 
        except Exception as e:
            yield f"ERROR: {str(e)}"
        finally:
            state.process = None
            state.lock.release()
                 

    return StreamingResponse(event_generator(), media_type="text/plain")

@router.post("/cancel")
async def cancel_generation():
    """Cancel the running newspaper generation process."""
    if state.process:
        try:
            state.process.kill()
            logger.info("Process killed by user request.")
        except Exception as e:
            logger.error(f"Failed to kill process: {e}")
        return {"status": "killed"}
    return {"status": "no_process"}
