# Image Surgeon

> `apps/image_surgeon/`

AI-powered image manipulation system for background replacement, virtual try-on, and clothing changes.

---

## 📁 Structure

```
image_surgeon/
├── engine.py              # ImageSurgeonEngine - central orchestrator
├── runner.py              # CLI interface
├── pipeline/              # Configuration & asset registry
│   ├── __init__.py        # Package exports
│   ├── pipeline_types.py  # SurgeonConfig dataclass
│   └── registry.py        # Asset discovery & scoring
├── tools/                 # Processing tools
│   ├── __init__.py        # Package exports
│   ├── person_extractor.py  # GroundingDINO + SAM2
│   ├── clothes_parser.py    # SegFormer masking
│   ├── clothes_inpaint.py   # ZenityX CLOTHES inpainting (NEW)
│   ├── catvton.py           # Virtual try-on engine
│   ├── inpaint.py           # SD inpainting
│   └── scoring.py           # CLIP/keyword asset matching
└── utils/                 # Utility modules
    ├── __init__.py        # Package exports
    ├── upscaler.py        # RealESRGAN + Lanczos upscaling
    ├── background_gen.py  # txt2img background generation (NEW)
    ├── diffusion_upscale.py # Diffusion-based upscaling (NEW)
    └── prompts.py         # Prompt optimization
```

---

## 🔧 Modes

### 1. Background Mode (`--mode background`)

Replace image background with:
- **Transparent** - Remove background entirely
- **Solid Color** - Black, white, red, etc.
- **Image** - Use a specific background image
- **Generated** - AI-generate background from prompt

**Pipeline:**
```
Extract Person (GroundingDINO + SAM2)
    → txt2img Background (Dreamshaper 8)
    → Diffusion Add Details
    → Composite
    → Diffusion Blend
    → ESRGAN 4x
    → Lanczos Polish
```

### 2. Clothes Mode (`--mode clothes`)

Two sub-modes:
- **Prompt-Based** - Describe new clothes (uses ClothesInpaint)
- **Garment-Based** - Use actual garment image (uses CatVTON)

**Prompt Pipeline:**
```
Segment Clothes (SegFormer)
    → ClothesInpaint (ZenityX, trigger: "Clothes")
    → ESRGAN 4x
    → Lanczos Polish
```

**Garment Pipeline:**
```
Segment Clothes (SegFormer)
    → CatVTON (FP32 Virtual Try-On)
    → ESRGAN 4x
    → Lanczos Polish
```

### 3. Auto Mode (`--mode auto`) - NEW

Combined background + clothes in one command.

**Format:** `--auto "{background_prompt, clothes_prompt}"`

**Pipeline:**
```
Stage A: Extract → Generate Background → Composite
Stage B: Segment Clothes → Inpaint (with quality enhancers)
Stage C: ESRGAN 4x → Lanczos Polish
```

---

## 🚀 Quick Start

```bash
# Activate venv
d:\neural_citadel\venvs\env\enhanced\Scripts\activate

# Background examples
python -m apps.image_surgeon.runner --mode background --image photo.jpg --transparent --open
python -m apps.image_surgeon.runner --mode background --image photo.jpg --solid black --open
python -m apps.image_surgeon.runner --mode background --image photo.jpg --prompt "sunset beach" --open

# Clothes examples
python -m apps.image_surgeon.runner --mode clothes --image photo.jpg --prompt "red dress" --open
python -m apps.image_surgeon.runner --mode clothes --image photo.jpg --garment dress.png --open

# Auto mode (combined)
python -m apps.image_surgeon.runner --mode auto --image photo.jpg --auto "{beach sunset, floral dress}" --open
```

---

## 📋 CLI Arguments

| Argument | Type | Description |
|----------|------|-------------|
| `--mode` | `background`/`clothes`/`auto` | Operation mode |
| `--image` | Path | Input image |
| `--solid` | Color name | Solid background (black, white, etc.) |
| `--transparent` | Flag | Transparent background |
| `--bg` | Path | Background image path |
| `--prompt` | Text | Generative prompt |
| `--garment` | Path | Specific garment file |
| `--auto` | Text | Auto mode: `"{bg_prompt, clothes_prompt}"` |
| `--open` | Flag | Open result after generation |
| `--upscale` | Float | Upscale factor (default: 4.0) |
| `--steps` | Int | Inference steps (default: 36) |
| `--list` | Flag | Show available assets |

---

## 🎨 Solid Colors

```python
SOLID_COLORS = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "red", "green", "blue", "gray", "yellow",
    "cyan", "magenta", "orange", "pink", "purple"
}
```

---

## 📂 Output Directories

| Mode | Path |
|------|------|
| Background | `assets/generated/image_surgeon/background/` |
| Clothes | `assets/generated/image_surgeon/clothes/` |
| Auto | `assets/generated/image_surgeon/auto/` |
| Raw Extracts | `assets/generated/image_surgeon/raw_extract/` |

---

## 🔗 Models Used

| Purpose | Model |
|---------|-------|
| Person Detection | GroundingDINO (Transformers) |
| Segmentation | SAM2 Large |
| Background Generation | Dreamshaper 8 |
| Clothes Inpainting | ZenityX Clothes (trigger: `Clothes`) |
| Virtual Try-On | CatVTON (FP32) |
| Upscaling | RealESRGAN 4x+ |
| Final Polish | Lanczos |

---

*See [instruction.md](instruction.md) for detailed usage examples.*
