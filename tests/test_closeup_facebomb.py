
import sys
import gc
import torch
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

# Import AFTER path update
from apps.image_gen.pipeline.closeup_anime import closeup_anime
from apps.image_gen.engine import DiffusionEngine

def run_test():
    print(f"\nRESTARTING ENGINE FOR: Closeup_FaceBomb_Test")
    print("-" * 50)
    
    engine = DiffusionEngine()
    
    try:
        # Test default "closeup_anime" which should now be FaceBombMix
        prompt = "magical girl with glowing blue eyes, intricate details"
        print(f"Prompt: {prompt}")
        
        config = closeup_anime(prompt)
        
        print(f"Model Name: {config.base_model.name}")
        # Verify it's FaceBomb (facebombmix_v1Bakedvae.safetensors)
        if "facebomb" in config.base_model.name.lower():
             print("✅ CHECK: FaceBombMix model detected in config.")
        else:
             print(f"❌ CHECK: Unexpected model: {config.base_model.name}")
             
        # Verify Template Trigger Injection
        if "ultra illustrated style" in config.prompt:
            print("✅ CHECK: Trigger word injected.")
        else:
            print("❌ CHECK: Trigger word MISSING.")

        output_path = engine.generate(config)
        print(f"SUCCESS: Generated {output_path.name}")
        
    except Exception as e:
        print(f"FAILED: Closeup_FaceBomb_Test - {e}")
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
