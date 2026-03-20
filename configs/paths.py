"""
Neural Citadel - Centralized Paths Configuration
=================================================

All model paths for the image generation system.
Edit this file if you move models to different locations.
"""

from pathlib import Path

# =============================================================================
# BASE DIRECTORIES (dynamically resolved from this file's location)
# =============================================================================
# This file is at: D:\neural_citadel\configs\paths.py
# So parent.parent gets us to: D:\neural_citadel
ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"
MODELS_DIR = ASSETS_DIR / "models" / "image_gen"


# =============================================================================
# UPSCALER MODELS
# =============================================================================
UPSCALERS_DIR = MODELS_DIR / "upscalers"

UPSCALER_MODELS = {
    # R-ESRGAN 4x+ - General purpose, excellent for realistic photos
    "R-ESRGAN 4x+": UPSCALERS_DIR / "RealESRGAN_x4plus.pth",
    
    # R-ESRGAN Anime6B - Lightweight, optimized for anime/illustrations
    "R-ESRGAN 4x+ Anime6B": UPSCALERS_DIR / "RealESRGAN_x4plus_anime_6B.pth",
    
    # R-ESRGAN 4x+ Fixed - For image_surgeon (color-corrected version)
    "R-ESRGAN 4x+ Fixed": UPSCALERS_DIR / "RealESRGAN_x4plus_fixed.pth",
}

# Model architecture configs (num_block for RRDB network)
UPSCALER_CONFIGS = {
    "R-ESRGAN 4x+": {"num_block": 23, "scale": 4},
    "R-ESRGAN 4x+ Anime6B": {"num_block": 6, "scale": 4},  # Smaller model
    "R-ESRGAN 4x+ Fixed": {"num_block": 23, "scale": 4},  # Same arch as 4x+
}


# =============================================================================
# CONTROLNET MODELS
# =============================================================================
CONTROLNET_DIR = MODELS_DIR / "controlnet"

CONTROLNET_MODELS = {
    # Canny edge detection - For line art and edge-based guidance
    "canny": CONTROLNET_DIR / "control_v11p_sd15_canny.pth",
    
    # Depth map - For 3D-aware composition
    "depth": CONTROLNET_DIR / "control_v11f1p_sd15_depth.pth",
    
    # OpenPose - For human pose guidance
    "openpose": CONTROLNET_DIR / "control_v11p_sd15_openpose.pth",
}

# =============================================================================
# IMAGE SURGEON MODELS (SAM2 / GroundingDINO)
# =============================================================================
IMAGE_SURGEON_MODELS_DIR = MODELS_DIR / "image_surgeon"

# SAM2 Models - User specified path
# Override if directory exists, otherwise fallback to standard default
_USER_SURGEON_PATH = Path(r"D:\neural_citadel\assets\models\image_surgeon")
if _USER_SURGEON_PATH.exists():
    IMAGE_SURGEON_MODELS_DIR = _USER_SURGEON_PATH

SAM2_MODELS = {
    "tiny": IMAGE_SURGEON_MODELS_DIR / "sam2.1_hiera_tiny.pt",
    "small": IMAGE_SURGEON_MODELS_DIR / "sam2.1_hiera_small.pt",
    "base_plus": IMAGE_SURGEON_MODELS_DIR / "sam2.1_hiera_base_plus.pt",
    "large": IMAGE_SURGEON_MODELS_DIR / "sam2.1_hiera_large.pt"
}

SAM2_CONFIGS = {
    "tiny": "sam2.1_hiera_t.yaml",
    "small": "sam2.1_hiera_s.yaml",
    "base_plus": "sam2.1_hiera_b+.yaml",
    "large": "sam2.1_hiera_l.yaml"
}

# =============================================================================
# IMAGE SURGEON MODELS (SAM2 / GroundingDINO)
# =============================================================================
IMAGE_SURGEON_MODELS_DIR = MODELS_DIR / "image_surgeon"

# SAM2 Models - User requested manual path: D:\neural_citadel\assets\models\image_surgeon
# Override if directory exists, otherwise fallback to standard default
_USER_SURGEON_PATH = Path(r"D:\neural_citadel\assets\models\image_surgeon")
if _USER_SURGEON_PATH.exists():
    IMAGE_SURGEON_MODELS_DIR = _USER_SURGEON_PATH

SAM2_MODELS = {
    "tiny": IMAGE_SURGEON_MODELS_DIR / "sam2.1_hiera_tiny.pt",
    "small": IMAGE_SURGEON_MODELS_DIR / "sam2.1_hiera_small.pt",
    "base_plus": IMAGE_SURGEON_MODELS_DIR / "sam2.1_hiera_base_plus.pt",
    "large": IMAGE_SURGEON_MODELS_DIR / "sam2.1_hiera_large.pt"
}

