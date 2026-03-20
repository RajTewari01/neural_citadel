# Image Surgeon - Quick Start Guide

> **Virtual Environment:** `d:\neural_citadel\venvs\env\enhanced`

## 🚀 Quick Commands

### Background Replacement

```bash
# Transparent background
python -m apps.image_surgeon.runner --mode background --image photo.jpg --transparent --open

# Solid color background
python -m apps.image_surgeon.runner --mode background --image photo.jpg --solid black --open

# AI-generated background
python -m apps.image_surgeon.runner --mode background --image photo.jpg --prompt "sunset beach tropical ocean" --open
```

### Clothes Change (Prompt-Based)

```bash
# Uses ZenityX CLOTHES inpainting model
python -m apps.image_surgeon.runner --mode clothes --image photo.jpg --prompt "red evening dress" --open
python -m apps.image_surgeon.runner --mode clothes --image photo.jpg --prompt "black full sleeve tuxedo" --open
```

### Clothes Change (CatVTON - With Garment Image)

```bash
# Virtual try-on with actual garment image
python -m apps.image_surgeon.runner --mode clothes --image photo.jpg --garment dress.png --open
```

### Auto Mode (Background + Clothes)

```bash
# Combined: Replace background AND change clothes
python -m apps.image_surgeon.runner --mode auto --image path/to/photo.jpg --auto "{beach sunset, floral summer dress}" --open
python -m apps.image_surgeon.runner --mode auto --image path/to/photo.jpg --auto "{office interior, formal business suit}" --open
```

---

## 📋 Argument Reference

| Argument | Description | Example |
|----------|-------------|---------|
| `--mode` | Operation mode | `background`, `clothes`, `auto` |
| `--image` | Input image path | `photo.jpg` |
| `--prompt` | AI generation prompt | `"sunset beach"` |
| `--solid` | Solid background color | `black`, `white`, `blue` |
| `--transparent` | Transparent background | (flag) |
| `--bg` | Background image to use | `beach.jpg` |
| `--garment` | Garment image for CatVTON | `dress.png` |
| `--auto` | Auto mode prompts | `"{bg_prompt, clothes_prompt}"` |
| `--upscale` | Upscale factor | `4.0` (default) |
| `--steps` | Inference steps | `36` |
| `--open` | Open result when done | (flag) |
| `--list` | List available assets | (flag) |

---

## 🔧 Pipelines

### Background Mode Pipeline
```
Input → GroundingDINO (detect) → SAM2 (segment) → Extract Person
     ↓
txt2img (Dreamshaper 8) → Diffusion Upscale (add details) → Composite
     ↓
Diffusion Blend (0.08 strength) → ESRGAN 4x → Lanczos → Output
```

### Clothes Mode Pipeline (Prompt-Based)
```
Input → SegFormer (clothes mask) → ClothesInpaint (ZenityX, trigger: Clothes)
     ↓
Prompt: "Clothes, (realistic:1.4), {user_prompt}"
     ↓
ESRGAN 4x → Lanczos → Output
```

### Clothes Mode Pipeline (CatVTON)
```
Input → SegFormer (clothes mask) → CatVTON (FP32, virtual try-on)
     ↓
ESRGAN 4x → Lanczos → Output
```

### Auto Mode Pipeline
```
Stage A: Extract Person → Generate Fresh Background → Composite
Stage B: Segment Clothes → Inpaint (CLOTHES + quality enhancers)
Stage C: ESRGAN 4x → Lanczos → Output
```

---

## 🎨 Solid Colors

| Color | RGB |
|-------|-----|
| `black` | (0, 0, 0) |
| `white` | (255, 255, 255) |
| `red` | (255, 0, 0) |
| `blue` | (0, 0, 255) |
| `green` | (0, 255, 0) |
| `gray` | (128, 128, 128) |
| `yellow` | (255, 255, 0) |
| `cyan` | (0, 255, 255) |
| `magenta` | (255, 0, 255) |
| `orange` | (255, 165, 0) |
| `pink` | (255, 192, 203) |
| `purple` | (128, 0, 128) |

---

## 📁 Output Locations

| Mode | Output Directory |
|------|------------------|
| Background | `assets/generated/image_surgeon/background/` |
| Clothes | `assets/generated/image_surgeon/clothes/` |
| Auto | `assets/generated/image_surgeon/auto/` |
| Raw Extracts | `assets/generated/image_surgeon/raw_extract/` |

---

## 💡 Tips

1. **Clothes prompts**: Be specific about style, color, and type (e.g., "black full sleeve leather jacket")
2. **Background prompts**: Include environment details (e.g., "tropical beach sunset palm trees ocean waves")
3. **Auto mode**: Great for complete makeovers with one command
4. **CatVTON**: Use when you have an actual garment image for realistic try-on
5. **Quality**: Higher steps (36-40) give better results but take longer

---

## ⚠️ Requirements

- GPU with 4GB+ VRAM (uses CPU offload for low memory)
- Virtual environment: `venvs/env/enhanced`
- Models: Dreamshaper 8, ZenityX Clothes Inpainting, RealESRGAN 4x+
