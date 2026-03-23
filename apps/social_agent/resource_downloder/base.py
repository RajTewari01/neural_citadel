"""
base.py - A class for the other class to inherit from.
------------------------------------------------------
Features :
    >>> Helps to santize search by stripping off emojis and urls by regex 
    >>> Gives the user various user agent for their request module.
   
"""

import unicodedata
import re 
from pathlib import Path
from typing import (
    List, Optional, Tuple, Union
)

class BaseGatherer:
    
    @staticmethod
    def sanitize_search_term(term: str) -> str:
        if not term:
            return ""        
        # 1. Normalize Unicode
        term = unicodedata.normalize('NFKD', term)
        # 2. ASCII Encode (Strip Emojis)
        term = term.encode('ascii', 'ignore').decode('utf-8')
        # 3. Replace separators with spaces
        term = re.sub(r'[-_.]', ' ', term)
        # 4. Remove non-alphanumeric
        term = re.sub(r'[^a-zA-Z0-9\s]', '', term)
        # 5. Collapse spaces
        return re.sub(r'\s+', ' ', term).strip().lower()