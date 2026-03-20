import subprocess
import json
import sys
import os
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent
CORE_PYTHON = r"D:\neural_citadel\venvs\env\coreagentvenv\Scripts\python.exe"
TRANSLATOR_SCRIPT = PROJECT_ROOT / "apps/newspaper_publisher/language/translator.py"
TEMP_JSON = PROJECT_ROOT / "test_input.json"

def test_translation():
    print("--- [TEST] Translation Pipeline ---")
    
    # 1. Create dummy data
    data = [
        {
            "title": "Artificial Intelligence transforms the world",
            "content": "AI is changing how we live and work. Neural Citadel is at the forefront.",
            "category": "TECHNOLOGY"
        }
    ]
    
    with open(TEMP_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
        
    print(f"[1] Created test data: {data[0]['title']}")
    
    # 2. Run subprocess
    target_lang = "Hindi"
    cmd = [
        CORE_PYTHON,
        str(TRANSLATOR_SCRIPT),
        "--input", str(TEMP_JSON),
        "--lang", target_lang
    ]
    
    print(f"[2] Running translator for: {target_lang}")
    try:
        subprocess.run(cmd, check=True)
        print("[3] Subprocess completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"[!] Subprocess FAILED: {e}")
        return

    # 3. Check result
    if not os.path.exists(TEMP_JSON):
        print("[!] Output file missing!")
        return
        
    with open(TEMP_JSON, "r", encoding="utf-8") as f:
        res = json.load(f)
        
    print("\n--- [RESULT] ---")
    print(f"Original Title: Artificial Intelligence transforms the world")
    print(f"Translated Title: {res[0]['title']}")
    print(f"Translated Content: {res[0]['content']}")
    print(f"Translated Category: {res[0]['category']}")
    print("----------------")
    
    # Cleanup
    os.remove(TEMP_JSON)

if __name__ == "__main__":
    test_translation()
