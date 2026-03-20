import asyncio
import logging
import json
import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import subprocess
import concurrent.futures

# Logger
logger = logging.getLogger("QR_API")

router = APIRouter(prefix="/qr", tags=["QR Studio"])

# Thread pool for running blocking QR generation
qr_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix="QR_Gen_")

# Paths
ROOT_DIR = Path(r"d:\neural_citadel")
# QR Studio runs on Global Python due to complex dependencies
QR_VENV_PYTHON = r"C:\Program Files\Python310\python.exe"
QR_RUNNER = "apps.qr_studio.runner"

# Active diffusion processes (session_id -> subprocess)
active_processes: Dict[str, subprocess.Popen] = {}

class QRRequest(BaseModel):
    handler: str = "url"
    data: str
    mode: str = "gradient" # gradient, svg, diffusion
    colors: Optional[List[str]] = None # For manual gradient
    mask: str = "radial"
    prompt: Optional[str] = None # For diffusion
    gradient_type: Optional[str] = None # radial, horizontal, vertical, diagonal
    module_drawer: Optional[str] = None # rounded, square, circle, gapped
    logo_path: Optional[str] = None # Path to center logo
    session_id: Optional[str] = None # For tracking/cancellation

class CancelRequest(BaseModel):
    session_id: str

