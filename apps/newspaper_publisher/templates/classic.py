from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph, Spacer, Frame, PageTemplate, NextPageTemplate, PageBreak, Flowable
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib.colors import black, lightgrey, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .base import NewspaperTemplate
from .registry import register_template

# Register fonts
import os
from pathlib import Path

# Project Root (calculated from this file location: apps/newspaper_publisher/templates/classic.py)
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Load fonts from local TTF folder (Noto fonts for Indic languages)
local_dir = PROJECT_ROOT / "assets" / "models" / "ttf"
if local_dir.exists():
    for f in local_dir.iterdir():
        # Only load TTF files, skip OTF (ReportLab can't render OTF properly)
        if f.suffix.lower() == '.ttf':
            try:
                pdfmetrics.registerFont(TTFont(f.stem, str(f)))
            except: pass

# Register Windows system fonts
system_fonts = {
    'TimesNewRoman': r'C:\Windows\Fonts\times.ttf',
    'TimesNewRoman-Bold': r'C:\Windows\Fonts\timesbd.ttf',
    # CJK fonts
    'MicrosoftYaHei': r'C:\Windows\Fonts\msyh.ttc',  # Chinese
    'MSGothic': r'C:\Windows\Fonts\msgothic.ttc',     # Japanese
    'MalgunGothic': r'C:\Windows\Fonts\malgun.ttf',   # Korean
    'SimSun': r'C:\Windows\Fonts\simsun.ttc',         # Chinese Traditional
    # Other scripts
    'Arial': r'C:\Windows\Fonts\arial.ttf',           # Arabic fallback
}
for name, path in system_fonts.items():
    if os.path.exists(path):
        try:
            if path.endswith('.ttc'):
                pdfmetrics.registerFont(TTFont(name, path, subfontIndex=0))
            else:
                pdfmetrics.registerFont(TTFont(name, path))
        except: pass


class ColumnDivider(Flowable):
    """Draws a vertical line to separate columns."""
    def __init__(self, height, color=lightgrey):
        Flowable.__init__(self)
        self.height = height
        self.color = color

    def draw(self):
        # We don't actually flow this *in* the column, 
        # simpler approach: we'll draw lines in the page template or header.
        pass