SAM2_CONFIGS = {
    "tiny": "sam2.1_hiera_t.yaml",
    "small": "sam2.1_hiera_s.yaml",
    "base_plus": "sam2.1_hiera_b+.yaml",
    "large": "sam2.1_hiera_l.yaml"
}

# =============================================================================
# DIFFUSION MODELS
# =============================================================================
DIFFUSION_DIR = MODELS_DIR / "diffusion"

# Add your base models here as you download them
DIFFUSION_MODELS = {
    # Anime / Stylized
    "bloodorangemix": DIFFUSION_DIR / "anime" / "BloodorangemixHardcore_bloodorangemix.safetensors",
    "azovya_rpg": DIFFUSION_DIR / "anime" / "aZovyaRPGArtistTools_v4VAE.safetensors",
    "abyssorangemix": DIFFUSION_DIR / "anime" / "abyssorangemix2_Hard.safetensors",
    "eerieorangemix_hard": DIFFUSION_DIR / "anime" / "eerieorangemix2Hardcore_eerieorangemix2.safetensors",
    "eerieorangemix_nsfw": DIFFUSION_DIR / "anime" / "eerieorangemix2NSFW_eerieorangemix2Half.safetensors",
    "meinamix": DIFFUSION_DIR / "anime" / "meinamix_v12Final.safetensors",
    "novaporn": DIFFUSION_DIR / "anime" / "novaPorn_v10.safetensors",
    "shiny_sissy": DIFFUSION_DIR / "anime" / "shiny sissy luxury latex dress for doll_trigger word.safetensors",
    "yesmix": DIFFUSION_DIR / "closeup_anime" / "CheckpointYesmix_v50.safetensors",
    "violet_evergarden": DIFFUSION_DIR / "closeup_anime" / "violet_evergarden_offset.safetensors",
    "qchan_mix": DIFFUSION_DIR / "realistic_anime" / "qchanMix_v70.safetensors",
    "qchan_realistic": DIFFUSION_DIR / "realistic_anime" / "qchanRealisticMix_v50.safetensors",

    # Realistic / Photo
    "dreamshaper": DIFFUSION_DIR / "realistic" / "dreamshaper_8.safetensors",
    "neverending_dream": DIFFUSION_DIR / "realistic" / "neverendingDreamNED_v122BakedVae.safetensors",
    "realistic_digital": DIFFUSION_DIR / "realistic" / "realisticDigital_v60.safetensors",
    "realistic_vision": DIFFUSION_DIR / "realistic" / "realisticVisionV60B1_v51HyperVAE (1).safetensors",
    "typhoon": DIFFUSION_DIR / "realistic" / "typhoonSD15_v2.safetensors",
    "majicmix": DIFFUSION_DIR / "ethinicity" / "majicmixRealistic_v7.safetensors",
    "asian_realistic": DIFFUSION_DIR / "ethinicity" / "asianrealisticSdlife_v60.safetensors",
    "facebomb": DIFFUSION_DIR / "ethinicity" / "facebombmix_v1Bakedvae.safetensors",
    "desi_tadka": DIFFUSION_DIR / "ethinicity" / "desiTadkaSD15Checkpoint_v10.safetensors",
    "kawaii_realistic": DIFFUSION_DIR / "ethinicity" / "kawaiiRealistic_v06.safetensors",
    "russian_ukraine": DIFFUSION_DIR / "ethinicity" / "paamaRUSSIANWOMAN_paamaUKRAINEWOMANV1.safetensors",
    "dif_consistency_checkpoint": DIFFUSION_DIR / "difconsistency" / "difconsistencyCheckpoint_v10.safetensors",
    
    # Closeup Anime
    "closeup_anime_checkpoint": DIFFUSION_DIR / "closeup_anime" / "CheckpointYesmix_v50.safetensors",

    # Fantasy / Artistic / Special
    
    "realistic_fantasy": DIFFUSION_DIR / "semi_realistic_fantasy" / "realisticFantasy_v20.safetensors",
    "realistic_futa": DIFFUSION_DIR / "futa_humanstyle" / "realisticFuta_ver4.safetensors",
    "midjourney_papercut": DIFFUSION_DIR / "papercut" / "midjourneyPapercut_v1.ckpt",
    "papercut_craft": DIFFUSION_DIR / "papercut" / "papercutcraft_v1.ckpt",
    "deep_space": DIFFUSION_DIR / "space" / "deepSpaceDiffusion_v1.ckpt",
    "walking_dead": DIFFUSION_DIR / "zombie" / "theWalkingDead_10.ckpt",

    # NSFW
    "realistic_lazy_mix": DIFFUSION_DIR / "nsfw" / "realisticLazyMixNSFW_v10.safetensors",
    "urpm": DIFFUSION_DIR / "nsfw" / "uberRealisticPornMerge_v23Final.safetensors",
    "pornmaster": DIFFUSION_DIR / "nsfw" / "pornmasterProV8_v8.safetensors",
    "realistic_futa": DIFFUSION_DIR / "futa_humanstyle" / "realisticFuta_ver4.safetensors",
    
    # Inpainting (dedicated SD 1.5 inpainting model)
    "sd15_inpainting": DIFFUSION_DIR / "inpainting" / "sd-v1-5-inpainting.safetensors",
    
    # Clothes inpainting (ZenityX AI - trigger word: CLOTHES)
    "clothes_inpainting": DIFFUSION_DIR / "inpainting" / "inpaintingByZenityxAI_v10.safetensors",
}

