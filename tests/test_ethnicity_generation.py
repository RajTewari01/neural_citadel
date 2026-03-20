"""
Test Ethnicity Pipeline with Diffusion Upscaling
"""
import sys
from pathlib import Path

# Add project root
_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT))

from apps.image_gen.engine import DiffusionEngine
from apps.image_gen.pipeline.ethnicity import get_ethnicity_config

prompt_text = "high quality, 16K Ultra HD, beautiful and sexy Bioluminescent woman with a slim figure medium teardrop breasts, beautiful flowing Bioluminescent flowers forming a beautiful woman, full depth of field and realistic textures"

print("=" * 60)
print("TEST: Ethnicity Pipeline with Diffusion Upscaling")
print("=" * 60)

# Get config for Chinese ethnicity (majicmix)
config = get_ethnicity_config(prompt_text, ethnicity="chinese")

# Override with diffusion upscaling
config.upscale_method = "diffusion"

print(f"\nConfig:")
print(f"  Model: {config.base_model.name}")
print(f"  Size: {config.width}x{config.height}")
print(f"  Upscale: {config.upscale_method}")
print(f"  Steps: {config.steps}")
print(f"  CFG: {config.cfg}")

# Create engine and generate
print("\nInitializing engine...")
engine = DiffusionEngine()

print("Loading model...")
engine.load_model(config)

print("\nGenerating image...")
result = engine.generate(config)

if result:
    print(f"\n✅ Generation complete!")
    print(f"   Saved to: {result}")
else:
    print("\n❌ Generation failed")

# Cleanup
engine.unload()
print("\nDone!")
