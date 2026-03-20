
from pathlib import Path
from sys import path

_ROOT = Path(__file__).resolve().parents[4]
if str(_ROOT) not in path:
    path.insert(0, str(_ROOT))

from apps.social_automation_agent.reels_creator.agents.base import ConfigPlatform
