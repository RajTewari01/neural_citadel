import asyncio
import logging
import json
import uuid
import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional

# Logger
logger = logging.getLogger("SURGEON_API")

router = APIRouter(prefix="/surgeon", tags=["Image Surgeon"])

# Paths
ROOT_DIR = Path(r"d:\neural_citadel")
SURGEON_VENV_PYTHON = r"d:\neural_citadel\venvs\env\enhanced\Scripts\python.exe"
SURGEON_RUNNER = "apps.image_surgeon.runner"

class SurgeonRequest(BaseModel):
    mode: str # background, clothes, auto
    # Note: For file uploads we usually use Form data, not JSON body. 
    # But we can split endpoints or use mixed form/file.
    # Below we use specific endpoints handling file up.

@router.get("/schema")
async def get_surgeon_schema():
    """
    Get dynamic schema for Image Surgeon UI.
    """
    try:
        # Dynamic import to scan assets
        from apps.image_surgeon.pipeline.registry import discover_assets
        
        # solid colors are in runner.py but can be hardcoded or imported
        # Let's hardcode the stable list from runner.py to avoid circular deps with CLI
        solid_colors = [
            "black", "white", "red", "green", "blue", "gray", "grey", "yellow", 
            "cyan", "magenta", "orange", "pink", "purple"
        ]
        
        # Scanned assets
        clothes = discover_assets("clothes") or {}
        backgrounds = discover_assets("backgrounds") or {}
        
        # Flatten asset lists for simple UI picker
        # Or return categorized? Categorized is better for UI.
        def format_assets(assets_dict):
             res = {}
             for cat, items in assets_dict.items():
                 res[cat] = [item.name for item in items]
             return res

        return {
            "modes": ["background", "clothes", "auto"],
            "solid_colors": solid_colors,
            "assets": {
                "clothes": format_assets(clothes),
                "backgrounds": format_assets(backgrounds)
            }
        }
    except Exception as e:
        logger.error(f"Schema Error: {e}")
        return {"error": str(e), "modes": ["background", "clothes", "auto"]}

@router.post("/process")
async def process_image(
    mode: str = Form(...),
    image: UploadFile = File(...),
    prompt: Optional[str] = Form(None),
    solid_color: Optional[str] = Form(None), # black, white...
    garment: Optional[UploadFile] = File(None),
    bg_image: Optional[UploadFile] = File(None)
):
    """
    Process image with Image Surgeon.
    """
    try:
        # Save input file
        import tempfile
        import os
        
        temp_dir = ROOT_DIR / "assets" / "temp" / "server_uploads"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        input_path = temp_dir / f"{uuid.uuid4()}_{image.filename}"
        with open(input_path, "wb") as f:
            f.write(await image.read())
            
        args = [
            SURGEON_VENV_PYTHON,
            "-m", SURGEON_RUNNER,
            "--mode", mode,
            "--image", str(input_path),
            "--output", f"surgeon_{uuid.uuid4().hex[:6]}" # let runner handle extension
        ]
        
        if prompt:
            args.extend(["--prompt", prompt])
            
        if solid_color:
            args.extend(["--solid", solid_color])
            
        garment_path = None
        if garment:
            garment_path = temp_dir / f"{uuid.uuid4()}_{garment.filename}"
            with open(garment_path, "wb") as f:
                f.write(await garment.read())
            args.extend(["--garment", str(garment_path)])
            
        bg_path = None
        if bg_image:
            bg_path = temp_dir / f"{uuid.uuid4()}_{bg_image.filename}"
            with open(bg_path, "wb") as f:
                f.write(await bg_image.read())
            args.extend(["--bg", str(bg_path)])
            
        logger.info(f"Running Surgeon: {args}")
        
        proc = await asyncio.create_subprocess_exec(
            *args,
            cwd=str(ROOT_DIR),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await proc.communicate()
        
        # Cleanup inputs
        try:
            if input_path.exists(): os.unlink(input_path)
            if garment_path and garment_path.exists(): os.unlink(garment_path)
            if bg_path and bg_path.exists(): os.unlink(bg_path)
        except: pass
        
        if proc.returncode != 0:
             raise Exception(f"Surgeon failed: {stderr.decode()}")
             
        # Parse output path
        output_data = stdout.decode('utf-8', errors='replace')
        for line in output_data.splitlines():
            if "Output:" in line:
                out_path = line.split("Output:", 1)[1].strip()
                # Return the file or path?
                # Probably return JSON with URL to download
                # We need a static mount for assets/output
                # Let's assume we return the path relative to assets for now
                # Or serve it directly?
                # Let's return local path for now.
                
                # If we want to serve it, we can use FileResponse directly?
                return FileResponse(out_path)
                
        raise Exception("Could not find output path in logs")

    except Exception as e:
        logger.error(f"Surgeon Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
