"""
CivitAI Image Metadata Extractor
================================

Extracts prompt data from downloaded CivitAI images.
PNG files often contain embedded generation parameters.

Usage:
    python extract_prompts.py <image_path_or_folder>
"""

from PIL import Image
from PIL.PngImagePlugin import PngInfo
import json
import sys
from pathlib import Path


def extract_from_png(image_path: Path) -> dict:
    """Extract generation data from PNG metadata."""
    
    try:
        img = Image.open(image_path)
        
        # PNG metadata is in img.info
        info = img.info or {}
        
        result = {
            'file': image_path.name,
            'width': img.width,
            'height': img.height,
        }
        
        # Common metadata keys used by different tools
        # CivitAI / Automatic1111
        if 'parameters' in info:
            result['parameters_raw'] = info['parameters']
            result.update(parse_a1111_params(info['parameters']))
        
        # ComfyUI
        if 'prompt' in info:
            result['comfyui_prompt'] = info['prompt']
            
        # Generic
        if 'Comment' in info:
            result['comment'] = info['Comment']
            
        # NAI / NovelAI
        if 'Description' in info:
            result['description'] = info['Description']
        
        # All other metadata
        other_keys = [k for k in info.keys() if k not in ['parameters', 'prompt', 'Comment', 'Description']]
        if other_keys:
            result['other_metadata'] = {k: str(info[k])[:200] for k in other_keys}
        
        return result
        
    except Exception as e:
        return {'file': image_path.name, 'error': str(e)}


def parse_a1111_params(params: str) -> dict:
    """Parse Automatic1111 style parameters string."""
    
    result = {}
    
    # Split by "Negative prompt:"
    if 'Negative prompt:' in params:
        parts = params.split('Negative prompt:', 1)
        result['prompt'] = parts[0].strip()
        rest = parts[1]
    else:
        rest = params
        result['prompt'] = ''
    
    # Find the settings line (starts with "Steps:")
    if 'Steps:' in rest:
        parts = rest.split('Steps:', 1)
        result['negative_prompt'] = parts[0].strip()
        settings_line = 'Steps:' + parts[1]
        
        # Parse key: value pairs
        for item in settings_line.split(','):
            if ':' in item:
                key, value = item.split(':', 1)
                result[key.strip().lower().replace(' ', '_')] = value.strip()
    else:
        result['negative_prompt'] = rest.strip()
    
    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_prompts.py <image_path_or_folder>")
        print("\nExamples:")
        print("  python extract_prompts.py image.png")
        print("  python extract_prompts.py ./downloaded_images/")
        sys.exit(1)
    
    path = Path(sys.argv[1])
    
    if path.is_file():
        # Single image
        result = extract_from_png(path)
        print(json.dumps(result, indent=2, default=str))
        
    elif path.is_dir():
        # Folder of images
        images = list(path.glob('*.png')) + list(path.glob('*.jpg')) + list(path.glob('*.jpeg'))
        print(f"Found {len(images)} images")
        
        results = []
        for img_path in images:
            print(f"Processing: {img_path.name}")
            result = extract_from_png(img_path)
            if 'prompt' in result and result.get('prompt'):
                results.append(result)
                print(f"  -> Found prompt!")
        
        print(f"\n=== Extracted {len(results)} prompts ===")
        
        # Save to JSON
        output_file = path / 'extracted_prompts.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Saved to: {output_file}")
        
        # Show first few
        for i, r in enumerate(results[:3], 1):
            print(f"\n--- Prompt {i} ---")
            print(f"Prompt: {r.get('prompt', '')[:100]}...")
            print(f"Negative: {r.get('negative_prompt', '')[:60]}...")
    else:
        print(f"Path not found: {path}")


if __name__ == "__main__":
    main()
