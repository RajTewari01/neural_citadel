"""
Full Car Pipeline Test with Diffusion Upscaling
================================================
Tests the car pipeline with detailed prompts and Diffusion upscaler.
Outputs to the pipeline's default directory (OUTPUT_DIR/images/cars).
"""

import sys
from pathlib import Path

# Add project root
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from apps.image_gen.pipeline.cars import get_car_config, GENERATED_OUTPUT
from apps.image_gen.engine import DiffusionEngine

# Detailed test prompts for each style
TEST_CASES = [
    {
        "style": "rx7",
        "prompt": "midnight blue Mazda RX-7 drifting on a winding mountain road, motion blur, sunset golden hour lighting, dramatic clouds"
    },
    {
        "style": "amsdr",
        "prompt": "classic yellow Ambassador taxi parked on a busy Kolkata street, Howrah Bridge in background, monsoon rain, reflections on wet road"
    },
    {
        "style": "retro",
        "prompt": "cherry red 1965 Ford Mustang convertible parked at a retro diner, neon signs, evening blue hour, chrome details gleaming"
    },
    {
        "style": "jetcar",
        "prompt": "Hanshin 5001 series train arriving at a suburban station, cherry blossom trees, spring afternoon, passengers waiting"
    },
    {
        "style": "f1",
        "prompt": "orange McLaren F1 LM supercar on a coastal highway, ocean waves crashing, dramatic storm clouds, professional automotive photography"
    }
]

def run_test():
    print(f"Initializing Engine...")
    engine = DiffusionEngine()
    
    print(f"Output Directory: {GENERATED_OUTPUT}")
    print(f"Testing {len(TEST_CASES)} styles with Diffusion upscaling\n")
    
    for test in TEST_CASES:
        style = test["style"]
        prompt = test["prompt"]
        
        print(f"\n{'='*60}")
        print(f"Style: {style.upper()}")
        print(f"Prompt: {prompt[:60]}...")
        print(f"{'='*60}")
        
        try:
            config = get_car_config(
                prompt=prompt, 
                style=style,
                width=768,
                height=512
            )
            
            # Enable Diffusion upscaling
            config.upscale_method = "Diffusion"
            config.steps = 30
            
            output_path = engine.generate(config)
            print(f"SUCCESS -> {output_path}")
            
        except Exception as e:
            print(f"FAILED -> {style}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    run_test()
