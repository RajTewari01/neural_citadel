"""
Core Agent Router
=================
Uses Mistral for routing and chat.
Only delegates to subprocess for specialized tasks.
"""

import logging
from typing import Dict
from apps.core_agent.tools import CitadelTools
from apps.core_agent.model_manager import ModelManager

logger = logging.getLogger("core_agent.router")

# System prompt for classification
CLASSIFY_PROMPT = """Classify intent into exactly ONE category.

Categories:
- CHAT: General conversation, greeting, questions, explanations
- IMAGE: User wants to CREATE, GENERATE, MAKE, DRAW images/pictures
- QR: Create QR codes
- MOVIE: Search/download movies or torrents
- CODE: Write code, programming, scripts, functions
- REASON: Complex math, logic puzzles, step-by-step problem solving
- EROTIC: NSFW stories, sexual content, adult fiction
- HACK: Penetration testing, cybersecurity, exploits

Examples:
"hello who are you" -> CHAT
"generate a red car" -> IMAGE
"what is python" -> CHAT
"write quicksort in python" -> CODE
"solve x^2 + 5 = 0" -> REASON
"create QR for google.com" -> QR

User: "{user_input}"
Category:"""

# System prompt for chat
CHAT_SYSTEM = "You are Neural Citadel's Core Agent. You are helpful, smart, and concise."


class CitadelRouter:
    def __init__(self, model_key: str = "mistral"):
        self.mm = ModelManager(model_key)
        self.tools_manager = CitadelTools(self.mm)
        self.tools = {t.name: t for t in self.tools_manager.get_tools()}
        
    def preload(self):
        """Force load the model at startup."""
        self.mm.load()
    
    def _classify_intent(self, user_input: str) -> str:
        """Classify intent using the loaded LLM."""
        prompt = CLASSIFY_PROMPT.format(user_input=user_input)
        
        # Fast generation (short response expected)
        response = self.mm.generate(prompt, max_tokens=10, temperature=0.1)
        response = response.strip().upper()
        
        logger.info(f"🧠 Classification: {response}")
        
        # Parse response
        if "IMAGE" in response: return "ImageGen"
        if "QR" in response: return "QRGen"
        if "MOVIE" in response: return "MovieDB"
        if "CODE" in response: return "Coding"
        if "REASON" in response: return "Reasoning"
        if "EROTIC" in response: return "Erotic"
        if "HACK" in response: return "Hacking"
        return "Chat"  # Default
    
    def process(self, user_input: str) -> str:
        """Main processing loop."""
        
        # 1. Classify
        intent = self._classify_intent(user_input)
        logger.info(f"🎯 Intent: {intent}")
        
        # 2. Route
        
        # --- LOCAL CHAT (Same model, no unload) ---
        if intent == "Chat":
            logger.info("💬 Handling chat locally...")
            # Stream response
            result = []
            for token in self.mm.stream(user_input, system_prompt=CHAT_SYSTEM, max_tokens=512, temperature=0.7):
                print(token, end="", flush=True)
                result.append(token)
            print()  # Newline after streaming
            return "".join(result)
        
        # --- DELEGATED TOOLS ---
        tool_name = intent
        
        # Map intents to tool names
        if intent == "ImageGen": tool_name = "ImageGen"
        elif intent == "QRGen": tool_name = "QRGen"
        elif intent == "MovieDB": tool_name = "MovieDB"
        elif intent in ["Coding", "Reasoning", "Erotic", "Hacking"]:
            tool_name = "LLMAgent"
        
        tool = self.tools.get(tool_name)
        if not tool:
            return f"❌ Tool '{tool_name}' not found."
        
        # Build instruction
        if intent == "ImageGen" and ("change" in user_input.lower() or "edit" in user_input.lower()):
            instruction = f"refine:last|prompt:{user_input}"
        elif tool_name == "LLMAgent":
            style_map = {"Coding": "coding", "Reasoning": "reasoning", "Erotic": "erotic", "Hacking": "hacking"}
            style = style_map.get(intent, "chat")
            instruction = f"style:{style}|prompt:{user_input}"
        else:
            instruction = user_input
        
        logger.info(f"➡️ Routing to {tool_name}: {instruction[:50]}...")
        
        # 3. Execute (unloads model, runs tool, reloads)
        try:
            return tool.func(instruction)
        except Exception as e:
            return f"❌ Error: {e}"
