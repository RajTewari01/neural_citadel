import json
import asyncio
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List

# Logger
logger = logging.getLogger("NSFW_API")

router = APIRouter(prefix="/nsfw", tags=["NSFW"])

# Global Subprocess (State)
# In production, use app.state or a Dependency Injection singleton
class EngineState:
    process: asyncio.subprocess.Process = None
    lock = asyncio.Lock()

state = EngineState()

class GenerateRequest(BaseModel):
    prompt: str
    persona: str = "erotica"
    style: str = "romance"
    history: Optional[List[dict]] = []

async def start_engine():
    """Start the NSFW engine subprocess."""
    venv_python = r"d:\neural_citadel\venvs\env\coreagentvenv\Scripts\python.exe"
    script = r"d:\neural_citadel\infra\standalone\nsfw_writing_engine.py"
    
    logger.info(f"Starting NSFW Engine: {script}")
    
    try:
        state.process = await asyncio.create_subprocess_exec(
            venv_python, script,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Wait for "READY" signal
        while True:
            line = await state.process.stdout.readline()
            if not line:
                break
            decoded = line.decode().strip()
            logger.info(f"Engine Init: {decoded}")
            if decoded == "READY":
                logger.info("NSFW Engine is READY")
                break
                
    except Exception as e:
        logger.error(f"Failed to start engine: {e}")

async def stop_engine():
    """Stop the engine."""
    if state.process:
        logger.info("Stopping NSFW Engine...")
        if state.process.stdin:
            try:
                state.process.stdin.write(b'{"action": "quit"}\n')
                await state.process.stdin.drain()
            except:
                pass
        try:
            state.process.terminate()
            await state.process.wait()
        except:
            pass
        state.process = None

# @router.on_event("startup")
# async def startup_event():
#     # Lazy loading enabled - removing auto-start
#     pass

@router.on_event("shutdown")
async def shutdown_event():
    await stop_engine()

@router.post("/generate")
async def generate(req: GenerateRequest):
    if not state.process:
        logger.info("Lazy Loading: Starting NSFW Engine...")
        await start_engine()
        if not state.process:
             raise HTTPException(status_code=503, detail="Failed to start engine")

    # Acquire lock to ensure sequential processing
    await state.lock.acquire()

    async def event_generator():
        try:
            # Prepare command
            cmd = {
                "action": "generate",
                "prompt": req.prompt,
                "persona": req.persona,
                "style": req.style,
                "history": req.history
            }
            cmd_str = json.dumps(cmd) + "\n"
            
            # Send to engine
            state.process.stdin.write(cmd_str.encode())
            await state.process.stdin.drain()
            
            # Read output loop
            while True:
                line = await state.process.stdout.readline()
                if not line:
                    break
                
                decoded = line.decode().strip()
                
                if decoded == "DONE":
                    break
                elif decoded.startswith("ERROR:"):
                    yield f"Error: {decoded[6:]}\n"
                    break
                elif decoded.startswith("TOKEN:"):
                    # Extract raw JSON token string: TOKEN:"the"
                    # We output raw text for the stream
                    try:
                        raw_json = decoded[6:]
                        token = json.loads(raw_json)
                        yield token
                    except:
                        pass
                        
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"[System Error: {e}]"
        finally:
             state.lock.release()

    return StreamingResponse(event_generator(), media_type="text/plain")
