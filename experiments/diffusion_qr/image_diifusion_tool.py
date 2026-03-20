import torch
from diffusers import StableDiffusionControlNetPipeline, ControlNetModel, EulerAncestralDiscreteScheduler
from PIL import Image
from pathlib import Path
from typing import Optional
import os
import gc
import uuid

def generate_qr_art(
    qr_image_path: str,
    prompt: str,
    negative_prompt: str = "blurry, ugly, low quality, distortion, text, watermark, border, frame, padding",
    control_scale: float = 2.0, # Slightly reduced for Euler A flexibility
    guidance_scale: float = 7.0,
    steps: int = 25, # Euler A often benefits from slightly higher steps (20-30)
    seed: Optional[int] = None,
    output_size: tuple = (512, 512)
) -> Optional[Path]:
    """
    Generates an artistic QR code using Stable Diffusion 1.5 and ControlNet.
    Uses Euler Ancestral scheduler. Designed for 6GB VRAM systems.
    """
    gc.collect()
    torch.cuda.empty_cache()
    
    if not os.path.exists(qr_image_path):
        print(f"Error: Input file '{qr_image_path}' not found.")
        return None

    try:
        # 1. Load ControlNet
        controlnet = ControlNetModel.from_pretrained(
            r"D:/neural_citadel/assets/models/image_gen/qr_controlnet/v2",
            torch_dtype=torch.float32
        )

        # 2. Load Stable Diffusion
        pipe = StableDiffusionControlNetPipeline.from_single_file(
            r"D:\neural_citadel\assets\models\image_gen\diffusion\realistic\realisticDigital_v60.safetensors",
            controlnet=controlnet,
            torch_dtype=torch.float32,
            safety_checker=None
        )

        # 3. SWITCH TO EULER ANCESTRAL SCHEDULER
        # This corresponds to "Euler a" in most WebUIs
        pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(pipe.scheduler.config)

        # 4. Optimize for Low VRAM - Enable all memory optimizations
        pipe.enable_sequential_cpu_offload()
        pipe.enable_vae_slicing()
        pipe.enable_attention_slicing(slice_size="max")

        # 5. Process Image
        source_qr = Image.open(qr_image_path)
        if source_qr.mode != "RGB":
            source_qr = source_qr.convert("RGB")
        
        # Resize to exact output size
        source_qr = source_qr.resize(output_size, Image.Resampling.LANCZOS)

        # 6. Handle Seed
        generator = None
        if seed is not None:
            generator = torch.Generator(device="cpu").manual_seed(seed)

        # 7. Generate
        print(f"Generating QR Art (Euler A) for: '{prompt}'...")
        result = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=source_qr,
            controlnet_conditioning_scale=control_scale,
            guidance_scale=guidance_scale,
            num_inference_steps=steps,
            generator=generator,
            height=output_size[1],
            width=output_size[0]
        ).images[0]

        output_path = f"{uuid.uuid4()}.png"
        result.save(output_path, quality=95)
        print(f"Success! Saved to: {output_path}")
        return output_path

    except Exception as e:
        print(f"An error occurred during generation: {e}")
        return None

# --- usage example ---
if __name__ == "__main__":
    generate_qr_art(
        qr_image_path=r"D:\neural_citadel\assets\qr_code\gradients\qr_url_20260115_125317_573daf864a89.png",
        prompt="RAW photo of an Indian castle surrounded by water and nature, village, volumetric lighting, photorealistic, insanely detailed and intricate, Fantasy, epic cinematic shot, trending on ArtStation, mountains, 8k ultra hd, magical, mystical, matte painting, bright sunny day, flowers, massive cliffs, Sweeper3D",
        # prompt="3D Digital Paintings,Early afternoon,Long Shot,landscape with sun,Bag,1girl,sole,sleepy,Effulgent,Crimped Hair,Gown,inverted-triangular,Informative,masterpiece, best quality",
        negative_prompt="blurry, ugly, low quality, distortion, text, watermark, border, frame, padding, vignette",
        control_scale=1.5,  # Euler A sometimes needs slightly less control force than UniPC
        guidance_scale=7.0,
        steps=30, # 20 is okay, but 30 gives Euler A more time to resolve details
        output_size=(768, 768)
    )