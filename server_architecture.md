# Neural Citadel - Server Architecture & Dependency Isolation

This document outlines the strict isolation strategy used in the Neural Citadel Backend (`infra/server`). The system is designed as a **Lightweight Gateway** that delegates heavy computational tasks to **Isolated Subprocesses**, each running in its own dedicated Virtual Environment.

## Core Design Principles
1.  **Gateway-Only Main Process**: The main FastAPI process (`main.py`) is lightweight. It does **not** import PyTorch, TensorFlow, Diffusers, or other heavy libraries. It only handles HTTP routing and subprocess management.
2.  **Strict Venv Isolation**: Each functional "App" (Reasoning, Image Gen, Movies) runs in a specific, separate virtual environment to prevent dependency conflicts (e.g., `numpy` version mismatches).
3.  **Lazy Loading**: Subprocesses are spawned only when a user requests a specific feature. They terminate after execution (except for persistent engines like Voice/Writing), saving RAM.

## Subsystem Map

| App Module | Router Path | Virtual Environment | Execution Mode |
| :--- | :--- | :--- | :--- |
| **Gateway** | `infra/server/main.py` | `server_venv` | **Persistent** (Lightweight) |
| **Movie Downloader** | `routers/movie.py` | `venvs/env/movie_venv` | **On-Demand** (One-shot CLI) |
| **Image Generation** | `routers/image.py` | `venvs/env/image_venv` | **On-Demand** (Streamed CLI) |
| **Reasoning (R1)** | `routers/chat.py` | `venvs/env/coreagentvenv` | **On-Demand** (One-shot CLI) |
| **Coding (DeepSeek)** | `routers/chat.py` | `venvs/env/coreagentvenv` | **On-Demand** (One-shot CLI) |
| **Hacking (Seneca)** | `routers/chat.py` | `venvs/env/coreagentvenv` | **On-Demand** (One-shot CLI) |
| **Voice (STT/TTS)** | `routers/voice.py` | `venvs/env/speech_venv` | **Persistent** (Background Service) |
| **QR Studio** | `routers/qr.py` | `server_venv` | **On-Demand** (One-shot CLI) |

## Implementation Proof (Audit Findings)

### 1. Movie Downloader
**Source**: `infra/server/routers/movie.py`
```python
MOVIE_VENV_PYTHON = r"d:\neural_citadel\venvs\env\movie_venv\Scripts\python.exe"
# ...
proc = await asyncio.create_subprocess_exec(MOVIE_VENV_PYTHON, ...)
```
*Status: ISOLATED. Uses `movie_venv`.*

### 2. Reasoning & Chat
**Source**: `infra/server/routers/chat.py`
```python
CORE_VENV_PYTHON = r"d:\neural_citadel\venvs\env\coreagentvenv\Scripts\python.exe"
# ...
await asyncio.create_subprocess_exec(CORE_VENV_PYTHON, "-m", REASONING_SCRIPT, ...)
```
*Status: ISOLATED. Uses `coreagentvenv`. Logic resides in `infra/standalone/*_engine.py`.*

### 3. Image Generation
**Source**: `infra/server/routers/image.py`
```python
IMAGE_VENV_PYTHON = r"d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe"
# ...
state.process = await asyncio.create_subprocess_exec(IMAGE_VENV_PYTHON, ...)
```
*Status: ISOLATED. Uses `image_venv`.*

## Request Flow
1.  **Mobile App** sends HTTP POST to `http://IP:8000/chat/reasoning`.
2.  **FastAPI Gateway** receives request.
3.  **Router** spawns `python.exe` from `coreagentvenv`.
4.  **Subprocess** loads PyTorch/LLM, processes prompt, streams output to stdout.
5.  **Router** reads stdout and streams response back to Mobile App.
6.  **Subprocess** terminates, freeing VRAM.

## flutter App Integration
The Flutter Mobile App is a **Thin Client**. It does not concern itself with Python dependencies. It simply calls the unified API endpoints, and the server handles the complexity of switching environments.
