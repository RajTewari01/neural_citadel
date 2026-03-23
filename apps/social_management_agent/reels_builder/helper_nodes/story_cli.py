"""
story_helper.py - Helper module for getting interesting stories like reddit without needing any outside dependency.
===================================================================================================================
"""
from typing import Optional, Tuple, Dict, Literal
import sys
from pathlib import Path
import gc
import json
import sqlite3
import re
import argparse

_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_ROOT))
from configs.paths import LLM_MODELS, STORIES_TITLE_HELPER, STORIES_TITLE_DATABASE

from llama_cpp import Llama
from torch import cuda

# --- PROMPT SETTINGS ---
_MODEL_SETTINGS = {
    'Reddit_story': (
        '[INST] You are a legendary writer on r/NoSleep. '
        'STRICT NEGATIVE CONSTRAINTS: '
        '- DO NOT use headers, section titles, or Roman numerals (e.g., "I. Introduction"). '
        '- DO NOT explain the story structure or add a summary at the end. '
        '- DO NOT use flowery, poetic language. Keep it raw and conversational. '
        '- DO NOT break character. Stay in the first-person perspective at all times. '
        '- DO NOT PUT GENERIC SMALL TITLE. '
        'GUIDE TO FOLLOW: '
        '**IMPORTANT** USE THIS EXACT FORMAT FOR TITLE :[TITLE] FOR STARTING THE TITLE AND [/TITLE] FOR ENDING THE TITLE. '
        '**IMPORTANT** FOLLOW THIS EXACT FORMAT FOR THE TITLE\'S EXAMPLE :[TITLE] My Story. [/TITLE] '
        'CONTEXT (PREVIOUSLY WRITTEN STORIES - AVOID THESE THEMES):\n{history}\n\n'
        'You are a master storyteller with a talent for gripping narratives. '
        'Write a masterpiece first person perspective story with a twist. '
        'Write a compelling short story based on: {user_prompt}. '
        "Start with a strong hook that grabs attention immediately. "
        "Focus on 'show, don't tell' by using visceral sensory details and deep character psychology. "
        "Build tension and drive the plot toward a memorable or twisting conclusion. "
        '[/INST]',
        1.2
    ),
    'Realism_reddit_story': (
        '[INST] You are a regular person posting on r/NoSleep. You are NOT a professional writer. '
        'Your goal is to scare people with a story that feels 100% real.\n\n'
        'STRICT NEGATIVE CONSTRAINTS (DO NOT IGNORE):'
        '- DO NOT use flowery, poetic, or "Lovecraftian" language (e.g., do not use words like "eldritch", "petrichor", "visceral", "crimson").'
        '- DO NOT use headers, section titles, or Roman numerals.'
        '- DO NOT explain the story structure or add a summary at the end.'
        '- DO NOT end the story with "I woke up and it was a dream". The horror must be real.\n\n'
        'FORMATTING GUIDE:'
        '**IMPORTANT** YOU MUST END THE TITLE WITH [/TITLE].'
        'Example: [TITLE] The thing in my basement [/TITLE]'
        '\n\n'
        'CONTEXT (PREVIOUSLY WRITTEN STORIES - AVOID THESE THEMES):\n{history}\n\n'
        'WRITING STYLE:'
        '- Write like a normal Reddit user: Use short sentences. It is okay to be slightly messy.'
        '- Focus on the psychological fear and the uncanny "wrongness".\n\n'
        'TASK: Write a gripping first-person story based on this prompt: {user_prompt}.'
        '[/INST]',
        0.9
    )
}

_ANSII_ESCAPE_SEQUENCE = {
    'cyan': '\033[36m',
    'red': '\033[31m',
    'reset': '\033[0m'
}

