from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph, Spacer, Frame, PageTemplate
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.colors import black, white, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from .base import NewspaperTemplate
from .registry import register_template
import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Load fonts from local TTF folder (skip OTF - ReportLab can't render them)
local_dir = PROJECT_ROOT / "assets" / "models" / "ttf"
if local_dir.exists():
    for f in local_dir.iterdir():
        if f.suffix.lower() == '.ttf':
            try:
                pdfmetrics.registerFont(TTFont(f.stem, str(f)))
            except: pass

# Register Windows system fonts
system_fonts = {
    'MicrosoftYaHei': r'C:\Windows\Fonts\msyh.ttc',   # Chinese
    'MSGothic': r'C:\Windows\Fonts\msgothic.ttc',      # Japanese
    'MalgunGothic': r'C:\Windows\Fonts\malgun.ttf',    # Korean
    'SimSun': r'C:\Windows\Fonts\simsun.ttc',
    'Arial': r'C:\Windows\Fonts\arial.ttf',            # Arabic/Thai
}
for name, path in system_fonts.items():
    if os.path.exists(path):
        try:
            if path.endswith('.ttc'):
                pdfmetrics.registerFont(TTFont(name, path, subfontIndex=0))
            else:
                pdfmetrics.registerFont(TTFont(name, path))
        except: pass


@register_template(
    name="modern",
    keywords=["modern", "horizon", "contemporary", "clean", "minimal"],
    description="Modern newspaper with dark header and 2-column layout"
)
class ModernNewspaper(NewspaperTemplate):
    def _create_header(self, c, doc):
        c.saveState()
        header_height = 1.5 * inch
        c.setFillColor(HexColor('#1a1a1a'))
        c.rect(0, self.height - header_height, self.width, header_height, fill=1, stroke=0)
        
        c.setFillColor(white)
        c.setFont('Helvetica-Bold', 32)
        c.drawString(0.5 * inch, self.height - 0.8 * inch, "THE NEURAL CITADEL")
        
        c.setFont('Helvetica', 12)
        c.drawRightString(self.width - 0.5 * inch, self.height - 0.8 * inch, "Daily Ai Intelligence")
        
        c.setFillColor(HexColor('#ff4d4d'))
        c.rect(0, self.height - header_height - 5, self.width, 5, fill=1, stroke=0)
        
        c.restoreState()
        self._create_footer(c, doc)

    def setup_page_templates(self, doc):
        margin = 0.5 * inch
        col_width = (self.width - 2*margin - 0.5*inch) / 2
        
        f1 = Frame(margin, margin, col_width, self.height - 2.5*inch, id='c1')
        f2 = Frame(margin + col_width + 0.5*inch, margin, col_width, self.height - 2.5*inch, id='c2')
        
        doc.addPageTemplates([PageTemplate(id='Modern', frames=[f1, f2], onPage=self._create_header)])

    def convert_articles_to_flowables(self, articles):
        story = []

        for article in articles:
            title_font = self._get_font_for_text(article.get('title', ''))
            body_font = self._get_font_for_text(article.get('content', ''))
            
            title_style = ParagraphStyle(
                name='ModernTitle', fontName=title_font, fontSize=18,
                leading=20, textColor=HexColor('#1a1a1a'), spaceAfter=10
            )
            
            body_style = ParagraphStyle(
                name='ModernBody', fontName=body_font, fontSize=10,
                leading=14, alignment=TA_LEFT, spaceAfter=10
            )
            
            cat_style = ParagraphStyle(
                name='ModernCat', fontName=body_font, fontSize=8,
                textColor=HexColor('#ff4d4d'), spaceAfter=2
            )

            story.append(Paragraph(article.get('category', 'NEWS'), cat_style))
            story.append(Paragraph(article['title'], title_style))
            
            if article.get('image'):
                col_width = (self.width - 1.5 * inch) / 2
                img = self.get_image(article['image'], width=col_width)
                if img:
                    story.append(img)
                    story.append(Spacer(1, 10))

            story.append(Paragraph(article['content'], body_style))
            story.append(Spacer(1, 30))
            
        return story

    def _get_font_for_text(self, text, default="Helvetica"):
        if not text:
            return default
        for char in text[:50]:
            code = ord(char)
            if code < 0x0400:
                continue
            if 0x0900 <= code <= 0x097F:
                return "NotoSansDevanagari-Regular"
            if 0x0980 <= code <= 0x09FF:
                return "NotoSansBengali-Regular"
            if 0x0B80 <= code <= 0x0BFF:
                return "NotoSansTamil-Regular"
            if 0x0C00 <= code <= 0x0C7F:
                return "NotoSansTelugu-Regular"
            if 0x0C80 <= code <= 0x0CFF:
                return "NotoSansKannada-Regular"
            if 0x0D00 <= code <= 0x0D7F:
                return "NotoSansMalayalam-Regular"
            if 0x0A80 <= code <= 0x0AFF:
                return "NotoSansGujarati-Regular"
            if 0x0A00 <= code <= 0x0A7F:
                return "NotoSansGurmukhi-Regular"
            # Arabic
            if 0x0600 <= code <= 0x06FF or 0x0750 <= code <= 0x077F:
                return "Arial"
            # Thai
            if 0x0E00 <= code <= 0x0E7F:
                return "Arial"
            # Korean (Hangul)
            if 0xAC00 <= code <= 0xD7AF or 0x1100 <= code <= 0x11FF:
                return "MalgunGothic"
            # Japanese (Hiragana, Katakana)
            if 0x3040 <= code <= 0x30FF:
                return "MSGothic"
            # CJK Unified Ideographs
            if 0x4E00 <= code <= 0x9FFF:
                return "MicrosoftYaHei"
        return default