# Pipeline-Specific Model Paths
MODEL_GHOSTMIX = DIFFUSION_DIR / "ghostmix" / "ghostmix_v20Bakedvae.safetensors"
MODEL_DIFFUSIONBRUSH = DIFFUSION_DIR / "illustrator" / "diffusionBrushEverythingSFWNSFWAll_v10.safetensors"
MODEL_DIFCONSISTENCY = DIFFUSION_DIR / "difconsistency" / "difconsistencyCheckpoint_v10.safetensors"
MODEL_CLOSEUP_ANIME = DIFFUSION_DIR / "closeup_anime" / "CheckpointYesmix_v50.safetensors"
MODEL_REALISTIC_VISION = DIFFUSION_DIR / "realistic" / "realisticVisionV60B1_v51HyperVAE (1).safetensors"
MODEL_WALKING_DEAD = DIFFUSION_DIR / "zombie" / "theWalkingDead_10.ckpt"
MODEL_MAJICMIX = DIFFUSION_DIR / "ethinicity" / "majicmixRealistic_v7.safetensors"
MODEL_HORROR = DIFFUSION_DIR / "horror" / "majicmixHorror_v1.safetensors"


# =============================================================================
# LORA MODELS
# =============================================================================
LORA_DIR = MODELS_DIR / "lora"

# Add your LoRA files here
LORA_MODELS = {
    # Car
    "car_mx5": LORA_DIR / "car" / "MX5NA_trigger_word_car_or_mx5na.safetensors",
    "car_speedtail": LORA_DIR / "car" / "Speedtail_trigger_word_speedtail sport car.safetensors",
    "car_sketch": LORA_DIR / "car" / "car sketch_trigger_word_car_sketch.safetensors",
    "car_f1": LORA_DIR / "car" / "f1_triggerwordf1lm sports car.safetensors",
    "car_retro": LORA_DIR / "car" / "retroMoto_trigger_word_retromoto.safetensors",
    "car_sedan": LORA_DIR / "car" / "sedan_trigger_word_car.safetensors",
    "car_amsdr": LORA_DIR / "car" / "trigger_word_amsdr.safetensors",
    "car_autohome": LORA_DIR / "car" / "trigger_word_autohome_car.safetensors",

    # Characters / Concepts
    "chastity_v1": LORA_DIR / "chastity" / "chastity cage.safetensors",
    "chastity_v2": LORA_DIR / "chastity" / "chastity_cage_v2.safetensors",
    "chastity_plastic": LORA_DIR / "chastity" / "plastic chastity cag_triggerworde.safetensors",
    "chinese_zombie": LORA_DIR / "chinesezombie" / "lora_Chinese_Qing_Zombie_triggerword.safetensors",
    
    # DifConsistency
    "dif_consistency_photo": DIFFUSION_DIR / "difconsistency" / "difConsistency_photo.safetensors",
    "dif_consistency_detail": DIFFUSION_DIR / "difconsistency" / "difConsistency_detail.safetensors",
    
    # Closeup Anime
    "violet_evergarden": DIFFUSION_DIR / "closeup_anime" / "violet_evergarden_offset.safetensors",

    # Car LoRAs
    "car_sketch": LORA_DIR / "car" / "car sketch_20231016143009.safetensors",
    "car_sedan": LORA_DIR / "car" / "sedan_trigger_word_car.safetensors",
    "car_retro": LORA_DIR / "car" / "retroMoto_trigger_word_retromoto.safetensors",
    "car_speedtail": LORA_DIR / "car" / "Speedtail_trigger_word_speedtail sport car.safetensors",
    "car_f1": LORA_DIR / "car" / "f1_triggerwordf1lm sports car.safetensors",
    "car_mx5": LORA_DIR / "car" / "MX5NA_trigger_word_car_or_mx5na.safetensors",
    "car_autohome": LORA_DIR / "car" / "autohomeHQHS7_1.0.safetensors",
    "car_amsdr": LORA_DIR / "car" / "trigger_word_amsdr.safetensors",
    "car_rx7": LORA_DIR / "car" / "Mazda_FD3S_v1.0.safetensors",
    "car_jetcar": LORA_DIR / "car" / "Hanshin5000_SD15_V1_DIM4.safetensors",
    "car_motorbike": LORA_DIR / "car" / "yhmotorbikev0.9-000001.safetensors",

    # NSFW LoRAs
    "porn_amateur": LORA_DIR / "nsfw" / "teenBody-v1.safetensors",
    "uniform_slut": LORA_DIR / "nsfw" / "slut-form-v1.safetensors",
    "trans_woman": LORA_DIR / "nsfw" / "transexual_V2.safetensors",
    "polaroid": LORA_DIR / "style" / "polaroid.safetensors",
}


