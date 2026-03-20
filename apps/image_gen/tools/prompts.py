"""
Prompt Enhancement for Image Generation
========================================

Enhances user prompts by learning from model-specific CivitAI data.
Automatically applies quality boosters, LoRAs, and optimal settings.

HOW TO ADD NEW MODEL PROMPTS
----------------------------

1. Scrape prompts from CivitAI using the API scraper:
   
   python tools/api_scraper.py https://civitai.com/models/<MODEL_ID>
   
   This saves prompts to: assets/prompts/model_<MODEL_ID>_prompts.json

2. The PromptEnhancer will automatically detect and use the new model's
   prompts when you call enhance_prompt() with that model_id.

3. Example workflow:
   
   # Step 1: Scrape a new model
   $ python tools/api_scraper.py https://civitai.com/models/12345
   
   # Step 2: Use in your code
   from apps.image_gen.tools import enhance_prompt
   result = enhance_prompt("a beautiful sunset", model_id=12345)

DIRECTORY STRUCTURE
-------------------

assets/prompts/
├── model_46294_prompts.json    # Diffusion Brush prompts
├── model_87371_prompts.json    # difConsistency prompts
└── model_XXXXX_prompts.json    # Your new model prompts

Usage:
    from apps.image_gen.tools import enhance_prompt, PromptEnhancer
    
    # Quick enhance with model ID
    result = enhance_prompt("a girl in forest", model_id=46294)
    
    # Or with model file path (auto-detects ID)
    result = enhance_prompt("ocean waves", model_path=Path("model_46294.safetensors"))
"""

import json
import re
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass, field
from collections import Counter


# ============================================================================
# Path Resolution (No hardcoded paths)
# ============================================================================

def get_project_root() -> Path:
    """
    Dynamically find project root by looking for known markers.
    Works regardless of where the code is called from.
    """
    current = Path(__file__).resolve().parent
    
    # Walk up until we find project markers
    for parent in [current] + list(current.parents):
        # Check for project indicators
        if (parent / "assets").exists() or \
           (parent / "configs").exists() or \
           (parent / "apps").exists():
            return parent
    
    # Fallback: assume 4 levels up from this file
    # apps/image_gen/tools/prompts.py -> project root
    return Path(__file__).resolve().parent.parent.parent.parent


def get_prompts_dir() -> Path:
    """Get the prompts directory path."""
    return get_project_root() / "assets" / "prompts"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class ModelStyle:
    """Learned style from a model's prompts."""
    model_id: int
    model_name: str = ""
    quality_boosters: List[str] = field(default_factory=list)
    common_loras: List[str] = field(default_factory=list)
    trigger_words: List[str] = field(default_factory=list)
    negative_prompt: str = ""
    steps: int = 30
    cfg_scale: float = 7.0
    sampler: str = "DPM++ 2M Karras"
    width: int = 512
    height: int = 768


@dataclass
class EnhancedPrompt:
    """Enhanced prompt with all generation settings."""
    prompt: str
    negative_prompt: str
    steps: int
    cfg_scale: float
    sampler: str
    width: int = 512
    height: int = 768
    loras: List[str] = field(default_factory=list)
    model_id: Optional[int] = None


# ============================================================================
# Prompt Enhancer
# ============================================================================

