import os
# Force detailed error reporting
os.environ["XFORMERS_MORE_DETAILS"] = "1"
print("Attempting to import xformers...")
try:
    import xformers
    print(f"xFormers version: {xformers.__version__}")
    import xformers.ops
    print("xFormers ops imported successfully")
except Exception as e:
    print(f"xFormers failed: {e}")
