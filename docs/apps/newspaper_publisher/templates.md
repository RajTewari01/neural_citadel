# Templates Guide

> Detailed documentation for all newspaper/magazine template styles.

---

## Template System

The template system uses a **registry pattern** for automatic discovery:

```python
from apps.newspaper_publisher.templates import (
    discover_templates,
    get_template_names,
    get_substyles,
    TEMPLATE_REGISTRY
)

# Discover all registered templates
discover_templates()

# List available templates
print(get_template_names())  # ['classic', 'modern', 'magazine']

# Get magazine substyles
print(get_substyles('magazine'))  # {'Neural Citadel': {...}, 'Vogue Classic': {...}, ...}
```

---

## Classic Template

**File**: `templates/classic.py`

NYT-style traditional newspaper layout.

### Features
- 3-column layout
- Serif fonts (Times New Roman)
- Classic header with date and masthead
- Column dividers
- Traditional footer

### Sample
```bash
python apps/newspaper_publisher/runner.py --category INDIA --style Classic --open
```

---

## Modern Template

**File**: `templates/modern.py`

Contemporary newspaper with bold header.

### Features
- 2-column layout
- Sans-serif fonts (Helvetica)
- Dark header bar with white text
- Clean, minimal footer
- Modern typography

### Sample
```bash
python apps/newspaper_publisher/runner.py --category USA --style Modern --open
```

---

## Magazine Template

**File**: `templates/magazine.py`

The most feature-rich template with 18+ substyles.

### Substyle Categories

#### 1. Original Block-Style Covers
These use `_draw_text_block()` for headlines with background boxes:

| Substyle | Font | Align | Accent |
|----------|------|-------|--------|
| Neural Citadel | Times-Bold | Center | Dynamic |
| The Tech | Courier | Left | Green (#00FF00) |
| The Times | Georgia | Center | Dynamic |
| The Minimal | Arial | Left | Dynamic |
| The Bold | Impact | Center | Yellow (#FFFF00) |
| The Elegant | Times-Roman | Left | Vogue Red (#C40233) |
| The Geo | Arial-Bold | Left | Gold (#FFD700) |
| The Star | Arial-Bold | Right | Pink (#FF0099) |
| The Noir | Times-Bold | Center | B&W |
| The Pop | Comic/Impact | Center | Dynamic |
| The Corporate | Segoe UI | Left | Navy (#003366) |
| The Future | Segoe UI | Center | Cyan (#00AAFF) |

#### 2. Premium Vogue-Style Covers
These use `_create_vogue_cover()` with floating text and high-fashion background images:

| Substyle | Background Image | Masthead Size | Text Color | Accent |
|----------|------------------|---------------|------------|--------|
| Vogue Classic | style_vogue_classic.png | 120pt | White | Vogue Red (#E60012) |
| Vogue Paris | style_vogue_paris.png | 100pt | Cream | Gold (#DAA520) |
| Vogue Noir | style_vogue_noir.png | 110pt | White | Dark Red (#8B0000) |
| Elle Style | style_elle.png | 100pt | White | Hot Pink (#FF1493) |
| Harpers Bazaar | style_harpers_bazaar.png | 90pt | Black | Firebrick (#B22222) |
| GQ Magazine | style_gq.png | 140pt | White | Blue (#1E90FF) |

---

## Creating Custom Styles

### 1. Add to STYLES dict

```python
# In templates/magazine.py

STYLES = {
    # ... existing styles ...
    
    'My Custom Style': {
        'font_masthead': 'Georgia-Bold',
        'font_main': 'Georgia',
        'font_body': 'Helvetica',
        'caps': True,
        'align': 'center',
        'bg': 'my_background.png',  # or None for article image
        'mode': 'vogue_premium',     # Use premium renderer
        'palette': HexColor('#FFFFFF'),
        'masthead_size': 110,
        'text_shadow': True,
        'floating_text': True,
        'accent_color': HexColor('#FF5500')
    }
}
```

### 2. Add DEFAULT_STYLE_CONTENT

```python
DEFAULT_STYLE_CONTENT = {
    # ... existing content ...
    
    'My Custom Style': [
        {'title': "Main Headline", 'author': "Author", 'category': "CAT", 'content': "..."},
        {'title': "Sub Headline 1", 'author': "Author 2", 'category': "CAT2", 'content': "..."},
        # ... more cover articles ...
    ]
}
```

### 3. Use It

```bash
python apps/newspaper_publisher/runner.py --category INDIA --style Magazine --substyle "My Custom Style" --open
```

---

## Style Properties Reference

| Property | Type | Description |
|----------|------|-------------|
| `font_masthead` | str | Font for main title |
| `font_main` | str | Font for headlines |
| `font_body` | str | Font for body text |
| `caps` | bool | Uppercase titles |
| `align` | str | left, center, right |
| `bg` | str/None | Background image filename or None |
| `mode` | str | `vogue_premium` or other |
| `palette` | HexColor | Main text color |
| `masthead_size` | int | Masthead font size (pts) |
| `text_shadow` | bool | Enable text shadows |
| `floating_text` | bool | No background boxes |
| `accent_color` | HexColor | Sub-headline accent |
| `overlay_darkness` | float | Darken cover image (0-1) |
| `minimal_layout` | bool | Fewer text elements |
| `sidebar_teasers` | bool | Right-side teasers |
| `bold_headlines` | bool | Extra bold headlines |
