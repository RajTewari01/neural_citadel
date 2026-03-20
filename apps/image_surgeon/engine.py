"""
Image Surgeon Engine
=====================
Central orchestrator for all image surgery operations.
Matches the architecture of apps/image_gen/engine.py.

Usage:
    engine = ImageSurgeonEngine()
    result = engine.process(config)
    engine.unload()
"""

import gc
import sys
import shutil
import uuid
from pathlib import Path
from typing import Optional, Union, Tuple
from PIL import Image

# Dynamic path detection (cross-platform)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from apps.image_surgeon.pipeline.pipeline_types import SurgeonConfig
from apps.image_surgeon.pipeline.registry import get_best_match, get_all_assets

# Output directories
RAW_EXTRACT_DIR = PROJECT_ROOT / "assets" / "generated" / "image_surgeon" / "raw_extract"
OUTPUT_DIR = PROJECT_ROOT / "assets" / "generated" / "image_surgeon"
TEMP_DIR = PROJECT_ROOT / "assets" / "generated" / "image_surgeon" / "temp"

# Solid colors
SOLID_COLORS = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "gray": (128, 128, 128),
    "grey": (128, 128, 128),
    "yellow": (255, 255, 0),
    "cyan": (0, 255, 255),
    "magenta": (255, 0, 255),
    "orange": (255, 165, 0),
    "pink": (255, 192, 203),
    "purple": (128, 0, 128),
    "transparent": None,
}


