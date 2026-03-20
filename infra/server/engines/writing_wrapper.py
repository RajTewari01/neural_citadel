import argparse
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Writing Engine Wrapper")
    parser.add_argument("--model_path", type=str, required=False, help="Path to GGUF model (SFW only)")
    parser.add_argument("--nsfw", action="store_true", help="Use NSFW Writing Engine")
    
    args = parser.parse_args()
    
    if args.nsfw:
        # Delegate directly to NSFW engine
        # Lazy import to prevent stdout conflict
        import infra.standalone.nsfw_writing_engine as nsfw_engine
        nsfw_engine.main()
    else:
        # SFW Mode: Patch the model path and run
        # Lazy import to prevent stdout conflict
        import infra.standalone.writing_engine as sfw_engine
        if args.model_path:
            sfw_engine.MODEL_PATH = Path(args.model_path)
        sfw_engine.main()

if __name__ == "__main__":
    main()
