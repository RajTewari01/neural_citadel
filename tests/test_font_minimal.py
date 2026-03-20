"""
Minimal test for Bengali font rendering in ReportLab.
This bypasses all magazine logic to isolate the font issue.
"""
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# Test Bengali Text
BENGALI_TEXT = "সেনেট একটি বিল পাস করেছে"  # "Senate passed a bill"
HINDI_TEXT = "सीनेट ने एक बिल पारित किया"  # Same in Hindi

# Font paths
FONT_DIR = r"D:\neural_citadel\assets\models\ttf"
OUTPUT_PDF = r"D:\neural_citadel\test_font_minimal.pdf"

def main():
    print("=== Minimal Font Test ===")
    
    # 1. Register fonts
    fonts_to_test = [
        ("NotoSansBengali", os.path.join(FONT_DIR, "NotoSansBengali-Regular.ttf")),
        ("NotoSansDevanagari", os.path.join(FONT_DIR, "NotoSansDevanagari-Regular.ttf")),
    ]
    
    registered = []
    for name, path in fonts_to_test:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                registered.append(name)
                print(f"[OK] Registered: {name}")
            except Exception as e:
                print(f"[FAIL] Could not register {name}: {e}")
        else:
            print(f"[MISSING] Font file not found: {path}")
    
    if not registered:
        print("[ERROR] No fonts registered. Cannot continue.")
        return
    
    # 2. Create PDF
    print(f"\nCreating PDF: {OUTPUT_PDF}")
    c = canvas.Canvas(OUTPUT_PDF, pagesize=A4)
    width, height = A4
    
    y = height - 100
    
    # Header
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, y, "Font Rendering Test")
    y -= 50
    
    # Bengali Test
    if "NotoSansBengali" in registered:
        c.setFont("Helvetica", 12)
        c.drawString(50, y, "Bengali (NotoSansBengali):")
        y -= 25
        c.setFont("NotoSansBengali", 20)
        c.drawString(50, y, BENGALI_TEXT)
        y -= 50
    
    # Hindi Test
    if "NotoSansDevanagari" in registered:
        c.setFont("Helvetica", 12)
        c.drawString(50, y, "Hindi (NotoSansDevanagari):")
        y -= 25
        c.setFont("NotoSansDevanagari", 20)
        c.drawString(50, y, HINDI_TEXT)
        y -= 50
    
    # Fallback test with Helvetica
    c.setFont("Helvetica", 12)
    c.drawString(50, y, "Same text with Helvetica (will show boxes):")
    y -= 25
    c.setFont("Helvetica", 20)
    c.drawString(50, y, BENGALI_TEXT)
    
    c.save()
    print(f"[DONE] PDF saved to: {OUTPUT_PDF}")
    print("\nOpen the PDF and check:")
    print("  - If NotoSans sections show TEXT -> Font works!")
    print("  - If NotoSans sections show BOXES -> Font file issue or ReportLab incompatibility")
    print("  - Helvetica section SHOULD show boxes (expected)")

if __name__ == "__main__":
    main()
