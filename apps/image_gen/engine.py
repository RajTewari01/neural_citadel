"""
Production Diffusion Engine for Neural Citadel
===============================================
Optimized for GTX 1650 (4GB VRAM) with Float32 precision.
Supports: VAE switching, LoRA, ControlNet, Multiple Schedulers, Upscaling
"""

import torch
import gc
import uuid
import time
import warnings
import importlib
from pathlib import Path
from PIL import Image
from typing import Optional, Union
from diffusers import (
    StableDiffusionPipeline,
    StableDiffusionControlNetPipeline,
    ControlNetModel,
    AutoencoderKL
)
from diffusers.utils.logging import set_verbosity_error

# Silence warnings
set_verbosity_error()
warnings.filterwarnings("ignore")

# Import only types (lightweight)
from .pipeline.pipeline_types import PipelineConfigs

# Import database module for tracking generated images
from assets.db.image_gen import save_image_record

# Import path for saving canny edge maps
from configs.paths import CANNY_TEMP_IMAGES

class DiffusionEngine:
    """
    Production-grade Stable Diffusion engine with full config support.
    Uses dynamic imports to avoid loading unused modules.
    """
    
    # VAE file mapping
    VAE_MAP = {
        "anime": "anime.vae.safetensors",
        "realistic": "vae-ft-mse-840000-ema-pruned.safetensors",
        "semi-realistic": "orangemix.vae.safetensors",
        "default": None  # Use baked-in VAE
    }
    
    # Scheduler module mapping (lazy loaded)
    SCHEDULER_MODULES = {
        "euler_a": "euler",
        "dpm++_2m_karras": "dpmpp_2m_karras",
        "dpm++_sde_karras": "dpmpp_sde_karras",
        "dpm++_2m_sde_karras": "dpmpp_2m_sde_karras",
        "ddim": "ddim",
        "lms": "lms"
    }
    
    # Upscaler module mapping (lazy loaded)
    UPSCALER_MODULES = {
        "None": None,
        "Lanczos": "lanczos",
        "R-ESRGAN 4x+": "realesrgan_4x",
        "R-ESRGAN 4x+ Anime6B": "realesrgan_anime",
        "Diffusion": "diffusion_upscale"
    }
    
    def __init__(self, vae_dir: Path = None):
        """
        Initialize the engine.
        
        Args:
            vae_dir: Directory containing VAE files (defaults to assets/models/image_gen/vae)
        """
        self.pipe = None
        self.current_model = None
        self.current_vae = None
        
        # Set VAE directory
        if vae_dir is None:
            self.vae_dir = Path(__file__).resolve().parent.parent.parent / "assets" / "models" / "image_gen" / "vae"
        else:
            self.vae_dir = Path(vae_dir)
            
    def _flush(self):
        """Clean up GPU memory"""
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    def _load_scheduler(self, scheduler_name: str):
        """
        Dynamically load scheduler module.
        
        Args:
            scheduler_name: Name from PipelineConfigs.scheduler_name
            
        Returns:
            Scheduler module with load() function
        """
        module_name = self.SCHEDULER_MODULES.get(scheduler_name)
        if not module_name:
            raise ValueError(f"Unknown scheduler: {scheduler_name}")
        
        try:
            module = importlib.import_module(f".schedulars.{module_name}", package="apps.image_gen")
            return module
        except ImportError as e:
            raise ImportError(f"Failed to load scheduler '{scheduler_name}': {e}")
    
    def _load_upscaler(self, upscaler_name: str):
        """
        Dynamically load upscaler module.
        
        Args:
            upscaler_name: Name from PipelineConfigs.upscale_method
            
        Returns:
            Upscaler module with upscale() function, or None
        """
        if upscaler_name == "None":
            return None
            
        module_name = self.UPSCALER_MODULES.get(upscaler_name)
        if not module_name:
            raise ValueError(f"Unknown upscaler: {upscaler_name}")
        
        try:
            module = importlib.import_module(f".upscalers.{module_name}", package="apps.image_gen")
            return module
        except ImportError as e:
            raise ImportError(f"Failed to load upscaler '{upscaler_name}': {e}")
    
    def _load_vae(self, vae_choice: Union[str, Path]) -> Optional[AutoencoderKL]:
        """
        Load VAE based on config choice or path.
        
        Args:
            vae_choice: "anime", "realistic", "semi-realistic", "default", or Path/str to VAE file
            
        Returns:
            AutoencoderKL instance or None (for default)
        """
        if str(vae_choice) == "default":
            print("   -> Using model's baked-in VAE")
            return None
            
        # 1. Try mapping first
        vae_filename = self.VAE_MAP.get(str(vae_choice))
        
        # 2. If mapped, use predefined path, else treat as custom path
        if vae_filename:
            vae_path = self.vae_dir / vae_filename
        else:
            try:
                vae_path = Path(vae_choice)
            except:
                print(f"   ⚠️ Invalid VAE path/choice '{vae_choice}', using default")
                return None
        
        if not vae_path.exists():
            print(f"   [!] VAE file not found: {vae_path}, using default")
            return None
            
        print(f"   -> Loading VAE: {vae_path.name}")
        vae = AutoencoderKL.from_single_file(
            str(vae_path),
            torch_dtype=torch.float32,
            use_safetensors=True,
            local_files_only=True
        )
        return vae
    
    def load_model(self, config: PipelineConfigs):
        """
        Load the Stable Diffusion model with all configurations.
        
        Args:
            config: PipelineConfigs dataclass instance
        """
        # Check if model needs reloading
        model_changed = self.current_model != config.base_model
        vae_changed = self.current_vae != config.vae
        
        if not model_changed and not vae_changed and self.pipe is not None:
            # Just handle embeddings and LoRA if needed (LoRA handled separately)
            if hasattr(config, "embeddings") and config.embeddings:
                print("[Embeddings] Reloading/Loading embeddings...")
                for emb_path in config.embeddings:
                    try:
                        self.pipe.load_textual_inversion(str(emb_path))
                    except Exception as e:
                        print(f"   [!] Failed to load embedding {emb_path.name}: {e}")
            print("   -> Model already loaded, skipping")
            return
            
        print(f"\n[+] Loading Model: {config.base_model.name}")
        start = time.time()
        self._flush()
        
        # 1. Load VAE
        vae = self._load_vae(config.vae)
        
        # 2. Prepare loading kwargs
        load_kwargs = {
            "torch_dtype": torch.float32,
            "use_safetensors": config.base_model.suffix == ".safetensors",
            "safety_checker": None,
            "requires_safety_checker": False,
            "local_files_only": True,
        }
        
        # Enable low CPU memory usage if accelerate is installed
        try:
            import accelerate
            load_kwargs["low_cpu_mem_usage"] = True
        except ImportError:
            pass
        
        # Add VAE if not default
        if vae is not None:
            load_kwargs["vae"] = vae
            
        # Add clip_skip if specified
        if config.clip_skip is not None and config.clip_skip > 1:
            print(f"   [config] Clip Skip: {config.clip_skip}")
            load_kwargs["clip_skip"] = config.clip_skip
            
        # Add model config if specified
        if config.model_config:
            load_kwargs["config"] = config.model_config
            print(f"   [config] Using config: {config.model_config}")
        
        # 3. Load Pipeline (with or without ControlNet)
        if config.c_net:
            print(f"[control] Loading {len(config.c_net)} ControlNet(s)...")
            controlnet_models = []
            
            for cn in config.c_net:
                # Dynamically import the ControlNet module
                cn_module_name = cn.control_type  # "canny", "depth", or "openpose"
                try:
                    cn_module = importlib.import_module(f".controlnet.{cn_module_name}", package="apps.image_gen")
                    
                    # Use the module's load_model() function
                    cn_model = cn_module.load_model(torch_dtype=torch.float32)
                    controlnet_models.append(cn_model)
                    print(f"   -> Loaded: {cn.control_type}")
                except ImportError as e:
                    raise ImportError(f"Failed to load ControlNet '{cn.control_type}': {e}")
            
            self.pipe = StableDiffusionControlNetPipeline.from_single_file(
                str(config.base_model),
                controlnet=controlnet_models if len(controlnet_models) > 1 else controlnet_models[0],
                **load_kwargs
            )
        else:
            self.pipe = StableDiffusionPipeline.from_single_file(
                str(config.base_model),
                **load_kwargs
            )
        
        # 3.5 Load Textual Inversion Embeddings
        if hasattr(config, "embeddings") and config.embeddings:
            print(f"[Embeddings] Loading {len(config.embeddings)} embedding(s)...")
            for emb_path in config.embeddings:
                try:
                    self.pipe.load_textual_inversion(str(emb_path))
                    print(f"   -> Loaded embedding: {emb_path.name}")
                except Exception as e:
                    print(f"   [!] Failed to load embedding {emb_path.name}: {e}")
        
        # 4. Apply VRAM Optimizations (GTX 1650 Survival Kit)
        self.pipe.enable_sequential_cpu_offload()
        self.pipe.enable_vae_slicing()
        self.pipe.enable_vae_tiling()
        self.pipe.enable_attention_slicing(slice_size="max")
        print("   -> Optimizations: Sequential Offload, VAE Slicing/Tiling, Attention Slicing")
        
        # 5. Load Scheduler (dynamically)
        scheduler_module = self._load_scheduler(config.scheduler_name)
        self.pipe.scheduler = scheduler_module.load(self.pipe.scheduler.config)
        print(f"   -> Scheduler: {config.scheduler_name}")
        
        # 6. Enable progress bar
        self.pipe.set_progress_bar_config(disable=False)
        
        self.current_model = config.base_model
        self.current_vae = config.vae
        print(f"[DONE] Model loaded in {time.time() - start:.2f}s\n")
    
    def generate(self, config: PipelineConfigs) -> Path:
        """
        Generate an image based on the configuration.
        
        Args:
            config: PipelineConfigs dataclass instance
            
        Returns:
            Path to the saved image
        """
        # 1. Load model
        self.load_model(config)
        
        # 2. Handle LoRAs
        if config.lora:
            print(f"[LoRA] Loading {len(config.lora)} LoRA(s)...")
            
            # Unfuse and unload previous LoRAs
            try:
                self.pipe.unfuse_lora()
            except:
                pass
            self.pipe.unload_lora_weights()
            
            # Load new LoRAs
            for lora_cfg in config.lora:
                print(f"   -> {lora_cfg.lora_path.name} (strength: {lora_cfg.scale})")
                self.pipe.load_lora_weights(str(lora_cfg.lora_path))
                self.pipe.fuse_lora(lora_scale=lora_cfg.scale)
                
                # Inject trigger word if specified
                if lora_cfg.lora_trigger_word:
                    if lora_cfg.lora_trigger_word.lower() not in config.prompt.lower():
                        config.prompt = f"{lora_cfg.lora_trigger_word} {config.prompt}"
        
        # 3. Prepare generation kwargs
        seed = config.seed if config.seed is not None else torch.randint(0, 2**32 - 1, (1,)).item()
        generator = torch.Generator("cpu").manual_seed(seed)
        
        print(f"[GEN] Generating: {config.prompt[:60]}...")
        print(f"   [Seed] {seed}")
        print(f"   [Size] {config.width}x{config.height}, Steps: {config.steps}, CFG: {config.cfg}")
        
        gen_kwargs = {
            "prompt": config.prompt,
            "negative_prompt": config.neg_prompt,
            "width": config.width,
            "height": config.height,
            "num_inference_steps": config.steps,
            "guidance_scale": config.cfg,
            "generator": generator
        }
        
        # Add ControlNet inputs if present
        if config.c_net:
            cn_images = []
            cn_scales = []
            
            # Ensure canny temp directory exists
            CANNY_TEMP_IMAGES.mkdir(parents=True, exist_ok=True)
            
            # Track the path of the canny edge map for DB
            canny_save_path = None
            
            for cn in config.c_net:
                # Dynamically import the ControlNet module for preprocessing
                cn_module_name = cn.control_type
                cn_module = importlib.import_module(f".controlnet.{cn_module_name}", package="apps.image_gen")
                
                # Load and preprocess the input image using the module's detect() function
                from PIL import Image as PILImage
                input_image = PILImage.open(cn.image_path)
                processed_image = cn_module.detect(input_image)
                
                # Save the edge map to temp directory
                edge_filename = f"{cn.control_type}_{uuid.uuid4().hex[:8]}.png"
                edge_save_path = CANNY_TEMP_IMAGES / edge_filename
                processed_image.save(edge_save_path)
                print(f"   [ControlNet] Saved {cn.control_type} edge map: {edge_save_path}")
                
                # Capture the path if this is a Canny ControlNet
                if cn.control_type == "canny" and canny_save_path is None:
                    canny_save_path = edge_save_path
                
                cn_images.append(processed_image)
                cn_scales.append(cn.scale)
            
            gen_kwargs["image"] = cn_images if len(cn_images) > 1 else cn_images[0]
            gen_kwargs["controlnet_conditioning_scale"] = cn_scales if len(cn_scales) > 1 else cn_scales[0]
        
        # 4. Generate
        start = time.time()
        result = self.pipe(**gen_kwargs)
        image = result.images[0]
        print(f"[Time] Generation time: {time.time() - start:.2f}s")
        
        # 5. Upscaling Pipeline: Diffusion (optional) → ESRGAN (auto) → Lanczos
        # =========================================================================
        
        # 5a. Diffusion Upscale (if --add_details flag set) - EXPENSIVE
        if config.add_details:
            print("[Upscaling] Step 1: Diffusion upscale (hallucinating details)...")
            diffusion_module = self._load_upscaler("Diffusion")
            image = diffusion_module.upscale(
                base_pipe=self.pipe,
                image=image,
                prompt=config.prompt,
                negative_prompt=config.neg_prompt
            )
            print(f"   [Diffusion] Upscale complete: {image.size}")
        
        # 5b. ESRGAN Upscale (auto-selected based on style_type)
        esrgan_name = "R-ESRGAN 4x+ Anime6B" if config.style_type == "anime" else "R-ESRGAN 4x+"
        print(f"[Upscaling] Step 2: {esrgan_name} (auto-selected for {config.style_type})...")
        esrgan_module = self._load_upscaler(esrgan_name)
        image = esrgan_module.upscale(image, scale=4.0)
        print(f"   [ESRGAN] Upscale complete: {image.size}")
        
        # 5c. Lanczos (final polish - fast CPU-based resize)
        print("[Upscaling] Step 3: Lanczos (final polish)...")
        lanczos_module = self._load_upscaler("Lanczos")
        image = lanczos_module.upscale(image, scale=1.0)  # Lanczos handles final sizing
        print(f"   [Lanczos] Final size: {image.size}")
        
        # 6. Save
        filename = f"gen_{uuid.uuid4().hex[:8]}.png"
        save_path = config.output_dir / filename
        image.save(save_path, quality=95)
        print(f"[Saved] Saved: {save_path}")
        
        # 7. Save to database for tracking
        try:
            # Prepare LoRA info for database
            loras_data = None
            if config.lora:
                loras_data = [
                    {"path": str(l.lora_path), "scale": l.scale, "trigger": l.lora_trigger_word}
                    for l in config.lora
                ]
            
            # Prepare ControlNet info for database
            cnets_data = None
            if config.c_net:
                cnets_data = [
                    {"type": cn.control_type, "image": str(cn.image_path), "scale": cn.scale}
                    for cn in config.c_net
                ]
            
            save_image_record(
                image_path=save_path,
                base_model=config.base_model,
                output_dir=config.output_dir,
                prompt=config.prompt,
                neg_prompt=config.neg_prompt,
                triggers=config.triggers,
                width=config.width,
                height=config.height,
                steps=config.steps,
                cfg=config.cfg,
                seed=seed,
                clip_skip=config.clip_skip,
                vae=str(config.vae) if config.vae else 'default',
                scheduler_name=config.scheduler_name,
                upscale_method=f"{'Diffusion+' if config.add_details else ''}{esrgan_name}+Lanczos",
                loras=loras_data,
                controlnets=cnets_data,
                canny_image_path=canny_save_path if 'canny_save_path' in locals() else None
            )
        except Exception as db_err:
            print(f"[DB Warning] Failed to save to database: {db_err}")
        
        print("")
        return save_path
    
    def unload(self):
        """Unload the model and free VRAM"""
        if self.pipe is not None:
            del self.pipe
            self.pipe = None
            self.current_model = None
            self.current_vae = None
        self._flush()
        print("[Clean] Model unloaded")
