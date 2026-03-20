"""
Test script for the production DiffusionEngine
"""
from pathlib import Path
import sys

# Add project root to path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from apps.image_gen.engine import DiffusionEngine
from apps.image_gen.pipeline.pipeline_types import PipelineConfigs

# Create a simple test configuration
config = PipelineConfigs(
    base_model=Path(r"D:\neural_citadel\assets\models\image_gen\diffusion\illustrator\diffusionBrushEverythingSFWNSFWAll_v10.safetensors"),
    output_dir=Path(r"D:\neural_citadel\assets\generated"),
    prompt="a beautiful sunset over mountains, vibrant colors, dramatic lighting, 8k, highly detailed",
    vae="realistic",
    neg_prompt="blurry, low quality, distorted",
    scheduler_name="euler_a",
    width=512,
    height=512,
    steps=25,
    cfg=7.0,
    upscale_method="None"
)

# Initialize engine and generate
print("=== Testing Production DiffusionEngine ===\n")
engine = DiffusionEngine()

try:
    output_path = engine.generate(config)
    print(f"\n[SUCCESS] TEST PASSED: Image generated successfully at {output_path}")
except Exception as e:
    print(f"\n[FAILED] TEST FAILED: {e}")
    import traceback
    traceback.print_exc()
finally:
    engine.unload()
