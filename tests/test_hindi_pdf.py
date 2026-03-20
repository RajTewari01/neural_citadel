"""
Simple test: Translate 20 words to Hindi and create a PDF.
Uses: CoreAgentVenv for translation, GlobalVenv for PDF (reportlab).
"""
import subprocess
import json
import os
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent
CORE_PYTHON = r"D:\neural_citadel\venvs\env\coreagentvenv\Scripts\python.exe"
OUTPUT_PDF = PROJECT_ROOT / "test_hindi_output.pdf"
TEMP_JSON = PROJECT_ROOT / "test_temp.json"

def translate_text(english_text: str, target_lang: str = "Hindi") -> str:
    """Call translator subprocess to translate text."""
    translator_script = PROJECT_ROOT / "apps/newspaper_publisher/language/translator.py"
    
    # Create temp article structure
    articles = [{"title": english_text, "content": "", "category": "TEST"}]
    
    with open(TEMP_JSON, 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False)
    
    cmd = [CORE_PYTHON, str(translator_script), "--input", str(TEMP_JSON), "--lang", target_lang]
    print(f"[1] Translating to {target_lang}...")
    
    try:
        subprocess.run(cmd, check=True)
        with open(TEMP_JSON, 'r', encoding='utf-8') as f:
            result = json.load(f)
        return result[0]['title']
    finally:
        if os.path.exists(TEMP_JSON):
            os.remove(TEMP_JSON)

def create_hindi_pdf(hindi_text: str, output_path: Path):
    """Create a simple PDF with Hindi text using reportlab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    
    # Register a Unicode font that supports Hindi
    font_paths = [
        r"C:\Windows\Fonts\Nirmala.ttf",  # Windows Nirmala UI (supports Hindi)
        r"C:\Windows\Fonts\mangal.ttf",   # Windows Mangal font
    ]
    
    font_registered = False
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('HindiFont', font_path))
                font_registered = True
                print(f"[2] Using font: {font_path}")
                break
            except:
                continue
    
    if not font_registered:
        print("[WARN] No Hindi font found!")
        return
    
    # Create PDF
    c = canvas.Canvas(str(output_path), pagesize=A4)
    width, height = A4
    
    c.setFont('HindiFont', 24)
    c.drawString(50, height - 100, "Translation Test")
    
    c.setFont('HindiFont', 16)
    c.drawString(50, height - 150, f"Hindi:")
    c.drawString(50, height - 180, hindi_text[:80])
    if len(hindi_text) > 80:
        c.drawString(50, height - 210, hindi_text[80:160])
    
    c.save()
    print(f"[3] PDF saved: {output_path}")

def main():
    english_text = "Artificial intelligence is transforming how we live and work every day."
    print(f"\nOriginal English: {english_text}\n")
    
    # Step 1: Translate
    hindi_text = translate_text(english_text, "Hindi")
    
    # Print Hindi (may fail on Windows console, but that's OK)
    try:
        print(f"\nTranslated Hindi: {hindi_text}\n")
    except UnicodeEncodeError:
        print(f"\n[Hindi translation complete - {len(hindi_text)} chars, cannot display in console]\n")
    
    # Step 2: Create PDF (this is the real test)
    create_hindi_pdf(hindi_text, OUTPUT_PDF)
    print(f"\n[DONE] Check: {OUTPUT_PDF}")

if __name__ == "__main__":
    main()
