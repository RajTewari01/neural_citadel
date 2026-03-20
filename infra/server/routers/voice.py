import asyncio
import logging
import json
import base64
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse, Response
from pydantic import BaseModel
from typing import Optional

# Logger
logger = logging.getLogger("VOICE_API")

router = APIRouter(prefix="/voice", tags=["Voice"])

class VoiceState:
    process: asyncio.subprocess.Process = None
    lock = asyncio.Lock()

state = VoiceState()

class SpeakRequest(BaseModel):
    text: str
    voice: str = "en-US" # Default or specific voice ID if supported
    speed: float = 1.0

async def start_engine():
    """Start the Voice engine (STT/TTS) subprocess."""
    # Use speech_venv
    venv_python = r"d:\neural_citadel\venvs\env\speech_venv\Scripts\python.exe"
    # Use existing or wrapper script. We might need a wrapper if the existing one is GUI-bound.
    # For now, let's assume we use a modified version or wrapper of voice_engine.py
    # But wait, existing voice_engine.py is for STT mainly. 
    # For TTS, we have `sherpa_tts.py` or similar. 
    # Let's point to a new wrapper we will create: `infra/standalone/voice_server_wrapper.py`
    script = r"d:\neural_citadel\infra\standalone\voice_server_wrapper.py"
    
    logger.info(f"Starting Voice Engine: {script}")
    
    try:
        state.process = await asyncio.create_subprocess_exec(
            venv_python, script,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Wait for "READY"
        while True:
            line = await state.process.stdout.readline()
            if not line:
                break
            decoded = line.decode().strip()
            logger.info(f"Voice Engine Init: {decoded}")
            if decoded == "READY":
                logger.info("Voice Engine is READY")
                break
                
    except Exception as e:
        logger.error(f"Failed to start voice engine: {e}")

async def stop_engine():
    if state.process:
        try:
            state.process.terminate()
            await state.process.wait()
        except:
            pass
        state.process = None

# @router.on_event("startup")
# async def startup_event():
#     # Lazy loading enabled
#     pass

@router.on_event("shutdown")
async def shutdown_event():
    await stop_engine()

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Accepts audio file, returns text."""
    if not state.process:
        logger.info("Lazy Loading: Starting Voice Engine...")
        await start_engine()
        if not state.process:
             raise HTTPException(status_code=503, detail="Voice Engine failed to start")
        
        
    await state.lock.acquire()
    try:
        # Save temp file
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp:
            content = await file.read()
            temp.write(content)
            temp_path = temp.name
            
        # Send command
        cmd = {
            "action": "transcribe",
            "file_path": temp_path
        }
        state.process.stdin.write((json.dumps(cmd) + "\n").encode())
        await state.process.stdin.drain()
        
        # Read response
        while True:
            line = await state.process.stdout.readline()
            if not line:
                break
            resp = json.loads(line.decode().strip())
            
            if resp.get("status") == "success":
                # Cleanup
                os.unlink(temp_path)
                return JSONResponse({"text": resp.get("text")})
            elif resp.get("status") == "error":
                os.unlink(temp_path)
                raise HTTPException(status_code=500, detail=resp.get("message"))
                
    except Exception as e:
        logger.error(f"Transcribe error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        state.lock.release()

@router.post("/speak")
async def text_to_speech(req: SpeakRequest):
    """Accepts text, returns audio stream or file."""
    if not state.process:
        logger.info("Lazy Loading: Starting Voice Engine...")
        await start_engine()
        if not state.process:
             raise HTTPException(status_code=503, detail="Voice Engine failed to start")

    await state.lock.acquire()
    try:
        cmd = {
            "action": "speak",
            "text": req.text,
            "voice": req.voice,
            "speed": req.speed
        }
        state.process.stdin.write((json.dumps(cmd) + "\n").encode())
        await state.process.stdin.drain()
        
        # Read response (Assuming engine returns path to generated file for now)
        while True:
            line = await state.process.stdout.readline()
            if not line:
                break
            resp = json.loads(line.decode().strip())
            
            if resp.get("status") == "success":
                audio_path = resp.get("audio_path")
                
                # Stream the file back
                def iterfile():
                    with open(audio_path, mode="rb") as file_like:
                        yield from file_like
                
                return StreamingResponse(iterfile(), media_type="audio/wav")
                
            elif resp.get("status") == "error":
                raise HTTPException(status_code=500, detail=resp.get("message"))

    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        state.lock.release()
