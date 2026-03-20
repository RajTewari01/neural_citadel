import asyncio
import logging
import json
import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Logger
logger = logging.getLogger("CHAT_API")

from infra.server import database as db


router = APIRouter(prefix="/chat", tags=["Chat"])

# Paths
ROOT_DIR = Path(r"d:\neural_citadel")
# All LLM engines use coreagentvenv
CORE_VENV_PYTHON = r"d:\neural_citadel\venvs\env\coreagentvenv\Scripts\python.exe"

# Engine Scripts
REASONING_SCRIPT = "infra.standalone.reasoning_engine"
CODE_SCRIPT = "infra.standalone.code_engine"
HACKING_SCRIPT = "infra.standalone.hacking_engine"
WRITING_SCRIPT = "infra.standalone.writing_engine"

class ChatRequest(BaseModel):
    prompt: str
    history: List[Dict[str, str]] = []
    model: str = "default" # For generic chat or code model selection
    user_email: Optional[str] = None

class WritingRequest(BaseModel):
    prompt: str
    persona: str = "therapist"
    style: str = "supportive"
    nsfw: bool = False
    history: List[Dict[str, str]] = []
    user_email: Optional[str] = None

class ChatState:
    # Writing engine is persistent
    writing_process: asyncio.subprocess.Process = None
    writing_lock = asyncio.Lock()
    
    # Simple lock for other one-shot engines to prevent OOM
    # (assuming we only want one heavy LLM running at a time)
    global_lock = asyncio.Lock()

state = ChatState()

# =============================================================================
# =============================================================================
# WRITING ENGINE (Persistent via Wrapper)
# =============================================================================
WRITING_SCRIPT_WRAPPER = "infra.server.engines.writing_wrapper"

# Model Paths
MODEL_PATH_SFW = r"d:\neural_citadel\assets\models\llm\llm\Mistral_7b_model\mistral-7b-instruct-v0.2.Q4_K_M.gguf"
MODEL_PATH_NSFW = r"d:\neural_citadel\assets\models\llm\llm\NSFW_Story_Model\Meta-Llama-3.1-8B-Instruct-abliterated-Q4_K_M.gguf"

@router.post("/writing")
async def chat_writing(req: WritingRequest):
    """Writing Persona Chat (Persistent)."""
    
    # Determine Model and Startup Args
    if req.nsfw:
        # NSFW Engine manages its own models internally (roleplay vs erotica)
        # We just tell the wrapper to switch to NSFW mode
        startup_args = ["--nsfw"]
        context_name = "Writing-NSFW"
    else:
        # SFW Engine takes an explicit model path
        startup_args = ["--model_path", MODEL_PATH_SFW]
        context_name = "Writing-SFW"

    # Extra payload for writing engine command
    payload = {
        "action": "generate",
        "persona": req.persona,
        "style": req.style
    }

    return await run_persistent_cli_llm(
        context_name, 
        WRITING_SCRIPT_WRAPPER, 
        req.prompt, 
        req.history, 
        startup_args=startup_args,
        extra_payload=payload
    )


# =============================================================================
# ONE-SHOT ENGINES (Reasoning, Hacking, Coding)
# =============================================================================

from infra.server.resource_manager import resource_manager

# Update script path to point to WRAPPER
REASONING_SCRIPT = "infra.server.engines.reasoning_wrapper"
CODE_SCRIPT_WRAPPER = "infra.server.engines.code_wrapper"
HACKING_SCRIPT_WRAPPER = "infra.server.engines.hacking_wrapper"

# ... (One-Shot fallback removed/unused)

