from huggingface_hub import snapshot_download
import os

print("--- STARTING DOWNLOAD ---")
print("This may take a while depending on your internet speed.\n")

# 1. Download ONLY the QR Code Monster ControlNet V2
print("Downloading QR Code Monster Model (V2)...")
try:
    path_c = snapshot_download(
        repo_id="monster-labs/control_v1p_sd15_qrcode_monster",
        local_dir=r"D:\neural_citadel\assets\models\image_gen\qr_controlnet",
        local_dir_use_symlinks=False,  # Forces real file download
        allow_patterns=["v2/*"]        # <--- THIS filters specifically for the v2 folder
    )
    print(f"✅ ControlNet V2 downloaded to: {path_c}\n")
except Exception as e:
    print(f"❌ Error downloading ControlNet: {e}")

print("--- DOWNLOAD FINISHED ---")