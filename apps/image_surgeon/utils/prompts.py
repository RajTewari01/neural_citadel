"""
Smart Background Prompts Library
================================
Match user input (keywords, vibe) to optimized background prompts for SD inpainting.
"""

import re
from typing import List, Dict, Tuple, Optional

# Categorized Background Prompts
# Each entry: (keywords_list, optimized_prompt)
BACKGROUND_LIBRARY = {
    "nature": [
        (["nature", "forest", "green", "trees", "calm"], 
         "lush green forest background, sun rays filtering through trees, detailed foliage, cinematic lighting, 8k, masterpiece, tranquil atmosphere"),
        (["beach", "ocean", "sea", "sand", "summer", "vacation"], 
         "beautiful tropical beach background, turquoise water, white sand, sunny sky, palm trees in distance, cinematic lighting, 8k"),
        (["mountain", "snow", "winter", "peaks", "cold"], 
         "majestic snowy mountain peaks background, winter landscape, clear blue sky, sharp details, photographic quality, 8k"),
        (["garden", "flowers", "park", "blooming"], 
         "beautiful botanical garden background, blooming flowers, soft sunlight, bokeh depth of field, vibrant colors, detailed"),
        (["desert", "sand dunes", "dry", "sunset"], 
         "golden desert sand dunes background, warm sunset lighting, vast landscape, cinematic, detailed"),
    ],
    
    "urban": [
        (["city", "street", "urban", "downtown", "busy"], 
         "bustling city street background, modern architecture, soft bokeh city lights, cinematic urban atmosphere, photorealistic"),
        (["cafe", "coffee shop", "interior", "cozy"], 
         "cozy cafe interior background, warm lighting, blurred coffee shop details, ambient atmosphere, photorealistic"),
        (["cyberpunk", "neon", "future", "night city"], 
         "futuristic cyberpunk city background, neon lights, rainy street reflection, night time, cinematic, high contrast, 8k"),
        (["office", "professional", "work", "corporate"], 
         "modern professional office background, blurred glass walls, bright workspace, corporate atmosphere, clean aesthetic"),
        (["luxury", "mansion", "rich", "interior"], 
         "luxury mansion interior background, golden hour lighting, expensive furniture in background, depth of field, elegant atmosphere"),
    ],
    
    "studio": [
        (["studio", "clean", "simple", "professional"], 
         "professional studio background, soft lighting, neutral backdrop, high quality portrait settings, 8k"),
        (["grey", "gray", "neutral"], 
         "solid grey studio backdrop, professional portrait lighting, soft shadows, clean background"),
        (["white", "bright", "clean"], 
         "bright white infinite studio background, high key lighting, clean crisp look, commercial photography style"),
        (["dark", "moody", "black"], 
         "dark moody atmospheric background, low key lighting, dramatic shadows, cinematic portrait style"),
    ],
    
    "fantasy": [
        (["fantasy", "magic", "mystical", "dream"], 
         "magical fantasy landscape background, glowing particles, ethereal atmosphere, dreamlike, intricate details, masterpiece"),
        (["space", "galaxy", "stars", "cosmic"], 
         "deep space background, nebula and stars, cosmic atmosphere, cinematic, vibrant colors, 8k"),
        (["castle", "medieval", "fortress"], 
         "majestic medieval castle background, epic sky, fantasy landscape, highly detailed, oil painting style"),
    ]
}

def get_best_background_prompt(user_input: str) -> str:
    """
    Score user input against the library and return the best matching optimized prompt.
    If no strong match found, returns a high-quality enhanced version of the input.
    """
    user_input_lower = user_input.lower()
    best_score = 0
    best_prompt = None
    
    # Iterate through all categories
    for category, items in BACKGROUND_LIBRARY.items():
        for keywords, optimized_prompt in items:
            # Score this item
            score = 0
            for kw in keywords:
                # Direct match
                if re.search(rf'\b{re.escape(kw)}\b', user_input_lower):
                    score += 2
                # Partial match
                elif kw in user_input_lower:
                    score += 1
            
            # Bonus score if category matches
            if category in user_input_lower:
                score += 1
                
            if score > best_score:
                best_score = score
                best_prompt = optimized_prompt
    
    # Threshold for using a library match
    if best_score > 0 and best_prompt:
        print(f"🎯 Matched background (Score: {best_score}): {best_prompt[:50]}...")
        return best_prompt
    
    # Fallback: Enhance the user input directly
    print("✨ Enhancing user input directly")
    return f"{user_input} background, highly detailed, cinematic lighting, 8k, masterpiece, photorealistic, depth of field"


def list_background_categories() -> List[str]:
    """Return list of available background categories."""
    return list(BACKGROUND_LIBRARY.keys())
