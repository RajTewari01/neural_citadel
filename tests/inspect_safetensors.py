from safetensors.torch import load_file
import sys

path = r"D:\neural_citadel\assets\models\image_gen\qr_controlnet\qrCodeMonster_v20.safetensors"
try:
    state_dict = load_file(path)
    print(f"Loaded {len(state_dict)} keys.")
    
    # Print first few keys to guess structure
    keys = list(state_dict.keys())
    for k in keys[:20]:
        print(k)
        
    print("\nChecking for middle_block keys:")
    for k in keys:
        if "middle_block" in k:
            print(k)
            break
            
    print("\nChecking for controlnet keys:")
    for k in keys:
        if "controlnet" in k:
            print(k)
            break

    print("\nTotal keys:", len(keys))
    
except Exception as e:
    print(e)