# =============================================================================
# VAE MODELS
# =============================================================================
VAE_DIR = MODELS_DIR / "vae"

VAE_MODELS = {
    "anime": VAE_DIR / "vae-ft-mse-840000-ema-pruned.safetensors",
    "orangemix": VAE_DIR / "orangemix.vae.safetensors",
    "ft_mse": VAE_DIR / "vae-ft-mse-840000-ema-pruned.safetensors",
}

VAE_DIFCONSISTENCY = DIFFUSION_DIR / "difconsistency" / "difconsistencyRAWVAE_v10.pt"

# =============================================================================
# EMBEDDINGS
# =============================================================================
EMBEDDING_DIFCONSISTENCY_NEG = DIFFUSION_DIR / "difconsistency" / "difConsistency_negative_v2.pt"
EMBEDDING_FASTNEGATIVE = DIFFUSION_DIR / "closeup_anime" / "FastNegativeV2.pt"


# =============================================================================
# OUTPUT DIRECTORIES
# =============================================================================
OUTPUT_DIR = ASSETS_DIR / "generated"
CANNY_CACHE_DIR = OUTPUT_DIR / "canny_cache"

# Centralized output directory for all image_gen pipelines
IMAGE_GEN_OUTPUT_DIR = OUTPUT_DIR / "images" / "image_gen_images"

# =============================================================================
# TEMP DIRECTORIES
# =============================================================================
TEMP_DIR = ASSETS_DIR / "temp"
CANNY_TEMP_IMAGES = TEMP_DIR / "canny_temp_images"

# =============================================================================
# NEWSPAPER PUBLISHER PATHS
# =============================================================================
NEWSPAPER_OUTPUT_DIR = ASSETS_DIR / "generated" / "newspaper"
NEWSPAPER_TEMP_DIR = TEMP_DIR / "newspaper_temp"


# =============================================================================
# MOVIE DOWNLOADER PATHS
# =============================================================================
MOVIE_DOWNLOAD_DIR = ASSETS_DIR / "downloaded" / "movie_downloaded"
WHISPER_MODELS_DIR = ASSETS_DIR / "models" / "whisper"  # Separate from image_gen
MOVIE_SUBTITLES_DIR = OUTPUT_DIR / "subtitles"
MOVIE_TEMP_DIR = TEMP_DIR / "movie_temp"

# Executables (cross-platform)
EXE_DIR = ASSETS_DIR / "exe"
ARIA2_EXE = EXE_DIR / "aria2c.exe"  # Windows, use aria2c on Linux/Mac

# =============================================================================
# TORRENT DOWNLOADER PATHS
# =============================================================================
TORRENT_DOWNLOAD_DIR = ASSETS_DIR / "downloaded" / "torrent_downloaded"
SOCIALS_ENV_FILE = ROOT_DIR / "configs" / "secrets" / "socials.env"
DEBUG_LOG_DIR = ROOT_DIR / "logs" / "movie_downloader"
DEBUG_JSONL_FILE = DEBUG_LOG_DIR / "debug.jsonl"

# Movie venv path (for subprocess calls)
MOVIE_VENV_DIR = ROOT_DIR / "venvs" / "env" / "movie_venv"
MOVIE_VENV_PYTHON = MOVIE_VENV_DIR / "Scripts" / "python.exe"

# =============================================================================
# PYQT GUI PATHS
# =============================================================================
PYQT_VENV_DIR = ROOT_DIR / "venvs" / "env" / "pyqt_venv"
PYQT_GUI_DIR = ROOT_DIR / "infra" / "gui"
IMAGE_VENV_DIR = ROOT_DIR / "venvs" / "env" / "image_venv"
IMAGE_VENV_PYTHON = IMAGE_VENV_DIR / "Scripts" / "python.exe"

# =============================================================================
# GUI ASSETS
# =============================================================================
GUI_ASSETS_DIR = ASSETS_DIR / "apps_assets" / "gui"
GUI_VIDEO_PATH = GUI_ASSETS_DIR / "Neural_Citadel_Ultra_Light.mp4"
# User History Backup
USER_HISTORY_DIR = ASSETS_DIR / "apps_assets" / "user_history"
USER_HISTORY_DIR.mkdir(parents=True, exist_ok=True)

# Image generation runner (for subprocess)
IMAGE_GEN_RUNNER = ROOT_DIR / "apps" / "image_gen" / "runner.py"
IMAGE_GEN_MODULE = "apps.image_gen.runner"  # For python -m style

