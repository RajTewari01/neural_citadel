"""
QR Code Diffusion Engine
=========================
A complete worker script for generating artistic QR codes using Stable Diffusion + ControlNet.

This script runs in the IMAGE_VENV environment (d:\\neural_citadel\\venvs\\env\\image_venv).
It is called via subprocess from the qr_studio app in the global environment.

Usage:
    [IMAGE_VENV_PYTHON] qr_image_engine.py --input <path> --prompt "forest theme"
"""

import gc
import json
import random
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

import torch
from PIL import Image
from diffusers import (
    StableDiffusionControlNetPipeline,
    ControlNetModel,
    EulerAncestralDiscreteScheduler,
)

# =============================================================================
# Dynamic Path Resolution (to avoid import issues from subprocess)
# =============================================================================
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from configs.paths import (
    CONTROLNET_QR,
    PROMPTS_QR_FILE,
    QR_CODE_DIFFUSION_DIR,
    DIFFUSION_MODELS,
    UPSCALER_MODELS,
)


# =============================================================================
# UPSCALER (RealESRGAN)
# =============================================================================
def upscale_image(image: Image.Image, scale: int = 4) -> Image.Image:
    """
    Upscale an image using RealESRGAN.
    Memory-efficient: loads, runs, and unloads the model.
    """
    from basicsr.archs.rrdbnet_arch import RRDBNet
    from realesrgan import RealESRGANer
    import numpy as np

    model_path = str(UPSCALER_MODELS.get("R-ESRGAN 4x+"))
    print(f"[UPSCALE] Loading RealESRGAN from: {model_path}", flush=True)

    model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)

    upsampler = RealESRGANer(
        scale=scale,
        model_path=model_path,
        model=model,
        tile=256,  # Low VRAM tile-based processing
        tile_pad=10,
        pre_pad=0,
        half=False  # Use full precision for GTX 1650
    )

    # Convert PIL to numpy (BGR for RealESRGAN)
    img_np = np.array(image)[:, :, ::-1]

    output, _ = upsampler.enhance(img_np, outscale=scale)

    # Convert back to PIL (RGB)
    result = Image.fromarray(output[:, :, ::-1])

    # Cleanup
    del upsampler
    del model
    gc.collect()
    torch.cuda.empty_cache()
    print("[UPSCALE] Cleanup complete.", flush=True)

    return result


