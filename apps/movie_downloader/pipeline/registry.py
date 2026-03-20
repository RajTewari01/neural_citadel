"""
Pipeline Registry
==================

Central registry for download pipelines.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable, Tuple
import logging

logger = logging.getLogger(__name__)

# Global registry
_PIPELINE_REGISTRY: Dict[str, Dict] = {}


@dataclass
class DownloadConfig:
    """Configuration for a download operation."""
    pipeline: str
    source: str
    output_dir: Optional[str] = None
    quality: str = "best"
    debug_mode: bool = False
    auto_scan: bool = True
    extra_options: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.extra_options = self.extra_options or {}


def register_pipeline(
    name: str,
    keywords: List[str] = None,
    description: str = "",
    category: str = "general",
    supported_sites: List[str] = None
):
    """Decorator to register a pipeline configuration function."""
    def decorator(func: Callable):
        _PIPELINE_REGISTRY[name] = {
            'name': name,
            'keywords': keywords or [],
            'description': description,
            'category': category,
            'supported_sites': supported_sites or [],
            'config_func': func
        }
        return func
    return decorator


def get_all_pipelines() -> Dict[str, Dict]:
    """Get all registered pipelines."""
    return _PIPELINE_REGISTRY.copy()


def get_pipeline_names() -> List[str]:
    """Get list of pipeline names."""
    return list(_PIPELINE_REGISTRY.keys())


def get_pipeline(name: str) -> Optional[Dict]:
    """Get pipeline by name."""
    return _PIPELINE_REGISTRY.get(name)


def find_pipeline_by_keyword(keyword: str) -> Tuple[Optional[str], Optional[Dict]]:
    """Find pipeline matching a keyword."""
    keyword_lower = keyword.lower()
    
    # Check for magnet links
    if keyword_lower.startswith('magnet:'):
        return 'torrent', get_pipeline('torrent')
    
    # Check URL patterns
    for name, info in _PIPELINE_REGISTRY.items():
        for site in info.get('supported_sites', []):
            if site in keyword_lower:
                return name, info
        for kw in info.get('keywords', []):
            if kw in keyword_lower:
                return name, info
    
    return None, None


def format_help_text() -> str:
    """Format help text for all pipelines."""
    lines = ["Available Pipelines:", "=" * 40]
    for name, info in _PIPELINE_REGISTRY.items():
        lines.append(f"\n{name}:")
        lines.append(f"  {info.get('description', 'No description')}")
        if info.get('supported_sites'):
            lines.append(f"  Sites: {', '.join(info['supported_sites'][:5])}")
    return '\n'.join(lines)


def discover_pipelines():
    """Trigger pipeline discovery by importing modules."""
    pass  # Pipelines register themselves on import
