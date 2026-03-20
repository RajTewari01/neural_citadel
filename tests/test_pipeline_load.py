"""
Test: Can we load the production engine pipeline?
"""
import sys
from pathlib import Path

# Add project root
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

print("Step 1: Importing engine...")
try:
    from apps.image_gen.engine import DiffusionEngine
    from apps.image_gen.pipeline.pipeline_types import PipelineConfigs
    print("   OK: Imports successful")
except Exception as e:
    print(f"   FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("Step 2: Creating config...")
try:
    config = PipelineConfigs(
        base_model=Path(r"D:\neural_citadel\assets\models\image_gen\diffusion\illustrator\diffusionBrushEverythingSFWNSFWAll_v10.safetensors"),
        output_dir=Path(r"D:\neural_citadel\assets\generated"),
        prompt="a cat",
        vae="realistic",
        scheduler_name="euler_a",
        upscale_method="None"
    )
    print("   OK: Config created")
except Exception as e:
    print(f"   FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("Step 3: Creating engine...")
try:
    engine = DiffusionEngine()
    print("   OK: Engine created")
except Exception as e:
    print(f"   FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("Step 4: Loading model...")
try:
    engine.load_model(config)
    print("   OK: Model loaded")
except Exception as e:
    print(f"   FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n=== ALL TESTS PASSED ===")
engine.unload()
