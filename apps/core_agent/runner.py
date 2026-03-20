"""
Neural Citadel Core Agent - CLI Runner
======================================
Entry point for the orchestration layer.
"""

import argparse
import logging
import sys
from pathlib import Path

# Path setup
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from apps.core_agent.router import CitadelRouter

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("runner")

BANNER = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║                NEURAL CITADEL CORE AGENT                      ║
    ║               Orchestration & Intelligence                    ║
    ║                                                               ║
    ║           Created by Biswadeep Tewari (Neural Citadel)        ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
"""


def main():
    parser = argparse.ArgumentParser(description="Neural Citadel Core Agent")
    parser.add_argument("--prompt", type=str, help="Single prompt to process")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive chat mode")
    parser.add_argument("--model", type=str, default="mistral", help="Model to use (default: mistral)")
    args = parser.parse_args()
    
    print(BANNER)
    
    logger.info("🚀 Starting Neural Citadel Core Agent...")
    logger.info("🧠 Initializing Router...")
    
    router = CitadelRouter(model_key=args.model)
    router.preload()
    
    logger.info("✅ Router initialized!")
    
    # Single prompt mode
    if args.prompt:
        print(f"\n👤 User: {args.prompt}")
        print("🤖 Agent: ", end="", flush=True)
        response = router.process(args.prompt)
        # Response already printed by streaming in router
        return
    
    # Interactive mode (default if no prompt)
    if args.interactive or not args.prompt:
        print("\n" + "=" * 60)
        print("🤖 Neural Citadel Interactive Mode")
        print("=" * 60)
        print("Type 'quit', 'exit', or 'q' to stop\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                print("🤖 Agent: ", end="", flush=True)
                response = router.process(user_input)
                # Response already printed by streaming in router for chat
                # For tool responses, print here
                if response and not response.startswith(""):  # Check if not already streamed
                    print()  # Just add newline
                print()
                
            except KeyboardInterrupt:
                print("\n👋 Exiting...")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
