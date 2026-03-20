
import sys
import gc
import torch
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from apps.image_gen.pipeline.ethnicity import get_ethnicity_config
from apps.image_gen.engine import DiffusionEngine

def run_test():
    print(f"\nRESTARTING ENGINE FOR: FaceBomb_Test")
    print("-" * 50)
    
    engine = DiffusionEngine()
    
    try:
        # Test default "asian" which should now be FaceBombMix
        prompt = "beautiful asian girl portrait, detailed face, soft lighting"
        print(f"Prompt: {prompt}")
        
        config = get_ethnicity_config(
            prompt=prompt,
            ethnicity="asian",
            auto_detect=False
        )
        
        print(f"Model Name: {config.base_model.name}")
        if "facebomb" in config.base_model.name.lower():
             print("✅ CHECK: FaceBombMix model detected in config.")
        else:
             print(f"❌ CHECK: Unexpected model: {config.base_model.name}")

        output_path = engine.generate(config)
        print(f"SUCCESS: Generated {output_path.name}")
        
    except Exception as e:
        print(f"FAILED: FaceBomb_Test - {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if 'engine' in locals():
            try:
                engine.unload()
            except:
                pass
            del engine
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print("Memory Cleaned.")

if __name__ == "__main__":
    run_test()
