import asyncio
import logging
import json
import uuid
import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

# Logger
logger = logging.getLogger("IMAGE_API")

router = APIRouter(prefix="/image", tags=["Image Gen"])

# Import paths
from configs.paths import ROOT_DIR, IMAGE_VENV_PYTHON, IMAGE_GEN_MODULE

# If IMAGE_GEN_MODULE isn't explicitly in paths.py (it was "apps.image_gen.runner" in variable), define it here
if not isinstance(IMAGE_GEN_MODULE, str):
    IMAGE_GEN_MODULE = "apps.image_gen.runner"

class ImageRequest(BaseModel):
    prompt: str
    style: str = "Cinematic" # Pipeline/Style name
    subtype: Optional[str] = None # Specific pipeline/model type (e.g. Flux, SDXL)
    ratio: str = "normal"  # Aspect ratio (portrait, landscape, normal)
    seed: Optional[int] = None
    negative_prompt: Optional[str] = None
    add_details: bool = True # User Requirement: Quality at any cost

class ImageState:
    process: asyncio.subprocess.Process = None
    lock = asyncio.Lock()

state = ImageState()

@router.post("/generate")
async def generate_image(req: ImageRequest):
    """
    Generate an image.
    Streams progress logs line-by-line.
    Final line should contain the output path or "IMAGE:<path>".
    """
    if state.process and state.process.returncode is None:
        raise HTTPException(status_code=503, detail="Another generation is in progress")

    await state.lock.acquire()

    async def event_generator():
        try:
            # Construct command
            # python -m apps.image_gen.runner "prompt" --style "Style" --aspect "Ratio" ...
            
            # Use provided ratio keyword directly (validated by CLI runner anyway)
            aspect_arg = req.ratio if req.ratio in ["portrait", "landscape", "normal"] else "normal"

            args = [
                IMAGE_VENV_PYTHON,
                "-m", IMAGE_GEN_MODULE,
                req.prompt,
                "--style", req.style,
                "--aspect", aspect_arg
            ]
            
            # Default is now True, so this likely runs unless explicitly disabled
            if req.add_details:
                args.append("--add_details")
            
            if req.subtype:
                 args.extend(["--type", req.subtype])
            
            if req.seed is not None:
                args.extend(["--seed", str(req.seed)])
            
            # TODO: Pass negative prompt if runner supports it via CLI
            
            logger.info(f"Starting Image Gen: {args}")
            
            # Environment setup (UTF-8)
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
                if not decoded:
                    continue
                
                # Check for output image path pattern
                # The CLI usually prints: "Image saved at: D:\..."
                if "saved at:" in decoded.lower():
                     # Extract path (e.g. D:\neural_citadel\assets\generated\image_gen_images\gen_123.png)
                     path_str = decoded.split("saved at:")[-1].strip()
                     
                     # Check if it's a valid path
                     if os.path.exists(path_str):
                         p = Path(path_str)
                         try:
                             # Try Mapping to Generated Dir
                             if "generated" in p.parts:
                                 # Find relative path from 'generated' dir
                                 # Brute force robust finding of 'generated'
                                 parts = list(p.parts)
                                 idx = parts.index("generated")
                                 rel_parts = parts[idx+1:]
                                 rel_path = "/".join(rel_parts)
                                 url_path = f"/static/generated/{rel_path}"
                                 yield f"RESULT:{url_path}\n"
                             
                             # Fallback: Try Mapping to Gallery
                             elif "gallery" in p.parts:
                                 idx = parts.index("gallery") 
                                 rel_parts = parts[idx+1:]
                                 rel_path = "/".join(rel_parts)
                                 url_path = f"/static/gallery/{rel_path}"
                                 yield f"RESULT:{url_path}\n"
                                 
                             else:
                                 # Unknown location, return absolute path (will likely fail on mobile but better than nothing)
                                 yield f"RESULT:{path_str}\n"

                         except Exception as e:
                             # Fallback if path parsing fails
                             yield f"RESULT:{path_str}\n"
                     else:
                         yield f"RESULT:{path_str}\n" 
                elif "%" in decoded or "it/s" in decoded:
                     # Attempt to extract percentage
                     # Example: 10%|█         | 2/20 [00:01<00:12,  1.42it/s]
                     try:
                         import re
                         match = re.search(r"(\d+)%", decoded)
                         if match:
                             yield f"PROGRESS:{match.group(1)}\n"
                     except:
                         pass
                     yield f"{decoded}\n"
                else:
                    yield f"{decoded}\n" # Stream logs
            
            # Wait for finish
            await state.process.wait()
            
            if state.process.returncode != 0:
                stderr = await state.process.stderr.read()
                yield f"ERROR: {stderr.decode()}"
                
        except Exception as e:
            logger.error(f"Image Gen Error: {e}")
            yield f"ERROR: {str(e)}"
        finally:
            state.process = None
            state.lock.release()

    return StreamingResponse(event_generator(), media_type="text/plain")

@router.post("/cancel")
async def cancel_generation():
    """
    Cancel the currently running image generation process.
    """
    if state.process and state.process.returncode is None:
        logger.info("Cancelling image generation process...")
        try:
            state.process.terminate()
            # Wait briefly for it to die
            try:
                await asyncio.wait_for(state.process.wait(), timeout=2.0)
            except asyncio.TimeoutError:
                logger.warning("Process did not terminate in time, killing...")
                state.process.kill()
                await state.process.wait()
                
            return {"status": "cancelled"}
        except Exception as e:
            logger.error(f"Error cancelling process: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    else:
         return {"status": "no_process_running"}

@router.get("/schema")
async def get_image_schema():
    """
    Get dynamic schema for Image Gen UI using authoritative definitions from PyQt GUI.
    """
    try:
        # Import authoritative definitions from GUI
        # IMAGE_MODELS is a list of tuples: (display_name, style, type, icon, description)
        try:
            from infra.gui.widgets.image_models import IMAGE_MODELS
        except ImportError:
             # Fallback: add root to path if needed (though main.py should handle this)
            import sys
            if str(ROOT_DIR) not in sys.path:
                sys.path.append(str(ROOT_DIR))
            from infra.gui.widgets.image_models import IMAGE_MODELS
        
        styles_map = {}
        
        for model in IMAGE_MODELS:
            # Unpack structure
            display_name, style, type_name, icon, desc = model
            
            if style not in styles_map:
                styles_map[style] = {
                    "description": desc, 
                    "types": []
                }
            
            # Add type if explicit (and unique to avoid dupes)
            if type_name and type_name not in styles_map[style]["types"]:
                styles_map[style]["types"].append(type_name)

        return {
            "styles": list(styles_map.keys()),
            "style_details": styles_map,
            # Hardcoded ratios as they are constant for now; can be dynamic if models.py exports them
            "ratios": ["1152:896", "896:1152", "1024:1024", "1344:768", "768:1344", "1280:720"],
            "schedulers": ["euler_a"] # Deprecated/Hidden logic
        }
    except Exception as e:
        logger.error(f"Schema Error: {e}")
        # Fallback to hardcoded if import completely fails
        return {
            "styles": ["anime", "car", "hyperrealistic", "zombie"], 
            "error": str(e)
        }

