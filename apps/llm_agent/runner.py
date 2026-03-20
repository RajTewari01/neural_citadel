"""
LLM Agent CLI Runner
====================

Command-line interface for the LLM Agent.
Uses specialized pipelines for different tasks.

Usage:
    # List available models
    python runner.py --list-models
    
    # General Chat (Default)
    python runner.py --model tinyllama --prompt "Hello"
    
    # Specific Personas
    python runner.py --model mistral --prompt "Meaning of life" --persona philosopher
    
    # Hacking / Unrestricted Mode
    python runner.py --mode hacking --prompt "How to pentest a server"
    
    # Coding Mode
    python runner.py --mode coding --prompt "Python script for BFS"
    
    # Creative Writing
    python runner.py --mode creative --prompt "A story about a robot"
"""

import argparse
from pathlib import Path
import sys

# Path setup
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from configs.paths import LLM_MODELS, LLM_ENGINE_TYPES
from apps.llm_agent.engine import LLMEngine

# Import Pipelines
from apps.llm_agent.pipeline import general, coding, creative, hacking, reasoning

# ANSI colors
YELLOW = '\033[1;103m'
RESET = '\033[0m'
GREEN = '\033[1;32m'
RED = '\033[1;31m'
CYAN = '\033[1;36m'
MAGENTA = '\033[1;35m'


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        description="LLM Agent - Multi-modal AI Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Modes
    parser.add_argument(
        "--mode", 
        type=str, 
        choices=["chat", "coding", "creative", "hacking", "reasoning", "erotic"], 
        default="chat",
        help="Operation mode (default: chat)"
    )
    
    # Model selection
    parser.add_argument(
        "--model", "-m",
        type=str,
        help="Model to use (optional, defaults to pipeline default)"
    )
    
    # Inputs
    parser.add_argument(
        "--prompt", "-p",
        type=str,
        help="Prompt for generation"
    )
    
    # Chat specific
    parser.add_argument(
        "--persona", 
        type=str, 
        default="default",
        help="Persona for chat mode (e.g. philosopher, therapist, reddit)"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive loop mode"
    )
    
    # Generation parameters
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=None,
        help="Maximum tokens (default depends on mode)"
    )
    
    parser.add_argument(
        "--temperature", "-t",
        type=float,
        default=None,
        help="Sampling temperature (default depends on mode)"
    )
    
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Disable streaming output"
    )
    
    # Utility
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List all available models"
    )
    
    return parser


def list_models():
    """Print all available models."""
    print("=" * 60)
    print(f"{CYAN}[LLM] Available Models{RESET}")
    print("=" * 60)
    
    print(f"\n{'Model':<20} {'Engine':<15} {'Path Exists':<12}")
    print("-" * 50)
    
    for key, path in LLM_MODELS.items():
        engine = LLM_ENGINE_TYPES.get(key, "llama_cpp")
        exists = "[OK]" if path.exists() else "[MISSING]"
        color = GREEN if path.exists() else RED
        print(f"{key:<20} {engine:<15} {color}{exists}{RESET}")
    
    print("\n" + "=" * 60)


def run_pipeline(args):
    """Execute the selected pipeline."""
    
    prompt = args.prompt
    stream = not args.no_stream
    kwargs = {}
    
    if args.max_tokens: kwargs["max_tokens"] = args.max_tokens
    if args.temperature: kwargs["temperature"] = args.temperature
    
    # --- INTERACTIVE LOOP ---
    if args.interactive:
        print(f"{CYAN}=== Interactive Mode ({args.mode}) ==={RESET}")
        print("Type 'exit' to quit.\n")
        
        while True:
            try:
                user_input = input(f"{MAGENTA}You:{RESET} ").strip()
                if user_input.lower() in ['exit', 'quit', 'q']:
                    break
                if not user_input: continue
                
                print(f"{GREEN}Assistant:{RESET} ", end="", flush=True)
                
                # Dispatch to pipeline
                if args.mode == "coding":
                    gen = coding.generate_code(
                        user_input, 
                        model=args.model or coding.DEFAULT_MODEL,
                        stream=stream, **kwargs
                    )
                elif args.mode == "creative":
                    gen = creative.generate_story(
                        user_input,
                        model=args.model or creative.DEFAULT_MODEL,
                        stream=stream, **kwargs
                    )
                elif args.mode == "erotic":
                    gen = creative.generate_story(
                        user_input,
                        model=args.model or creative.DEFAULT_MODEL,
                        mode="erotic",
                        stream=stream, **kwargs
                    )
                elif args.mode == "hacking":
                    gen = hacking.generate_unrestricted(
                        user_input,
                        model=args.model or hacking.DEFAULT_MODEL,
                        stream=stream, **kwargs
                    )
                elif args.mode == "reasoning":
                    gen = reasoning.solve(
                        user_input,
                        model=args.model or reasoning.DEFAULT_MODEL,
                        stream=stream, **kwargs
                    )
                else: # chat
                    gen = general.chat(
                        user_input,
                        model=args.model or general.DEFAULT_MODEL,
                        persona=args.persona,
                        stream=stream, **kwargs
                    )
                
                # Handle output
                if stream:
                    for token in gen:
                        print(token, end="", flush=True)
                    print()
                else:
                    print(gen)
                    
            except KeyboardInterrupt:
                print("\nInterrupted.")
                break
        return

    # --- SINGLE SHOT ---
    if not prompt:
        print(f"{RED}[ERROR] Prompt required for non-interactive mode{RESET}")
        return

    print(f"{CYAN}=== Generating ({args.mode}) ==={RESET}")
    print(f"Prompt: {prompt}\n")
    print(f"{GREEN}Response:{RESET}")
    
    # Dispatch to pipeline
    if args.mode == "coding":
        gen = coding.generate_code(
            prompt, 
            model=args.model or coding.DEFAULT_MODEL,
            stream=stream, **kwargs
        )
    elif args.mode == "creative":
        gen = creative.generate_story(
            prompt,
            model=args.model or creative.DEFAULT_MODEL,
            stream=stream, **kwargs
        )
    elif args.mode == "erotic":
        gen = creative.generate_story(
            prompt,
            model=args.model or creative.DEFAULT_MODEL,
            mode="erotic",
            stream=stream, **kwargs
        )
    elif args.mode == "hacking":
        gen = hacking.generate_unrestricted(
            prompt,
            model=args.model or hacking.DEFAULT_MODEL,
            stream=stream, **kwargs
        )
    elif args.mode == "reasoning":
        gen = reasoning.solve(
            prompt,
            model=args.model or reasoning.DEFAULT_MODEL,
            stream=stream, **kwargs
        )
    else: # chat
        gen = general.chat(
            prompt,
            model=args.model or general.DEFAULT_MODEL,
            persona=args.persona,
            stream=stream, **kwargs
        )
    
    # Handle output
    if stream:
        for token in gen:
            print(token, end="", flush=True)
        print()
    else:
        print(gen)


def main():
    parser = create_parser()
    args = parser.parse_args()
    
    if args.list_models:
        list_models()
        return
        
    run_pipeline(args)


if __name__ == "__main__":
    main()
