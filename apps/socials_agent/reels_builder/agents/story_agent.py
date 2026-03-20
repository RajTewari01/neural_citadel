"""
Story Agent - Automated voice generation pipeline.
==================================================

Features:
    - Local/APIs integration
    - AI-generated stories
    - Customizable personas, styles, and tones
    - Multi-platform export
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from apps.socials_agent.reels_builder.agents.base import ConfigPlatform
from typing import Optional,Literal,List,Union,Dict,Tuple
import subprocess
import json
import re

class StoryTellerAgent:
    def __init__(self):
        self._ROOT = Path(__file__).resolve().parents[4]
        self._VENV = ConfigPlatform.config_venv("coreagentvenv")
        self._SCRIPTS = self._ROOT / 'apps/social_automation_agent/reels_creator/helper_workers/offline_story_helper.py'
    
    def generate_story_locally(
        self,
        prompt: Optional[str] = None,
        full_prompt: Optional[str] = None,
        personas: Optional[Literal['Reddit_story','Realism_reddit_story']] = 'Reddit_story',
        append_history: int = 0,
        appear_cli: bool = False 
        ) -> Tuple[Optional[str], Optional[str]]:

        if not self._VENV.exists(): raise FileNotFoundError("Cannot find the venv file path.")
        if not self._SCRIPTS.exists(): raise FileNotFoundError("Cannot find the helper/bridge file path.")

        command = [
            str(self._VENV),
            str(self._SCRIPTS),
            '--generate',
            '--history', str(append_history)
        ]

        if full_prompt is not None and prompt is not None:
            command.extend(['--full_prompt', full_prompt])
        if full_prompt is not None and prompt is None:
            command.extend(['--full_prompt', full_prompt])
        if personas is not None:
            command.extend(['--model_character', personas])
        if prompt is not None and full_prompt is None:
            command.extend(['--prompt', prompt])
        command.append('--unload')

        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                bufsize=1
            )

            captured_output = []
            
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    # <--- CHECK ADDED HERE
                    if appear_cli:
                        print(line, end='', flush=True)
                    captured_output.append(line)
            
            full_stdout = "".join(captured_output)
            
            messy_lines = full_stdout.strip().split('[FINAL]')
            if len(messy_lines) < 2:
                return None
            else:
                sanitize_output = messy_lines[-1]
                if isinstance(sanitize_output, str):
                    sanitize_output = json.loads(sanitize_output)
                
                unsanitize_title = sanitize_output.get('title')
                unsanitize_story = sanitize_output.get('story')
                title = None
                story = None
                if unsanitize_title is not None:    
                    title = re.sub(r'[^a-zA-Z0-9\s.,!?;:"\'\-]', '', unsanitize_title)
                    title = re.sub(r'\s+', ' ', title).strip()
                
                if unsanitize_story is not None:
                    story = unsanitize_story.split("[TITLE]")[0] if "[TITLE]" in unsanitize_story else unsanitize_story
                    story = re.sub(r'[^a-zA-Z0-9\s.,!?;:"\'\-]', '', story)
                    story = re.sub(r'\s+', ' ', story).strip()

                return (title, story)

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return None
        
    
if __name__ == "__main__":
    agent = StoryTellerAgent()
    print(agent.generate_story_locally(prompt="A wild divorce reddit story...", append_history=1, appear_cli=True))