async def run_persistent_cli_llm(context_name: str, script_module: str, prompt: str, history: List[Dict] = [], startup_args: List[str] = [], extra_payload: Dict[str, Any] = {}, user_email: str = None):
    """Run persistent CLI LLM with interactive JSON protocol."""
    
    async def process_creator():
        env = {"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
        import os
        full_env = os.environ.copy()
        full_env.update(env)
        
        args = [CORE_VENV_PYTHON, "-m", script_module] + startup_args
        
        proc = await asyncio.create_subprocess_exec(
            *args,
            cwd=str(ROOT_DIR),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=full_env
        )
        
        # Wait for READY
        try:
            # Loop until we see READY or timeout/EOF
            start_time = asyncio.get_event_loop().time()
            while True:
                if asyncio.get_event_loop().time() - start_time > 60.0:
                    raise asyncio.TimeoutError("Startup timed out")
                    
                line = await asyncio.wait_for(proc.stdout.readline(), timeout=60.0) 
                if not line: break
                
                decoded = line.decode().strip()
                if decoded == "READY":
                    break
                # Ignore "LOADED" or other noise
                logger.info(f"{context_name} startup msg: {decoded}")
                
        except Exception as e:
            logger.error(f"Startup error for {context_name}: {e}")
            if proc.returncode is None:
                proc.terminate()
            raise e
            
        return proc

    # Request execution (reuse if active)
    try:
        # Use context name to differentiate models (e.g. Coding-deepseek vs Coding-qwen)
        process = await resource_manager.request_execution(context_name, process_creator())
    except Exception as e:
        # If resource manager failed, maybe fallback?
        raise HTTPException(status_code=500, detail=f"Failed to load {context_name}: {e}")

    async def event_generator():
        try:
            # Send Command
            cmd = {
                "prompt": prompt,
                "history": history
            }
            # Merge extra payload
            cmd.update(extra_payload)

            process.stdin.write((json.dumps(cmd) + "\n").encode())
            await process.stdin.drain()
            
            # Accumulate response for logging
            full_response = []
            
            while True:
                line = await process.stdout.readline()
                if not line: break
                
                decoded = line.decode('utf-8', errors='replace').strip()
                if not decoded: continue
                
                if decoded == "DONE":
                    break
                elif decoded.startswith("TOKEN:"):
                    # Protocol: TOKEN:"json_string"
                    content = decoded[6:]
                    try:
                        token_text = json.loads(content)
                        # Re-emit with TOKEN: prefix and newline for Dart client
                        yield f"TOKEN:{json.dumps(token_text)}\n"
                        full_response.append(token_text)
                    except:
                        # Fallback
                        yield f"TOKEN:{content}\n"
                        full_response.append(content)
                elif decoded == "THINK_START":
                    yield "THINK_START\n"
                elif decoded == "THINK_END":
                    yield "THINK_END\n"
                elif decoded.startswith("ERROR:"):
                    yield f"ERROR:{decoded}\n"
            
            # Log Event for Admin Dashboard (POST-CHAT)
            try:
                from infra.server import database as db
                # We assume generic 'user' if not passed, but we really need it. 
                # Ideally pass user_email in extra_payload or history mechanism
                # For now using generic log.
                response_text = "".join(full_response)
                # Pass User Email here!
                db.log_event("chat", user_email=user_email, metadata={
                    "prompt": prompt, 
                    "response": response_text,
                    "context": context_name,
                    "model": extra_payload.get('model', 'unknown')
                })
            except Exception as e:
                logger.error(f"DB Log Error: {e}")
                
        except Exception as e:
            yield f" [System Error: {str(e)}]"
            
    return StreamingResponse(event_generator(), media_type="text/plain")


@router.post("/reasoning")
async def chat_reasoning(req: ChatRequest):
    """DeepSeek R1 Reasoning (Persistent Wrapper)."""
    # Security Check
    if req.user_email:
        u = db.get_user_by_email(req.user_email)
        if u and u.get('is_blocked') == 1:
             raise HTTPException(status_code=403, detail="ACCESS DENIED: User is terminated.")

    # Use persistent logic
    return await run_persistent_cli_llm("Reasoning", REASONING_SCRIPT, req.prompt, req.history, user_email=req.user_email)


@router.post("/code")
async def chat_code(req: ChatRequest):
    """DeepSeek/Qwen Coder (Persistent)."""
    # Security Check
    if req.user_email:
        u = db.get_user_by_email(req.user_email)
        if u and u.get('is_blocked') == 1:
             raise HTTPException(status_code=403, detail="ACCESS DENIED: User is terminated.")

    model = req.model if req.model in ["deepseek", "qwen"] else "deepseek"
    # Differentiate context by model so we can switch without killing the other if needed,
    # or just use one. Let's use unique context.
    context_name = f"Coding-{model}"
    
    return await run_persistent_cli_llm(
        context_name, 
        CODE_SCRIPT_WRAPPER, 
        req.prompt, 
        req.history,
        startup_args=["--model", model],
        user_email=req.user_email
    )


@router.post("/hacking")
async def chat_hacking(req: ChatRequest):
    """Seneca Hacking LLM (Persistent)."""
    # Security Check
    if req.user_email:
        u = db.get_user_by_email(req.user_email)
        if u and u.get('is_blocked') == 1:
             raise HTTPException(status_code=403, detail="ACCESS DENIED: User is terminated.")

    return await run_persistent_cli_llm("Hacking", HACKING_SCRIPT_WRAPPER, req.prompt, req.history, user_email=req.user_email)
