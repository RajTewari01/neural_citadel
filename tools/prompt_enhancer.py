"""
Smart Prompt Enhancer - Learns from Model-Specific Prompts
==========================================================

Instead of hardcoded presets, this analyzes scraped prompts from specific
models and LEARNS what keywords, LoRAs, quality boosters, and settings
work best for each model.

Features:
- Analyzes model-specific prompt patterns
- Extracts common quality boosters, LoRAs, trigger words
- Learns optimal settings (steps, CFG, sampler) per model
- Creates enhanced prompts that match the model's style

Usage:
    from tools.prompt_enhancer import ModelPromptEnhancer
    
    enhancer = ModelPromptEnhancer(model_id=46294)  # Load model's prompts
    result = enhancer.enhance("a girl in forest")
"""

import json
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Set, Tuple
from dataclasses import dataclass, field
from collections import Counter


@dataclass
class ModelStyle:
    """Learned style from a model's prompts."""
    model_id: int
    model_name: str = ""
    
    # Learned patterns
    quality_boosters: List[str] = field(default_factory=list)
    common_loras: List[str] = field(default_factory=list)
    trigger_words: List[str] = field(default_factory=list)
    negative_prompt: str = ""
    
    # Optimal settings (mode/median from prompts)
    steps: int = 30
    cfg_scale: float = 7.0
    sampler: str = "DPM++ 2M Karras"
    common_sizes: List[Tuple[int, int]] = field(default_factory=list)


@dataclass 
class EnhancedPrompt:
    """Enhanced prompt with all settings."""
    prompt: str
    negative_prompt: str
    steps: int
    cfg_scale: float
    sampler: str
    width: int = 512
    height: int = 768
    loras_used: List[str] = field(default_factory=list)