# =============================================================================
# SPEECH RECOGNITION (Sherpa-ONNX)
# =============================================================================
SPEECH_VENV_DIR = ROOT_DIR / "venvs" / "env" / "speech_venv"
SPEECH_VENV_PYTHON = SPEECH_VENV_DIR / "Scripts" / "python.exe"
SPEECH_EXPERIMENT_DIR = ROOT_DIR / "experiments" / "speech_recognition"
SPEECH_MODELS_DIR = ASSETS_DIR / "models" / "speech"

# =============================================================================
# VOICE / TTS MODELS (Sherpa-ONNX VITS)
# =============================================================================
VOICE_MODELS_DIR = ASSETS_DIR / "models" / "voice" / "Language"
VAD_MODEL_PATH = SPEECH_MODELS_DIR / "silero_vad.onnx"



# =============================================================================
# IMAGE SURGEON (SAM2) PATHS
# =============================================================================
IMAGE_SURGEON_MODELS_DIR = ASSETS_DIR / "models" / "image_surgeon"

# SAM2 Model Checkpoints
SAM2_MODELS = {
    "tiny": IMAGE_SURGEON_MODELS_DIR / "sam2.1_hiera_tiny.pt",    # ~150MB, fastest
    "small": IMAGE_SURGEON_MODELS_DIR / "sam2.1_hiera_small.pt",  # ~185MB, balanced
    "base_plus": IMAGE_SURGEON_MODELS_DIR / "sam2.1_hiera_base_plus.pt",  # ~320MB
    "large": IMAGE_SURGEON_MODELS_DIR / "sam2.1_hiera_large.pt",  # ~890MB, most accurate
}
SAM2_DEFAULT_MODEL = SAM2_MODELS["small"]  # Default for 4GB VRAM

# SAM2 Config files
SAM2_CONFIGS = {
    "tiny": "configs/sam2.1/sam2.1_hiera_t.yaml",
    "small": "configs/sam2.1/sam2.1_hiera_s.yaml",
    "base_plus": "configs/sam2.1/sam2.1_hiera_b+.yaml",
    "large": "configs/sam2.1/sam2.1_hiera_l.yaml",
}

# Output directories
IMAGE_SURGEON_OUTPUT_DIR = OUTPUT_DIR / "image_surgeon"
EXTRACTED_SUBJECTS_DIR = IMAGE_SURGEON_OUTPUT_DIR / "extracted_subjects"
BACKGROUND_REPLACED_DIR = IMAGE_SURGEON_OUTPUT_DIR / "background_replaced"
DRESS_MODIFIED_DIR = IMAGE_SURGEON_OUTPUT_DIR / "dress_modified"

# Venv path for subprocess calls
IMAGE_SURGEON_VENV = ROOT_DIR / "venvs" / "env" / "enhanced"

# =============================================================================
# QR-CODE PATHS
# =============================================================================

QR_CODE_DIR = ASSETS_DIR / "qr_code"
QR_CODE_SVG_DIR = QR_CODE_DIR / "svg"
QR_CODE_GRADIENT_DIR = QR_CODE_DIR / "gradients"
QR_CODE_LOGO_DIR = QR_CODE_DIR / "logos"

# QR Studio Runner (for subprocess calls from GUI)
QR_STUDIO_RUNNER = ROOT_DIR / "apps" / "qr_studio" / "runner.py"

# Global Python (NOT a venv - for apps using global site-packages like qr_studio)
GLOBAL_PYTHON = Path("C:/Program Files/Python310/python.exe")

# QR Diffusion (artistic QR generation)
QR_CODE_DIFFUSION_DIR = QR_CODE_DIR / "diffusion"
CONTROLNET_QR = MODELS_DIR / "qr_controlnet" / "v2"
PROMPTS_QR_FILE = ASSETS_DIR / "prompts" / "qr_codemodel_111006_prompts.json"
QR_DIFFUSION_ENGINE = ROOT_DIR / "experiments" / "diffusion_qr" / "qr_image_engine.py"


# =============================================================================
# LLM MODELS (Large Language Models)
# =============================================================================
LLM_MODELS_DIR = ASSETS_DIR / "models" / "llm" / "llm"
LLM_DEBUG_DIR = ASSETS_DIR / "db" / "llm_agent"

# Core agent venv for LLM operations
LLM_AGENT_VENV = ROOT_DIR / "venvs" / "env" / "coreagentvenv"

# Individual model directories
LLM_MODELS = {
    # Coding Models (GGUF/llama_cpp)
    "deepseek_coder": LLM_MODELS_DIR / "Deepseek_Model",
    "deepseek_r1": LLM_MODELS_DIR / "Deepseek_R1_Model",
    "qwen_coder": LLM_MODELS_DIR / "Qwen_Coder_Model",
    "qwen_small": LLM_MODELS_DIR / "Qwen_small_llm",
    
    # General / Creative Models (GGUF/llama_cpp)
    "mistral": LLM_MODELS_DIR / "Mistral_7b_model",
    "seneca_cyber": LLM_MODELS_DIR / "SenecaCyberLLM",
    "tinyllama": LLM_MODELS_DIR / "TinyLlama_Model",
    
    # Uncensored / Creative Writing Models
    "nsfw_story": LLM_MODELS_DIR / "NSFW_Story_Model",
    "realistic_rp": LLM_MODELS_DIR / "Realistic_RP_Model",
    
    # Core Agent Router
    "core_agent": LLM_MODELS_DIR / "Qwen_small_llm",
}

