# 🏭 Systems Architecture

The architectural beauty of **Neural Citadel** lies in its decoupling of the heavy AI/ML libraries from the core web and desktop frameworks. 

## The Dual-Client Bridge Pattern

Neural Citadel services two primary clients, but they interface with the backend in radically different ways due to their deployment constraints.

### 1. The Mobile HTTP Path (FastAPI Gateway)
The **Flutter Mobile App** (`mobile_citadel`) operates remotely over a local area network (LAN) or tunnel.
- It connects to the `infra/server/main.py` FastAPI instance.
- **Isolation Constraint:** The `server_venv` contains **ZERO** machine learning libraries (`torch`, `diffusers`, etc.). If it did, Uvicorn would crash under the memory weight just booting up.
- When an API endpoint is hit, the gateway uses native Python `subprocess.Popen` to spin up a completely isolated Python environment (e.g., `image_venv`), passes the arguments via `stdin` or CLI, and streams the `stdout` response back down to the mobile client in real-time using FastAPI SSE (Server-Sent Events).

### 2. The Desktop QProcess Path
The **PyQt6 Desktop App** (`infra/gui/main_window.py`) runs on the host machine.
- It bypasses the FastAPI HTTP gateway entirely to eliminate network serialization latency.
- Instead, it leverages Qt's massive C++ core using `QProcess` workers.
- When you click "Generate" in the GUI, a `QProcess` thread points directly to `venvs\env\image_venv\Scripts\python.exe` and executes `apps\image_gen\runner.py`.

## IPC Protocols

Because both clients rely on spinning up headless python scripts, Neural Citadel relies on robust **Inter-Process Communication (IPC)** via standard inputs/outputs.

1. **One-Shot Batching Mode:**
   Used for tasks like Image Generation or Movie Downloading. The gateway or GUI passes a JSON payload to the subprocess upon start. The subprocess executes the heavy lifting, dumps intermediate progress to `stdout` (which the gateway relays to the UI), and then exits, freeing all VRAM instantly.

2. **Persistent Streaming Mode:**
   Used primarily for LLM interaction (`core_agent`) and voice transcription. The script boots up, loads the LLM/Whisper model into VRAM, and enters an infinite `while True:` loop, continually listening to `stdin` for new commands and streaming token-by-token back out through `stdout`.
