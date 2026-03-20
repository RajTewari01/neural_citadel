"""
Image Surgeon Test Script
=========================
Verifies SAM2 installation and basic functionality.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all modules can be imported."""
    print("1. Testing imports...")
    
    try:
        from configs.paths import (
            SAM2_MODELS, IMAGE_SURGEON_OUTPUT_DIR, 
            EXTRACTED_SUBJECTS_DIR, IMAGE_SURGEON_VENV
        )
        print("   ✅ configs.paths imports OK")
    except Exception as e:
        print(f"   ❌ configs.paths failed: {e}")
        return False
    
    try:
        from apps.image_surgeon.engine import SAM2Engine
        print("   ✅ SAM2Engine import OK")
    except Exception as e:
        print(f"   ❌ SAM2Engine import failed: {e}")
        return False
    
    return True


def test_model_exists():
    """Test that SAM2 model file exists."""
    print("\n2. Testing model files...")
    
    from configs.paths import SAM2_MODELS, SAM2_DEFAULT_MODEL
    
    for name, path in SAM2_MODELS.items():
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            print(f"   ✅ {name}: {path.name} ({size_mb:.1f} MB)")
        else:
            print(f"   ⚠️  {name}: NOT FOUND")
    
    if SAM2_DEFAULT_MODEL.exists():
        print(f"   ✅ Default model (small) exists")
        return True
    else:
        print(f"   ❌ Default model NOT FOUND: {SAM2_DEFAULT_MODEL}")
        return False


def test_engine_init():
    """Test SAM2Engine initialization."""
    print("\n3. Testing engine initialization...")
    
    from apps.image_surgeon.engine import SAM2Engine
    
    try:
        engine = SAM2Engine(model_size="small")
        print(f"   ✅ Engine created (device: {engine.device})")
        return True
    except Exception as e:
        print(f"   ❌ Engine init failed: {e}")
        return False


def test_sam2_import():
    """Test that SAM2 library can be imported."""
    print("\n4. Testing SAM2 library...")
    
    try:
        import sam2
        print(f"   ✅ sam2 package imported")
    except ImportError as e:
        print(f"   ❌ sam2 import failed: {e}")
        print("   Run: pip install sam2")
        return False
    
    try:
        from sam2.build_sam import build_sam2
        from sam2.sam2_image_predictor import SAM2ImagePredictor
        print(f"   ✅ SAM2 core modules OK")
        return True
    except ImportError as e:
        print(f"   ❌ SAM2 modules failed: {e}")
        return False


def test_vram_check():
    """Check VRAM availability."""
    print("\n5. Checking GPU/VRAM...")
    
    try:
        import torch
        
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            total_vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
            print(f"   ✅ GPU: {gpu_name}")
            print(f"   ✅ Total VRAM: {total_vram:.1f} GB")
            
            if total_vram < 4:
                print("   ⚠️  Less than 4GB VRAM - use 'tiny' model")
            else:
                print("   ✅ VRAM sufficient for 'small' model")
        else:
            print("   ⚠️  No CUDA GPU detected - will use CPU (slower)")
        
        return True
    except Exception as e:
        print(f"   ❌ GPU check failed: {e}")
        return False


def main():
    print("=" * 60)
    print("Image Surgeon - Verification Test")
    print("=" * 60)
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("Model Files", test_model_exists()))
    results.append(("Engine Init", test_engine_init()))
    results.append(("SAM2 Library", test_sam2_import()))
    results.append(("GPU/VRAM", test_vram_check()))
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {name}: {status}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 All tests passed! Image Surgeon is ready.")
    else:
        print("⚠️  Some tests failed. Review the output above.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