# HuggingFace download info for auto-download
LLM_HF_REPOS = {
    "deepseek_coder": {
        "repo_id": "TheBloke/deepseek-coder-6.7B-instruct-GGUF",
        "filename": "deepseek-coder-6.7b-instruct.Q4_K_M.gguf",
    },
    "qwen_coder": {
        "repo_id": "bartowski/Qwen2.5-Coder-7B-Instruct-GGUF",
        "filename": "Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf",
    },
    "mistral": {
        "repo_id": "TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
        "filename": "mistral-7b-instruct-v0.2.Q4_K_M.gguf",
    },
    "nsfw_story": {
        "repo_id": "bartowski/Meta-Llama-3.1-8B-Instruct-Abliterated-GGUF",
        "filename": "Meta-Llama-3.1-8B-Instruct-abliterated-Q4_K_M.gguf",
    },
    "tinyllama": {
        "repo_id": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
        "filename": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
    },
}

# Engine type for each model (transformers or llama_cpp)
LLM_ENGINE_TYPES = {
    "deepseek_coder": "llama_cpp",
    "deepseek_r1": "llama_cpp",
    "qwen_coder": "llama_cpp",
    "qwen_small": "llama_cpp",
    "mistral": "llama_cpp",
    "dolphin_qwen": "llama_cpp",
    "tinyllama": "llama_cpp",
    "nsfw_story": "llama_cpp",
    "realistic_rp": "llama_cpp",
}


# =============================================================================
# DATABASE PATHS
# =============================================================================
DB_DIR = ASSETS_DIR / "db"
TEST_DB_PATH = DB_DIR / "test" / "test.db"
IMAGE_GEN_DB_DIR = DB_DIR / "image_gen"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def get_upscaler_path(name: str) -> Path:
    """Get the path to an upscaler model by name."""
    if name not in UPSCALER_MODELS:
        raise ValueError(f"Unknown upscaler: {name}. Available: {list(UPSCALER_MODELS.keys())}")
    return UPSCALER_MODELS[name]


def get_controlnet_path(name: str) -> Path:
    """Get the path to a ControlNet model by name."""
    if name not in CONTROLNET_MODELS:
        raise ValueError(f"Unknown controlnet: {name}. Available: {list(CONTROLNET_MODELS.keys())}")
    return CONTROLNET_MODELS[name]


def validate_paths():
    """Check if all configured model paths exist. Returns list of missing files."""
    missing = []
    
    for name, path in UPSCALER_MODELS.items():
        if not path.exists():
            missing.append(f"Upscaler '{name}': {path}")
    
    for name, path in CONTROLNET_MODELS.items():
        if not path.exists():
            missing.append(f"ControlNet '{name}': {path}")

    for name, path in DIFFUSION_MODELS.items():
        if not path.exists():
            missing.append(f"Diffusion '{name}': {path}")

    for name, path in LORA_MODELS.items():
        if not path.exists():
            missing.append(f"LoRA '{name}': {path}")

    for name, path in VAE_MODELS.items():
        if not path.exists():
            missing.append(f"VAE '{name}': {path}")
            
    
    return missing


# =============================================================================
# IMAGE CAPTIONER (Florence-2)
# =============================================================================
IMAGE_CAPTIONER_MODELS_DIR = ASSETS_DIR / "models" / "photo-recognizer"
IMAGE_CAPTIONER_VENV = ROOT_DIR / "venvs" / "env" / "image_captioner"
IMAGE_CAPTIONER_PYTHON = IMAGE_CAPTIONER_VENV / "Scripts" / "python.exe"

# Florence-2 model name on HuggingFace 
FLORENCE2_MODEL_NAME = "microsoft/Florence-2-base"


# =============================================================================
# REASONING ENGINE (DeepSeek R1)
# =============================================================================
# Uses coreagentvenv with llama_cpp_python - called via subprocess only
COREAGENT_VENV = ROOT_DIR / "venvs" / "env" / "coreagentvenv"
COREAGENT_VENV_PYTHON = COREAGENT_VENV / "Scripts" / "python.exe"

# DeepSeek R1 model path
LLM_MODELS_DIR = ASSETS_DIR / "models" / "llm" / "llm"
DEEPSEEK_R1_MODEL = LLM_MODELS_DIR / "Deepseek_R1_Model" / "DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf"


# Reasoning engine CLI script (runs in coreagentvenv)
REASONING_ENGINE = ROOT_DIR / "infra" / "standalone" / "reasoning_engine.py"


