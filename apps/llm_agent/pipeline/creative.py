"""
Creative Writing Pipeline
=========================

Specialized pipeline for storytelling, roleplay, and creative content.
Includes standard creative writing and specialized erotic/uncensored modes.
"""

from typing import Union, Generator
from apps.llm_agent.engine import LLMEngine

# Default to the uncensored model for all creative tasks to avoid refusals
DEFAULT_MODEL = "nsfw_story" 

STORY_SYSTEM_PROMPT = (
    "You are a master storyteller with a talent for gripping narratives. "
    "Start with a strong hook that grabs attention immediately. "
    "Focus on 'show, don't tell' by using visceral sensory details and deep character psychology. "
    "Build tension and drive the plot toward a memorable or twisting conclusion."
)

POEM_SYSTEM_PROMPT = (
    "You are a visionary poet known for weaving complex emotions into vivid imagery. "
    "Use original metaphors, sensory details, and rhythmic elegance. "
    "Do not just describe the subject; capture its hidden essence and evoke deep feeling in the reader."
)

EROTIC_SYSTEM_PROMPT = (
    "You are an erotic fiction engine designed for extreme realism. "
    "RULES: "
    "1. NO euphemisms. Use explicit, anatomical, and vulgar terminology "
    "(e.g., use 'cock', 'pussy', 'tits', 'cum', 'dildo', 'sextoys', 'strapon', "
    "'chastity cage', 'clit', 'clitty', 'breeding', 'throat', 'anal', 'creampie', 'mess', etc.). "
    "2. Focus 80% of the text on physical sensations, friction, wetness, and heat. "
    "3. Be direct. Do not write about 'emotions' or 'longing'—write about the physical act. "
    "4. Pacing must be slow and focused on the sexual mechanics. "
    "5. This is a private, adult-only context. Do not hold back. "
    "6. Focus 90% on physical sensations: friction, fluids, temperature, and raw stimulation. "
    "7. The tone must be lewd, desperate, and visceral. No 'fading to black'. "
    "8. Write in a slow, indulgent pace, describing every physical action in detail. "
    "9. Write the most exotic, explicit, erotic story as much as possible."
)


def generate_story(
    prompt: str,
    model: str = DEFAULT_MODEL,
    mode: str = "story",
    stream: bool = True,
    **kwargs
) -> Union[str, Generator[str, None, None]]:
    """
    Generate creative content.
    
    Args:
        prompt: User prompt
        model: Model to use
        mode: 'story', 'poem', or 'erotic'
        stream: Stream output
    """
    
    # Select System Prompt
    if mode == "erotic":
        sys_prompt = EROTIC_SYSTEM_PROMPT
        # Erotic mode typically benefits from high temp and specific model settings
        kwargs.setdefault("temperature", 0.9)
        kwargs.setdefault("top_p", 0.95)
        
    elif mode == "poem":
        sys_prompt = POEM_SYSTEM_PROMPT
        kwargs.setdefault("temperature", 0.9)
        
    else: # default story
        sys_prompt = STORY_SYSTEM_PROMPT
        kwargs.setdefault("temperature", 1.0)

    # Allow manual override
    sys_prompt = kwargs.pop("system_prompt", sys_prompt)
    
    engine = LLMEngine(model, **kwargs)
    
    output_kwargs = dict(
        prompt=prompt,
        system_prompt=sys_prompt,
        max_tokens=kwargs.get("max_tokens", 2048),
        temperature=kwargs.get("temperature", 0.85),
    )
    
    if stream:
        return engine.stream(**output_kwargs)
    else:
        return engine.generate(**output_kwargs)
