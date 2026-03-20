"""
CatVTON Virtual Try-On Wrapper

Simplified wrapper for CatVTON clothes swapping.
Uses Person image + Garment image + Mask (from SegFormer) → Person wearing new clothes

Based on https://github.com/Zheng-Chong/CatVTON
"""

import sys
import torch
import numpy as np
from pathlib import Path
from PIL import Image, ImageFilter

# Dynamic path detection (cross-platform)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CATVTON_ROOT = PROJECT_ROOT / "tools" / "CatVTON"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(CATVTON_ROOT))


class CatVTONEngine:
    """
    Virtual try-on engine using CatVTON.
    Swaps clothes from a garment image onto a person image.
    """
    
    def __init__(self, device: str = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.pipeline = None
        
    def load(self):
        """Load CatVTON pipeline from HuggingFace."""
        if self.pipeline is not None:
            return
        
        from model.pipeline import CatVTONPipeline
        from diffusers import UNet2DConditionModel, AutoencoderKL
        import torch
        import gc
        import time
        
        # Cleanup aggressively (SegFormer might have left GPU dirty)
        print("🧹 Cleaning up GPU...")
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        time.sleep(1)  # Wait for GPU to reclaim resources
        
        print("[CatVTON] Loading CatVTON (FP32 Full Precision)...")
        # Using FP32 to avoid NaN errors on GTX 1650 which cause dark images
        
        try:
            self.pipeline = CatVTONPipeline(
                attn_ckpt_version="vitonhd",
                attn_ckpt="zhengchong/CatVTON",
                base_ckpt="booksforcharlie/stable-diffusion-inpainting",
                weight_dtype=torch.float32,  # FP32 for GTX 1650
                device='cuda',
                skip_safety_check=True
            )
            
            print(f"[CatVTON] CatVTON loaded successfully (FP32)")
            
        except Exception as e:
            print(f"[CatVTON] Load failed: {e}")
            raise e
            
    def unload(self):
        """Free GPU memory."""
        if self.pipeline is not None:
            del self.pipeline
            self.pipeline = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            print("🔓 CatVTON unloaded")
    
    def try_on(
        self,
        person_image: Image.Image,
        garment_image: Image.Image,
        mask: np.ndarray,
        num_steps: int = 40,  # High quality
        guidance_scale: float = 2.5,  # CatVTON default
        seed: int = 0
    ) -> Image.Image:
        """
        Perform virtual try-on.
        """
        if self.pipeline is None:
            self.load()
        
        from diffusers.image_processor import VaeImageProcessor
        
        # Prepare processors
        vae_processor = VaeImageProcessor(vae_scale_factor=8)
        mask_processor = VaeImageProcessor(
            vae_scale_factor=8, 
            do_normalize=False, 
            do_binarize=True, 
            do_convert_grayscale=True
        )
        
        # Small size for fast generation - we upscale later
        height, width = 512, 384
        
        # Preprocess images
        person_tensor = vae_processor.preprocess(person_image, height, width)[0].unsqueeze(0)
        garment_tensor = vae_processor.preprocess(garment_image, height, width)[0].unsqueeze(0)
        
        # Preprocess mask
        mask_pil = Image.fromarray((mask * 255).astype(np.uint8))
        mask_tensor = mask_processor.preprocess(mask_pil, height, width)[0].unsqueeze(0)
        
        # Generator - use random seed for variety
        import random
        actual_seed = seed if seed != 0 else random.randint(0, 2**32-1)
        generator = torch.Generator(device=self.device).manual_seed(actual_seed)
        print(f"   Seed: {actual_seed}")
        
        print(f"🔄 Generating virtual try-on...")
        # Since pipeline.device might be cuda (due to offload hack), we ensure inputs are on correct device
        # But Accelerate handles this usually.
        
        result = self.pipeline(
            person_tensor,
            garment_tensor,
            mask_tensor,
            num_inference_steps=num_steps,
            guidance_scale=guidance_scale,
            height=height,
            width=width,
            generator=generator,
        )[0]
        
        # Resize back to original
        result = result.resize(person_image.size, Image.LANCZOS)
        
        return result


def virtual_try_on(
    person_path: str,
    garment_path: str,
    mask_path: str = None,
    output_name: str = None
) -> Path:
    """
    Perform virtual try-on.
    """
    from apps.image_surgeon.tools.clothes_parser import segment_clothes
    import cv2
    
    output_dir = PROJECT_ROOT / "assets/generated/image_surgeon/try_on"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    person_path = Path(person_path)
    garment_path = Path(garment_path)
    
    print(f"[CatVTON] Virtual Try-On")
    print(f"   Person: {person_path.name}")
    print(f"   Garment: {garment_path.name}")
    
    # Load images
    person_img = Image.open(person_path).convert("RGB")
    garment_img = Image.open(garment_path).convert("RGB")
    
    # Get or load mask
    if mask_path:
        mask = np.array(Image.open(mask_path)) > 127
    else:
        print("[CatVTON] Generating clothes mask with SegFormer...")
        mask_result = segment_clothes(str(person_path))
        mask = np.array(Image.open(mask_result).convert("L")) > 127
    
    # Perform try-on
    engine = CatVTONEngine()
    engine.load()
    
    try:
        result = engine.try_on(
            person_image=person_img,
            garment_image=garment_img,
            mask=mask
        )
    finally:
        engine.unload()
    
    # Upscale for higher quality
    print("[CatVTON] Upscaling with RealESRGAN 4x...")
    from apps.image_surgeon.utils.upscaler import upscale_image, unload_esrgan
    try:
        # User requested high quality upscale - 4.0x
        result = upscale_image(result, scale=4.0)
    finally:
        unload_esrgan()
    
    # Save
    stem = output_name or f"{person_path.stem}_tryon"
    output_path = output_dir / f"{stem}.png"
    result.save(output_path)
    print(f"[CatVTON] Saved: {output_path}")
    
    return output_path


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CatVTON Virtual Try-On")
    parser.add_argument("--person_image", type=str, required=True, help="Path to person image")
    parser.add_argument("--garment_image", type=str, required=True, help="Path to garment image")
    parser.add_argument("--mask_output", type=str, default=None, help="Optional pre-existing mask")
    parser.add_argument("--output_dir", type=str, help="Directory to save result")
    parser.add_argument("--steps", type=int, default=40, help="Denoising steps")
    parser.add_argument("--upscale", type=float, default=4.0, help="Upscale factor")
    
    args = parser.parse_args()
    
    virtual_try_on(args.person_image, args.garment_image, args.mask_output, output_name=None)
