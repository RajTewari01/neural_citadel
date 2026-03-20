"""
QR Studio Engine
================

The core QR code generation engine. Takes QRConfig from any pipeline
and generates the actual QR code image.

Usage:
    from apps.qr_studio.engine import QREngine
    from apps.qr_studio.pipeline.svg import svg_url
    
    engine = QREngine()
    config = svg_url("https://github.com")
    output_path = engine.generate(config)
"""

import os
import uuid
import random
import platform
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, Union
import sys

# =============================================================================
# PATH SETUP
# =============================================================================

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# =============================================================================
# IMPORTS
# =============================================================================

import qrcode
import qrcode.image.svg
from PIL import ImageColor
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import (
    RadialGradiantColorMask,
    VerticalGradiantColorMask,
    HorizontalGradiantColorMask,
    SquareGradiantColorMask,
)
from qrcode.image.styles.moduledrawers import (
    SquareModuleDrawer,
    GappedSquareModuleDrawer,
    CircleModuleDrawer,
    RoundedModuleDrawer,
)

from configs.paths import (
    QR_CODE_SVG_DIR,
    QR_CODE_GRADIENT_DIR,
    QR_CODE_LOGO_DIR,
    QR_CODE_DIFFUSION_DIR,
    QR_DIFFUSION_ENGINE,
    IMAGE_VENV_PYTHON,
    DB_DIR,
)
from apps.qr_studio.pipeline.pipeline_types import QRConfig
from apps.qr_studio.data import handlers

# =============================================================================
# LOGGING SETUP
# =============================================================================

LOG_DIR = _ROOT / "logs" / "qr_studio"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "qr_studio.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)-8s - [%(filename)s:%(lineno)d] - %(message)s'
)

# =============================================================================
# DATABASE SETUP
# =============================================================================

QR_DB_DIR = DB_DIR / "qr_studio"
QR_DB_DIR.mkdir(parents=True, exist_ok=True)
QR_DB_FILE = QR_DB_DIR / "analytics.db"

# =============================================================================
# MODULE DRAWER MAP
# =============================================================================

MODULE_DRAWER_MAP = {
    "rounded": RoundedModuleDrawer,
    "square": SquareModuleDrawer,
    "circle": CircleModuleDrawer,
    "gapped": GappedSquareModuleDrawer,
}

# =============================================================================
# COLOR MASK MAP
# =============================================================================

COLOR_MASK_MAP = {
    "radial": RadialGradiantColorMask,
    "vertical": VerticalGradiantColorMask,
    "horizontal": HorizontalGradiantColorMask,
    "diagonal": SquareGradiantColorMask,  # Square acts as diagonal
}

# =============================================================================
# ERROR CORRECTION MAP
# =============================================================================

ERROR_CORRECTION_MAP = {
    "L": qrcode.constants.ERROR_CORRECT_L,
    "M": qrcode.constants.ERROR_CORRECT_M,
    "Q": qrcode.constants.ERROR_CORRECT_Q,
    "H": qrcode.constants.ERROR_CORRECT_H,
}

# =============================================================================
# HANDLER REGISTRY (Built dynamically from handlers.py)
# =============================================================================

def _build_handler_map():
    """Build flat handler map from categorized HANDLERS dict."""
    handler_map = {}
    all_handlers = handlers.get_all_handlers()
    for category, category_handlers in all_handlers.items():
        for name, func in category_handlers.items():
            handler_map[name] = func
    # Add aliases for backwards compatibility
    handler_map["normal"] = lambda text: text
    handler_map["plain_text"] = lambda text: text
    return handler_map

HANDLER_MAP = _build_handler_map()


# =============================================================================
# QR ENGINE CLASS
# =============================================================================

