import torch
import torchvision
print(f"Torch Version: {torch.__version__}")
print(f"Torch Path: {torch.__file__}")
print(f"Torchvision Version: {torchvision.__version__}")
print(f"Torchvision Path: {torchvision.__file__}")
print(f"CUDA Available: {torch.cuda.is_available()}")
try:
    import torchvision.transforms
    print("Torchvision transforms imported successfully")
except Exception as e:
    print(f"Torchvision transforms failed: {e}")

try:
    print(f"Flash Attention Available: {torch.backends.cuda.flash_sdp_enabled()}") # flash_sdp_enabled is often the check
    # The error specifically said 'is_flash_attention_available'
    if hasattr(torch.backends.cuda, 'is_flash_attention_available'):
        print(f"is_flash_attention_available: {torch.backends.cuda.is_flash_attention_available()}")
    else:
        print("is_flash_attention_available: NOT FOUND")
except Exception as e:
    print(f"Flash Check Error: {e}")