# =============================================================================
# QR DIFFUSION ENGINE
# =============================================================================
class QRDiffusionEngine:
    """
    Engine for generating artistic QR codes using Stable Diffusion + ControlNet.
    Designed for 4GB VRAM (GTX 1650) with aggressive memory management.
    """

    DEFAULT_NEGATIVE_PROMPT = (
        "blurry, ugly, low quality, distorted, text, watermark, "
        "border, frame, padding, worst quality, jpeg artifacts, "
        "signature, username, error, cropped"
    )

    QUALITY_BOOSTERS = [
        "highly insanely detailed",
        "masterpiece",
        "top quality",
        "best quality",
        "highres",
        "8k",
        "RAW photo",
        "very aesthetic",
        "sharp focus",
        "photorealistic",
    ]

    # Style keywords to match user prompts with JSON dataset
    STYLE_KEYWORDS = {
        "forest": ["nature", "tree", "leaf", "green", "forest", "jungle", "botanical"],
        "cyber": ["cyber", "neon", "futuristic", "tech", "digital", "synthwave", "vaporwave"],
        "fantasy": ["magic", "fantasy", "mystical", "enchanted", "dragon", "castle"],
        "space": ["space", "galaxy", "cosmic", "star", "nebula", "planet", "universe"],
        "horror": ["horror", "dark", "scary", "zombie", "gothic", "creepy"],
        "anime": ["anime", "manga", "cartoon", "girl", "kawaii"],
        "realistic": ["photo", "realistic", "raw", "photorealistic", "cinematic"],
        "abstract": ["abstract", "pattern", "texture", "geometric", "art"],
    }

    def __init__(self):
        self.pipe = None
        self.prompts_data = None
        self._load_prompts()

    def _load_prompts(self):
        """Load pre-defined prompts from JSON for quality enhancement."""
        if PROMPTS_QR_FILE.exists():
            with open(PROMPTS_QR_FILE, "r", encoding="utf-8") as f:
                self.prompts_data = json.load(f)
            print(f"[ENGINE] Loaded {self.prompts_data.get('prompt_count', 0)} prompts from JSON", flush=True)
        else:
            print(f"[ENGINE] Warning: Prompts file not found at {PROMPTS_QR_FILE}", flush=True)
            self.prompts_data = {"prompts": []}

    def _find_matching_style(self, user_prompt: str) -> Optional[dict]:
        """
        Find a matching prompt from JSON dataset based on user keywords.
        Returns the best matching prompt dict or None.
        """
        user_lower = user_prompt.lower()
        prompts = self.prompts_data.get("prompts", [])
        
        if not prompts:
            return None
        
        # Score each prompt based on keyword overlap
        best_match = None
        best_score = 0
        
        for prompt_entry in prompts:
            prompt_text = prompt_entry.get("prompt", "").lower()
            score = 0
            
            # Check for direct keyword matches
            for word in user_lower.split():
                if len(word) > 3 and word in prompt_text:
                    score += 2
            
            # Check style category matches
            for category, keywords in self.STYLE_KEYWORDS.items():
                if any(kw in user_lower for kw in keywords):
                    if any(kw in prompt_text for kw in keywords):
                        score += 3
            
            if score > best_score:
                best_score = score
                best_match = prompt_entry
        
        return best_match if best_score > 0 else None

    def _enhance_prompt(self, user_prompt: str) -> tuple:
        """
        Intelligently enhance user prompt using the proven 96-prompt dataset.
        
        Strategy:
        1. If no user prompt: pick random from dataset
        2. If simple prompt: find matching style and inject quality boosters
        3. Use proven negative prompts from dataset
        
        Returns (enhanced_prompt, negative_prompt).
        """
        prompts = self.prompts_data.get("prompts", [])
        
        # Case 1: No user prompt - pick random from dataset
        if not user_prompt.strip():
            if prompts:
                chosen = random.choice(prompts)
                print(f"[PROMPT] No user prompt. Using random style from dataset.", flush=True)
                neg = chosen.get("negative_prompt", "") or self.DEFAULT_NEGATIVE_PROMPT
                return chosen.get("prompt", "abstract art"), neg
            return "abstract colorful pattern, highly detailed, masterpiece", self.DEFAULT_NEGATIVE_PROMPT
        
        # Case 2: Find matching style from dataset
        matched = self._find_matching_style(user_prompt)
        
        if matched:
            # Combine user theme with proven prompt structure
            base_prompt = matched.get("prompt", "")
            neg_prompt = matched.get("negative_prompt", "") or self.DEFAULT_NEGATIVE_PROMPT
            
            # Extract quality boosters from matched prompt
            quality_parts = []
            for booster in self.QUALITY_BOOSTERS:
                if booster.lower() in base_prompt.lower():
                    quality_parts.append(booster)
            
            # Build enhanced prompt: quality + user theme + style elements
            if not quality_parts:
                quality_parts = random.sample(self.QUALITY_BOOSTERS, 5)
            
            enhanced = f"({', '.join(quality_parts)}), {user_prompt}, {base_prompt[:200]}"
            print(f"[PROMPT] Matched style! Enhanced: {enhanced[:120]}...", flush=True)
            return enhanced, neg_prompt
        
        # Case 3: No match - use quality boosters only
        boosters = ", ".join(random.sample(self.QUALITY_BOOSTERS, 5))
        enhanced = f"({boosters}), {user_prompt}, highly insanely detailed, masterpiece, top quality, best quality, highres, 4k, 8k"
        print(f"[PROMPT] Enhanced with boosters: {enhanced[:120]}...", flush=True)
        return enhanced, self.DEFAULT_NEGATIVE_PROMPT

    def load(self, model_key: str = "realistic_digital"):
        """
        Load Stable Diffusion pipeline with ControlNet.
        Memory optimizations applied for 4GB VRAM.
        """
        print("[ENGINE] Cleaning memory before load...", flush=True)
        gc.collect()
        torch.cuda.empty_cache()

        print(f"[ENGINE] Loading ControlNet from: {CONTROLNET_QR}", flush=True)
        controlnet = ControlNetModel.from_pretrained(
            str(CONTROLNET_QR),
            torch_dtype=torch.float32
        )

        model_path = DIFFUSION_MODELS.get(model_key)
        if not model_path or not model_path.exists():
            print(f"[ENGINE] Model '{model_key}' not found, falling back to 'realistic_digital'", flush=True)
            model_path = DIFFUSION_MODELS.get("realistic_digital")

        print(f"[ENGINE] Loading SD model from: {model_path}", flush=True)
        self.pipe = StableDiffusionControlNetPipeline.from_single_file(
            str(model_path),
            controlnet=controlnet,
            torch_dtype=torch.float32,
            safety_checker=None
        )

        # Use Euler Ancestral for artistic style
        self.pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(
            self.pipe.scheduler.config
        )

        # VRAM optimizations
        print("[ENGINE] Applying VRAM optimizations...", flush=True)
        self.pipe.enable_sequential_cpu_offload()
        self.pipe.enable_vae_slicing()
        self.pipe.enable_attention_slicing(slice_size="max")

        print("[ENGINE] Pipeline loaded successfully.", flush=True)

    def generate(
        self,
        qr_image_path: str,
        prompt: str,
        control_scale: float = 1.6,
        guidance_scale: float = 7.0,
        steps: int = 25,
        seed: Optional[int] = None,
    ) -> Optional[Path]:
        """
        Generate artistic QR code from input image.
        
        Args:
            qr_image_path: Path to the base QR code image
            prompt: User prompt describing the style
            control_scale: ControlNet influence (higher = more QR visible)
            guidance_scale: CFG scale for prompt adherence
            steps: Number of diffusion steps
            seed: Random seed for reproducibility
        
        Returns:
            Path to the generated image, or None on failure
        """
        if self.pipe is None:
            print("[ERROR] Pipeline not loaded. Call load() first.", flush=True)
            return None

        input_path = Path(qr_image_path)
        if not input_path.exists():
            print(f"[ERROR] Input file not found: {input_path}", flush=True)
            return None

        # Load and prepare QR image (keep original size, don't resize)
        qr_image = Image.open(input_path).convert("RGB")
        original_size = qr_image.size
        print(f"[GENERATE] Input QR size: {original_size}", flush=True)

        # Resize to 768x768 for viable QR code diffusion
        qr_image_resized = qr_image.resize((768, 768), Image.LANCZOS)

        # Enhance prompt
        enhanced_prompt, negative_prompt = self._enhance_prompt(prompt)

        # Set seed
        if seed is None:
            seed = random.randint(0, 2**32 - 1)
        generator = torch.Generator(device="cpu").manual_seed(seed)
        print(f"[GENERATE] Seed: {seed}", flush=True)

        # Generate
        print("[GENERATE] Running diffusion...", flush=True)
        output = self.pipe(
            prompt=enhanced_prompt,
            negative_prompt=negative_prompt,
            image=qr_image_resized,
            controlnet_conditioning_scale=control_scale,
            guidance_scale=guidance_scale,
            num_inference_steps=steps,
            generator=generator,
        )

        result_image = output.images[0]
        print(f"[GENERATE] Diffusion complete. Output size: {result_image.size}", flush=True)
        
        # Free diffusion memory BEFORE upscaling
        del output
        del qr_image_resized
        del qr_image
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print("[GENERATE] Freed diffusion memory.", flush=True)

        # Upscale to restore quality
        print("[GENERATE] Upscaling...", flush=True)
        upscaled_image = upscale_image(result_image, scale=4)
        print(f"[GENERATE] Upscaled size: {upscaled_image.size}", flush=True)
        
        # Free result_image
        del result_image
        gc.collect()

        # Save output
        QR_CODE_DIFFUSION_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = QR_CODE_DIFFUSION_DIR / f"qr_diffusion_{timestamp}.png"
        upscaled_image.save(output_path, quality=95)
        print(f"[GENERATE] Saved: {output_path}", flush=True)
        
        # Free upscaled_image
        del upscaled_image
        gc.collect()

        return output_path

    def unload(self):
        """
        Aggressively clean up GPU memory - ensures clean state for next run.
        """
        print("[ENGINE] Unloading pipeline...", flush=True)
        
        if self.pipe is not None:
            # Delete all sub-components explicitly
            if hasattr(self.pipe, 'unet'):
                del self.pipe.unet
            if hasattr(self.pipe, 'vae'):
                del self.pipe.vae
            if hasattr(self.pipe, 'text_encoder'):
                del self.pipe.text_encoder
            if hasattr(self.pipe, 'controlnet'):
                del self.pipe.controlnet
            if hasattr(self.pipe, 'scheduler'):
                del self.pipe.scheduler
            if hasattr(self.pipe, 'tokenizer'):
                del self.pipe.tokenizer
            
            del self.pipe
            self.pipe = None
        
        # Force garbage collection multiple times
        gc.collect()
        gc.collect()
        
        # Clear CUDA cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            torch.cuda.empty_cache()
        
        print("[ENGINE] Memory cleaned: Pipeline fully deleted.", flush=True)


