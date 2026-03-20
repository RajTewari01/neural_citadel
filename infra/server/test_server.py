import subprocess
import time
import requests
import sys
import os
import threading

python_exe = r"d:\neural_citadel\venvs\env\server_venv\Scripts\python.exe"
server_script = r"d:\neural_citadel\infra\server\main.py"

print(f"Starting server: {server_script}")

# Capture stdout/stderr to check for startup logs
server_proc = subprocess.Popen(
    [python_exe, server_script],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

def stream_reader(stream, name):
    for line in stream:
        print(f"[{name}] {line.strip()}")

# Start reader threads
t1 = threading.Thread(target=stream_reader, args=(server_proc.stdout, "SERVER_OUT"))
t1.daemon = True
t1.start()
t2 = threading.Thread(target=stream_reader, args=(server_proc.stderr, "SERVER_ERR"))
t2.daemon = True
t2.start()

try:
    print("Waiting 15s for startup (Model loading takes time)...")
    time.sleep(15)
    
    try:
        print("Checking http://localhost:8000/status...")
        resp = requests.get("http://localhost:8000/status")
        print(f"Status: {resp.json()}")
        
        print("\nChecking NSFW Gen (Dry Run)...")
        # We won't send a real prompt to avoid waiting for heavy generation, 
        # but we check if endpoint exists (422 Unprocessable if args missing is a good sign)
        resp2 = requests.post("http://localhost:8000/nsfw/generate", json={}) 
        print(f"Gen Response Code: {resp2.status_code}")
        
        if resp.status_code == 200:
            print("\n✅ TEST PASSED: Server is online!")
        else:
            print("\n❌ TEST FAILED: Bad status code")
            
    except Exception as e:
        print(f"\n❌ TEST FAILED: Connection error: {e}")
finally:
    print("Stopping server...")
    server_proc.terminate()
    try:
        server_proc.wait(timeout=5)
    except:
        server_proc.kill()
