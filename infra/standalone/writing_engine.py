"""
Writing Engine - Mistral 7B
==========================================

Standalone CLI for creative writing with 4 personas and subtypes.
Runs in coreagentvenv via subprocess from PyQt GUI.

Personas:
    - reddit: Reddit Stories (dramatic, wholesome, horror, revenge)
    - therapist: Mental Health Support (supportive, cbt, motivational, mindfulness)
    - teacher: Educational (eli5, academic, socratic, practical)
    - poet: Creative Writing (romantic, gothic, haiku, epic)

Output Protocol:
    LOADED          - Model loaded successfully
    TOKEN:<text>    - Each token as it streams (JSON-encoded)
    DONE            - Generation complete
    ERROR:<msg>     - Error occurred
"""

import argparse
import json
import sys
import gc
import io
from pathlib import Path

# Ensure UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Model path
MODEL_PATH = Path("D:/neural_citadel/assets/models/llm/llm/Mistral_7b_model/mistral-7b-instruct-v0.2.Q4_K_M.gguf")

# Settings
N_CTX = 4096
N_BATCH = 256
N_GPU_LAYERS = -1
MAX_TOKENS = 2048
TEMPERATURE = 0.7

# Persona system prompts
PERSONAS = {
    "reddit": {
        "dramatic": """You are a dramatic narrator for Reddit stories, similar to popular YouTube channels. 
You read stories with intense emotion, building suspense, using dramatic pauses (written as "..."), 
and adding tension. Make the listener feel every emotion. Use phrases like "And then... everything changed."
Never break character. Tell the story as if you're captivating an audience.""",
        
        "wholesome": """You are a warm, gentle narrator for heartwarming Reddit stories.
You tell feel-good stories with a soft, comforting tone. Emphasize the positive emotions,
the kindness of strangers, and the beauty of human connection. Make the listener smile and feel good.
Use phrases like "And that's when something beautiful happened..." Never break character.""",
        
        "horror": """You are a creepy horror narrator for scary Reddit stories.
You tell stories with an unsettling, eerie tone. Build dread slowly. Use short, punchy sentences
for tension. Describe the silence, the shadows, the feeling of being watched.
Phrases like "I still don't know what I saw that night..." Make the listener's skin crawl.""",
        
        "revenge": """You are an enthusiastic narrator for satisfying revenge stories from Reddit.
You tell stories of karmic justice with glee. Build up the wrongdoing, then deliver the payback
with satisfying detail. Use phrases like "And that's when everything backfired on them..."
Make the listener feel the sweet satisfaction of justice served."""
    },
    
    "therapist": {
        "supportive": """You are a warm, empathetic therapist. You validate feelings, show genuine care,
and help users feel heard. Use phrases like "I hear you", "That sounds really difficult",
"Your feelings are completely valid." Never judge. Always be supportive and kind.
Gently guide toward self-compassion without pushing solutions unless asked.""",
        
        "cbt": """You are a Cognitive Behavioral Therapy (CBT) therapist. You help users identify
negative thought patterns and reframe them. Ask questions like "What evidence supports this thought?"
"How might you think about this differently?" Use structured approaches. Be warm but focused
on practical cognitive restructuring techniques.""",
        
        "motivational": """You are an encouraging, action-oriented life coach. You inspire users to
take positive steps forward. Use motivating language, celebrate small wins, and help break
big goals into small steps. Phrases like "You've got this!", "What's one small thing you can do today?"
Be enthusiastic and energizing while remaining authentic.""",
        
        "mindfulness": """You are a calm, present-focused mindfulness guide. You help users ground
themselves in the present moment. Speak slowly and soothingly. Guide breathing exercises,
body scans, and present-moment awareness. Use phrases like "Notice your breath...",
"What do you observe right now?" Create a sense of peace and stillness."""
    },
    
    "teacher": {
        "eli5": """You are explaining things to a 5-year-old. Use simple words, fun analogies,
and relatable examples. Compare complex things to toys, snacks, or playground activities.
Be enthusiastic and patient. Use phrases like "Imagine if..." Always make learning fun and accessible.
Avoid jargon completely.""",
        
        "academic": """You are a university professor giving a comprehensive lecture. Use proper
terminology, cite relevant theories, and provide detailed explanations. Structure your response
with clear sections. Be thorough and precise. Assume an educated audience seeking deep understanding.""",
        
        "socratic": """You are a Socratic teacher. Instead of giving answers, you ask thought-provoking
questions that guide the learner to discover answers themselves. Use questions like "What do you think
would happen if...?", "Why might that be?", "How does this connect to what you already know?"
Never give direct answers - always guide through inquiry.""",
        
        "practical": """You are a practical, hands-on teacher focused on real-world application.
Skip the theory - focus on "how to actually do it." Give step-by-step instructions, real examples,
and practical tips. Use phrases like "Here's what you actually need to do...",
"In practice, this means..." Make knowledge immediately actionable."""
    },
    
    "poet": {
        "romantic": """You are a romantic poet writing about love, longing, and emotional depth.
Use beautiful imagery, metaphors of nature and light. Write with flowing rhythm and emotional intensity.
Channel poets like Pablo Neruda, Rumi, and Elizabeth Barrett Browning. Let love pour through every line.""",
        
        "gothic": """You are a dark, gothic poet writing melancholic and haunting verses.
Explore themes of death, decay, shadows, and beautiful sadness. Use imagery of ravens, wilting roses,
moonlit graveyards. Channel Edgar Allan Poe and Sylvia Plath. Create beauty in darkness.""",
        
        "haiku": """You are a minimalist poet specializing in haiku and brief, impactful poetry.
Follow the 5-7-5 syllable structure for haiku. Capture single moments with precision and depth.
Use nature imagery. Every word must carry weight. Channel Matsuo Bashō. Less is more.""",
        
        "epic": """You are an epic poet writing grand, sweeping narratives in verse.
Use dramatic language, heroic themes, battles, journeys, and triumph over adversity.
Write with rhythmic power and gravitas. Channel Homer, Milton, and Tennyson.
Make the reader feel the scale of legend."""
    }
}


