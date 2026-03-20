"""
SegFormer Human Parsing - Clothes Segmentation

Uses SegFormer model fine-tuned on ATR dataset for precise human/clothing parsing.
18 categories including Upper-clothes, Pants, Face, Left/Right-arm, Hair.

This provides semantic understanding - the model knows what "clothes" vs "skin" means.
"""

import torch
import numpy as np
from PIL import Image
from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ATR Labels (18 categories)
ATR_LABELS = [
    'Background',    # 0
    'Hat',           # 1
    'Hair',          # 2
    'Sunglasses',    # 3
    'Upper-clothes', # 4 -- Main clothes
    'Skirt',         # 5
    'Pants',         # 6
    'Dress',         # 7
    'Belt',          # 8
    'Left-shoe',     # 9
    'Right-shoe',    # 10
    'Face',          # 11
    'Left-leg',      # 12
    'Right-leg',     # 13
    'Left-arm',      # 14
    'Right-arm',     # 15
    'Bag',           # 16
    'Scarf'          # 17
]

# Indices for clothes mask
CLOTHES_INDICES = [4, 5, 6, 7, 17]  # Upper-clothes, Skirt, Pants, Dress, Scarf


class SegFormerHumanParser:
    """
    SegFormer model for human parsing with 18 categories.
    Automatically segments clothes vs body parts.
    """
    
    def __init__(self, device: str = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.processor = None
        
    def load(self):
        """Load model from HuggingFace."""
        if self.model is not None:
            return
            
        from transformers import SegformerImageProcessor, SegformerForSemanticSegmentation
        import gc
        
        print("[SegFormer] Loading SegFormer Human Parser...")
        
        self.processor = SegformerImageProcessor.from_pretrained("mattmdjaga/segformer_b2_clothes")
        # Force low_cpu_mem_usage=False to avoid meta tensor errors with accelerate
        self.model = SegformerForSemanticSegmentation.from_pretrained(
            "mattmdjaga/segformer_b2_clothes",
            low_cpu_mem_usage=False 
        )
        self.model.to(self.device)
        
        print(f"[SegFormer] SegFormer loaded on {self.device}")
        
    def unload(self):
        """Free GPU memory."""
        if self.model is not None:
            del self.model
            del self.processor
            self.model = None
            self.processor = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    
    def parse(self, image: Image.Image) -> np.ndarray:
        """
        Parse human in image into 18 categories.
        Returns (H, W) array with category indices.
        """
        if self.model is None:
            self.load()
        
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
        
        # Upsample to original size
        upsampled = torch.nn.functional.interpolate(
            logits,
            size=image.size[::-1],
            mode='bilinear',
            align_corners=False
        )
        
        return upsampled.argmax(dim=1).squeeze().cpu().numpy()
    
    def get_clothes_mask(self, image: Image.Image) -> np.ndarray:
        """Get binary mask for clothes only."""
        parsing = self.parse(image)
        return np.isin(parsing, CLOTHES_INDICES)


def segment_clothes(
    image_path: str,
    output_name: str = None
) -> Path:
    """
    Create clothes mask using SegFormer human parsing.
    Automatically excludes face, arms, legs, hair.
    
    Args:
        image_path: Path to input image
        output_name: Optional output filename
        
    Returns:
        Path to saved mask file
    """
    import cv2
    
    image_path = Path(image_path)
    output_dir = PROJECT_ROOT / "assets" / "generated" / "image_surgeon" / "masks"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"[SegFormer] Clothes Parsing: {image_path.name}")
    
    img = Image.open(image_path).convert("RGB")
    
    parser = SegFormerHumanParser()
    parser.load()
    
    try:
        # Get full parsing result
        parsing = parser.parse(img)
        
        # Print category stats
        print("\n[SegFormer] Parsing Results:")
        for i, label in enumerate(ATR_LABELS):
            count = np.sum(parsing == i)
            if count > 0:
                pct = count / parsing.size * 100
                print(f"   {i:2d} {label:15s}: {count:,} pixels ({pct:.1f}%)")
        
        # Create clothes-only mask
        clothes_mask = np.isin(parsing, CLOTHES_INDICES)
        
        # Morphological cleanup
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        clothes_mask = cv2.erode(clothes_mask.astype(np.uint8), kernel, iterations=1)
        clothes_mask = cv2.dilate(clothes_mask, kernel, iterations=2)
        clothes_mask = clothes_mask.astype(bool)
        
        print(f"\n   Clothes: {np.sum(clothes_mask):,} pixels")
        
    finally:
        parser.unload()
    
    # Save outputs
    stem = output_name or f"{image_path.stem}_clothes"
    
    # Binary mask
    mask_path = output_dir / f"{stem}_mask.png"
    Image.fromarray((clothes_mask * 255).astype(np.uint8)).save(mask_path)
    print(f"[SegFormer] Mask: {mask_path}")
    
    # Preview
    preview = np.array(img)
    preview[clothes_mask] = (preview[clothes_mask] * 0.5 + np.array([255, 0, 0]) * 0.5).astype(np.uint8)
    preview_path = output_dir / f"{stem}_preview.png"
    Image.fromarray(preview).save(preview_path)
    print(f"[SegFormer] Preview: {preview_path}")
    
    # Full parsing visualization
    palette = _get_palette()
    parsing_vis = Image.fromarray(parsing.astype(np.uint8))
    parsing_vis.putpalette(palette)
    parsing_vis.save(output_dir / f"{stem}_parsing.png")
    
    print(f"[SegFormer] Done!")
    return mask_path


def _get_palette():
    """Color palette for parsing visualization."""
    colors = [
        (0, 0, 0),       # Background
        (128, 0, 0),     # Hat
        (255, 0, 0),     # Hair
        (0, 128, 0),   # Sunglasses
        (0, 255, 0),     # Upper-clothes
        (0, 0, 128),     # Skirt
        (0, 0, 255),     # Pants
        (128, 128, 0),   # Dress
        (128, 0, 128),   # Belt
        (0, 128, 128),   # Left-shoe
        (128, 128, 128), # Right-shoe
        (255, 128, 0), # Face
        (255, 0, 128), # Left-leg
        (0, 255, 128), # Right-leg
        (128, 255, 0), # Left-arm
        (0, 128, 255), # Right-arm
        (255, 128, 128), # Bag
        (128, 255, 128),   # Scarf
    ]
    palette = []
    for i in range(256):
        if i < len(colors):
            palette.extend(colors[i])
        else:
            palette.extend([0, 0, 0])
    return palette


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        segment_clothes(sys.argv[1])
    else:
        print("Usage: python clothes_parser.py <image_path>")
