from PIL import Image
import os

src = 'd:/neural_citadel/assets/apps_assets/gui/neural_citadel.ico'
dst = 'd:/neural_citadel/assets/apps_assets/gui/app_icon.png'

try:
    img = Image.open(src)
    img.save(dst, format='PNG')
    print(f"Successfully converted {src} to {dst}")
except Exception as e:
    print(f"Error converting icon: {e}")
