"""
Verify New Car Styles
=====================
Targeted verification for the recently added LoRA styles:
1. RX7
2. JetCar
3. Motorbike
4. Autohome
5. Sketch (Updated)
"""

import sys
from pathlib import Path

# Add project root
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from apps.image_gen.pipeline.cars import get_car_config
from apps.image_gen.engine import DiffusionEngine

TEST_OUTPUT = _ROOT / "tests" / "output" / "new_cars"
TEST_OUTPUT.mkdir(parents=True, exist_ok=True)

def run_test():
    print(f"Initializing Engine...")
    engine = DiffusionEngine()
    
    # The 5 new/updated styles
    new_styles = ["rx7", "jetcar", "motorbike", "autohome", "sketch"]
    
    print(f"Testing {len(new_styles)} new styles: {new_styles}")
    
    for style in new_styles:
        print(f"\n{'='*50}")
        print(f"Generating Style: {style.upper()}")
        print(f"{'='*50}")
        
        try:
            config = get_car_config(
                prompt="test verification", 
                style=style,
                width=512, 
                height=384 
            )
            
            # Override for speed
            config.output_dir = TEST_OUTPUT
            config.upscale_method = "None" 
            config.steps = 15 
            
            output_path = engine.generate(config)
            print(f"SUCCESS -> {output_path}")
            
        except Exception as e:
            print(f"FAILED -> {style}: {e}")

if __name__ == "__main__":
    run_test()
