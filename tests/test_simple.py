"""
Simple test for production engine - captures full error
"""
import sys
from pathlib import Path

# Add project root
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

try:
    from apps.image_gen.engine import DiffusionEngine
    from apps.image_gen.pipeline.pipeline_types import PipelineConfigs
    
    config = PipelineConfigs(
        base_model=Path(r"D:\neural_citadel\assets\models\image_gen\diffusion\illustrator\diffusionBrushEverythingSFWNSFWAll_v10.safetensors"),
        output_dir=Path(r"D:\neural_citadel\assets\generated"),
        prompt="a cat",
        vae="realistic"
    )
    
    engine = DiffusionEngine()
    output = engine.generate(config)
    print(f"SUCCESS: {output}")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
