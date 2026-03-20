"""
Generate an image using the production engine
"""
import sys
from pathlib import Path

# Add project root
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

# Redirect output to file to avoid Unicode issues
log = open("d:/neural_citadel/generation_log.txt", "w", encoding="utf-8")

try:
    log.write("Starting image generation...\n")
    log.flush()
    
    from apps.image_gen.engine import DiffusionEngine
    from apps.image_gen.pipeline.pipeline_types import PipelineConfigs
    
    config = PipelineConfigs(
        base_model=Path(r"D:\neural_citadel\assets\models\image_gen\diffusion\illustrator\diffusionBrushEverythingSFWNSFWAll_v10.safetensors"),
        output_dir=Path(r"D:\neural_citadel\assets\generated"),
        prompt="A sinister hooded figure in black robes kneeling before a stone altar, inside an ancient gothic cathedral crypt, surrounded by hundreds of burning red candles, mysterious occult ritual, dramatic cast shadows, cinematic atmosphere, dark fantasy, hyperrealistic, 8k",
        neg_prompt="blurry, low quality, distorted, cartoon, painting",
        vae="realistic",
        scheduler_name="euler_a",
        width=512,
        height=768,
        steps=30,
        cfg=7.0,
        upscale_method="None"
    )
    
    log.write("Config created\n")
    log.flush()
    
    engine = DiffusionEngine()
    log.write("Engine created\n")
    log.flush()
    
    output_path = engine.generate(config)
    log.write(f"SUCCESS: Image saved to {output_path}\n")
    
    engine.unload()
    log.write("Engine unloaded\n")
    
    # Print result to console too
    print(f"Image generated: {output_path}")
    
except Exception as e:
    import traceback
    log.write(f"ERROR: {e}\n")
    traceback.print_exc(file=log)
    print(f"Error: {e}")
finally:
    log.flush()
    log.close()