@router.post("/generate")
async def generate_qr(req: QRRequest):
    """
    Generate QR Code (SVG or Gradient mode).
    Returns JSON with output path (as static URL).
    Runs in background thread to avoid blocking server.
    """
    try:
        args = [
            QR_VENV_PYTHON,
            "-m", QR_RUNNER,
            "--handler", req.handler,
            "--data", req.data,
            "--no-print"  # Prevent ASCII print (fails on Windows)
        ]
        
        if req.mode == "svg":
            args.append("--svg")
        elif req.mode == "gradient":
            if req.colors and len(req.colors) >= 2:
                args.append("--gradient")
                args.append("manual")
                # Runner expects 3 colors: BACK CENTER EDGE
                # BACK = white (background), CENTER = start color, EDGE = end color
                back = "#FFFFFF"  # Always white background
                center = req.colors[0]  # Start color
                edge = req.colors[1]    # End color
                args.extend(["--colors", back, center, edge])
                args.extend(["--mask", req.mask])
            else:
                args.append("--gradient")
                args.append("auto")
            
            # Add module drawer
            if req.module_drawer:
                args.extend(["--drawer", req.module_drawer])
            
            # Add logo
            if req.logo_path:
                args.extend(["--logo", req.logo_path])
                
        elif req.mode == "diffusion":
            args.append("--diffusion")
            if req.prompt:
                args.extend(["--prompt", req.prompt])
            
        logger.info(f"Generating QR: {args}")
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(qr_executor, _run_qr_subprocess, args)
        return result

    except Exception as e:
        logger.error(f"QR Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _run_qr_subprocess(args: list) -> dict:
    """Run QR generation subprocess in thread (blocking call)."""
    proc = subprocess.run(
        args,
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )
    
    if proc.returncode != 0:
        raise Exception(f"QR Gen failed: {proc.stderr}")
         
    # Parse output for path
    output = proc.stdout
    for line in output.splitlines():
        if "[OUTPUT]" in line:
            raw_path = line.split("[OUTPUT]", 1)[1].strip()
            # Convert local path to static URL
            path_obj = Path(raw_path)
            
            # Find relative path from assets/qr_code directory
            qr_code_dir = ROOT_DIR / "assets" / "qr_code"
            try:
                rel_path = path_obj.relative_to(qr_code_dir)
                static_url = f"/static/qr_code/{rel_path.as_posix()}"
            except ValueError:
                # Fallback: just use filename in qr_code root
                static_url = f"/static/qr_code/{path_obj.name}"
            
            return {"status": "success", "path": static_url, "local_path": raw_path}
    
    raise Exception("Could not find output path in logs")


@router.post("/generate-stream")
async def generate_qr_stream(req: QRRequest):
    """
    Generate QR Code with SSE streaming (for diffusion mode).
    Streams progress from subprocess stdout asynchronously.
    """
    async def stream_generator():
        try:
            args = [
                QR_VENV_PYTHON,
                "-m", QR_RUNNER,
                "--handler", req.handler,
                "--data", req.data,
                "--diffusion"
            ]
            
            if req.prompt:
                args.extend(["--prompt", req.prompt])
            
            logger.info(f"Generating QR (streaming): {args}")
            
            # Use asyncio create_subprocess_exec for NON-BLOCKING I/O
            proc = await asyncio.create_subprocess_exec(
                *args,
                cwd=str(ROOT_DIR),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            # Track for cancellation
            session_id = req.session_id or str(uuid.uuid4())
            active_processes[session_id] = proc
            
            try:
                while True:
                    # Read line asynchronously - this yields control to event loop!
                    line_bytes = await proc.stdout.readline()
                    if not line_bytes:
                        break
                    
                    line = line_bytes.decode('utf-8', errors='replace').strip()
                    if not line:
                        continue
                    
                    # Check for output path
                    if "[OUTPUT]" in line:
                        raw_path = line.split("[OUTPUT]", 1)[1].strip()
                        path_obj = Path(raw_path)
                        qr_code_dir = ROOT_DIR / "assets" / "qr_code"
                        try:
                            rel_path = path_obj.relative_to(qr_code_dir)
                            static_url = f"/static/qr_code/{rel_path.as_posix()}"
                        except ValueError:
                            static_url = f"/static/qr_code/{path_obj.name}"
                        
                        yield f"data: {json.dumps({'status': 'complete', 'path': static_url})}\n\n"
                    else:
                        # Send progress status
                        yield f"data: {json.dumps({'status': line})}\n\n"
                
                await proc.wait()
                
            finally:
                if session_id in active_processes:
                    del active_processes[session_id]
                    
        except Exception as e:
            logger.error(f"SSE Error: {e}")
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/cancel")
async def cancel_generation(req: CancelRequest):
    """Cancel an active diffusion QR generation."""
    if req.session_id in active_processes:
        proc = active_processes[req.session_id]
        try:
            proc.terminate()
            # Handle asyncio process (which returns awaitable from wait())
            import inspect
            if inspect.iscoroutinefunction(proc.wait) or hasattr(proc, 'wait') and inspect.isawaitable(proc.wait()):
                # It's an asyncio process
                try:
                    await asyncio.wait_for(proc.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    proc.kill()
            else:
                # Synchronous Popen
                proc.wait(timeout=5)
        except Exception as e:
            logger.warning(f"Error terminating process: {e}")
            try:
                proc.kill()
            except:
                pass
                
        if req.session_id in active_processes:
            del active_processes[req.session_id]
            
        logger.info(f"Cancelled QR generation: {req.session_id}")
        return {"status": "cancelled"}
    return {"status": "not_found"}


@router.get("/schema")
async def get_qr_schema():
    """
    Get schema for QR Studio UI generation.
    Returns handlers as flat list (for Flutter), plus style options.
    """
    try:
        from apps.qr_studio.data import handlers
        import inspect
        
        # Build FLAT handlers list (Flutter expects: List<QRHandlerSchema>)
        handler_list = []
        
        full_map = handlers.get_all_handlers()
        
        for category, cat_handlers in full_map.items():
            for name, func in cat_handlers.items():
                # Inspect function params
                sig = inspect.signature(func)
                params = []
                for param_name, param in sig.parameters.items():
                    p_info = {
                        "name": param_name,
                        "required": param.default == inspect.Parameter.empty,
                        "type": "str"  # Default to string input
                    }
                    params.append(p_info)
                
                # Get docstring for description
                desc = func.__doc__ or name
                
                handler_list.append({
                    "id": name,
                    "name": name.replace("_", " ").title(),
                    "category": category,
                    "description": desc.split("\n")[0].strip(),
                    "params": params
                })

        # Style options
        return {
            "handlers": handler_list,
            "drawers": ["rounded", "square", "circle", "gapped"],
            "gradients": ["radial", "vertical", "horizontal", "diagonal"],
            "eye_styles": ["square", "rounded", "circle"]
        }

    except Exception as e:
        logger.error(f"Schema Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
