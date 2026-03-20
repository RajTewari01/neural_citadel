# LLM Agent Package
from pathlib import Path
import sys

# Add project root to path
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
