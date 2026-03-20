# Neural Citadel - Project Documentation

> **AI-Powered Image Generation System**

This documentation covers the entire project structure, modules, and how each component works.

---

## 📁 Project Structure

```
neural_citadel/
├── apps/                      # Main application modules
│   └── image_gen/             # Image generation system
│       ├── tools/             # Prompt enhancement utilities
│       ├── schedulars/        # Noise scheduler implementations
│       ├── upscalers/         # Image upscaling modules
│       ├── controlnet/        # ControlNet guidance modules
│       └── pipeline/          # Pipeline configuration types
├── tools/                     # CLI utilities and scrapers
├── configs/                   # Centralized configuration
├── tests/                     # Test files and engine testing
├── assets/                    # Models, prompts, generated images
│   ├── models/image_gen/      # AI model weights
│   ├── prompts/               # Scraped CivitAI prompts
│   └── generated/             # Output images
└── docs/                      # This documentation
```

---

## 🚀 Quick Start

### Generate an Image
```python
from tests.engine import DiffusionEngine

engine = DiffusionEngine()
image = engine.generate(
    prompt="a mystical forest at night",
    width=512,
    height=768,
    steps=30
)
engine.unload()
```

### Enhance a Prompt
```python
from apps.image_gen.tools import enhance_prompt

result = enhance_prompt("forest at night", model_id=46294)
print(result.prompt)  # Enhanced with quality boosters
```

### Scrape CivitAI Prompts
```bash
python tools/api_scraper.py https://civitai.com/models/46294
```

---

## 📚 Module Documentation

| Module | Description |
|--------|-------------|
| [apps/image_gen/](apps/image_gen/README.md) | Image generation system |
| [tools/](tools/README.md) | CLI utilities and scrapers |
| [configs/](configs/README.md) | Centralized configuration |
| [tests/](tests/README.md) | Test files |

---

## 🔧 Hardware Configuration

This system is optimized for **NVIDIA GTX 1650 (4GB VRAM)**:

| Setting | Value | Reason |
|---------|-------|--------|
| Precision | `float32` | Prevents NaN/black images |
| Memory | Sequential CPU Offload | Fits models in 4GB |
| Slicing | Aggressive | Reduces peak VRAM |
| Speed | ~3-5s/step | Stable generation |

---

## 📦 Dependencies

- `torch` - PyTorch for GPU computation
- `diffusers` - Hugging Face diffusion library
- `PIL` - Image processing
- `requests` - HTTP for CivitAI API
- `basicsr` - Real-ESRGAN upscaling

---

## 🔄 Workflow

1. **Scrape Prompts** → Use `api_scraper.py` to collect successful prompts from CivitAI
2. **Enhance Prompt** → Use `prompt_enhancer` to add quality boosters
3. **Generate Image** → Use `DiffusionEngine` to create the image
4. **Upscale** → Use upscaler modules for 4x resolution boost

---

*Last updated: 2026-01-04*