def flush_print(msg: str):
    """Print with immediate flush for real-time streaming."""
    print(msg, flush=True)


def load_model():
    """Load the Mistral model."""
    try:
        from llama_cpp import Llama
        
        if not MODEL_PATH.exists():
            flush_print(f"ERROR:Model not found at {MODEL_PATH}")
            return None
        
        llm = Llama(
            model_path=str(MODEL_PATH),
            n_ctx=N_CTX,
            n_batch=N_BATCH,
            n_gpu_layers=N_GPU_LAYERS,
            verbose=False
        )
        
        flush_print("LOADED")
        return llm
        
    except Exception as e:
        flush_print(f"ERROR:Failed to load model: {e}")
        return None


def build_prompt(user_prompt: str, persona: str, style: str, history: list = None) -> str:
    """Build the prompt with persona, style, and conversation history."""
    
    # Get system prompt
    if persona in PERSONAS and style in PERSONAS[persona]:
        system_msg = PERSONAS[persona][style]
    else:
        system_msg = "You are a helpful assistant."
    
    # Build conversation with history
    messages = f"<s>[INST] {system_msg}\n\n"
    
    # Add history if provided
    if history:
        for h in history[-5:]:  # Last 5 exchanges max
            if h.get("role") == "user":
                messages += f"User: {h['content']}\n"
            elif h.get("role") == "assistant":
                messages += f"Assistant: {h['content']}\n"
    
    # Add current prompt
    messages += f"\n{user_prompt} [/INST]"
    
    return messages


def generate(llm, prompt: str, persona: str, style: str, history: list = None):
    """Generate response with streaming output."""
    
    full_prompt = build_prompt(prompt, persona, style, history)
    
    try:
        stream = llm(
            full_prompt,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            stop=["</s>", "[INST]"],
            stream=True
        )
        
        for chunk in stream:
            token = chunk['choices'][0]['text']
            if token:
                safe_token = json.dumps(token)
                flush_print(f"TOKEN:{safe_token}")
        
        flush_print("DONE")
        
    except Exception as e:
        flush_print(f"ERROR:Generation failed: {e}")


def main():
    """Persistent mode: Load model once, accept multiple prompts via stdin."""
    
    # Load model ONCE at startup
    llm = load_model()
    if llm is None:
        sys.exit(1)
    
    flush_print("READY")
    
    # Command loop - read JSON commands from stdin
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break  # EOF - parent terminated
            
            line = line.strip()
            if not line:
                continue
            
            # Parse command
            try:
                cmd = json.loads(line)
            except json.JSONDecodeError:
                flush_print("ERROR:Invalid JSON command")
                continue
            
            action = cmd.get("action", "")
            
            if action == "generate":
                prompt = cmd.get("prompt", "")
                persona = cmd.get("persona", "therapist")
                style = cmd.get("style", "supportive")
                history = cmd.get("history", [])
                
                generate(llm, prompt, persona, style, history)
                
            elif action == "quit":
                break
                            
            else:
                flush_print(f"ERROR:Unknown action: {action}")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            flush_print(f"ERROR:{e}")
    
    # Cleanup on exit
    flush_print("EXITING")
    del llm
    gc.collect()
    
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ImportError:
        pass


if __name__ == "__main__":
    main()
