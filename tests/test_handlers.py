"""
End-to-end test with corrected field detection
"""
import subprocess
import json
import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[0]
sys.path.insert(0, str(ROOT))

from apps.qr_studio.data import handlers as handler_module

GLOBAL_PYTHON = r"C:\Program Files\Python310\python.exe"
RUNNER = ROOT / "apps" / "qr_studio" / "runner.py"

def _get_handler_fields(handler_name):
    func = getattr(handler_module, f"format_{handler_name}", None)
    if func:
        sig = inspect.signature(func)
        fields = []
        for name, param in sig.parameters.items():
            annotation = param.annotation
            if annotation != inspect.Parameter.empty:
                ann_str = str(annotation)
                if 'dict' in ann_str.lower() or 'list' in ann_str.lower():
                    continue
            if param.default == inspect.Parameter.empty:
                fields.append(name)
            elif len(fields) < 4 and param.default in ('', None):
                fields.append(name)
        return fields[:6]
    return ['data']

# Get all handlers
all_handlers = [name[7:] for name in dir(handler_module) if name.startswith('format_')]
print(f"Testing {len(all_handlers)} handlers...")

errors = []
successes = []

for handler_name in all_handlers:
    fields = _get_handler_fields(handler_name)
    
    # Build test data
    test_data = {}
    for fname in fields:
        if 'lat' in fname.lower():
            test_data[fname] = 28.6139
        elif 'lon' in fname.lower():
            test_data[fname] = 77.2090
        elif fname in ('latitude', 'longitude'):
            test_data[fname] = 28.6139
        else:
            test_data[fname] = "testvalue"
    
    # Build data arg
    if len(test_data) == 1:
        data_arg = str(list(test_data.values())[0])
    else:
        data_arg = json.dumps(test_data)
    
    cmd = [GLOBAL_PYTHON, str(RUNNER), "--handler", handler_name, "--data", data_arg, "--svg", "--no-print"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, cwd=str(ROOT))
        if "[OK]" in result.stdout or result.returncode == 0:
            successes.append(handler_name)
        else:
            errors.append((handler_name, fields))
    except Exception as e:
        errors.append((handler_name, fields))

print(f"\nSuccessful: {len(successes)}/{len(all_handlers)}")
print(f"Errors: {len(errors)}")

if errors:
    print(f"\nFailed handlers:")
    for name, fields in errors[:20]:
        print(f"  {name}: {fields}")
