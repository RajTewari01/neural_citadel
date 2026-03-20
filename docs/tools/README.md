# CLI Tools

> `tools/`

Command-line utilities for prompt scraping and enhancement.

---

## Overview

```
tools/
├── api_scraper.py      # Scrape prompts from CivitAI
├── extract_prompts.py  # Extract prompts from PNG metadata
└── prompt_enhancer.py  # CLI prompt enhancement
```

---

## `api_scraper.py` - CivitAI Prompt Scraper

Scrapes prompts and settings from CivitAI model pages using the API.

### Usage

```bash
# Scrape prompts from a model
python tools/api_scraper.py https://civitai.com/models/46294

# Output: assets/prompts/model_46294_prompts.json
```

### How It Works

1. Extracts model ID from URL
2. Calls CivitAI Images API with model filter
3. Extracts metadata (prompt, negative, steps, CFG, sampler)
4. Saves to JSON sorted by reactions

### API Key

Uses your CivitAI API key for authentication:
```python
API_KEY = "your_api_key_here"  # Line 19
```

### Output Format

```json
{
  "model_id": 46294,
  "prompt_count": 100,
  "prompts": [
    {
      "prompt": "hyper realistic, 8k, ...",
      "negative_prompt": "bad anatomy, ...",
      "steps": 24,
      "cfg_scale": 3.5,
      "sampler": "DPM++ SDE",
      "seed": 123456789,
      "size": "1024x1536",
      "reactions": 5
    }
  ]
}
```

### Classes

- `CivitAIClient` - API client with authentication
- `scrape_model(client, model_id)` - Scrape all prompts from a model

---

## `extract_prompts.py` - PNG Metadata Extractor

Extracts generation parameters from PNG image metadata (useful for downloaded images).

### Usage

```bash
# Extract from a single image
python tools/extract_prompts.py image.png

# Extract from all images in a folder
python tools/extract_prompts.py folder/
```

### How It Works

1. Opens PNG file
2. Reads `parameters` or `prompt` from PNG metadata
3. Parses prompt, negative prompt, and settings
4. Outputs to console or saves to JSON

### Metadata Fields

Standard A1111/Comfy metadata:
- `prompt` - Generation prompt
- `negative_prompt` - Negative prompt
- `steps` - Inference steps
- `cfg_scale` / `CFG scale` - Guidance scale
- `sampler` / `sampler_name` - Scheduler used
- `seed` - Random seed
- `model` / `model_hash` - Model identifier

---

## `prompt_enhancer.py` - CLI Prompt Enhancement

Command-line interface for the prompt enhancer.

### Usage

```bash
# Enhance with auto-detected style
python tools/prompt_enhancer.py "a girl in forest"

# Enhance with specific model
python tools/prompt_enhancer.py "ocean sunset" 46294
```

### Output

```
Original prompt: ocean sunset
Model ID: 46294
------------------------------------------------------------

=== Model 46294 Style ===
Quality boosters: hyper realistic, atmospheric, 8k, epic composition, cinematic
Common LoRAs: more_details, zhongfenghuaxiyou-000018, ghost
Trigger words: DiscoElysiumStyle, McQuarrie
Best settings: 24 steps, CFG 3.5, DPM++ SDE
Common sizes: (1024, 1536)
------------------------------------------------------------

=== ENHANCED PROMPT ===
hyper realistic, atmospheric, 8k, epic composition, cinematic, 
ocean sunset, <lora:more_details:0.5>

=== NEGATIVE PROMPT ===
hand, easynegative, greyscale, monochrome, water mark...

=== RECOMMENDED SETTINGS ===
Steps: 24
CFG: 3.5
Sampler: DPM++ SDE
Size: 1024x1536
LoRAs: more_details
```

### Classes

- `ModelPromptEnhancer` - Main enhancer class
- `ModelStyle` - Learned style dataclass
- `EnhancedPrompt` - Output dataclass

### Functions

- `enhance_for_model(prompt, model_id)` - Quick enhance
- `detect_theme(prompt)` - Auto-detect style

---

## Workflow

1. **Scrape:** `python tools/api_scraper.py <civitai_url>`
2. **Enhance:** Use in code or CLI
3. **Generate:** Pass enhanced prompt to engine

---

## Adding API Key

1. Go to [CivitAI](https://civitai.com/user/account)
2. Scroll to API Keys section
3. Create new key
4. Add to `api_scraper.py` line 19
