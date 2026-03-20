"""
 __init__.py 
 >>> initialize root directory dynamically.
 """

from pathlib import Path
from sys import path

_ROOT = Path(__file__).resolve().parents[4]
if str(_ROOT) not in path:
    path.insert(0, str(_ROOT))