# =============================================================================
# CLI ENTRY POINT
# =============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Generate artistic QR codes using Stable Diffusion + ControlNet"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        required=True,
        help="Path to input QR code image"
    )
    parser.add_argument(
        "--prompt", "-p",
        type=str,
        default="",
        help="Prompt describing the desired style (optional)"
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default="realistic_digital",
        help="Model key from DIFFUSION_MODELS (default: realistic_digital)"
    )
    parser.add_argument(
        "--control-scale",
        type=float,
        default=1.5,
        help="ControlNet scale (higher = more QR visible, default: 1.5)"
    )
    parser.add_argument(
        "--guidance-scale",
        type=float,
        default=7.0,
        help="CFG scale for prompt adherence (default: 7.0)"
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=25,
        help="Number of diffusion steps (default: 25)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility"
    )

    args = parser.parse_args()

    print(f"[WORKER] Starting QR Diffusion Engine", flush=True)
    print(f"[WORKER] Input: {args.input}", flush=True)
    print(f"[WORKER] Prompt: {args.prompt}", flush=True)

    # Engine workflow
    engine = QRDiffusionEngine()
    try:
        engine.load(model_key=args.model)
        output = engine.generate(
            qr_image_path=args.input,
            prompt=args.prompt,
            control_scale=args.control_scale,
            guidance_scale=args.guidance_scale,
            steps=args.steps,
            seed=args.seed,
        )
        if output:
            print(f"[SUCCESS] Generated: {output}", flush=True)
            # Print path for subprocess capture
            print(f"OUTPUT_PATH:{output}", flush=True)
        else:
            print("[FAILED] Generation failed.", flush=True)
            sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Exception: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        engine.unload()


if __name__ == "__main__":
    main()