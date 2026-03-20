import sys
import os

user_site = r"C:\Users\tewar\AppData\Roaming\Python\Python310\site-packages"
if user_site not in sys.path:
    sys.path.append(user_site)

print("Attempting to import transformers...")
try:
    import transformers
    print(f"Transformers version: {transformers.__version__}")
except ImportError as e:
    print(f"Failed to import transformers: {e}")
    sys.exit(1)

print("Attempting to import CLIPImageProcessor...")
try:
    from transformers import CLIPImageProcessor
    print("Successfully imported CLIPImageProcessor")
except ImportError as e:
    print(f"Failed direct import: {e}")
    try:
        from transformers.models.clip.image_processing_clip import CLIPImageProcessor
        print("Successfully imported from submodule")
    except ImportError as e2:
        print(f"Failed submodule import: {e2}")

print("Checking Pillow...")
try:
    import PIL
    print(f"Pillow version: {PIL.__version__}")
except ImportError as e:
    print(f"Failed to import PIL: {e}")
