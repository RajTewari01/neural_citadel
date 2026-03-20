"""
Core Agent Tools
================
Connects the Core Agent to other Neural Citadel apps.
Handles virtual environment switching and complex workflows (like image refinement).
"""

import subprocess
import logging
from pathlib import Path
from typing import Dict, Optional, Any
from langchain_core.tools import Tool

from configs.paths import (
    ROOT_DIR, 
    LLM_AGENT_VENV,    # Point to coreagentvenv (d:\neural_citadel\venvs\env\coreagentvenv)
    IMAGE_SURGEON_VENV # Point to enhanced (d:\neural_citadel\venvs\env\enhanced)
)
from apps.core_agent.model_manager import ModelManager

logger = logging.getLogger("core_agent.tools")

# Define explicitly verified VENV paths
IMAGE_GEN_VENV = ROOT_DIR / "venvs" / "env" / "image_venv"
MOVIE_VENV = ROOT_DIR / "venvs" / "env" / "movie_venv"
QR_VENV = LLM_AGENT_VENV # QR Studio shares core env usually

class CitadelTools:
    def __init__(self, model_manager: ModelManager):
        self.mm = model_manager
        
    def _run_subprocess(self, venv_path: Path, script_path: str, args: list) -> str:
        """Run a script in a specific virtual environment with real-time streaming."""
        python_exe = venv_path / "Scripts" / "python.exe"
            
        if not python_exe.exists():
            return f"❌ Error: Python not found at {python_exe}"
            
        cmd = [str(python_exe), script_path] + args
        logger.info(f"🚀 Executing in {venv_path.name}: {' '.join(cmd)}")
        
        try:
            # We wrap this in model manager to ensure VRAM is free
            def execution_logic():
                # Use Popen to stream output
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, # Merge stderr
                    text=True,
                    cwd=str(ROOT_DIR),
                    encoding='utf-8',
                    errors='replace',
                    bufsize=1 # Line buffered
                )
                
                output_lines = []
                # Stream output
                for line in process.stdout:
                    print(line, end='', flush=True) # Show to user immediately
                    output_lines.append(line)
                    
                process.wait()
                return process.returncode, "".join(output_lines)

            # Execute via ModelManager
            return_code, full_output = self.mm.run_external_tool(execution_logic)
            
            if return_code == 0:
                return full_output.strip()
            else:
                return f"❌ Error (Exit Code {return_code}):\n{full_output}"
                
        except Exception as e:
            return f"❌ Execution failed: {e}"

    def generate_image(self, instruction: str) -> str:
        """
        Generate or Refine Images.
        Syntax: "style:car|prompt:red car" OR "refine:last|prompt:blue car"
        """
        params = self._parse_instruction(instruction)
        prompt = params.get("prompt", instruction)
        
        # Handle Refinement (fetched from DB/Filesystem -> Canny -> Generate)
        if params.get("refine") == "last" or "change" in instruction.lower():
            logger.info("♻️ Refinement request detected. Delegating to update script...")
            
            # Call our helper script inside image_venv
            return self._run_subprocess(
                IMAGE_GEN_VENV,
                "apps/image_gen/refine.py", 
                ["--prompt", prompt, "--style", params.get("style", "general")]
            )
            
        else:
            # Standard Generation
            style = params.get("style", "general")
            return self._run_subprocess(
                IMAGE_GEN_VENV,
                "apps/image_gen/runner.py",
                ["--prompt", prompt, "--style", style]
            )

    def generate_qr(self, instruction: str) -> str:
        """Generate QR Code."""
        params = self._parse_instruction(instruction)
        data = params.get("data", params.get("prompt", instruction))
        
        return self._run_subprocess(
            QR_VENV, 
            "apps/qr_studio/runner.py",
            ["--data", data, "--output", "assets/generated/qr/latest.png"]
        )

    def chat_llm(self, instruction: str) -> str:
        """Delegate to specialized LLM agents (Coding, Erotic, Reasoning)."""
        params = self._parse_instruction(instruction)
        prompt = params.get("prompt", instruction)
        style = params.get("style", "chat")
        
        mode_map = {
            "chat": "chat",
            "code": "coding",
            "hacking": "hacking",
            "erotic": "erotic",
            "reasoning": "reasoning"
        }
        mode = mode_map.get(style, "chat")
        
        return self._run_subprocess(
            LLM_AGENT_VENV,
            "apps/llm_agent/runner.py",
            ["--mode", mode, "--prompt", prompt]
        )

    def search_movies(self, instruction: str) -> str:
        """Search/Download movies."""
        return self._run_subprocess(
            MOVIE_VENV,
            "apps/movie_downloader/runner.py",
            ["--search", instruction]
        )

    def _parse_instruction(self, instruction: str) -> Dict[str, str]:
        """Parse 'key:value|key2:value2' string."""
        if "|" in instruction and ":" in instruction:
            params = {}
            for part in instruction.split("|"):
                if ":" in part:
                    k, v = part.split(":", 1)
                    params[k.strip()] = v.strip()
            return params
        return {"prompt": instruction}

    def get_tools(self):
        return [
            Tool(name="ImageGen", func=self.generate_image, description="Generate images. Use 'refine:last' or 'change dress' to edit previous image."),
            Tool(name="QRGen", func=self.generate_qr, description="Generate QR codes."),
            Tool(name="LLMAgent", func=self.chat_llm, description="Complex reasoning, coding, or erotic/hacking chat."),
            Tool(name="MovieDB", func=self.search_movies, description="Search for movies.")
        ]
