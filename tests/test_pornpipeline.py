
import sys
import gc
import torch
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

# Import engine only when needed to control memory
from apps.image_gen.pipeline.porn import get_porn_config

def run_test_case(case_name, prompt, ratio="portrait"):
    print(f"\nRESTARTING ENGINE FOR: {case_name}")
    print("-" * 50)
    
    # Import inside function to potentially help with cleanup
    from apps.image_gen.engine import DiffusionEngine
    
    engine = DiffusionEngine()
    
    try:
        print(f"Prompt: {prompt}")
        
        # force_uniform/trans checks handled by prompt keywords in porn.py
        config = get_porn_config(
            prompt=prompt,
            aspect_ratio=ratio
        )
        
        # Ensure we are using URPM (Stable on 4GB)
        # porn.py detection uses URPM for "hyperrealistic" or default
        
        output_path = engine.generate(config)
        print(f"SUCCESS: Generated {output_path.name}")
        
    except Exception as e:
        print(f"FAILED: {case_name} - {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Aggressive cleanup from OUTSIDE engine
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
    # Test Cases - All optimized for URPM (2.1GB) to ensure they run on 4GB VRAM
    
    # 1. General NSFW
    # run_test_case(
    #     "URPM_General", 
    #     "hyperrealistic 8k uhd photo of nude amateur selfie in bedroom, messy hair, detailed skin"
    # )
    
    # 2. Uniform Fetish (Trigger: uniform)
    # run_test_case(
    #     "URPM_Uniform",
    #     "hyperrealistic 8k uhd photo of schoolgirl in uniform classroom, slut uniform, detailed"
    # )
    
    # 3. Trans Fetish (Trigger: futa) - User requested ONLY verify this
    run_test_case(
        "Futa_Model_Test",
        "hyperrealistic 8k uhd photo of futanari with large erection, 1girl penis, testicles, posing"
    )
