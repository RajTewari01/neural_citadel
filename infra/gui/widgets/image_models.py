"""
Image Generation Models Metadata
================================

Complete list of all available models (pipeline + type combinations)
for display in the PyQt GUI with descriptions for the info tooltips.

IMPORTANT: These MUST match the actual pipelines in apps/image_gen/pipeline/
- style parameter = pipeline name
- type parameter = type registered in @register_pipeline
"""

# Model definitions: (display_name, style, type, icon, description)
# style = --style argument
# type = --type argument (None for auto-detect pipelines)
IMAGE_MODELS = [
    # =========================================================================
    # ANIME MODELS (7) - style: anime
    # =========================================================================
    ("Anime - Meinamix", "anime", "meinamix", "🎨", "Beautiful anime art, classic style"),
    ("Anime - Novaporn", "anime", "novaporn", "🎨", "Photo-realistic anime style"),
    ("Anime - BloodOrangeMix", "anime", "bloodorangemix", "🎨", "Dark, intense anime with red tones"),
    ("Anime - AbyssOrangeMix", "anime", "abyssorangemix", "🎨", "Dark fantasy anime style"),
    ("Anime - EerieOrangeMix", "anime", "eerieorangemix", "🎨", "Creepy, supernatural anime"),
    ("Anime - Azovya RPG", "anime", "azovya", "🎨", "Fantasy RPG character art"),
    ("Anime - Shiny Sissy", "anime", "shiny_sissy", "🎨", "Glossy latex/shiny materials"),
    
    # =========================================================================
    # CLOSEUP ANIME (1) - style: closeup_anime (no type)
    # =========================================================================
    ("Closeup Anime", "closeup_anime", None, "👁️", "Close-up anime face/eye detail"),
    
    # =========================================================================
    # CAR MODELS (11) - style: car
    # =========================================================================
    ("Car - Sketch", "car", "sketch", "🚗", "Car sketch/drawing style"),
    ("Car - Sedan", "car", "sedan", "🚗", "Luxury sedan on highway"),
    ("Car - Retro", "car", "retro", "🚗", "Vintage 1960s classic cars"),
    ("Car - Speedtail", "car", "speedtail", "🚗", "McLaren Speedtail hypercar"),
    ("Car - F1", "car", "f1", "🚗", "Formula 1 racing cars"),
    ("Car - MX5", "car", "mx5", "🚗", "Mazda MX5 Miata roadster"),
    ("Car - Autohome", "car", "autohome", "🚗", "Modern SUV showroom quality"),
    ("Car - AMSDR", "car", "amsdr", "🚗", "City taxi/urban vehicles"),
    ("Car - RX7", "car", "rx7", "🚗", "Mazda RX7 FD3S JDM drift"),
    ("Car - Jetcar", "car", "jetcar", "🚗", "Trains and locomotives"),
    ("Car - Motorbike", "car", "motorbike", "🚗", "Sports motorcycles"),
    
    # =========================================================================
    # DRAWING MODELS (4) - style: drawing
    # =========================================================================
    ("Drawing - Rachel Walker", "drawing", "rachel_walker", "✏️", "Watercolor animals, nature scenes"),
    ("Drawing - Matcha Pixiv", "drawing", "matcha_pixiv", "✏️", "Pixiv anime sketch style"),
    ("Drawing - Pareidolia", "drawing", "pareidolia", "✏️", "Surreal floating islands art"),
    ("Drawing - Chinese Ink", "drawing", "chinese_ink", "✏️", "Traditional ink scroll paintings"),
    
    # =========================================================================
    # HYPERREALISTIC MODELS (5) - style: hyperrealistic
    # =========================================================================
    ("Hyperrealistic - Realistic Vision", "hyperrealistic", "realistic_vision", "📷", "Ultra-realistic photo quality"),
    ("Hyperrealistic - Dreamshaper", "hyperrealistic", "dreamshaper", "📷", "Dreamy, soft realistic photos"),
    ("Hyperrealistic - Neverending", "hyperrealistic", "neverending", "📷", "Detailed faces with freckles"),
    ("Hyperrealistic - Digital", "hyperrealistic", "digital", "📷", "Clean digital portrait style"),
    ("Hyperrealistic - Typhoon", "hyperrealistic", "typhoon", "📷", "Dramatic lighting portraits"),
    
    # =========================================================================
    # ETHNICITY MODELS (5) - style: ethnicity
    # =========================================================================
    ("Ethnicity - Asian", "ethnicity", "asian", "🌏", "Asian beauty portraits"),
    ("Ethnicity - Indian", "ethnicity", "indian", "🌏", "Indian traditional/saree"),
    ("Ethnicity - Russian", "ethnicity", "russian", "🌏", "Russian/Ukrainian models"),
    ("Ethnicity - European", "ethnicity", "european", "🌏", "European blonde portraits"),
    ("Ethnicity - Chinese", "ethnicity", "chinese", "🌏", "Chinese qipao/silk dress"),
    
    # =========================================================================
    # PAPERCUT MODELS (2) - style: papercut
    # =========================================================================
    ("Papercut - Midjourney", "papercut", "midjourney", "📄", "Layered paper art style"),
    ("Papercut - Craft", "papercut", "papercutcraft", "📄", "Cute origami/paper craft"),
    
    # =========================================================================
    # DIFCONSISTENCY MODELS (3) - style: difconsistency
    # =========================================================================
    ("DifConsistency - Photo", "difconsistency", "photo", "🔬", "Food photography, product shots"),
    ("DifConsistency - Detail", "difconsistency", "detail", "🔬", "Macro/extreme detail shots"),
    ("DifConsistency - Raw", "difconsistency", "raw", "🔬", "Raw, unprocessed photo style"),
    
    # =========================================================================
    # HORROR (auto-detect from prompt, no type needed) - style: horror
    # =========================================================================
    ("Horror", "horror", None, "👻", "Vampires, demons, dark scenes"),
    
    # =========================================================================
    # ZOMBIE SUBTYPES (4) - style: zombie
    # =========================================================================
    ("Zombie - Close-up", "zombie", "close", "🧟", "Single zombie portrait"),
    ("Zombie - Mid-shot", "zombie", "mid", "🧟", "2-3 zombies group shot"),
    ("Zombie - Horde", "zombie", "horde", "🧟", "Wide zombie horde"),
    ("Zombie - Chinese", "zombie", "chinese", "🧟", "Chinese Qing dynasty jiangshi"),
    
    # =========================================================================
    # GHOST (auto-detect, no type needed) - style: ghost
    # =========================================================================
    ("Ghost", "ghost", None, "👻", "Ethereal spirits, apparitions"),
    
    # =========================================================================
    # SPACE (no subtypes) - style: space
    # =========================================================================
    ("Space", "space", None, "🌌", "Nebulas, galaxies, cosmic scenes"),
    
    # =========================================================================
    # DIFFUSIONBRUSH (no subtypes) - style: diffusionbrush
    # =========================================================================
    ("Diffusion Brush", "diffusionbrush", None, "🖌️", "Digital art, fantasy warriors"),
    
    # =========================================================================
    # NSFW SUBTYPES (4) - style: nsfw
    # =========================================================================
    ("NSFW - Lazy Mix", "nsfw", "lazy_mix", "🔞", "General purpose NSFW"),
    ("NSFW - URPM", "nsfw", "urpm", "🔞", "Uber Realistic Porn Merge"),
    ("NSFW - PornMaster", "nsfw", "pornmaster", "🔞", "Reddit/Subreddit style"),
    ("NSFW - Futa", "nsfw", "realistic_futa", "🔞", "Trans/Futa specialized"),
]

# Aspect ratio options
ASPECT_RATIOS = [
    ("Portrait", "portrait", "512x768 - Vertical orientation"),
    ("Landscape", "landscape", "768x512 - Horizontal orientation"),
    ("Square", "normal", "512x512 - Square format"),
]

def get_model_by_name(name: str):
    """Get model tuple by display name."""
    for model in IMAGE_MODELS:
        if model[0] == name:
            return model
    return None

def get_model_names():
    """Get list of all model display names."""
    return [model[0] for model in IMAGE_MODELS]
