"""
pipeline_types.py 
==============================================================
Configuration structures for the media processing pipeline.
"""

from dataclasses import dataclass, field
from typing import Literal, Optional, Union
from pathlib import Path
import json
import sys
import random

__ROOT__ = Path(__file__).resolve().parents[5]

@dataclass
class PipelineConfig:
    """
    Configuration dataclass for the downloading pipeline.
    
    This class handles the setup of search parameters, directory management,
    and dynamic defaults for item counts based on media type.
    """

    # --- 1. REQUIRED FIELDS (Must be defined first) ---
    safe_search: Literal['off', 'modest'] ='off'

    # --- 2. OPTIONAL FIELDS (With defaults) ---
    search_term: Optional[str] = None
    download_type: Literal['image', 'video'] = 'image'
    debug: bool = True
    item_count: Optional[int] = None
    download_method: Literal['fast', 'safe'] = 'fast'
    request_limit: int = 50  # API rate limit buffer per day
    output_dir: Optional[Union[Path, str]] = None 

    def __post_init__(self):
        """
        Post-initialization processing:
        1. Converts output_dir to Path and creates it if missing.
        2. Loads a random search term if none is provided.
        3. Sets default item_count based on download_type (Video vs Image).
        """
        
        # --- Handle Output Directory ---
        if self.output_dir is not None:
            # Ensure it is a Path object
            self.output_dir = Path(self.output_dir)
            # Create directory if it doesn't exist
            if not self.output_dir.exists():
                self.output_dir.mkdir(parents=True, exist_ok=True)

        # --- Handle Random Search Term From The Configs ---
        if self.search_term is None:
            # Add to system path to allow imports (must be string)
            self.search_term = self._fetch_random_search_term()
            
            
        # --- Handle User Search Term From The Base And Sanitize Them ---
        if self.search_term:
            self.search_term = self._sanitize_word(self.search_term)
        

        # --- Handle Dynamic Item Count ---
        if self.item_count is None:
            if self.download_type == 'image':
                self.item_count = 15
            elif self.download_type == 'video':
                self.item_count = 5
    
    def _fetch_random_search_term(self) -> str :
        """
        Fetch a random search term from the JSON file.
        """
        # Add to system path to allow imports (must be string)
        try:
            if str(__ROOT__) not in sys.path:
                sys.path.insert(0, str(__ROOT__))
                
                # Import path config
                from configs.paths import IDEAS_FOR_VIDEOS_AND_IMAGES_SEARCH_TERM
        except Exception as e:
                if self.debug:
                    print(f"Error loading search terms: {e}")
                    import traceback
                    print(traceback.format_exc())
                return 'lamborghini'
        
        else:
            # Load search terms from JSON
            try:
                with open(IDEAS_FOR_VIDEOS_AND_IMAGES_SEARCH_TERM, 'r') as infile:
                    data = json.load(infile) 
                    needed_data = data.get('search_term',[])
                    # we provide a list so if the configs.json is missing then it will return a empty list not the defualt one.
                    if not needed_data :
                        print("Fallback to default search term !! JSON NOT FOUND !")
                        return 'lamborghini'
                search_term = random.choice(needed_data)
                return search_term

            except Exception as e:
                if self.debug:
                    print(f"Error loading search terms: {e}")
                search_term = 'lamborghini'
                return search_term
        
    def _sanitize_word(self, term : str) ->str:
        """
        Local sanitizer or lazy wrapper around BaseGatherer.
        Prevents global instantiation of BaseGatherer.

        Features :
            >>> 1. Remove Emojis.
            >>> 2. Remove Special Characters.
            >>> 3. Remove Extra Spaces.
            >>> 4. Convert to Lowercase.
        """
        # Lazy import only when needed
        if str(__ROOT__) not in sys.path:
            sys.path.insert(0, str(__ROOT__))
            
        from apps.social_automation_agent.reels_creator.resource_gatherer.base import BaseGatherer
        _INITIALIZE_SANITIZING = BaseGatherer()
        return _INITIALIZE_SANITIZING.sanitize_search_term(term=term)


        
        