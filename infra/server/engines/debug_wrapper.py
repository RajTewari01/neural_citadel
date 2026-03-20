
import sys
import os
import traceback

log_path = r"d:\neural_citadel\debug_log.txt"

with open(log_path, "w") as f:
    f.write(f"Python: {sys.executable}\n")
    f.write(f"CWD: {os.getcwd()}\n")
    
    # 1. Setup Path
    try:
        from pathlib import Path
        ROOT_DIR = Path(__file__).resolve().parents[3]
        f.write(f"Calculated ROOT_DIR: {ROOT_DIR}\n")
        if str(ROOT_DIR) not in sys.path:
            sys.path.append(str(ROOT_DIR))
            f.write("Added ROOT_DIR to sys.path\n")
    except Exception:
        f.write(f"Path Setup Failed:\n{traceback.format_exc()}\n")

    # 2. Try Import Standalone
    try:
        f.write("Attempting to import infra.standalone.reasoning_engine...\n")
        import infra.standalone.reasoning_engine
        f.write("SUCCESS: Imported reasoning_engine.\n")
    except Exception as e:
        f.write(f"FAIL: reasoning_engine import failed: {e}\n")
        f.write(traceback.format_exc() + "\n")
        f.write(f"Sys Path: {sys.path}\n")

    # 3. Try Import Llama
    try:
        import llama_cpp
        f.write("SUCCESS: Imported llama_cpp.\n")
    except Exception as e:
        f.write(f"FAIL: llama_cpp import failed: {e}\n")

print("Debug run complete.")