class StoryHelper:

    def __init__(self, load_model=True):
        self.llm_path = LLM_MODELS.get('mistral') / 'mistral-7b-instruct-v0.2.Q4_K_M.gguf'
        self.db_path = STORIES_TITLE_DATABASE
        self.db_connection = sqlite3.connect(self.db_path / 'stories.db')
        self.cursor = self.db_connection.cursor()
        self._init_db()
        
        self.llm = None
        if load_model:
            print(f"{_ANSII_ESCAPE_SEQUENCE['cyan']}Loading Model...{_ANSII_ESCAPE_SEQUENCE['reset']}")
            self.llm = Llama(
                model_path=str(self.llm_path),
                n_ctx=3086,
                n_gpu_layers=-1, 
                verbose=False
            )

    def unload(self):
        self.db_connection.close()
        if self.llm:
            del self.llm
            self.llm = None
        gc.collect()
        if cuda.is_available():
            cuda.empty_cache()
    
    def _init_db(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS stories
                            (
                            id TEXT PRIMARY KEY,
                            content TEXT,
                            posted INTEGER DEFAULT 0,
                            generated_output TEXT
                            )
                                ''')
        self.db_connection.commit() 
    
    def sync_json_to_db(self):
        try:
            if not STORIES_TITLE_HELPER.exists(): return None
            with open(STORIES_TITLE_HELPER, 'r', encoding='utf-8', errors='ignore') as infile:
                data = json.load(infile)
            
            count = 0
            for story_id, story_data in data.get('stories', {}).items():
                self.cursor.execute(
                    "INSERT OR IGNORE INTO stories (id, content) VALUES (?, ?)", 
                    (story_id, story_data)
                )
                if self.cursor.rowcount > 0:
                    count += 1
            
            self.db_connection.commit()
            if count > 0:
                print(f"Synced {count} new prompts to database.")
        except Exception as e:
            print(f"Error syncing DB: {e}")
                
    def get_prompt_from_db(self) -> Tuple[Optional[str], Optional[str]]:
        self.cursor.execute("SELECT id, content FROM stories WHERE posted = 0 ORDER BY RANDOM() LIMIT 1")
        result = self.cursor.fetchone()
        if result:
            return result[0], result[1]
        return None, None

    def get_history(self, limit=3) -> str:
        """Fetches the titles of the last few posted stories to avoid repetition."""
        try:
            self.cursor.execute("SELECT content FROM stories WHERE posted = 1 ORDER BY rowid DESC LIMIT ?", (limit,))
            rows = self.cursor.fetchall()
            if not rows:
                return "No previous stories."
            return "\n".join([f"- {row[0]}" for row in rows])
        except Exception:
            return "No history available."

    def mark_as_posted(self, story_id: str, final_output: str):
        if story_id:
            self.cursor.execute("UPDATE stories SET posted = 1, generated_output = ? WHERE id = ?", (final_output, story_id))
            self.db_connection.commit()

    def _parse_story_output(self, raw_text: str, fallback_title: str = "") -> Dict[str, str]:
        """
        Extracts title and body using multiple Regex patterns to catch different AI formats.
        Priorities:
        1. [TITLE] My Title [/TITLE]
        2. [My Title] (at start of text)
        3. Title: My Title (at start of text)
        """
        raw_text = raw_text.strip()
        title = fallback_title.title() if fallback_title else "Untitled Horror"
        story_body = raw_text

        # Pattern 1: Explicit Tags [TITLE] ... [/TITLE]
        match_tags = re.search(r"\[TITLE\]\s*(.*?)\s*\[/TITLE\]", raw_text, re.IGNORECASE | re.DOTALL)
        
        # Pattern 2: Bracketed Title at start [The Haunting of Hill House]
        match_brackets = re.search(r"^\[([^\]]+)\]", raw_text)

        # Pattern 3: "Title:" format (Title: The Ghost)
        match_text_prefix = re.search(r"^Title:\s*(.*)", raw_text, re.IGNORECASE)

        if match_tags:
            title = match_tags.group(1).strip()
            story_body = raw_text.replace(match_tags.group(0), "").strip()
        
        elif match_brackets:
            possible_title = match_brackets.group(1).strip()
            if "INST" not in possible_title.upper():
                title = possible_title
                story_body = raw_text[match_brackets.end():].strip()
        
        elif match_text_prefix:
            title = match_text_prefix.group(1).strip()
            story_body = raw_text[match_text_prefix.end():].strip()

        # CLEANUP 1: Remove trailing period from title if present
        if title.endswith('.'):
            title = title[:-1]

        # CLEANUP 2: Normalize Story Whitespace
        story_body = re.sub(r'\s+', ' ', story_body).strip()

        return {
            "title": title,
            "story": story_body
        }

    def generate_story(self, prompt: str = None, full_prompt: Optional[str] = None, 
                       model_character: Optional[Literal['Realism_reddit_story','Reddit_story']] = None,
                       history_limit: int = 3) -> Optional[Dict[str, str]]:
        if not self.llm:
            print("Model not loaded! Initialize with load_model=True")
            return None
        
        # 1. Select Model Persona
        if model_character is None:
            PROMPT_TEMPLATE, TEMP = _MODEL_SETTINGS.get('Realism_reddit_story')
        else:
            PROMPT_TEMPLATE, TEMP = _MODEL_SETTINGS.get(model_character, _MODEL_SETTINGS['Realism_reddit_story'])

        story_id = None 

        # 2. Determine Prompt Source (DB vs Manual)
        if prompt is None and full_prompt is None:
            self.sync_json_to_db()
            story_id, db_prompt = self.get_prompt_from_db()
            if not db_prompt:
                print(f"{_ANSII_ESCAPE_SEQUENCE['red']}No new stories in Database!{_ANSII_ESCAPE_SEQUENCE['reset']}")
                return None
            prompt = db_prompt
        
        # 3. Inject History
        history_text = self.get_history(limit=history_limit)
        
        # 4. Format the final prompt
        if full_prompt:
            FULL_PROMPT = full_prompt
        else:
            FULL_PROMPT = PROMPT_TEMPLATE.format(user_prompt=prompt, history=history_text)

        try:
            stream = self.llm(
                FULL_PROMPT,
                temperature=TEMP,
                max_tokens=1500,
                stream=True,
                stop=["[/INST]"], 
                echo=False
            )

            raw_text = ''
            sys.stdout.write(_ANSII_ESCAPE_SEQUENCE['cyan'])
            for word in stream:
                text = word['choices'][0]['text']
                sys.stdout.write(text)
                sys.stdout.flush()
                raw_text += text
            sys.stdout.write(_ANSII_ESCAPE_SEQUENCE['reset'])
            print("\n")
            
            # Parse the raw text into JSON structure, passing prompt as fallback title
            final_json = self._parse_story_output(raw_text, fallback_title=prompt)

            # Only mark as posted if it came from the DB
            if story_id:
                self.mark_as_posted(story_id, raw_text)
                
            return final_json

        except Exception as e:
            print(f"Error in generate_story: {e}")
            return None

if __name__ == '__main__':
    EPILOG = """
==============================================================================
STORY HELPER CLI - AI Horror Story Generator
==============================================================================

DESCRIPTION:
  This tool generates scary Reddit-style stories using a local Mistral 7B LLM.
  It manages a SQLite database to ensure stories are not repeated and maintains
  a history context to keep the AI from writing the same themes twice.

EXAMPLES:

  1. Automatic Generation (Recommended):
     This pulls a random prompt from your 'stories.json', generates a story,
     saves the result, and marks the prompt as used.
     
     $ python story_helper.py --generate

  2. Manual Prompt:
     Generates a story based on your specific idea. Does not save to DB history.
     
     $ python story_helper.py --generate --prompt "I found a door in my floor"

  3. Specific Persona:
     Use the 'Reddit_story' persona (more dramatic) instead of the default 'Realism'.
     
     $ python story_helper.py --generate --model_character Reddit_story

  4. Adjust History Context:
     Look at the last 5 stories to avoid repetition (default is 3).
     
     $ python story_helper.py --generate --history 5

  5. Check Model Info:
     
     $ python story_helper.py --model

OUTPUT FORMAT:
  The tool returns a JSON object printed to stdout:
  {
      "title": "The extracted title",
      "story": "The body of the story..."
  }
==============================================================================
    """
    
    parser = argparse.ArgumentParser(
        description="Story Helper CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EPILOG
    )
    parser.add_argument('--generate', action='store_true', help='Generate a new story')
    parser.add_argument('--prompt', type=str, default=None, help='Manual prompt override')
    parser.add_argument('--model', action='store_true', help='Show Model Info')
    parser.add_argument('--full_prompt', type=str, default=None, help='Full prompt override (advanced)')
    parser.add_argument('--model_character', type=str, choices=['Realism_reddit_story', 'Reddit_story'], default=None, help='Choose the writing persona')
    parser.add_argument('--history', type=int, default=3, help='Number of past stories to include in context (default: 3)')
    parser.add_argument('--unload', action='store_true', help='Unload model after use')
    
    args = parser.parse_args()

    if args.model:
        MODEL_INFO = (
            'HUGGINGFACE_REPO_ID = TheBloke/Mistral-7B-Instruct-v0.2-GGUF',
            'ALTERNATIVE_HUGGINGFACE_REPO_ID = MaziyarPanahi/Mistral-7B-Instruct-v0.2-GGUF',
            'ORIGINAL_MODEL_REPO_ID = mistralai/Mistral-7B-Instruct-v0.2',
            'FILENAME = mistral-7b-instruct-v0.2.Q4_K_M.gguf',
            'QUANTIZATION_METHOD = GGUF (GPT-Generated Unified Format)',
            'QUANTIZED_VERSION = Q4_K_M (4-bit, Medium, Balanced Quality/Speed)',
            'TOTAL_PARAMETERS = 7.24 Billion',
            'FILE_SIZE = ~4.37 GB',
            'RAM_REQUIRED = ~6.5 GB (minimum)',
            'CONTEXT_WINDOW = 3086 tokens',
            'CREATED_BY = Mistral AI',
            'QUANTIZED_BY = TheBloke (Tom Jobbins)',
            'LICENSE = Apache 2.0',
            'ARCHITECTURE = Llama-based (Sliding Window Attention)',
            'USE_CASE = Instruction Following, Creative Writing, Chatbots',
            'RELEASE_DATE = December 2023'
        )
        for info in MODEL_INFO:
            print(info)
            
        if not args.generate:
            sys.exit(0)

    if args.generate:
        helper = StoryHelper(load_model=True)
        
        result = helper.generate_story(
            prompt=args.prompt,
            full_prompt=args.full_prompt,
            model_character=args.model_character,
            history_limit=args.history
        )
        
        if result:
            print("\n[FINAL]")
            print(json.dumps(result, indent=4))
        
        helper.unload()
    
    if args.unload:
        engine=StoryHelper(load_model=False)
        engine.unload()