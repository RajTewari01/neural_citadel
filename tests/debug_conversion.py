import torch
from diffusers.pipelines.stable_diffusion.convert_from_ckpt import convert_controlnet_checkpoint
from diffusers import ControlNetModel
from omegaconf import OmegaConf
from safetensors.torch import load_file
import json

checkpoint_path = r"D:/neural_citadel/assets/models/image_gen/qr_controlnet/qrCodeMonster_v20.safetensors"
original_config_path = r"D:/neural_citadel/assets/models/image_gen/qr_controlnet/cldm_v15.yaml"
config_path = r"D:/neural_citadel/assets/models/image_gen/qr_controlnet/config.json"

try:
    print("Loading original config...")
    original_config = OmegaConf.load(original_config_path)
    
    print("Loading checkpoint...")
    checkpoint = load_file(checkpoint_path)
    
    print("Converting checkpoint...")
    converted_state_dict = convert_controlnet_checkpoint(
        checkpoint,
        original_config,
        checkpoint_path,
        image_size=512,
        upcast_attention=True,
        extract_ema=False
    )
    
    print(f"Converted {len(converted_state_dict)} keys.")
    print("First 10 converted keys:")
    keys = list(converted_state_dict.keys())
    for k in keys[:10]:
        print(k)

    print("\nChecking mid_block keys in converted dict:")
    for k in keys:
        if "mid" in k:
            print(k)
            break
            
    print("\nLoading target config...")
    with open(config_path, 'r') as f:
        target_config = json.load(f)
        
    print(f"Target mid_block_type: {target_config.get('mid_block_type')}")
    
    # Try to instantiate model and load keys manually to see exact missing keys
    print("\nInstantiating model...")
    model = ControlNetModel.from_config(target_config)
    
    print("Loading state dict into model...")
    missing, check = model.load_state_dict(converted_state_dict, strict=False)
    print("Missing keys:", len(missing))
    if len(missing) > 0:
        print("First 20 missing keys:")
        for k in missing[:20]:
            print(k)
            
    print("Unexpected keys:", len(check))
    if len(check) > 0:
        print("First 20 unexpected keys:")
        for k in check[:20]:
            print(k)

except Exception as e:
    import traceback
    traceback.print_exc()
