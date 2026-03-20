from pathlib import Path
from sys import path


# ... (Your path insertion logic is fine here) ...
__ROOT = Path(__file__).resolve().parents[4]
if str(__ROOT) not in path:
    path.insert(0, str(__ROOT))

from apps.social_automation_agent.reels_creator.resource_gatherer.pipeline_types import PipelineConfigs
from typing import List, Optional, Dict, Literal, Tuple, Union



# --- Main Factory Function ---
def get_unsplash_config(
    # PipelineConfigs dataclass fields
    
    search_term: str,
    download_type: Literal['image', 'video'] = 'image',
    debug: bool = False,
    cleanup_photos: bool = False,
    item_count: int = 15,
    download_method: Literal['fast', 'safe'] = 'fast',
    output_dir: Optional[Union[str, Path]] = None,
    request_limit: int = 1200,
    safe_search : Literal['off', 'modest'] ='off'

) -> PipelineConfigs:
    """
    Factory to create a sanitized PipelineConfigs object for DuckDuckGo.
    """
  

    # 1. Return the Config Object
    return PipelineConfigs(
        safe_search = safe_search,
        search_term=search_term,
        download_type=download_type,
        debug=debug,
        cleanup_photos=cleanup_photos,
        item_count=item_count,
        download_method=download_method,
        output_dir=output_dir,
        request_limit=request_limit
    )