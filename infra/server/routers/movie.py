import asyncio
import logging
import json
import uuid
import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional

# Logger
logger = logging.getLogger("MOVIE_API")

router = APIRouter(prefix="/movie", tags=["Movie Downloader"])

# Paths
ROOT_DIR = Path(r"d:\neural_citadel")
MOVIE_VENV_PYTHON = r"d:\neural_citadel\venvs\env\movie_venv\Scripts\python.exe"
MOVIE_RUNNER = "apps.movie_downloader.runner"

class SearchRequest(BaseModel):
    query: str
    limit: int = 10

class DownloadRequest(BaseModel):
    magnet: str
    
class MovieState:
    process: asyncio.subprocess.Process = None
    lock = asyncio.Lock()

state = MovieState()

@router.get("/trending")
async def get_trending_movies():
    """
    Get trending movies list via CLI.
    """
    try:
        args = [
            MOVIE_VENV_PYTHON,
            "-m", MOVIE_RUNNER,
            "trending-list"
        ]
        
        # logger.info(f"Fetching Trending: {args}")
        
        proc = await asyncio.create_subprocess_exec(
            *args,
            cwd=str(ROOT_DIR),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
             # Fallback or error
             logger.error(f"Trending fetch failed: {stderr.decode()}")
             return {"results": [], "error": "Failed to fetch trending"}
             
        try:
            output = stdout.decode().strip()
            # Parse the last line as JSON
            lines = output.splitlines()
            if not lines: return {"results": []}
            
            data = json.loads(lines[-1])
            return data
        except:
             return {"results": [], "error": "Invalid output format"}
        
    except Exception as e:
         return {"error": str(e)}


@router.post("/search")
async def search_movie(req: SearchRequest):
    """
    Search for movies. 
    Execute subprocess: python -m apps.movie_downloader.runner torrent-search "query" --limit 10
    Returns JSON directly.
    """
    try:
        args = [
            MOVIE_VENV_PYTHON,
            "-m", MOVIE_RUNNER,
            "torrent-search",
            req.query,
            "--limit", str(req.limit)
        ]
        
        logger.info(f"Searching Movie: {args}")
        
        proc = await asyncio.create_subprocess_exec(
            *args,
            cwd=str(ROOT_DIR),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
             raise Exception(f"Search failed: {stderr.decode()}")
             
        # Parse JSON output
        try:
            output = stdout.decode().strip()
            # Find JSON part (sometimes there might be logs before it)
            # We look for the last line usually
            lines = output.splitlines()
            json_line = lines[-1] if lines else "{}"
            data = json.loads(json_line)
            return data
        except Exception as e:
            logger.error(f"Failed to parse search output: {output}")
            raise HTTPException(status_code=500, detail="Failed to parse search results")
            
    except Exception as e:
        logger.error(f"Search Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/download")
async def download_movie(req: DownloadRequest):
    """
    Download movie via magnet link.
    Streams progress logs.
    """
    if state.process and state.process.returncode is None:
         # Optional: Allow parallel downloads? For now, lock it for simplicity or check if we want background job
         # But the user might want to see progress.
         pass
         
    # We allow this to run in background or stream? 
    # Let's stream for now so the user sees "Downloading..."
    
    async def event_generator():
        try:
             args = [
                MOVIE_VENV_PYTHON,
                "-m", MOVIE_RUNNER,
                "torrent-download",
                req.magnet,
                "--debug"
            ]
             
             logger.info(f"Starting Download: {req.magnet[:20]}...")
             
             # Environment setup (UTF-8)
             env = {"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
             import os
             full_env = os.environ.copy()
             full_env.update(env)

             proc = await asyncio.create_subprocess_exec(
                *args,
                cwd=str(ROOT_DIR),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=full_env
            )
             
             # Read stdout
             while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                
                decoded = line.decode('utf-8', errors='replace').strip()
                if decoded:
                    # Check for scan result which is JSON
                    if decoded.startswith("SCAN_RESULT:"):
                        yield f"{decoded}\n"
                    else:
                        yield f"{decoded}\n"
             
             await proc.wait()
             
             if proc.returncode != 0:
                 stderr = await proc.stderr.read()
                 yield f"ERROR: {stderr.decode()}"
             else:
                 yield "DONE"
                 
        except Exception as e:
            yield f"ERROR: {str(e)}"

    return StreamingResponse(event_generator(), media_type="text/plain")
