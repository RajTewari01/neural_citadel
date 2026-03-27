# 🛠️ Setup & Installation Guide

Neural Citadel is built primarily for **Windows 10/11**, utilizing batch scripts and Windows-specific process isolation via `QProcess` and subprocesses.

## Prerequisites
- **OS:** Windows 10 or 11 (64-bit)
- **GPU:** Minimum Nvidia GTX 1650 (4GB VRAM target via strict FP32/CPU offloading)
- **Git:** Installed and added to PATH
- **Python:** Python 3.11.x (Add to PATH during installation)
- **System Tools:** FFmpeg (required for `movie_venv` and audio/video processing)

## Installation Workflow

### 1. Clone the Monorepo
```bash
git clone https://github.com/RajTewari01/neural_citadel.git
cd neural_citadel
```

### 2. Environment Setup
The platform relies on 11 distinct virtual environments to prevent dependency conflicts (e.g., PyTorch vs Diffusers vs Llama-CPP versions).

Navigate to the `venvs/` directory and execute the setup batch scripts. These scripts will automatically generate the corresponding `venv` folders inside `venvs/env/` to match the exact `pip list` requirements documented in the Engine Registry.

### 3. Model Weights & SafeTensors
Weights for models like **Stable Diffusion**, **BLIP-2**, and **Llama 3** are strictly `.gitignore`'d. 
- You must download them manually to the respective `apps/` dictionaries or allow the engines to pull them from Hugging Face upon initial execution.
- We strongly recommend using FP16 weights but forcing execution parameters to FP32 if you are on Turing architecture to prevent NaN errors.

### 4. Running the Ecosystem

**To launch the FastAPI Gateway (for Mobile Client / API Access):**
```bash
cd infra/server
..\..\venvs\env\server_venv\Scripts\python main.py
```
This runs `uvicorn` on `0.0.0.0:8000`, exposing all 15 routers for the mobile UI.

**To launch the PyQt Desktop Dashboard:**
```bash
cd infra/gui
..\..\venvs\env\pyqt_venv\Scripts\python main_window.py
```
This will launch the native GUI which connects directly to the underlying scripts via `QProcess` bypassing the HTTP API layer entirely for zero-latency execution.
