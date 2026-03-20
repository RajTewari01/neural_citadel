"""
Verify All Car Styles
=====================
Generates a sample image for every supported style in `cars.py` to verify:
1. LoRA loading
2. Trigger word injection
3. VAE usage (None/Baked)
4. Scheduler compatibility

Output: tests/output/cars
"""

import sys
from pathlib import Path

# Add project root
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from apps.image_gen.pipeline.cars import get_car_config, CAR_STYLE_MAP
from apps.image_gen.engine import DiffusionEngine

# Test Configuration
TEST_OUTPUT = _ROOT / "tests" / "output" / "cars"
TEST_OUTPUT.mkdir(parents=True, exist_ok=True)
TEST_PROMPT = "concept art, studio lighting, side view"

def run_test():
    print(f"Initializing Engine...")
    engine = DiffusionEngine()
    
    styles = list(CAR_STYLE_MAP.keys())
    print(f"Testing {len(styles)} styles: {styles}")
    
    for style in styles:
        print(f"\n{'='*50}")
        print(f"Generating Style: {style.upper()}")
        print(f"{'='*50}")
        
        try:
            # Get default config
            config = get_car_config(
                prompt=TEST_PROMPT, 
                style=style,
                width=512, # Smaller for faster testing
                height=384 
            )
            
            # OVERRIDES for Verification
            config.output_dir = TEST_OUTPUT
            config.upscale_method = "None" 
            config.steps = 20 # Faster verification
            
            # Generate
            output_path = engine.generate(config)
            print(f"SUCCESS -> {output_path}")
            
        except Exception as e:
            print(f"FAILED -> {style}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    run_test()