@register_template(
    name="classic",
    keywords=["classic", "newspaper", "traditional", "nyt", "chronicle"],
    description="NYT-style classic newspaper with 3-column layout and serif fonts"
)
class ClassicNewspaper(NewspaperTemplate):
    def _create_header(self, c, doc):
        # Custom "New York Times" style header
        c.saveState()
        
        # Top Date/Meta bar
        c.setFont('Times-Roman', 9)
        c.setStrokeColor(black)
        c.setLineWidth(0.5)
        c.line(0, self.height - 0.5*inch, self.width, self.height - 0.5*inch)
        c.drawString(0.5*inch, self.height - 0.4*inch, "VOL. CXXVI... No. 43,123")
        c.drawRightString(self.width - 0.5*inch, self.height - 0.4*inch, "New York, Wednesday, January 14, 2026")
        
        # MASTHEAD
        c.setFont('Times-Bold', 42)
        c.drawCentredString(self.width / 2.0, self.height - 1.1 * inch, "The Neural Chronicle")
        
        # Motto
        c.setFont('Times-Italic', 10)
        c.drawCentredString(self.width / 2.0, self.height - 1.35 * inch, "All the News That's Fit to Compute")
        
        # Double separator line
        y_line = self.height - 1.5 * inch
        c.setLineWidth(1)
        c.line(0.5*inch, y_line, self.width-0.5*inch, y_line)
        c.setLineWidth(0.5)
        c.line(0.5*inch, y_line - 3, self.width-0.5*inch, y_line - 3)
        
        c.restoreState()
        self._create_footer(c, doc)
        
        # Draw Column Dividers (Manual approach for simplicity on the canvas)
        # 3 Cols -> 2 Dividers
        c.saveState()
        c.setStrokeColor(lightgrey)
        c.setLineWidth(0.5)
        
        # Calculate positions (must match setup_page_templates)
        margin = 0.5 * inch
        gap = 0.2 * inch
        col_width = (self.width - 2*margin - 2*gap) / 3
        
        # Divider 1
        x1 = margin + col_width + gap/2
        c.line(x1, margin, x1, self.height - 1.6*inch)
        
        # Divider 2
        x2 = margin + 2*col_width + 1.5*gap
        c.line(x2, margin, x2, self.height - 1.6*inch)
        
        c.restoreState()

    def setup_page_templates(self, doc):
        # 3 Columns, tighter margins
        margin = 0.5 * inch
        gap = 0.2 * inch
        col_width = (self.width - 2*margin - 2*gap) / 3
        
        # Top margin accounts for the large header
        frames = []
        for i in range(3):
            left = margin + i * (col_width + gap)
            f = Frame(left, margin, col_width, self.height - 2.1 * inch, id=f'col{i}')
            frames.append(f)
        
        doc.addPageTemplates([PageTemplate(id='ThreeCol', frames=frames, onPage=self._create_header)])

    def convert_articles_to_flowables(self, articles):
        story = []
        
        for article in articles:
            # Detect font based on content
            title_text = article.get('title', '')
            body_text = article.get('content', '')
            title_font = self._get_font_for_text(title_text)
            body_font = self._get_font_for_text(body_text)
            
            # Styles with detected fonts
            title_style = ParagraphStyle(
                name='ClassicTitle',
                fontName=title_font,
                fontSize=14,
                leading=16,
                alignment=TA_LEFT,
                spaceAfter=4,
            )
            
            meta_style = ParagraphStyle(
                name='ClassicMeta',
                fontName=body_font,
                fontSize=8,
                leading=9,
                textColor=black,
                alignment=TA_LEFT,
                spaceAfter=6
            )
            
            body_style = ParagraphStyle(
                name='ClassicBody',
                fontName=body_font,
                fontSize=9.5,
                leading=10.5,
                alignment=TA_JUSTIFY,
                firstLineIndent=10,
                spaceAfter=6,
            )

            # Title
            story.append(Paragraph(article['title'], title_style))
            
            # Author / Date line
            if 'author' in article:
                story.append(Paragraph(f"By {article['author'].upper()}", meta_style))
            
            # Image
            if article.get('image'):
                col_width = (self.width - 1.4 * inch) / 3
                img = self.get_image(article['image'], width=col_width)
                if img:
                    story.append(img)
                    story.append(Spacer(1, 4))

            # Content
            story.append(Paragraph(article['content'], body_style))
            
            # Separator
            story.append(Spacer(1, 8))
            story.append(Paragraph("___", ParagraphStyle('tiny_sep', alignment=TA_CENTER, leading=6)))
            story.append(Spacer(1, 12))
            
        return story
    
    def _get_font_for_text(self, text, default="Helvetica"):
        """Detect script and return appropriate font."""
        if not text:
            return default
        for char in text[:50]:
            code = ord(char)
            # Latin (including Spanish, French, etc.)
            if code < 0x0400:
                continue
            # Cyrillic (Russian)
            if 0x0400 <= code <= 0x04FF:
                return default  # Helvetica handles Cyrillic
            # Devanagari (Hindi)
            if 0x0900 <= code <= 0x097F:
                return "NotoSansDevanagari-Regular"
            # Bengali
            if 0x0980 <= code <= 0x09FF:
                return "NotoSansBengali-Regular"
            # Tamil
            if 0x0B80 <= code <= 0x0BFF:
                return "NotoSansTamil-Regular"
            # Telugu
            if 0x0C00 <= code <= 0x0C7F:
                return "NotoSansTelugu-Regular"
            # Kannada
            if 0x0C80 <= code <= 0x0CFF:
                return "NotoSansKannada-Regular"
            # Malayalam
            if 0x0D00 <= code <= 0x0D7F:
                return "NotoSansMalayalam-Regular"
            # Gujarati
            if 0x0A80 <= code <= 0x0AFF:
                return "NotoSansGujarati-Regular"
            # Punjabi
            if 0x0A00 <= code <= 0x0A7F:
                return "NotoSansGurmukhi-Regular"
            # Arabic
            if 0x0600 <= code <= 0x06FF or 0x0750 <= code <= 0x077F:
                return "Arial"  # Arial has good Arabic support
            # Thai
            if 0x0E00 <= code <= 0x0E7F:
                return "Arial"
            # Korean (Hangul)
            if 0xAC00 <= code <= 0xD7AF or 0x1100 <= code <= 0x11FF:
                return "MalgunGothic"
            # Japanese (Hiragana, Katakana)
            if 0x3040 <= code <= 0x30FF:
                return "MSGothic"
            # CJK Unified Ideographs (Chinese/Japanese/Korean)
            if 0x4E00 <= code <= 0x9FFF:
                return "MicrosoftYaHei"
        return default