class ImageSurgeonEngine:
    """
    Central orchestrator for image surgery operations.
    Handles both background replacement and clothes change.
    """
    
    def __init__(self):
        self.device = "cuda"
        self._temp_files = []
        
        # Ensure directories exist
        RAW_EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
    def _flush(self):
        """Clean up GPU memory."""
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass
    
    def _register_temp(self, path: Path):
        """Register a temp file for cleanup."""
        self._temp_files.append(path)
    
    def _cleanup_temps(self):
        """Delete all registered temp files."""
        for temp in self._temp_files:
            try:
                if temp.exists():
                    temp.unlink()
            except Exception:
                pass
        self._temp_files.clear()
    
    def process(self, config: SurgeonConfig) -> Path:
        """
        Process an image based on configuration.
        
        Args:
            config: SurgeonConfig with mode, input, options
            
        Returns:
            Path to output image
        """
        if config.mode == "background":
            return self._process_background(config)
        elif config.mode == "clothes":
            return self._process_clothes(config)
        elif config.mode == "auto":
            return self._process_auto(config)
        else:
            raise ValueError(f"Unknown mode: {config.mode}. Use 'background', 'clothes', or 'auto'")
    
    def _process_background(self, config: SurgeonConfig) -> Path:
        """Replace background with solid color, image, or generated content."""
        from apps.image_surgeon.tools.person_extractor import extract_person_grounded
        
        print(f"[BACKGROUND MODE]")
        print(f"   Input: {config.input_image.name}")
        
        # Step 1: Extract person
        print("Extracting person...")
        extracted_path = extract_person_grounded(str(config.input_image))
        extracted_path = Path(extracted_path)
        
        # Save raw extraction
        if config.save_raw_extract:
            raw_name = f"{config.input_image.stem}_raw_{uuid.uuid4().hex[:6]}.png"
            raw_path = RAW_EXTRACT_DIR / raw_name
            shutil.copy2(extracted_path, raw_path)
            print(f"Raw extraction saved: {raw_path.name}")
        
        # Step 2: Apply background
        extracted_img = Image.open(extracted_path).convert("RGBA")
        
        if config.solid_color:
            print(f"Applying solid color: {config.solid_color}")
            bg = Image.new("RGBA", extracted_img.size, config.solid_color + (255,))
            bg.paste(extracted_img, (0, 0), extracted_img)
            result = bg.convert("RGB")
        elif config.transparent:
            result = extracted_img
        elif config.background_image:
            print(f"Using background image: {config.background_image.name}")
            bg = Image.open(config.background_image).convert("RGBA")
            bg = bg.resize(extracted_img.size, Image.LANCZOS)
            bg.paste(extracted_img, (0, 0), extracted_img)
            result = bg.convert("RGB")
        elif config.prompt:
            # Generate fresh background using txt2img (no original image context)
            from apps.image_surgeon.utils.background_gen import BackgroundGenerator
            from apps.image_surgeon.utils.diffusion_upscale import DiffusionUpscaler
            from apps.image_surgeon.utils.upscaler import upscale_image, unload_esrgan, lanczos_upscale
            from apps.image_surgeon.utils.prompts import get_best_background_prompt
            
            # Optimize prompt using prompt library
            optimized_prompt = get_best_background_prompt(config.prompt)
            print(f"Generating fresh background: {optimized_prompt[:60]}...")
            
            # Get aspect ratio from extracted person, cap at 780 max dimension
            orig_w, orig_h = extracted_img.size
            max_dim = 780
            if orig_w > orig_h:
                gen_w = min(orig_w, max_dim)
                gen_h = int(gen_w * orig_h / orig_w)
            else:
                gen_h = min(orig_h, max_dim)
                gen_w = int(gen_h * orig_w / orig_h)
            # Round to nearest 64 for SD compatibility
            gen_w = (gen_w // 64) * 64
            gen_h = (gen_h // 64) * 64
            
            print(f"   Target size: {orig_w}x{orig_h} → Generate: {gen_w}x{gen_h}")
            
            # =========================================================================
            # Stage 1: txt2img - Generate small background
            # =========================================================================
            print("\n[Stage 1/6] Generating fresh background (txt2img)...")
            bg_gen = BackgroundGenerator()
            try:
                background = bg_gen.generate(
                    prompt=optimized_prompt,
                    width=gen_w,
                    height=gen_h,
                    negative_prompt="person, human, face, portrait, selfie, ugly, blurry",
                    steps=25,
                    cfg=7.5
                )
            finally:
                bg_gen.unload()
            
            # =========================================================================
            # Stage 2: Diffusion - Add details to background
            # =========================================================================
            print("[Stage 2/6] Diffusion add details to background...")
            diffusion_up = DiffusionUpscaler()
            try:
                background = diffusion_up.upscale(
                    background,
                    prompt=optimized_prompt,
                    strength=0.35,  # Medium - add details
                    scale=orig_w / gen_w,  # Scale to original size
                    steps=12
                )
            finally:
                diffusion_up.unload()
            
            # =========================================================================
            # Stage 3: Composite - Paste extracted person
            # =========================================================================
            print("[Stage 3/6] Compositing person onto background...")
            result = background.convert("RGBA")
            result = result.resize(extracted_img.size, Image.LANCZOS)  # Ensure exact match
            result.paste(extracted_img, (0, 0), extracted_img)
            result = result.convert("RGB")
            
            # =========================================================================
            # Stage 4: Diffusion - Blend person with background (very low)
            # =========================================================================
            print("[Stage 4/6] Diffusion blend (very low strength)...")
            diffusion_up = DiffusionUpscaler()
            try:
                result = diffusion_up.upscale(
                    result,
                    prompt=f"photorealistic, natural lighting, {optimized_prompt}",
                    strength=0.08,  # VERY low - just blend edges
                    scale=1.0,
                    steps=5  # Very few steps
                )
            finally:
                diffusion_up.unload()
            
            # =========================================================================
            # Stage 5: ESRGAN 4x upscale
            # =========================================================================
            print("[Stage 5/6] ESRGAN 4x upscale...")
            try:
                result = upscale_image(result, scale=4.0)
            finally:
                unload_esrgan()
            
            # =========================================================================
            # Stage 6: Lanczos final polish
            # =========================================================================
            print("[Stage 6/6] Lanczos final polish...")
            result = lanczos_upscale(result, scale=1.0)
            
            print(f"[PIPELINE] Complete! Final size: {result.size}")
        else:
            result = extracted_img
        
        # Step 3: Save output
        output_dir = config.output_dir or OUTPUT_DIR / "background"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_name = config.output_name or f"{config.input_image.stem}_bg_{uuid.uuid4().hex[:6]}"
        output_path = output_dir / f"{output_name}.png"
        result.save(output_path)
        
        # DB Tracking
        self._track_operation(config, output_path)
        
        # Cleanup temp extraction (not the raw save)
        if extracted_path != raw_path if config.save_raw_extract else True:
            try:
                extracted_path.unlink()
            except Exception:
                pass
        
        print(f"Saved: {output_path}")
        return output_path
    
    def _process_clothes(self, config: SurgeonConfig) -> Path:
        """
        Change clothes using either:
        - CatVTON (if garment_path provided - virtual try-on with real garment)
        - ClothesInpaint (if just prompt - uses CLOTHES trigger inpainting)
        """
        from apps.image_surgeon.tools.clothes_parser import segment_clothes
        from apps.image_surgeon.utils.upscaler import upscale_image, unload_esrgan, lanczos_upscale
        
        print(f"[CLOTHES MODE]")
        print(f"   Input: {config.input_image.name}")
        
        # =========================================================================
        # Route based on whether garment_path is provided
        # =========================================================================
        if config.garment_path:
            # Use CatVTON for virtual try-on with actual garment image
            return self._clothes_catvton(config)
        elif config.prompt:
            # Use ClothesInpaint for prompt-based clothes change
            return self._clothes_inpaint(config)
        else:
            raise ValueError("Must provide --garment or --prompt for clothes mode")
    
    def _clothes_catvton(self, config: SurgeonConfig) -> Path:
        """Virtual try-on using CatVTON with actual garment image."""
        from apps.image_surgeon.tools.catvton import CatVTONEngine
        from apps.image_surgeon.tools.clothes_parser import segment_clothes
        from apps.image_surgeon.utils.upscaler import upscale_image, unload_esrgan, lanczos_upscale
        
        print("   Mode: CatVTON (virtual try-on)")
        print(f"   Garment: {config.garment_path.name}")
        
        # Step 1: Generate clothes mask
        print("Generating clothes mask...")
        mask_path = segment_clothes(str(config.input_image))
        self._register_temp(Path(mask_path))
        
        # Step 2: Run CatVTON
        print("Running CatVTON (FP32)...")
        catvton = CatVTONEngine()
        try:
            catvton.load()
            
            person_img = Image.open(config.input_image).convert("RGB")
            garment_img = Image.open(config.garment_path).convert("RGB")
            
            import numpy as np
            mask = np.array(Image.open(mask_path).convert("L")) > 127
            
            result = catvton.try_on(
                person_image=person_img,
                garment_image=garment_img,
                mask=mask,
                num_steps=config.steps or 40
            )
        finally:
            catvton.unload()
        
        # Step 3: Upscale
        print("Upscaling with ESRGAN 4x...")
        try:
            result = upscale_image(result, scale=4.0)
        finally:
            unload_esrgan()
        
        result = lanczos_upscale(result, scale=1.0)
        
        # Save
        return self._save_clothes_result(config, result, "catvton")
    
    def _clothes_inpaint(self, config: SurgeonConfig) -> Path:
        """Change clothes using ClothesInpaint (CLOTHES trigger)."""
        from apps.image_surgeon.tools.clothes_inpaint import ClothesInpaintEngine
        from apps.image_surgeon.tools.clothes_parser import segment_clothes
        from apps.image_surgeon.utils.upscaler import upscale_image, unload_esrgan, lanczos_upscale
        
        print(f"   Mode: Clothes Inpaint (prompt-based)")
        print(f"   Prompt: {config.prompt}")
        
        # Step 1: Generate clothes mask
        print("Generating clothes mask with SegFormer...")
        mask_path = segment_clothes(str(config.input_image))
        self._register_temp(Path(mask_path))
        
        # Step 2: Inpaint with CLOTHES trigger
        print("Inpainting clothes (ZenityX CLOTHES model)...")
        inpaint = ClothesInpaintEngine()
        try:
            person_img = Image.open(config.input_image).convert("RGB")
            mask_img = Image.open(mask_path).convert("L")
            
            result = inpaint.inpaint(
                image=person_img,
                mask=mask_img,
                prompt=config.prompt,
                steps=config.steps if config.steps else 36  # Use config or default to 36
            )
        finally:
            inpaint.unload()
        
        # Step 3: Upscale
        print("Upscaling with ESRGAN 4x...")
        try:
            result = upscale_image(result, scale=4.0)
        finally:
            unload_esrgan()
        
        result = lanczos_upscale(result, scale=1.0)
        
        # Save
        return self._save_clothes_result(config, result, "inpaint")
    
    def _save_clothes_result(self, config: SurgeonConfig, result: Image.Image, suffix: str) -> Path:
        """Save clothes result and cleanup."""
        output_dir = config.output_dir or OUTPUT_DIR / "clothes"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_name = config.output_name or f"{config.input_image.stem}_clothes_{suffix}_{uuid.uuid4().hex[:6]}"
        output_path = output_dir / f"{output_name}.png"
        result.save(output_path)
        
        # DB Tracking
        self._track_operation(config, output_path)
        
        # Cleanup temps
        self._cleanup_temps()
        
        print(f"Saved: {output_path}")
        return output_path
    
    def _process_auto(self, config: SurgeonConfig) -> Path:
        """
        Auto mode: Run background replacement THEN clothes change.
        Uses prompt-based clothes inpainting (not CatVTON).
        """
        from apps.image_surgeon.utils.background_gen import BackgroundGenerator
        from apps.image_surgeon.utils.diffusion_upscale import DiffusionUpscaler
        from apps.image_surgeon.utils.upscaler import upscale_image, unload_esrgan, lanczos_upscale
        from apps.image_surgeon.utils.prompts import get_best_background_prompt
        from apps.image_surgeon.tools.clothes_inpaint import ClothesInpaintEngine
        from apps.image_surgeon.tools.clothes_parser import segment_clothes
        from apps.image_surgeon.tools.person_extractor import extract_person_grounded
        
        print(f"[AUTO MODE]")
        print(f"   Input: {config.input_image.name}")
        print(f"   Background: {config.bg_prompt}")
        print(f"   Clothes: {config.clothes_prompt}")
        
        # =======================================================================
        # STAGE A: Background replacement (same as background mode)
        # =======================================================================
        print("\n[STAGE A] Background Replacement...")
        
        # Extract person
        extracted_path = extract_person_grounded(
            str(config.input_image)
        )
        extracted_img = Image.open(extracted_path).convert("RGBA")
        
        # Generate fresh background
        optimized_bg_prompt = get_best_background_prompt(config.bg_prompt)
        orig_w, orig_h = extracted_img.size
        max_dim = 780
        if orig_w > orig_h:
            gen_w = min(orig_w, max_dim)
            gen_h = int(gen_w * orig_h / orig_w)
        else:
            gen_h = min(orig_h, max_dim)
            gen_w = int(gen_h * orig_w / orig_h)
        gen_w = (gen_w // 64) * 64
        gen_h = (gen_h // 64) * 64
        
        bg_gen = BackgroundGenerator()
        try:
            background = bg_gen.generate(
                prompt=optimized_bg_prompt,
                width=gen_w,
                height=gen_h,
                steps=25
            )
        finally:
            bg_gen.unload()
        
        # Diffusion add details
        diffusion_up = DiffusionUpscaler()
        try:
            background = diffusion_up.upscale(
                background,
                prompt=optimized_bg_prompt,
                strength=0.35,
                scale=orig_w / gen_w,
                steps=12
            )
        finally:
            diffusion_up.unload()
        
        # Composite
        result = background.convert("RGBA")
        result = result.resize(extracted_img.size, Image.LANCZOS)
        result.paste(extracted_img, (0, 0), extracted_img)
        result = result.convert("RGB")
        
        # Save intermediate result for clothes processing
        temp_bg_path = TEMP_DIR / f"auto_bg_{uuid.uuid4().hex[:6]}.png"
        result.save(temp_bg_path)
        self._register_temp(temp_bg_path)
        
        # =======================================================================
        # STAGE B: Clothes change (prompt-based with quality enhancers)
        # =======================================================================
        print("\n[STAGE B] Clothes Change...")
        
        # Enhance clothes prompt with quality keywords
        clothes_prompt = config.clothes_prompt
        quality_enhancers = ", perfect fit, ultra HD, realistic fabric, high detail"
        enhanced_clothes_prompt = clothes_prompt + quality_enhancers
        print(f"   Enhanced prompt: {enhanced_clothes_prompt[:60]}...")
        
        # Generate clothes mask
        mask_path = segment_clothes(str(temp_bg_path))
        self._register_temp(Path(mask_path))
        
        # Inpaint clothes
        inpaint = ClothesInpaintEngine()
        try:
            result = inpaint.inpaint(
                image=result,  # Use the composited result
                mask=Image.open(mask_path).convert("L"),
                prompt=enhanced_clothes_prompt,
                steps=36
            )
        finally:
            inpaint.unload()
        
        # =======================================================================
        # STAGE C: Final Upscaling
        # =======================================================================
        print("\n[STAGE C] Final Upscaling...")
        
        # ESRGAN 4x
        try:
            result = upscale_image(result, scale=4.0)
        finally:
            unload_esrgan()
        
        # Lanczos polish
        result = lanczos_upscale(result, scale=1.0)
        
        # Save
        output_dir = config.output_dir or OUTPUT_DIR / "auto"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_name = config.output_name or f"{config.input_image.stem}_auto_{uuid.uuid4().hex[:6]}"
        output_path = output_dir / f"{output_name}.png"
        result.save(output_path)
        
        self._track_operation(config, output_path)
        self._cleanup_temps()
        
        print(f"\n[AUTO MODE] Complete! Final size: {result.size}")
        print(f"Saved: {output_path}")
        return output_path
    
    def _track_operation(self, config: SurgeonConfig, output_path: Path, asset_used: Path = None):
        """Log operation to database."""
        try:
            from assets.db.img_surgeon import save_record
            save_record(
                input_path=str(config.input_image),
                output_path=str(output_path),
                mode=config.mode,
                prompt=config.prompt,
                asset_used=str(asset_used) if asset_used else None
            )
        except Exception as e:
            print(f"DB tracking failed: {e}")
    
    def unload(self):
        """Clean up resources."""
        self._cleanup_temps()
        self._flush()
        print("Engine unloaded")

