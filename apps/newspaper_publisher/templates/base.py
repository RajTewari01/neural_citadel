
from abc import ABC, abstractmethod
from datetime import datetime
from reportlab.lib import pagesizes
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Frame, PageTemplate, BaseDocTemplate, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# --- Font Registration & Detection Logic ---

def register_all_fonts():
    fonts = {}
    
    # 0. Local Fonts (User Bundled) - PRIORITY
    local_dir = r"D:\neural_citadel\assets\models\ttf"
    if os.path.exists(local_dir):
        print(f"Loading local fonts from: {local_dir}")
        for f in os.listdir(local_dir):
            if f.lower().endswith(('.ttf', '.ttc', '.otf')):
                name = os.path.splitext(f)[0] # e.g. "NotoSansBengali-Regular"
                fonts[name] = os.path.join(local_dir, f)

    # 1. System Fonts (Windows Defaults)
    fonts.update({
        'Helvetica': r'C:\Windows\Fonts\arial.ttf',
        'Helvetica-Bold': r'C:\Windows\Fonts\arialbd.ttf',
        'Times-Roman': r'C:\Windows\Fonts\times.ttf',
        'Times-Bold': r'C:\Windows\Fonts\timesbd.ttf',
        'Impact': r'C:\Windows\Fonts\impact.ttf',
        'Arial': r'C:\Windows\Fonts\arial.ttf',
        'Arial-Bold': r'C:\Windows\Fonts\arialbd.ttf',
        # Indic/Global defaults
        'Arial-Unicode': r'C:\Windows\Fonts\ARIALUNI.TTF',
        'Nirmala': r'C:\Windows\Fonts\Nirmala.ttf',
        'Nirmala-Bold': r'C:\Windows\Fonts\NirmalaB.ttf',
        'Mangal': r'C:\Windows\Fonts\mangal.ttf',
        'Vrinda': r'C:\Windows\Fonts\vrinda.ttf',
        'Shonar': r'C:\Windows\Fonts\Shonar.ttf',
        'Latha': r'C:\Windows\Fonts\latha.ttf',
        'Gautami': r'C:\Windows\Fonts\gautami.ttf',
        'Tunga': r'C:\Windows\Fonts\tunga.ttf',
        'Kartika': r'C:\Windows\Fonts\kartika.ttf',
        'Shruti': r'C:\Windows\Fonts\shruti.ttf',
        'Raavi': r'C:\Windows\Fonts\raavi.ttf',
        'Kalinga': r'C:\Windows\Fonts\kalinga.ttf',
        # CJK
        'Meiryo': r'C:\Windows\Fonts\meiryo.ttc',
        'Microsoft-YaHei': r'C:\Windows\Fonts\msyh.ttc',
    })
    
    registered = set()
    for name, path in fonts.items():
        if os.path.exists(path):
            try:
                if path.lower().endswith('.ttc'):
                     pdfmetrics.registerFont(TTFont(name, path, subfontIndex=0))
                     registered.add(name)
                else:
                    pdfmetrics.registerFont(TTFont(name, path))
                    registered.add(name)
            except: pass
    return registered

REGISTERED_FONTS = register_all_fonts()

