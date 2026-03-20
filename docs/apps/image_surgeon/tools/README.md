# Processing Tools

> `apps/image_surgeon/tools/`

Core processing tools for image surgery operations.

---

## 📁 Structure

```
tools/
├── __init__.py          # Package exports
├── person_extractor.py  # GroundingDINO + SAM2 extraction
├── clothes_parser.py    # SegFormer clothes masking
├── catvton.py           # CatVTON virtual try-on
├── inpaint.py           # SD inpainting engine
└── scoring.py           # CLIP/keyword asset scoring
```

---

## 1. Person Extractor (`person_extractor.py`)

Extracts person from image using GroundingDINO detection + SAM2 segmentation.

```python
def extract_person_grounded(image_path: str, output_path: str = None) -> Path:
    """
    Extract person from image with transparent background.
    
    Pipeline:
        1. GroundingDINO detects "person" bounding box
        2. SAM2 segments person within box
        3. Apply mask to create RGBA output
    
    Args:
        image_path: Input image path
        output_path: Optional output path (default: {stem}_extracted_grounded.png)
        
    Returns:
        Path to extracted image (RGBA with transparent background)
    """
```

**Dependencies:**
- `transformers` (GroundingDINO)
- `sam2` (SAM2 segmentation)
- Models from `configs.paths.SAM2_MODELS`

---

## 2. Clothes Parser (`clothes_parser.py`)

SegFormer-based human body parsing for clothes masking.

```python
class SegFormerHumanParser:
    """
    Human body parsing using SegFormer.
    Segments 18 body part categories.
    """
    
    def parse(self, image: Image) -> np.ndarray:
        """Returns segmentation map (H, W) with category IDs"""
        
    def get_clothes_mask(self, image: Image) -> np.ndarray:
        """Returns binary mask of clothing area"""
```

**Category IDs:**

| ID | Part |
|----|------|
| 5 | Upper-clothes |
| 6 | Dress |
| 7 | Coat |
| 9 | Pants |
| 12 | Skirt |

```python
def segment_clothes(image_path: str) -> str:
    """
    Generate clothes mask for an image.
    
    Returns:
        Path to saved mask image
    """
```

---

## 3. Clothes Inpaint (`clothes_inpaint.py`) - NEW

ZenityX CLOTHES model for prompt-based clothing changes.

```python
class ClothesInpaintEngine:
    """
    Clothes inpainting using ZenityX model.
    Changes clothes based on text prompt (no garment image needed).
    
    Trigger word: "Clothes"
    """
    
    def load(self):
        """Load inpainting pipeline with VRAM optimizations"""
        
    def inpaint(
        self,
        image: Image,
        mask: Image,
        prompt: str,
        negative_prompt: str = "ugly, blurry, low quality...",
        strength: float = 0.95,
        steps: int = 36,
        cfg: float = 15.0
    ) -> Image:
        """
        Inpaint clothes on a person.
        
        Prompt format: "Clothes, (realistic:1.4), {user_prompt}"
        
        Args:
            image: Person photo
            mask: Clothes region mask
            prompt: Clothes description (e.g., "red evening dress")
            
        Returns:
            Image with new clothes
        """
        
    def unload(self):
        """Free VRAM"""
```

**Model:** `inpaintingByZenityxAI_v10.safetensors`

---

## 4. CatVTON Engine (`catvton.py`)

Virtual try-on using CatVTON diffusion model.

```python
class CatVTONEngine:
    """
    Virtual try-on engine using CatVTON.
    Swaps clothes from garment image onto person image.
    """
    
    def load(self):
        """Load CatVTON model (FP32)"""
        
    def try_on(
        self,
        person_image: Image,
        garment_image: Image,
        mask: np.ndarray,
        num_steps: int = 40
    ) -> Image:
        """
        Perform virtual try-on.
        
        Args:
            person_image: Person photo
            garment_image: Garment to apply
            mask: Clothes region mask
            num_steps: Diffusion steps
            
        Returns:
            Result image with garment applied
        """
        
    def unload(self):
        """Free VRAM"""
```

---

## 4. Inpaint Engine (`inpaint.py`)

Stable Diffusion inpainting for background generation.

```python
class InpaintEngine:
    """
    Lightweight inpainting engine using StableDiffusionInpaintPipeline.
    Optimized for 4GB VRAM.
    """
    
    def __init__(self, model_key: str = "dreamshaper"):
        """
        Args:
            model_key: Key from configs.paths.DIFFUSION_MODELS
        """
        
    def load_model(self):
        """Load SD inpaint pipeline with VRAM optimizations"""
        
    def inpaint(
        self,
        image: Union[str, Path, Image],
        mask: Union[str, Path, Image, np.ndarray],
        prompt: str,
        negative_prompt: str = "ugly, blurry, low quality",
        strength: float = 0.85,
        steps: int = 25,
        cfg: float = 7.0,
        seed: Optional[int] = None
    ) -> Image:
        """
        Inpaint masked region with generated content.
        
        Args:
            image: Original image
            mask: Binary mask (white = inpaint region)
            prompt: What to generate
            
        Returns:
            Inpainted PIL Image
        """
        
    def unload(self):
        """Free VRAM"""
```

**VRAM Optimizations:**
- `enable_sequential_cpu_offload()`
- `enable_vae_slicing()`
- `enable_vae_tiling()`
- `enable_attention_slicing(slice_size="max")`

---

## 5. Asset Scoring (`scoring.py`)

Match text prompts to assets using keyword or CLIP scoring.

```python
def score_assets_keyword(prompt: str, assets: List[Path]) -> List[Tuple[Path, float]]:
    """
    Score assets using keyword matching.
    
    Scoring:
        - Filename contains keyword: +2 points
        - Category contains keyword: +1 point
        
    Returns:
        List of (path, score) tuples, sorted descending
    """

def score_assets_clip(prompt: str, assets: List[Path]) -> List[Tuple[Path, float]]:
    """
    Score assets using CLIP embeddings.
    Falls back to keyword matching if CLIP unavailable.
    """

def get_best_asset(prompt: str, assets: List[Path], use_clip: bool = False) -> Optional[Path]:
    """
    Get best matching asset for a prompt.
    
    Args:
        prompt: Text description (e.g., "red evening dress")
        assets: List of asset paths to score
        use_clip: Use CLIP scoring (slower but more accurate)
        
    Returns:
        Best matching path, or None if no assets
    """
```

---

## Usage Examples

### Extract Person
```python
from apps.image_surgeon.tools import extract_person_grounded

result = extract_person_grounded("photo.jpg")
# -> "photo_extracted_grounded.png"
```

### Generate Clothes Mask
```python
from apps.image_surgeon.tools.clothes_parser import segment_clothes

mask_path = segment_clothes("photo.jpg")
```

### Inpaint Background
```python
from apps.image_surgeon.tools.inpaint import InpaintEngine

engine = InpaintEngine()
result = engine.inpaint(
    image="photo.jpg",
    mask=bg_mask,
    prompt="sunset beach, golden hour"
)
engine.unload()
```
