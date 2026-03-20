
import sys
import os
from pathlib import Path

# Setup Path
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

print(f"Running test from: {os.getcwd()}")
print(f"Calculated ROOT_DIR: {ROOT_DIR}")

try:
    from infra.standalone.reasoning_engine import load_model, MODEL_PATH
    print(f"Imported standalone. MODEL_PATH={MODEL_PATH}")
    print(f"Exists? {MODEL_PATH.exists()}")
    
    print("Calling load_model()...")
    llm = load_model()
    
    if llm:
        print("SUCCESS: Model loaded.")
    else:
        print("FAILURE: load_model() returned None.")

except Exception as e:
    print(f"CRITICAL EXCEPTION: {e}")
    import traceback
    traceback.print_exc()