# =============================================================================
# CODE ENGINE (DeepSeek Coder / Qwen Coder)
# =============================================================================
# Uses coreagentvenv with llama_cpp_python - called via subprocess only

# DeepSeek Coder model (Master - more capable)
DEEPSEEK_CODER_MODEL = LLM_MODELS_DIR / "Deepseek_Model" / "deepseek-coder-6.7b-instruct.Q4_K_M.gguf"

# Qwen Coder model (Efficient - faster)
QWEN_CODER_MODEL = LLM_MODELS_DIR / "Qwen_Coder_Model" / "Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf"

# Code engine CLI script (runs in coreagentvenv)
CODE_ENGINE = ROOT_DIR / "infra" / "standalone" / "code_engine.py"


# =============================================================================
# HACKING ENGINE (Seneca Cybersecurity LLM x Qwen2.5-7B)
# =============================================================================
# Uses coreagentvenv with llama_cpp_python - called via subprocess only
# Trained on: Exploit Development, Reverse Engineering, Malware Analysis

# Seneca Cybersecurity LLM model path
SENECA_CYBER_MODEL_PATH = LLM_MODELS_DIR / "SenecaCyberLLM" / "senecallm_x_qwen2.5-7b-cybersecurity-q4_k_m.gguf"

# Hacking Engine Script
HACKING_ENGINE_SCRIPT = ROOT_DIR / "infra" / "standalone" / "hacking_engine.py"


# =============================================================================
# WRITING ENGINE (Mistral 7B)
# =============================================================================
# Uses coreagentvenv with llama_cpp_python - supports 4 personas with subtypes

# Mistral 7B model
MISTRAL_MODEL_PATH = LLM_MODELS_DIR / "Mistral_7b_model" / "mistral-7b-instruct-v0.2.Q4_K_M.gguf"

# Writing Engine Script
WRITING_ENGINE_SCRIPT = ROOT_DIR / "infra" / "standalone" / "writing_engine.py"


# ==============================================================================
#  VIDEO REELS 
# ==============================================================================
# uses different apis and duckduckgo to download images to convert to video or having downloaded templates previously from
# the internet.

AUTOMATION_DIR = ROOT_DIR / "assets" / "generated" 
DANCE_VIDEO = AUTOMATION_DIR / "dance_videos"
VIRAL_LAYOVER = AUTOMATION_DIR / "viral_layover"
FINAL_REELS = AUTOMATION_DIR / "final_reel"
MUSIC_DIR = ROOT_DIR / "assets/downloaded/songs"
PREDOWNLOADED_MIXER_SONGS = ROOT_DIR / "assets/downloaded/songs/mixer_songs"


# =============================================================================
# VITS PIPER TTS MODELS
# =============================================================================
# Format: "key" -> dict with full paths for OfflineTtsVitsModelConfig