class ModelPromptEnhancer:
    """
    Learns prompt patterns from a specific model's scraped data.
    """
    
    def __init__(self, model_id: int = None, prompts_file: Path = None):
        """
        Initialize with a model ID or direct prompts file.
        
        Args:
            model_id: CivitAI model ID (will look for model_{id}_prompts.json)
            prompts_file: Direct path to prompts JSON file
        """
        self.prompts_dir = Path(__file__).parent.parent / "assets" / "prompts"
        self.prompts: List[Dict] = []
        self.style: Optional[ModelStyle] = None
        
        if prompts_file:
            self._load_file(prompts_file)
        elif model_id:
            self._load_model(model_id)
        else:
            # Load all prompts
            self._load_all()
        
        # Analyze and learn
        if self.prompts:
            self.style = self._analyze_prompts()
    
    def _load_file(self, path: Path):
        """Load prompts from a specific file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict):
            self.prompts = data.get('prompts', [])
            self.model_id = data.get('model_id', 0)
        else:
            self.prompts = data
            self.model_id = 0
        
        print(f"Loaded {len(self.prompts)} prompts from {path.name}")
    
    def _load_model(self, model_id: int):
        """Load prompts for a specific model ID."""
        self.model_id = model_id
        path = self.prompts_dir / f"model_{model_id}_prompts.json"
        
        if path.exists():
            self._load_file(path)
        else:
            print(f"No prompts found for model {model_id}")
            print(f"Run: python api_scraper.py https://civitai.com/models/{model_id}")
    
    def _load_all(self):
        """Load all available prompts."""
        self.model_id = 0
        
        if not self.prompts_dir.exists():
            return
        
        for json_file in self.prompts_dir.glob("model_*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, dict) and 'prompts' in data:
                    self.prompts.extend(data['prompts'])
            except Exception as e:
                print(f"Error loading {json_file}: {e}")
        
        print(f"Loaded {len(self.prompts)} total prompts")
    
    def _analyze_prompts(self) -> ModelStyle:
        """Analyze prompts and extract patterns."""
        
        style = ModelStyle(model_id=self.model_id)
        
        # Collect data
        all_quality = Counter()
        all_loras = Counter()
        all_triggers = Counter()
        all_negatives = Counter()
        steps_list = []
        cfg_list = []
        samplers = Counter()
        sizes = Counter()
        
        for p in self.prompts:
            prompt = p.get('prompt', '')
            negative = p.get('negative_prompt', '')
            
            # Extract LoRAs: <lora:name:weight>
            loras = re.findall(r'<lora:([^:>]+):[^>]+>', prompt)
            for lora in loras:
                all_loras[lora] += 1
            
            # Extract LyCORIS: <lyco:name:weight>
            lycos = re.findall(r'<lyco:([^:>]+):[^>]+>', prompt)
            for lyco in lycos:
                all_loras[f"lyco:{lyco}"] += 1
            
            # Extract quality boosters (common patterns)
            quality_patterns = [
                r'masterpiece', r'best quality', r'highly detailed',
                r'hyper realistic', r'8k', r'4k', r'hd',
                r'epic composition', r'cinematic', r'atmospheric',
                r'sharp focus', r'professional', r'ultra detailed',
                r'photorealistic', r'intricate', r'detailed',
            ]
            for pattern in quality_patterns:
                if re.search(pattern, prompt, re.IGNORECASE):
                    all_quality[pattern] += 1
            
            # Extract trigger words (capitalized or special format)
            # Words that appear frequently and aren't common English
            words = re.findall(r'\b([A-Z][a-z]+[A-Z]\w*|\b\w+style\b)\b', prompt)
            for word in words:
                all_triggers[word] += 1
            
            # Negative prompt patterns
            if negative:
                neg_words = [w.strip() for w in negative.split(',')]
                for w in neg_words[:10]:  # First 10 are usually important
                    if w and len(w) > 2:
                        all_negatives[w] += 1
            
            # Settings
            if p.get('steps'):
                steps_list.append(p['steps'])
            if p.get('cfg_scale'):
                cfg_list.append(p['cfg_scale'])
            if p.get('sampler'):
                samplers[p['sampler']] += 1
            if p.get('size'):
                sizes[p['size']] += 1
        
        # Build style from most common patterns
        style.quality_boosters = [k for k, v in all_quality.most_common(8)]
        style.common_loras = [k for k, v in all_loras.most_common(5)]
        style.trigger_words = [k for k, v in all_triggers.most_common(3)]
        
        # Build negative prompt from most common negative words
        common_negatives = [k for k, v in all_negatives.most_common(20)]
        style.negative_prompt = ", ".join(common_negatives)
        
        # Settings (use mode/median)
        if steps_list:
            style.steps = int(Counter(steps_list).most_common(1)[0][0])
        if cfg_list:
            style.cfg_scale = Counter(cfg_list).most_common(1)[0][0]
        if samplers:
            style.sampler = samplers.most_common(1)[0][0]
        if sizes:
            # Parse "1024x1536" format
            size_str = sizes.most_common(1)[0][0]
            if 'x' in str(size_str):
                w, h = size_str.split('x')
                style.common_sizes = [(int(w), int(h))]
        
        return style
    
    def get_style_summary(self) -> str:
        """Get a human-readable summary of learned style."""
        if not self.style:
            return "No style learned yet"
        
        s = self.style
        lines = [
            f"=== Model {s.model_id} Style ===",
            f"Quality boosters: {', '.join(s.quality_boosters[:5])}",
            f"Common LoRAs: {', '.join(s.common_loras[:3]) if s.common_loras else 'None'}",
            f"Trigger words: {', '.join(s.trigger_words) if s.trigger_words else 'None'}",
            f"Best settings: {s.steps} steps, CFG {s.cfg_scale}, {s.sampler}",
            f"Common sizes: {s.common_sizes[0] if s.common_sizes else '512x768'}",
        ]
        return "\n".join(lines)
    
    def enhance(
        self,
        prompt: str,
        include_loras: bool = True,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> EnhancedPrompt:
        """
        Enhance a prompt using learned model style.
        
        Args:
            prompt: Your simple prompt
            include_loras: Whether to include commonly used LoRAs
            width/height: Override size (uses model's common size if not specified)
        
        Returns:
            EnhancedPrompt with all settings
        """
        if not self.style:
            # Fallback to basic enhancement
            return self._basic_enhance(prompt, width, height)
        
        s = self.style
        parts = []
        loras_used = []
        
        # 1. Add quality boosters
        if s.quality_boosters:
            parts.append(", ".join(s.quality_boosters[:5]))
        
        # 2. Add user prompt
        parts.append(prompt)
        
        # 3. Add trigger words if relevant
        if s.trigger_words:
            parts.extend(s.trigger_words[:2])
        
        # 4. Add common LoRAs (optional)
        if include_loras and s.common_loras:
            for lora in s.common_loras[:2]:
                if not lora.startswith('lyco:'):
                    parts.append(f"<lora:{lora}:0.5>")
                    loras_used.append(lora)
        
        # Combine
        enhanced = ", ".join(parts)
        
        # Clean up
        enhanced = re.sub(r',\s*,', ',', enhanced)
        enhanced = re.sub(r'\s+', ' ', enhanced).strip()
        
        # Determine size
        if width and height:
            w, h = width, height
        elif s.common_sizes:
            w, h = s.common_sizes[0]
        else:
            w, h = 512, 768
        
        return EnhancedPrompt(
            prompt=enhanced,
            negative_prompt=s.negative_prompt or "lowres, bad anatomy, worst quality",
            steps=s.steps,
            cfg_scale=s.cfg_scale,
            sampler=s.sampler,
            width=w,
            height=h,
            loras_used=loras_used,
        )
    
    def _basic_enhance(self, prompt: str, width: int, height: int) -> EnhancedPrompt:
        """Basic enhancement when no model style is loaded."""
        enhanced = f"masterpiece, best quality, highly detailed, {prompt}"
        
        return EnhancedPrompt(
            prompt=enhanced,
            negative_prompt="lowres, bad anatomy, bad hands, worst quality, low quality",
            steps=30,
            cfg_scale=7.0,
            sampler="DPM++ 2M Karras",
            width=width or 512,
            height=height or 768,
        )
    
    def find_similar(self, prompt: str, limit: int = 3) -> List[Dict]:
        """Find similar prompts from the database."""
        query_words = set(prompt.lower().split())
        scored = []
        
        for p in self.prompts:
            prompt_text = p.get('prompt', '').lower()
            prompt_words = set(re.findall(r'\w+', prompt_text))
            matches = len(query_words & prompt_words)
            
            if matches > 0:
                scored.append((matches, p))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in scored[:limit]]


# ============================================================================
# Convenience function
# ============================================================================

def enhance_for_model(prompt: str, model_id: int, **kwargs) -> EnhancedPrompt:
    """Quick enhance for a specific model."""
    enhancer = ModelPromptEnhancer(model_id=model_id)
    return enhancer.enhance(prompt, **kwargs)


# ============================================================================
# CLI
# ============================================================================

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Smart Prompt Enhancer - Learns from model-specific prompts")
        print("\nUsage:")
        print("  python prompt_enhancer.py <prompt> [model_id]")
        print("\nExamples:")
        print('  python prompt_enhancer.py "a girl in forest"')
        print('  python prompt_enhancer.py "ocean landscape" 46294')
        print("\nAvailable models:")
        
        prompts_dir = Path(__file__).parent.parent / "assets" / "prompts"
        if prompts_dir.exists():
            for f in prompts_dir.glob("model_*.json"):
                model_id = re.search(r'model_(\d+)', f.name)
                if model_id:
                    print(f"  - Model {model_id.group(1)}: {f.name}")
        return
    
    prompt = sys.argv[1]
    model_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    print(f"\nOriginal prompt: {prompt}")
    print(f"Model ID: {model_id or 'All models'}")
    print("-" * 60)
    
    enhancer = ModelPromptEnhancer(model_id=model_id)
    
    if enhancer.style:
        print("\n" + enhancer.get_style_summary())
        print("-" * 60)
    
    result = enhancer.enhance(prompt)
    
    print(f"\n=== ENHANCED PROMPT ===")
    print(result.prompt)
    print(f"\n=== NEGATIVE PROMPT ===")
    print(result.negative_prompt)
    print(f"\n=== RECOMMENDED SETTINGS ===")
    print(f"Steps: {result.steps}")
    print(f"CFG: {result.cfg_scale}")
    print(f"Sampler: {result.sampler}")
    print(f"Size: {result.width}x{result.height}")
    if result.loras_used:
        print(f"LoRAs: {', '.join(result.loras_used)}")
    
    # Show similar prompts
    similar = enhancer.find_similar(prompt, limit=2)
    if similar:
        print(f"\n=== SIMILAR PROMPTS FROM DATABASE ===")
        for i, p in enumerate(similar, 1):
            print(f"\n{i}. {p['prompt'][:100]}...")
            print(f"   Settings: {p.get('steps')} steps, CFG {p.get('cfg_scale')}")


if __name__ == "__main__":
    main()