class PromptEnhancer:
    """
    Enhances user prompts by learning from model-specific CivitAI data.
    
    The enhancer analyzes scraped prompts and extracts:
    - Quality boosters (masterpiece, 8k, hyper realistic, etc.)
    - Common LoRAs used with the model
    - Optimal settings (steps, CFG, sampler)
    - Effective negative prompts
    
    Example:
        enhancer = PromptEnhancer()
        result = enhancer.enhance("a girl in forest", model_id=46294)
    """
    
    def __init__(self, prompts_dir: Path = None):
        """
        Initialize the enhancer.
        
        Args:
            prompts_dir: Directory containing scraped prompt JSON files.
                        Defaults to assets/prompts/ (auto-detected)
        """
        self.prompts_dir = prompts_dir or get_prompts_dir()
        self._style_cache: Dict[int, ModelStyle] = {}
    
    def enhance(
        self,
        prompt: str,
        model_id: Optional[int] = None,
        model_path: Optional[Path] = None,
        include_loras: bool = True,
        width: int = 512,
        height: int = 768,
    ) -> EnhancedPrompt:
        """
        Enhance a user prompt using learned model patterns.
        
        Args:
            prompt: User's simple prompt (e.g., "a girl in forest")
            model_id: CivitAI model ID (loads model-specific patterns)
            model_path: Path to model file (extracts ID from filename)
            include_loras: Whether to include commonly used LoRAs
            width: Target image width
            height: Target image height
        
        Returns:
            EnhancedPrompt with optimized prompt and settings
        """
        # Try to detect model ID from path if not provided
        if model_id is None and model_path:
            model_id = self._extract_model_id(model_path)
        
        # Load or get cached style
        style = self._get_style(model_id)
        
        if style:
            return self._enhance_with_style(prompt, style, include_loras, width, height)
        else:
            return self._basic_enhance(prompt, width, height, model_id)
    
    def _extract_model_id(self, model_path: Path) -> Optional[int]:
        """Extract model ID from filename."""
        name = model_path.stem if isinstance(model_path, Path) else str(model_path)
        match = re.search(r'(\d{4,})', name)
        if match:
            return int(match.group(1))
        return None
    
    def _get_style(self, model_id: Optional[int]) -> Optional[ModelStyle]:
        """Get style for a model (loads from cache or analyzes prompts)."""
        if model_id is None:
            return None
        
        if model_id in self._style_cache:
            return self._style_cache[model_id]
        
        prompts_file = self.prompts_dir / f"model_{model_id}_prompts.json"
        
        if not prompts_file.exists():
            return None
        
        try:
            with open(prompts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            prompts = data.get('prompts', []) if isinstance(data, dict) else data
            
            if prompts:
                style = self._analyze_prompts(model_id, prompts)
                self._style_cache[model_id] = style
                return style
        except Exception as e:
            print(f"Error loading prompts for model {model_id}: {e}")
        
        return None
    
    def _analyze_prompts(self, model_id: int, prompts: List[Dict]) -> ModelStyle:
        """Analyze prompts and extract patterns."""
        
        style = ModelStyle(model_id=model_id)
        
        quality_counter = Counter()
        lora_counter = Counter()
        negative_counter = Counter()
        steps_list = []
        cfg_list = []
        samplers = Counter()
        sizes = Counter()
        
        quality_patterns = [
            'masterpiece', 'best quality', 'highly detailed',
            'hyper realistic', '8k', '4k', 'epic composition',
            'cinematic', 'atmospheric', 'sharp focus', 'professional',
            'ultra detailed', 'photorealistic', 'intricate',
        ]
        
        for p in prompts:
            prompt_text = p.get('prompt', '')
            negative_text = p.get('negative_prompt', '')
            
            # Extract LoRAs: <lora:name:weight>
            for lora in re.findall(r'<lora:([^:>]+):[^>]+>', prompt_text):
                lora_counter[lora] += 1
            
            # Extract LyCORIS: <lyco:name:weight>
            for lyco in re.findall(r'<lyco:([^:>]+):[^>]+>', prompt_text):
                lora_counter[f"lyco:{lyco}"] += 1
            
            # Extract quality boosters
            for pattern in quality_patterns:
                if pattern.lower() in prompt_text.lower():
                    quality_counter[pattern] += 1
            
            # Extract negative prompt patterns
            if negative_text:
                for word in negative_text.split(',')[:20]:
                    word = word.strip()
                    if word and len(word) > 2:
                        negative_counter[word] += 1
            
            # Collect settings
            if p.get('steps'):
                steps_list.append(p['steps'])
            if p.get('cfg_scale'):
                cfg_list.append(p['cfg_scale'])
            if p.get('sampler'):
                samplers[p['sampler']] += 1
            if p.get('size'):
                sizes[p['size']] += 1
        
        # Build style from most common patterns
        style.quality_boosters = [k for k, _ in quality_counter.most_common(6)]
        style.common_loras = [k for k, _ in lora_counter.most_common(3)]
        style.negative_prompt = ", ".join(k for k, _ in negative_counter.most_common(15))
        
        # Settings (use mode)
        if steps_list:
            style.steps = int(Counter(steps_list).most_common(1)[0][0])
        if cfg_list:
            style.cfg_scale = float(Counter(cfg_list).most_common(1)[0][0])
        if samplers:
            style.sampler = samplers.most_common(1)[0][0]
        if sizes:
            size_str = str(sizes.most_common(1)[0][0])
            if 'x' in size_str:
                w, h = size_str.split('x')
                style.width = int(w)
                style.height = int(h)
        
        return style
    
    def _enhance_with_style(
        self,
        prompt: str,
        style: ModelStyle,
        include_loras: bool,
        width: int,
        height: int,
    ) -> EnhancedPrompt:
        """Enhance prompt using learned style."""
        
        parts = []
        loras_used = []
        
        # Add quality boosters
        if style.quality_boosters:
            parts.append(", ".join(style.quality_boosters[:5]))
        
        # Add user prompt
        parts.append(prompt)
        
        # Add LoRAs if requested
        if include_loras and style.common_loras:
            for lora in style.common_loras[:2]:
                if not lora.startswith('lyco:'):
                    parts.append(f"<lora:{lora}:0.5>")
                    loras_used.append(lora)
        
        # Combine and clean
        enhanced = ", ".join(parts)
        enhanced = re.sub(r',\s*,', ',', enhanced)
        enhanced = re.sub(r'\s+', ' ', enhanced).strip()
        
        # Use style's size if not overridden
        final_width = width if width != 512 else style.width
        final_height = height if height != 768 else style.height
        
        return EnhancedPrompt(
            prompt=enhanced,
            negative_prompt=style.negative_prompt or "lowres, bad anatomy, worst quality",
            steps=style.steps,
            cfg_scale=style.cfg_scale,
            sampler=style.sampler,
            width=final_width,
            height=final_height,
            loras=loras_used,
            model_id=style.model_id,
        )
    
    def _basic_enhance(
        self,
        prompt: str,
        width: int,
        height: int,
        model_id: Optional[int] = None,
    ) -> EnhancedPrompt:
        """Basic enhancement when no model data is available."""
        
        enhanced = f"masterpiece, best quality, highly detailed, {prompt}"
        
        return EnhancedPrompt(
            prompt=enhanced,
            negative_prompt="lowres, bad anatomy, bad hands, worst quality, low quality, watermark",
            steps=30,
            cfg_scale=7.0,
            sampler="DPM++ 2M Karras",
            width=width,
            height=height,
            model_id=model_id,
        )
    
    def get_available_models(self) -> List[Dict]:
        """Get list of models with scraped prompts."""
        models = []
        if self.prompts_dir.exists():
            for f in self.prompts_dir.glob("model_*.json"):
                match = re.search(r'model_(\d+)', f.name)
                if match:
                    model_id = int(match.group(1))
                    # Try to get prompt count
                    try:
                        with open(f, 'r') as fp:
                            data = json.load(fp)
                        count = len(data.get('prompts', []))
                    except:
                        count = 0
                    
                    models.append({
                        'model_id': model_id,
                        'file': f.name,
                        'prompt_count': count,
                    })
        return models
    
    def get_style_summary(self, model_id: int) -> str:
        """Get a summary of learned style for a model."""
        style = self._get_style(model_id)
        if not style:
            return f"No prompts found for model {model_id}"
        
        return f"""
Model {model_id} Style:
  Quality: {', '.join(style.quality_boosters[:4])}
  LoRAs: {', '.join(style.common_loras[:3]) or 'None'}
  Settings: {style.steps} steps, CFG {style.cfg_scale}, {style.sampler}
  Size: {style.width}x{style.height}
""".strip()


# ============================================================================
# Convenience Functions
# ============================================================================

_enhancer: Optional[PromptEnhancer] = None


def get_enhancer() -> PromptEnhancer:
    """Get or create global enhancer instance."""
    global _enhancer
    if _enhancer is None:
        _enhancer = PromptEnhancer()
    return _enhancer


def enhance_prompt(
    prompt: str,
    model_id: Optional[int] = None,
    **kwargs
) -> EnhancedPrompt:
    """
    Quick function to enhance a prompt.
    
    Args:
        prompt: Your simple prompt
        model_id: CivitAI model ID (optional)
        **kwargs: Additional args (include_loras, width, height)
    
    Returns:
        EnhancedPrompt with optimized prompt and settings
    
    Example:
        result = enhance_prompt("a girl in forest", model_id=46294)
        print(result.prompt)
    """
    return get_enhancer().enhance(prompt, model_id=model_id, **kwargs)


def enhance_for_model(prompt: str, model_path: Path, **kwargs) -> EnhancedPrompt:
    """
    Enhance prompt using model path to detect settings.
    
    Args:
        prompt: Your simple prompt
        model_path: Path to the model file
    
    Returns:
        EnhancedPrompt with optimized prompt and settings
    """
    return get_enhancer().enhance(prompt, model_path=model_path, **kwargs)


def list_available_models() -> List[Dict]:
    """List all models with scraped prompts."""
    return get_enhancer().get_available_models()
