
import sys
import gc
import torch
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from apps.image_gen.pipeline.ethnicity import get_ethnicity_config

def run_test_case(case_name, prompt, ethnicity=None):
    print(f"\nRESTARTING ENGINE FOR: {case_name}")
    print("-" * 50)
    
    from apps.image_gen.engine import DiffusionEngine
    
    engine = DiffusionEngine()
    
    try:
        print(f"Prompt: {prompt}")
        
        config = get_ethnicity_config(
            prompt=prompt,
            ethnicity=ethnicity,
            auto_detect=True
        )
        
        # Verify LoRA presence
        polaroid_present = any("polaroid" in str(l.lora_path).lower() for l in config.lora)
        if polaroid_present:
            print("✅ CHECK: Polaroid LoRA detected in config.")
        else:
            print("❌ CHECK: Polaroid LoRA MISSING from config!")
        
        output_path = engine.generate(config)
        print(f"SUCCESS: Generated {output_path.name}")
        
    except Exception as e:
        print(f"FAILED: {case_name} - {e}")
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
    # Test 1: Indian + Polaroid
    run_test_case(
        "Indian_Polaroid", 
        "polaroid photo of beautiful indian woman in traditional saree",
        ethnicity="indian"
    )
    
    # Test 2: Asian (Auto) + Polaroid
    run_test_case(
        "Asian_Polaroid_Auto",
        "polaroid style portrait of vietnamese girl smiling"
    )
