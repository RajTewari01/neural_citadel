# Newspaper Publisher

> **AI-Powered News Aggregation & Premium Magazine Generation**

Neural Citadel's newspaper publisher fetches real-time news from RSS feeds worldwide and generates beautiful PDF publications with multiple style options.

---

## 📁 File Structure

```
apps/newspaper_publisher/
├── runner.py              # CLI entry point
├── engine.py              # Core engine (fetch + generate)
├── config_types.py        # NewsConfig dataclass
├── generate_dummies.py    # Generate placeholder images
│
├── templates/
│   ├── registry.py        # Self-registering template system
│   ├── base.py            # Base template class
│   ├── factory.py         # Template instantiation
│   ├── classic.py         # NYT-style classic newspaper
│   ├── modern.py          # Modern 2-column layout
│   ├── magazine.py        # Vibrant magazine (18+ substyles)
│   └── overlay.py         # Image overlay utilities
│
└── rss_sites/
    ├── india.py           # 55 Indian news feeds
    ├── usa.py             # US news feeds
    └── global_news.py     # International feeds
```

---

## 🚀 Quick Start

### CLI Mode
```bash
# Generate with auto-open
python apps/newspaper_publisher/runner.py --category INDIA --style Magazine --open

# Specific premium style
python apps/newspaper_publisher/runner.py --category USA --style Magazine --substyle "Vogue Classic" --open

# Classic newspaper style
python apps/newspaper_publisher/runner.py --category GLOBAL --style Classic --open
```

### Interactive Mode
```bash
python apps/newspaper_publisher/runner.py
# Follow prompts to select region and style
```

---

## 🎨 Available Styles

### Main Styles

| Style | Description |
|-------|-------------|
| **Classic** | NYT-style 3-column newspaper with serif fonts |
| **Modern** | Contemporary dark header, 2-column layout |
| **Magazine** | Vibrant covers with 18+ substyles |

### Magazine Substyles

#### Original Styles
| Substyle | Mode | Description |
|----------|------|-------------|
| Neural Citadel | classic_vogue | The flagship style |
| The Tech | neon_tech | Green neon, courier fonts |
| The Times | classic_serif | Traditional serif elegance |
| The Minimal | clean_swiss | Swiss design, clean layout |
| The Bold | poster_impact | Impact font, yellow accents |
| The Elegant | delicate_fashion | Vogue red accent |
| The Geo | nature_box | National Geographic style |
| The Star | tabloid_chaos | Tabloid pink, right-aligned |
| The Noir | bw_contrast | Black & white contrast |
| The Pop | pop_art | Comic style, colorful |
| The Corporate | modern_biz | Business blue, Segoe UI |
| The Future | future_clean | Futuristic cyan accents |

#### Premium Vogue Styles (NEW)
| Substyle | Background Image | Features |
|----------|------------------|----------|
| **Vogue Classic** | style_vogue_classic.png | Elegant serif, white text, Vogue red accent |
| **Vogue Paris** | style_vogue_paris.png | French elegance, cream/gold palette |
| **Vogue Noir** | style_vogue_noir.png | Dark dramatic, 30% overlay |
| **Elle Style** | style_elle.png | Modern colorful, hot pink accent |
| **Harpers Bazaar** | style_harpers_bazaar.png | Ultra-minimal, black text |
| **GQ Magazine** | style_gq.png | Bold Impact masthead, blue accent |

---

## ⚙️ Configuration

### NewsConfig Dataclass

```python
from apps.newspaper_publisher.config_types import NewsConfig

config = NewsConfig(
    category="INDIA",           # INDIA, USA, or GLOBAL
    style="Magazine",           # Classic, Modern, or Magazine
    substyle="Vogue Classic",   # For Magazine style
    
    limit_per_feed=10,          # Articles per RSS feed
    max_workers=20,             # Parallel fetch threads
    require_image=True,         # Discard articles without images
    
    image_max_width=600,        # Resize images (optimization)
    image_quality=85,           # JPEG quality
    
    auto_open=True              # Open PDF after generation
)
```

### Programmatic Usage

```python
from apps.newspaper_publisher.engine import NewsEngine
from apps.newspaper_publisher.config_types import NewsConfig
from apps.newspaper_publisher.rss_sites.india import feeds

# Create config
config = NewsConfig(
    category="INDIA",
    style="Magazine",
    substyle="Vogue Classic",
    auto_open=True
)

# Run engine
engine = NewsEngine()
articles = engine.fetch_with_config(config, feeds)
output_path = engine.generate_with_config(config, articles)
engine.cleanup()

print(f"Generated: {output_path}")
```

---

## 🏗️ Architecture

### Registry Pattern
Templates use a self-registering decorator system (like `image_gen`):

```python
from apps.newspaper_publisher.templates.registry import register_template

@register_template(
    name="magazine",
    keywords=["magazine", "glossy", "vogue"],
    description="Vibrant magazine covers",
    substyles=STYLES
)
class VibrantMagazine(NewspaperTemplate):
    ...
```

### Engine Flow

```
NewsConfig → NewsEngine
    │
    ├── fetch_with_config()
    │   └── ThreadPoolExecutor (20 workers)
    │       └── fetch_from_feed() × N feeds
    │           ├── feedparser (RSS parsing)
    │           └── _download_image() (Pillow resize)
    │
    └── generate_with_config()
        └── TemplateClass.build(articles)
            ├── _create_cover() or _create_vogue_cover()
            └── convert_articles_to_flowables()
```

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| Feeds (INDIA) | 55 |
| Articles fetched | ~300 |
| Fetch time | ~15-20s |
| Generation time | ~11s |
| Image optimization | 600px max width, JPEG 85% |

### Optimizations
- **Parallel fetching**: `ThreadPoolExecutor` with 20 workers
- **Image resizing**: Pillow LANCZOS to 600px max width
- **Strict filtering**: Articles without images are discarded
- **Temp cleanup**: All temp images deleted after generation

---

## 🖼️ Premium Cover Features

The new Vogue-style covers (`mode: vogue_premium`) include:

- **Floating text**: No background boxes, text overlays image directly
- **Text shadows**: 2px offset for readability
- **Full-bleed images**: First article image fills entire cover
- **Dynamic masthead**: Scales to fit with preserved aspect
- **Accent colors**: Style-specific accent for sub-headlines
- **Optional overlay**: Darken image for better contrast

---

## 📝 CLI Arguments

| Argument | Short | Description |
|----------|-------|-------------|
| `--category` | `-c` | INDIA, USA, or GLOBAL |
| `--style` | | Classic, Modern, or Magazine |
| `--substyle` | | Magazine substyle name |
| `--url` | `-u` | Single custom RSS URL |
| `--open` | | Auto-open generated PDF |
| `--interactive` | `-i` | Force interactive mode |

---

## 🔧 Dependencies

- `reportlab` - PDF generation
- `feedparser` - RSS parsing  
- `newspaper3k` - Article extraction
- `Pillow` - Image processing
- `requests` - HTTP fetching

---

## 📂 Output Location

Generated PDFs are saved to:
```
D:\neural_citadel\assets\generated\newspaper\
```

Filename format:
```
{style}_{CATEGORY}_ALL_{uuid}.pdf
```

Example: `vogue_classic_INDIA_ALL_5ae772d7.pdf`
