
import sys
import os
import asyncio
import json
from pathlib import Path

# Setup Path
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

async def test_interactive():
    print(f"Testing interactive wrapper from: {os.getcwd()}")
    
    # Python executable from coreagentvenv
    python_exe = r"d:\neural_citadel\venvs\env\coreagentvenv\Scripts\python.exe"
    wrapper_script = r"d:\neural_citadel\infra\server\engines\reasoning_wrapper.py"
    
    # 1. Start Process
    proc = await asyncio.create_subprocess_exec(
        python_exe, wrapper_script,
        cwd=str(ROOT_DIR),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    print("Process started. Waiting for READY...")
    
    # 2. Wait for READY
    while True:
        line = await proc.stdout.readline()
        if not line: break
        decoded = line.decode().strip()
        print(f"STDOUT: {decoded}")
        if decoded == "READY":
            print("Received READY signal.")
            break
            
    # 3. Send Prompt
    prompt_payload = {
        "prompt": "Say hello world",
        "history": []
    }
    input_json = json.dumps(prompt_payload) + "\n"
    print(f"Sending: {input_json.strip()}")
    
    proc.stdin.write(input_json.encode())
    await proc.stdin.drain()
    
    # 4. Read Response
    print("Reading response...")
    while True:
        line = await proc.stdout.readline()
        if not line: break
        
        decoded = line.decode().strip()
        print(f"STDOUT: {decoded}")
        if decoded == "DONE":
            print("Received DONE signal.")
            break
            
    proc.terminate()
    print("Test Complete.")

if __name__ == "__main__":
    asyncio.run(test_interactive())