def get_script_font(text, default_font="Helvetica", is_bold=False):
    """Detects script of text and returns appropriate registered font."""
    if not text: return default_font
    
    for char in text[:50]:
        code = ord(char)
        if code < 128: continue
        
        # Devanagari (Hindi)
        if 0x0900 <= code <= 0x097F: 
            if "NotoSansDevanagari-Regular" in REGISTERED_FONTS: return "NotoSansDevanagari-Regular"
            if "Mangal" in REGISTERED_FONTS: return "Mangal"
            return "Nirmala" if "Nirmala" in REGISTERED_FONTS else default_font
            
        # Bengali
        if 0x0980 <= code <= 0x09FF: 
            if "NotoSansBengali-Regular" in REGISTERED_FONTS: return "NotoSansBengali-Regular"
            if "Vrinda" in REGISTERED_FONTS: return "Vrinda"
            return "Nirmala" if "Nirmala" in REGISTERED_FONTS else default_font

        # Tamil
        if 0x0B80 <= code <= 0x0BFF: return "NotoSansTamil-Regular" if "NotoSansTamil-Regular" in REGISTERED_FONTS else ("Latha" if "Latha" in REGISTERED_FONTS else default_font)
        
        # Telugu
        if 0x0C00 <= code <= 0x0C7F: return "NotoSansTelugu-Regular" if "NotoSansTelugu-Regular" in REGISTERED_FONTS else ("Gautami" if "Gautami" in REGISTERED_FONTS else default_font)
        
        # Kannada
        if 0x0C80 <= code <= 0x0CFF: return "NotoSansKannada-Regular" if "NotoSansKannada-Regular" in REGISTERED_FONTS else ("Tunga" if "Tunga" in REGISTERED_FONTS else default_font)
        
        # Malayalam
        if 0x0D00 <= code <= 0x0D7F: return "NotoSansMalayalam-Regular" if "NotoSansMalayalam-Regular" in REGISTERED_FONTS else ("Kartika" if "Kartika" in REGISTERED_FONTS else default_font)
        
        # Gujarati
        if 0x0A80 <= code <= 0x0AFF: return "NotoSansGujarati-Regular" if "NotoSansGujarati-Regular" in REGISTERED_FONTS else ("Shruti" if "Shruti" in REGISTERED_FONTS else default_font)
        
        # Punjabi
        if 0x0A00 <= code <= 0x0A7F: return "NotoSansGurmukhi-Regular" if "NotoSansGurmukhi-Regular" in REGISTERED_FONTS else ("Raavi" if "Raavi" in REGISTERED_FONTS else default_font)

        # Cyrillic
        if 0x0400 <= code <= 0x04FF:
            if "NotoSans-Regular" in REGISTERED_FONTS: return "NotoSans-Regular"
            return default_font 
        
        # Japanese / CJK
        if 0x3040 <= code <= 0x30FF or 0x4E00 <= code <= 0x9FFF:
            if "NotoSansJP-Regular" in REGISTERED_FONTS: return "NotoSansJP-Regular"
            if "NotoSansSC-Regular" in REGISTERED_FONTS: return "NotoSansSC-Regular"
            if "Meiryo" in REGISTERED_FONTS: return "Meiryo"
            return default_font

        # General Unicode
        if "Nirmala" in REGISTERED_FONTS: return "Nirmala"
        if "Arial-Unicode" in REGISTERED_FONTS: return "Arial-Unicode"
        
    return default_font


class NewspaperTemplate(ABC):
    def __init__(self, filename, paper_size=pagesizes.A4):
        self.filename = filename
        self.paper_size = paper_size
        self.styles = getSampleStyleSheet()
        self.width, self.height = self.paper_size
        self.story = []
        
    def _create_header(self, canvas, doc):
        """Draws the newspaper header (masthead). To be customized by subclasses."""
        pass

    def _create_footer(self, canvas, doc):
        """Draws the footer (page numbers, etc.)."""
        canvas.saveState()
        canvas.setFont('Times-Roman', 9)
        canvas.drawString(inch, 0.75 * inch, f"Page {doc.page}")
        canvas.drawRightString(self.width - inch, 0.75 * inch, datetime.now().strftime("%B %d, %Y"))
        canvas.restoreState()

    def get_image(self, path, width):
        """Helper to create a ReportLab Image with correct aspect ratio."""
        if not path or not os.path.exists(path):
            return None
        try:
            img = Image(path)
            img_width = img.drawWidth
            img_height = img.drawHeight
            aspect = img_height / float(img_width)
            
            img.drawWidth = width
            img.drawHeight = width * aspect
            return img
        except Exception as e:
            print(f"Error loading image {path}: {e}")
            return None

    def build(self, articles):
        """
        Main method to generate the PDF.
        articles: List of dicts {'title': str, 'content': str, 'author': str}
        """
        self.articles = articles # Store for access in page templates (like cover)
        doc = BaseDocTemplate(self.filename, pagesize=self.paper_size)
        
        # Define Frames (Concept of columns)
        # We will let subclasses define more complex templates, but here is a default
        self.setup_page_templates(doc)
        
        # Convert articles to flowables
        self.story = self.convert_articles_to_flowables(articles)
        
        doc.build(self.story)
        print(f"PDF generated: {self.filename}")

    @abstractmethod
    def setup_page_templates(self, doc):
        """Define frames and page templates."""
        pass

    @abstractmethod
    def convert_articles_to_flowables(self, articles):
        """Convert structure data to Platypus objects."""
        pass