class QREngine:
    """
    Core QR code generation engine.
    
    Takes QRConfig from any pipeline and generates the QR code.
    Supports SVG, PNG with gradients, and logo embedding.
    """
    
    def __init__(self):
        """Initialize the QR engine and ensure directories exist."""
        QR_CODE_SVG_DIR.mkdir(parents=True, exist_ok=True)
        QR_CODE_GRADIENT_DIR.mkdir(parents=True, exist_ok=True)
        QR_CODE_LOGO_DIR.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self._init_db()
    
    def _init_db(self):
        """Initialize analytics database."""
        import sqlite3
        conn = sqlite3.connect(QR_DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qr_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT,
                template_type TEXT,
                output_type TEXT,
                gradient_direction TEXT,
                module_drawer TEXT,
                file_path TEXT
            )
        ''')
        conn.commit()
        conn.close()
        self.logger.info("Analytics DB initialized")
    
    def _log_generation(self, config: QRConfig, file_path: Path):
        """Log QR generation to analytics database."""
        import sqlite3
        conn = sqlite3.connect(QR_DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO qr_analytics (created_at, template_type, output_type, gradient_direction, module_drawer, file_path)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            config.template_type,
            config.output_type,
            config.gradient_direction,
            config.module_drawer,
            str(file_path)
        ))
        conn.commit()
        conn.close()
    
    def _resolve_data(self, config: QRConfig) -> str:
        """Convert config.data dict to QR-encodable string."""
        handler = HANDLER_MAP.get(config.template_type)
        
        if handler is None:
            # Try to find handler dynamically from handlers module
            handler_name = f"format_{config.template_type}"
            handler = getattr(handlers, handler_name, None)
        
        if handler is None:
            raise ValueError(f"Unknown template_type: {config.template_type}")
        
        if config.data:
            if isinstance(config.data, str):
                return handler(config.data)
            return handler(**config.data)
        raise ValueError("config.data cannot be empty")
    
    def _get_output_path(self, config: QRConfig) -> Path:
        """Generate unique output filename."""
        unique_id = uuid.uuid4().hex[:12]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if config.output_type == "svg":
            ext = "svg"
            output_dir = config.output_dir or QR_CODE_SVG_DIR
        else:
            ext = "png"
            if config.gradient_direction:
                output_dir = config.output_dir or QR_CODE_GRADIENT_DIR
            elif config.logo_path:
                output_dir = config.output_dir or QR_CODE_LOGO_DIR
            else:
                output_dir = config.output_dir or QR_CODE_SVG_DIR
        
        filename = f"qr_{config.template_type}_{timestamp}_{unique_id}.{ext}"
        return Path(output_dir) / filename
    
    def _open_file(self, filepath: Path):
        """Cross-platform file opener."""
        filepath_str = str(filepath)
        system = platform.system()
        
        try:
            if system == 'Windows':
                os.startfile(filepath_str)
            elif system == 'Darwin':  # macOS
                subprocess.call(['open', filepath_str])
            else:  # Linux
                subprocess.call(['xdg-open', filepath_str])
            self.logger.info(f"Opened file: {filepath_str}")
        except Exception as e:
            self.logger.error(f"Failed to open file: {e}")
            print(f"[WARN] Could not open file automatically: {e}")
    
    @staticmethod
    def parse_color(color_input: Union[str, Tuple[int, int, int]]) -> Tuple[int, int, int]:
        """
        Parse color from various formats to RGB tuple.
        
        Accepts:
            - RGB tuple: (255, 0, 0)
            - RGB string: "(255, 0, 0)" or "255,0,0"
            - Hex string: "#ff0000" or "ff0000"
            - Named color: "red", "blue", etc.
        
        Returns:
            Tuple[int, int, int]: RGB values
        """
        if isinstance(color_input, tuple):
            return color_input
        
        color_str = str(color_input).strip()
        
        # Try RGB tuple string format: "(255, 0, 0)" or "255,0,0"
        if ',' in color_str:
            cleaned = color_str.replace('(', '').replace(')', '').replace(' ', '')
            parts = cleaned.split(',')
            if len(parts) == 3:
                try:
                    return tuple(int(p) for p in parts)
                except ValueError:
                    pass
        
        # Try hex or named color via PIL
        try:
            return ImageColor.getrgb(color_str)
        except ValueError:
            pass
        
        # Default fallback
        raise ValueError(f"Cannot parse color: {color_input}")
    
    @staticmethod
    def random_color() -> Tuple[int, int, int]:
        """Generate a random RGB color."""
        return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    
    def generate(self, config: QRConfig, open_file: bool = False) -> Path:
        """
        Generate QR code from configuration.
        
        Args:
            config: QRConfig from any pipeline
            open_file: If True, open the generated file
            
        Returns:
            Path to the generated QR code file
        """
        # --- 1. RESOLVE DATA ---
        qr_data = self._resolve_data(config)
        self.logger.info(f"Generating QR: type={config.template_type}, data_len={len(qr_data)}")
        
        # --- 2. CREATE QR OBJECT ---
        error_correction = ERROR_CORRECTION_MAP.get(config.error_correction, qrcode.constants.ERROR_CORRECT_H)
        
        qr = qrcode.QRCode(
            version=config.version,
            error_correction=error_correction,
            box_size=config.box_size,
            border=config.border,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # --- 3. GENERATE IMAGE ---
        if config.output_type == "svg":
            # Pure SVG output
            factory = qrcode.image.svg.SvgPathImage
            img = qrcode.make(qr_data, image_factory=factory)
        else:
            # PNG with optional styling
            module_drawer_class = MODULE_DRAWER_MAP.get(config.module_drawer, RoundedModuleDrawer)
            module_drawer = module_drawer_class()
            
            # Build make_image kwargs
            make_kwargs = {
                "image_factory": StyledPilImage,
                "module_drawer": module_drawer,
            }
            
            # Add logo if present
            if config.logo_path:
                make_kwargs["embeded_image_path"] = str(config.logo_path)
            
            # Add gradient color mask if present
            if config.gradient_direction and config.gradient_colors:
                mask_class = COLOR_MASK_MAP.get(config.gradient_direction)
                if mask_class:
                    colors = config.gradient_colors
                    
                    # Parse colors if needed
                    back_color = self.parse_color(colors[0]) if len(colors) > 0 else (255, 255, 255)
                    center_color = self.parse_color(colors[1]) if len(colors) > 1 else self.random_color()
                    edge_color = self.parse_color(colors[2]) if len(colors) > 2 else self.random_color()
                    
                    # Different masks have different parameter names
                    if config.gradient_direction == "horizontal":
                        make_kwargs["color_mask"] = mask_class(
                            back_color=back_color,
                            left_color=center_color,
                            right_color=edge_color,
                        )
                    elif config.gradient_direction == "vertical":
                        make_kwargs["color_mask"] = mask_class(
                            back_color=back_color,
                            top_color=center_color,
                            bottom_color=edge_color,
                        )
                    else:  # radial, diagonal
                        make_kwargs["color_mask"] = mask_class(
                            back_color=back_color,
                            center_color=center_color,
                            edge_color=edge_color,
                        )
            
            img = qr.make_image(**make_kwargs)
        
        # --- 4. SAVE FILE ---
        output_path = self._get_output_path(config)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(output_path))
        
        self.logger.info(f"QR saved: {output_path}")
        print(f"[OK] QR Code saved: {output_path}")
        
        # --- 5. PRINT ASCII TO TERMINAL ---
        if config.print_qr and config.output_type != "svg":
            qr.print_ascii(invert=True)
        
        # --- 6. LOG TO ANALYTICS ---
        self._log_generation(config, output_path)
        
        # --- 7. OPEN FILE ---
        if open_file:
            self._open_file(output_path)
        
        return output_path
    
    def run_diffusion_subprocess(
        self,
        input_qr_path: Path,
        prompt: str = "",
        model: str = "realistic_digital",
        control_scale: float = 1.6,
        guidance_scale: float = 7.0,
        steps: int = 25,
        seed: Optional[int] = None,
        delete_input: bool = True
    ) -> Optional[Path]:
        """
        Run the QR diffusion engine in a subprocess (image_venv environment).
        
        Args:
            input_qr_path: Path to the base QR code image
            prompt: AI generation prompt
            model: Diffusion model key
            control_scale: ControlNet influence
            guidance_scale: CFG scale
            steps: Diffusion steps
            seed: Random seed
            delete_input: Delete input file after processing (default: True)
        
        Returns:
            Path to the generated diffusion QR, or None on failure
        """
        if not input_qr_path.exists():
            self.logger.error(f"Input QR not found: {input_qr_path}")
            print(f"[ERROR] Input QR not found: {input_qr_path}")
            return None
        
        if not IMAGE_VENV_PYTHON.exists():
            self.logger.error(f"Image venv Python not found: {IMAGE_VENV_PYTHON}")
            print(f"[ERROR] Image venv not found: {IMAGE_VENV_PYTHON}")
            return None
        
        if not QR_DIFFUSION_ENGINE.exists():
            self.logger.error(f"Diffusion engine not found: {QR_DIFFUSION_ENGINE}")
            print(f"[ERROR] Diffusion engine not found: {QR_DIFFUSION_ENGINE}")
            return None
        
        # Ensure output directory exists
        QR_CODE_DIFFUSION_DIR.mkdir(parents=True, exist_ok=True)
        
        # Build command with -u for unbuffered output
        cmd = [
            str(IMAGE_VENV_PYTHON),
            "-u",  # Unbuffered output for real-time display
            str(QR_DIFFUSION_ENGINE),
            "--input", str(input_qr_path),
            "--prompt", prompt,
            "--model", model,
            "--control-scale", str(control_scale),
            "--guidance-scale", str(guidance_scale),
            "--steps", str(steps),
        ]
        
        if seed is not None:
            cmd.extend(["--seed", str(seed)])
        
        print(f"[DIFFUSION] Running subprocess...")
        print(f"   Python: {IMAGE_VENV_PYTHON.name}")
        print(f"   Engine: {QR_DIFFUSION_ENGINE.name}")
        print(f"   Prompt: '{prompt[:40]}...'" if len(prompt) > 40 else f"   Prompt: '{prompt}'")
        
        self.logger.info(f"Running diffusion: {' '.join(cmd[:6])}...")
        
        try:
            # Run subprocess and capture output
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout for long generations
            )
            
            # Print subprocess output
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    print(f"   [WORKER] {line}")
            else:
                print("   [WORKER] (no stdout)")
            
            # Always print stderr for debugging
            if result.stderr:
                print(f"   [WORKER STDERR]:")
                for line in result.stderr.strip().split('\n'):
                    print(f"      {line}")
            
            if result.returncode != 0:
                self.logger.error(f"Diffusion failed with code {result.returncode}")
                print(f"[ERROR] Diffusion subprocess failed with exit code: {result.returncode}")
                return None
            
            # Extract output path from subprocess output
            output_path = None
            for line in result.stdout.split('\n'):
                if line.startswith("OUTPUT_PATH:"):
                    output_path = Path(line.split(":", 1)[1].strip())
                    break
            
            if output_path and output_path.exists():
                print(f"[OK] Diffusion complete: {output_path}")
                self.logger.info(f"Diffusion complete: {output_path}")
                
                # Delete input temp file
                if delete_input:
                    try:
                        input_qr_path.unlink()
                        print(f"[CLEANUP] Deleted temp input: {input_qr_path.name}")
                    except Exception as e:
                        self.logger.warning(f"Failed to delete temp input: {e}")
                
                return output_path
            else:
                print("[ERROR] No output path found in subprocess response")
                return None
        
        except subprocess.TimeoutExpired:
            self.logger.error("Diffusion subprocess timed out")
            print("[ERROR] Diffusion subprocess timed out (>10 minutes)")
            return None
        except Exception as e:
            self.logger.error(f"Subprocess error: {e}")
            print(f"[ERROR] Subprocess error: {e}")
            return None


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def generate(config: QRConfig, open_file: bool = False) -> Path:
    """Convenience function to generate QR without instantiating engine."""
    engine = QREngine()
    return engine.generate(config, open_file=open_file)


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    from apps.qr_studio.pipeline.svg import svg_url
    
    print("=" * 60)
    print("QR Studio Engine Test")
    print("=" * 60)
    
    engine = QREngine()
    
    # Test 1: Simple URL QR
    print("\n📍 Test 1: URL QR Code")
    config = svg_url("https://github.com")
    path = engine.generate(config)
    print(f"   Generated: {path}")
