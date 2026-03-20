import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

# Test import
print("Testing imports...")
try:
    from apps.image_gen.engine import DiffusionEngine
    print("Engine imported successfully")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
