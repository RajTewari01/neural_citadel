"""
Neural Citadel Newspaper Translator
====================================
Translates articles using either:
- OFFLINE: Local NLLB-200 model (slower, ~47s, no internet required)
- ONLINE: Google Translate via deep-translator (fast, requires internet)

Usage:
    python translator.py --input articles.json --lang Hindi --mode offline
    python translator.py --input articles.json --lang Hindi --mode online
"""

import argparse
import json
import sys
import os
from pathlib import Path

# ==============================================================================
# LANGUAGE MAPPINGS
# ==============================================================================

# NLLB language codes (for offline mode)
SCRIPT_DIR = Path(__file__).parent
LANGUAGES_FILE = SCRIPT_DIR / "languages.json"

def load_languages():
    """Load language mappings from JSON file."""
    if LANGUAGES_FILE.exists():
        with open(LANGUAGES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Filter out comment keys
            return {k: v for k, v in data.items() if not k.startswith('_')}
    return {"English": "eng_Latn", "Hindi": "hin_Deva"}

NLLB_LANGUAGES = load_languages()

# Google Translate language codes (for online mode)
GOOGLE_LANG_CODES = {
    "English": "en", "Hindi": "hi", "Bengali": "bn", "Tamil": "ta",
    "Telugu": "te", "Marathi": "mr", "Gujarati": "gu", "Kannada": "kn",
    "Malayalam": "ml", "Punjabi": "pa", "Urdu": "ur", "Odia": "or",
    "Assamese": "as", "Nepali": "ne", "Sanskrit": "sa",
    "Spanish": "es", "French": "fr", "German": "de", "Portuguese": "pt",
    "Italian": "it", "Dutch": "nl", "Polish": "pl", "Russian": "ru",
    "Ukrainian": "uk", "Greek": "el", "Turkish": "tr", "Japanese": "ja",
    "Chinese": "zh-CN",  # Shorthand for Simplified
    "Chinese (Simplified)": "zh-CN", "Chinese (Traditional)": "zh-TW",
    "Korean": "ko", "Thai": "th", "Vietnamese": "vi", "Indonesian": "id",
    "Malay": "ms", "Arabic": "ar", "Hebrew": "he", "Persian": "fa",
    "Swahili": "sw", "Filipino": "tl"
}

# ==============================================================================
# ONLINE TRANSLATION (Google Translate)
# ==============================================================================

def translate_online(articles: list, target_lang: str) -> list:
    """Translate using Google Translate (fast, requires internet)."""
    from deep_translator import GoogleTranslator
    
    # Get Google language code
    lang_code = GOOGLE_LANG_CODES.get(target_lang)
    if not lang_code:
        print(f"[ERROR] Language '{target_lang}' not supported for online mode")
        return articles
    
    print(f"[Translator] ONLINE mode - Using Google Translate ({lang_code})")
    
    translator = GoogleTranslator(source='auto', target=lang_code)
    translated = []
    
    for i, article in enumerate(articles):
        try:
            new_article = article.copy()
            
            # Translate title
            if article.get('title'):
                new_article['title'] = translator.translate(article['title'])
            
            # Translate content (Google has 5000 char limit, so chunk if needed)
            if article.get('content'):
                content = article['content']
                if len(content) > 4500:
                    # Chunk it
                    chunks = [content[i:i+4500] for i in range(0, len(content), 4500)]
                    translated_chunks = [translator.translate(chunk) for chunk in chunks]
                    new_article['content'] = ''.join(translated_chunks)
                else:
                    new_article['content'] = translator.translate(content)
            
            # Translate category
            if article.get('category'):
                new_article['category'] = translator.translate(article['category'])
            
            translated.append(new_article)
            
            if (i + 1) % 10 == 0:
                print(f"   [+] Translated {i+1}/{len(articles)} articles")
                
        except Exception as e:
            print(f"   [!] Error translating article {i}: {e}")
            translated.append(article)
    
    return translated

# ==============================================================================
# OFFLINE TRANSLATION (NLLB Model)
# ==============================================================================

def translate_offline(articles: list, target_lang: str) -> list:
    """Translate using local NLLB-200 model (slow, no internet needed)."""
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
    import torch
    
    # Model path
    MODEL_PATH = Path(r"D:\neural_citadel\assets\models\language_translation\nllb-200-distilled-600M")
    
    # Get NLLB language code
    nllb_code = NLLB_LANGUAGES.get(target_lang)
    if not nllb_code:
        print(f"[ERROR] Language '{target_lang}' not found in languages.json")
        return articles
    
    print(f"[Translator] OFFLINE mode - Using NLLB Model ({nllb_code})")
    print(f"             Model Path: {MODEL_PATH}")
    
    # Load model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[Translator] Using Device: {device.upper()}")
    
    tokenizer = AutoTokenizer.from_pretrained(str(MODEL_PATH))
    model = AutoModelForSeq2SeqLM.from_pretrained(str(MODEL_PATH))
    
    translator = pipeline(
        'translation',
        model=model,
        tokenizer=tokenizer,
        src_lang='eng_Latn',
        tgt_lang=nllb_code,
        max_length=512,
        device=0 if device == "cuda" else -1
    )
    
    translated = []
    for i, article in enumerate(articles):
        try:
            new_article = article.copy()
            
            # Translate title
            if article.get('title'):
                result = translator(article['title'])
                new_article['title'] = result[0]['translation_text']
            
            # Translate content (truncate if too long for model)
            if article.get('content'):
                content = article['content'][:2000]  # NLLB has token limits
                result = translator(content)
                new_article['content'] = result[0]['translation_text']
            
            # Translate category
            if article.get('category'):
                result = translator(article['category'])
                new_article['category'] = result[0]['translation_text']
            
            translated.append(new_article)
            
        except Exception as e:
            print(f"   [!] Error translating article {i}: {e}")
            translated.append(article)
    
    return translated

# ==============================================================================
# MAIN
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="Translate newspaper articles")
    parser.add_argument("--input", required=True, help="Path to JSON file with articles")
    parser.add_argument("--lang", required=True, help="Target language (e.g., Hindi, Bengali)")
    parser.add_argument("--mode", default="online", choices=["online", "offline"],
                        help="Translation mode: 'online' (Google) or 'offline' (NLLB)")
    
    args = parser.parse_args()
    
    # Load articles
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[ERROR] Input file not found: {input_path}")
        sys.exit(1)
    
    with open(input_path, 'r', encoding='utf-8') as f:
        articles = json.load(f)
    
    print(f"[Translator] Translating {len(articles)} articles to {args.lang}...")
    
    import time
    start = time.time()
    
    # Translate based on mode
    if args.mode == "online":
        translated = translate_online(articles, args.lang)
    else:
        translated = translate_offline(articles, args.lang)
    
    elapsed = time.time() - start
    print(f"[Translator] Success! Processed in {elapsed:.2f}s")
    
    # Save back to same file
    with open(input_path, 'w', encoding='utf-8') as f:
        json.dump(translated, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