VITS_PIPER_MODELS = {
    # English (US) - Male
    "en_US_male": {
        "model": VOICE_MODELS_DIR / "vits-piper-en_US-hfc_male-medium" / "en_US-hfc_male-medium.onnx",
        "tokens": VOICE_MODELS_DIR / "vits-piper-en_US-hfc_male-medium" / "tokens.txt",
        "lexicon": "",  # Not used for Piper models
        "data_dir": VOICE_MODELS_DIR / "vits-piper-en_US-hfc_male-medium" / "espeak-ng-data",
        "language": "en",
        "voice": "hfc_male",
        "quality": "medium",
        "description": "English (US) - Male voice",
    },
    # English (US) - LibriTTS
    "en_US_libritts": {
        "model": VOICE_MODELS_DIR / "vits-piper-en_US-libritts_r-medium" / "en_US-libritts_r-medium.onnx",
        "tokens": VOICE_MODELS_DIR / "vits-piper-en_US-libritts_r-medium" / "tokens.txt",
        "lexicon": "",
        "data_dir": VOICE_MODELS_DIR / "vits-piper-en_US-libritts_r-medium" / "espeak-ng-data",
        "language": "en",
        "voice": "libritts",
        "quality": "medium",
        "description": "English (US) - LibriTTS voice",
    },
    # Spanish (Spain)
    "es_ES_carlfm": {
        "model": VOICE_MODELS_DIR / "vits-piper-es_ES-carlfm-x_low" / "es_ES-carlfm-x_low.onnx",
        "tokens": VOICE_MODELS_DIR / "vits-piper-es_ES-carlfm-x_low" / "tokens.txt",
        "lexicon": "",
        "data_dir": VOICE_MODELS_DIR / "vits-piper-es_ES-carlfm-x_low" / "espeak-ng-data",
        "language": "es",
        "voice": "carlfm",
        "quality": "x_low",
        "description": "Spanish (Spain) - Carlfm voice",
    },
    # Hindi (India) - Pratham Male
    "hi_IN_pratham": {
        "model": VOICE_MODELS_DIR / "vits-piper-hi_IN-pratham-medium" / "hi_IN-pratham-medium.onnx",
        "tokens": VOICE_MODELS_DIR / "vits-piper-hi_IN-pratham-medium" / "tokens.txt",
        "lexicon": "",
        "data_dir": VOICE_MODELS_DIR / "vits-piper-hi_IN-pratham-medium" / "espeak-ng-data",
        "language": "hi",
        "voice": "pratham",
        "quality": "medium",
        "description": "Hindi (India) - Pratham male voice",
    },
    # Hindi (India) - Priyamvada Female
    "hi_IN_priyamvada": {
        "model": VOICE_MODELS_DIR / "vits-piper-hi_IN-priyamvada-medium" / "hi_IN-priyamvada-medium.onnx",
        "tokens": VOICE_MODELS_DIR / "vits-piper-hi_IN-priyamvada-medium" / "tokens.txt",
        "lexicon": "",
        "data_dir": VOICE_MODELS_DIR / "vits-piper-hi_IN-priyamvada-medium" / "espeak-ng-data",
        "language": "hi",
        "voice": "priyamvada",
        "quality": "medium",
        "description": "Hindi (India) - Priyamvada female voice",
    },
    # Russian - Irina Female
    "ru_RU_irina": {
        "model": VOICE_MODELS_DIR / "vits-piper-ru_RU-irina-medium" / "ru_RU-irina-medium.onnx",
        "tokens": VOICE_MODELS_DIR / "vits-piper-ru_RU-irina-medium" / "tokens.txt",
        "lexicon": "",
        "data_dir": VOICE_MODELS_DIR / "vits-piper-ru_RU-irina-medium" / "espeak-ng-data",
        "language": "ru",
        "voice": "irina",
        "quality": "medium",
        "description": "Russian - Irina female voice",
    },
    
    # ========== NEW HIGH QUALITY VOICES ==========
    
    # English (US) - Ryan High Quality Male
    # "en_US_ryan": {
    #     "model": VOICE_MODELS_DIR / "vits-piper-en_US-ryan-high" / "en_US-ryan-high.onnx",
    #     "tokens": VOICE_MODELS_DIR / "vits-piper-en_US-ryan-high" / "tokens.txt",
    #     "lexicon": "",
    #     "data_dir": VOICE_MODELS_DIR / "vits-piper-en_US-ryan-high" / "espeak-ng-data",
    #     "language": "en",
    #     "voice": "ryan",
    #     "quality": "high",
    #     "description": "English (US) - Ryan high quality male voice",
    # },
    # English (US) - Lessac High Quality
    # "en_US_lessac": {
    #     "model": VOICE_MODELS_DIR / "vits-piper-en_GB-amy-high" / "en_US-lessac-high.onnx",
    #     "tokens": VOICE_MODELS_DIR / "vits-piper-en_GB-amy-high" / "tokens.txt",
    #     "lexicon": "",
    #     "data_dir": VOICE_MODELS_DIR / "vits-piper-en_GB-amy-high" / "espeak-ng-data",
    #     "language": "en",
    #     "voice": "lessac",
    #     "quality": "high",
    #     "description": "English (US) - Lessac high quality voice",
    # },
    # Hindi (India) - Rohan Medium Male
    # "hi_IN_rohan": {
    #     "model": VOICE_MODELS_DIR / "vits-piper-hi_IN-rohan-medium" / "hi_IN-rohan-medium.onnx",
    #     "tokens": VOICE_MODELS_DIR / "vits-piper-hi_IN-rohan-medium" / "tokens.txt",
    #     "lexicon": "",
    #     "data_dir": VOICE_MODELS_DIR / "vits-piper-hi_IN-rohan-medium" / "espeak-ng-data",
    #     "language": "hi",
    #     "voice": "rohan",
    #     "quality": "medium",
    #     "description": "Hindi (India) - Rohan male voice (finetuned from lessac)",
    # },
}

# Indic TTS (Transformers-based - larger model)
INDIC_TTS_MODEL = VOICE_MODELS_DIR / "Indic_TTS" / "local_indic_tts"

# Helper to get model config for sherpa-onnx
def get_piper_model(key: str) -> dict:
    """Get Piper TTS model info by key for OfflineTtsVitsModelConfig."""
    if key not in VITS_PIPER_MODELS:
        raise ValueError(f"Unknown Piper model: {key}. Available: {list(VITS_PIPER_MODELS.keys())}")
    return VITS_PIPER_MODELS[key]


STORIES_TITLE_HELPER = ASSETS_DIR/"apps_assets/social_automation_agent/stories_ideas.json"
STORIES_TITLE_DATABASE = ASSETS_DIR / "db/social_automation_agent"
IDEAS_FOR_VIDEOS_AND_IMAGES_SEARCH_TERM = ASSETS_DIR /"apps_assets/social_automation_agent\configs.json"

