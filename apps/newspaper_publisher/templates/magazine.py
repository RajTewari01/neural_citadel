
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph, Spacer, Frame, PageTemplate, NextPageTemplate, PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.colors import HexColor, white, black, gold, red, Color
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage
import random
import os
from .base import NewspaperTemplate
from .overlay import ImageWithTextOverlay
from .registry import register_template

from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# --- 1. Font Loader ---
def register_system_fonts():
    # 0. Local Fonts (User Bundled) - PRIORITY (skip OTF, ReportLab can't render)
    local_dir = PROJECT_ROOT / "assets" / "models" / "ttf"
    if local_dir.exists():
        print(f"Loading local fonts from: {local_dir}")
        for f in local_dir.iterdir():
            if f.suffix.lower() == '.ttf':
                name = f.stem 
                path = str(f)
                try:
                   pdfmetrics.registerFont(TTFont(name, path))
                except: pass

    fonts = {
        'Impact': r'C:\Windows\Fonts\impact.ttf',
        'Arial': r'C:\Windows\Fonts\arial.ttf',
        'Arial-Bold': r'C:\Windows\Fonts\arialbd.ttf',
        'SegoeUI': r'C:\Windows\Fonts\segoeui.ttf',
        'SegoeUI-Bold': r'C:\Windows\Fonts\segoeuib.ttf',
        'Georgia': r'C:\Windows\Fonts\georgia.ttf',
        'Georgia-Bold': r'C:\Windows\Fonts\georgiab.ttf',
        'Comic': r'C:\Windows\Fonts\comic.ttf',
        'Comic-Bold': r'C:\Windows\Fonts\comicbd.ttf',
        'CourierNew': r'C:\Windows\Fonts\cour.ttf',
        'CourierNew-Bold': r'C:\Windows\Fonts\courbd.ttf',
    }
    for name, path in fonts.items():
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
            except: pass

    # CJK & Other fonts from Windows
    cjk_fonts = {
        'MicrosoftYaHei': r'C:\Windows\Fonts\msyh.ttc',   # Chinese
        'MSGothic': r'C:\Windows\Fonts\msgothic.ttc',      # Japanese
        'MalgunGothic': r'C:\Windows\Fonts\malgun.ttf',    # Korean
        'SimSun': r'C:\Windows\Fonts\simsun.ttc',
    }
    for name, path in cjk_fonts.items():
        if os.path.exists(path):
            try:
                if path.endswith('.ttc'):
                    pdfmetrics.registerFont(TTFont(name, path, subfontIndex=0))
                else:
                    pdfmetrics.registerFont(TTFont(name, path))
            except: pass

register_system_fonts()

# --- Font Detection ---
def get_font_for_text(text, default="Helvetica"):
    """Detect script and return appropriate font."""
    if not text:
        return default
    for char in text[:50]:
        code = ord(char)
        # Latin (ASCII + Extended - Spanish, French, German etc.)
        if code < 0x0400:
            continue
        # Cyrillic (Russian)
        if 0x0400 <= code <= 0x04FF:
            return default
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
        # Punjabi (Gurmukhi)
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

# --- 2. Color Logic ---
def get_dominant_color(image_path):
    try:
        img = PILImage.open(image_path)
        img = img.resize((150, 150))
        result = img.convert('P', palette=PILImage.ADAPTIVE, colors=10).convert('RGB')
        main_colors = result.getcolors(150*150)
        ordered = sorted(main_colors, key=lambda x: x[0], reverse=True)
        chosen_rgb = (0, 0, 0)
        for count, rgb in ordered:
            if sum(rgb) < 30 or sum(rgb) > 700: continue
            chosen_rgb = rgb
            break
        r, g, b = chosen_rgb
        return HexColor(f"#{r:02x}{g:02x}{b:02x}"), chosen_rgb
    except:
        return HexColor('#000000'), (0,0,0)

def generate_palette(base_rgb):
    r, g, b = base_rgb
    if max(r,g,b) - min(r,g,b) < 60:
        fashion_colors = [(229, 9, 20), (0, 51, 153), (255, 69, 0), (218,165,32), (50, 205, 50)]
        r, g, b = random.choice(fashion_colors)
    
    pastel_r, pastel_g, pastel_b = int((r + 255*3)/4), int((g + 255*3)/4), int((b + 255*3)/4)
    comp_r, comp_g, comp_b = 255-r, 255-g, 255-b
    
    return {
        'primary': HexColor(f"#{r:02x}{g:02x}{b:02x}"),
        'pastel': HexColor(f"#{pastel_r:02x}{pastel_g:02x}{pastel_b:02x}"),
        'pop': HexColor(f"#{comp_r:02x}{comp_g:02x}{comp_b:02x}"),
        'dark': HexColor("#000000"),
        'white': white, 'black': black
    }

# --- 3. Style Definitions ---
ASSET_DIR = r"D:\neural_citadel\assets\apps_assets\newspaper"

STYLES = {
    # =========================================================================
    # EXISTING STYLES (Preserved)
    # =========================================================================
    'Neural Citadel': { # The Flagship
        'font_masthead': 'Times-Bold', 'font_main': 'Times-Bold', 'font_body': 'Helvetica',
        'caps': True, 'align': 'center', 'bg': 'style_neural.png', 'mode': 'classic_vogue'
    },
    'The Tech': {
        'font_masthead': 'CourierNew-Bold', 'font_main': 'CourierNew-Bold', 'font_body': 'CourierNew',
        'caps': False, 'align': 'left', 'bg': 'style_tech.png', 'mode': 'neon_tech', 'palette': HexColor('#00FF00')
    },
    'The Times': {
        'font_masthead': 'Georgia-Bold', 'font_main': 'Georgia', 'font_body': 'Georgia',
        'caps': True, 'align': 'center', 'bg': 'style_times.png', 'mode': 'classic_serif'
    },
    'The Minimal': {
        'font_masthead': 'Arial-Bold', 'font_main': 'Arial', 'font_body': 'Arial',
        'caps': True, 'align': 'left', 'bg': 'style_minimal.png', 'mode': 'clean_swiss'
    },
    'The Bold': {
        'font_masthead': 'Impact', 'font_main': 'Impact', 'font_body': 'Arial',
        'caps': True, 'align': 'center', 'bg': 'style_bold.png', 'mode': 'poster_impact', 'palette': HexColor('#FFFF00')
    },
    'The Elegant': {
        'font_masthead': 'Times-Roman', 'font_main': 'Times-Roman', 'font_body': 'Helvetica',
        'caps': True, 'align': 'left', 'bg': 'style_elegant.png', 'mode': 'delicate_fashion',
        'palette': HexColor('#C40233') # Signature Vogue Red
    },
    'The Geo': {
        'font_masthead': 'Arial-Bold', 'font_main': 'Arial-Bold', 'font_body': 'Georgia',
        'caps': True, 'align': 'left', 'bg': 'style_geo.png', 'mode': 'nature_box', 'palette': HexColor('#FFD700')
    },
    'The Star': {
        'font_masthead': 'Arial-Bold', 'font_main': 'Arial-Bold', 'font_body': 'Arial',
        'caps': True, 'align': 'right', 'bg': 'style_star.png', 'mode': 'tabloid_chaos', 'palette': HexColor('#FF0099')
    },
    'The Noir': {
        'font_masthead': 'Times-Bold', 'font_main': 'Times-Bold', 'font_body': 'CourierNew',
        'caps': True, 'align': 'center', 'bg': 'style_noir.png', 'mode': 'bw_contrast'
    },
    'The Pop': {
        'font_masthead': 'Comic-Bold' if 'Comic-Bold' in pdfmetrics.getRegisteredFontNames() else 'Impact', 
        'font_main': 'Comic-Bold' if 'Comic-Bold' in pdfmetrics.getRegisteredFontNames() else 'Impact', 
        'font_body': 'Arial',
        'caps': True, 'align': 'center', 'bg': 'style_pop.png', 'mode': 'pop_art'
    },
    'The Corporate': {
        'font_masthead': 'SegoeUI-Bold', 'font_main': 'SegoeUI-Bold', 'font_body': 'SegoeUI',
        'caps': True, 'align': 'left', 'bg': 'style_corporate.png', 'mode': 'modern_biz', 'palette': HexColor('#003366')
    },
    'The Future': {
        'font_masthead': 'SegoeUI-Bold', 'font_main': 'CourierNew-Bold', 'font_body': 'Arial',
        'caps': True, 'align': 'center', 'bg': 'style_future.png', 'mode': 'future_clean', 'palette': HexColor('#00AAFF')
    },
    
    # =========================================================================
    # NEW PREMIUM VOGUE-STYLE MAGAZINE COVERS
    # =========================================================================
    
    # Classic Vogue - The iconic fashion magazine look
    'Vogue Classic': {
        'font_masthead': 'Times-Bold', 'font_main': 'Times-Roman', 'font_body': 'Helvetica',
        'caps': True, 'align': 'center', 'bg': 'style_vogue_classic.png', 'mode': 'vogue_premium',
        'palette': HexColor('#FFFFFF'),  # White text on dark images
        'masthead_size': 120,
        'text_shadow': True,
        'floating_text': True,  # No boxes, text floats on image
        'accent_color': HexColor('#E60012')  # Vogue Red
    },
    
    # Vogue Paris - French elegance with thin serif fonts
    'Vogue Paris': {
        'font_masthead': 'Georgia-Bold', 'font_main': 'Georgia', 'font_body': 'Georgia',
        'caps': True, 'align': 'center', 'bg': 'style_vogue_paris.png', 'mode': 'vogue_premium',
        'palette': HexColor('#F5F5DC'),  # Soft cream/beige
        'masthead_size': 100,
        'text_shadow': True,
        'floating_text': True,
        'accent_color': HexColor('#DAA520')  # Gold accent
    },
    
    # Vogue Noir - Dark, dramatic high-fashion
    'Vogue Noir': {
        'font_masthead': 'Times-Bold', 'font_main': 'Times-Bold', 'font_body': 'Helvetica',
        'caps': True, 'align': 'center', 'bg': 'style_vogue_noir.png', 'mode': 'vogue_premium',
        'palette': HexColor('#FFFFFF'),
        'masthead_size': 110,
        'text_shadow': True,
        'floating_text': True,
        'accent_color': HexColor('#8B0000'),  # Dark red
        'overlay_darkness': 0.3  # Darken cover image
    },
    
    # Elle Style - Modern, colorful fashion magazine
    'Elle Style': {
        'font_masthead': 'Arial-Bold', 'font_main': 'Arial-Bold', 'font_body': 'Arial',
        'caps': True, 'align': 'left', 'bg': 'style_elle.png', 'mode': 'vogue_premium',
        'palette': HexColor('#FFFFFF'),
        'masthead_size': 100,
        'text_shadow': True,
        'floating_text': True,
        'accent_color': HexColor('#FF1493'),  # Hot pink
        'sidebar_teasers': True  # Side teasers like Elle
    },
    
    # Harper's Bazaar - Ultra-minimal luxury
    'Harpers Bazaar': {
        'font_masthead': 'Times-Roman', 'font_main': 'Times-Roman', 'font_body': 'Helvetica',
        'caps': True, 'align': 'center', 'bg': 'style_harpers_bazaar.png', 'mode': 'vogue_premium',
        'palette': HexColor('#000000'),  # Black text (for light images)
        'masthead_size': 90,
        'text_shadow': False,
        'floating_text': True,
        'accent_color': HexColor('#B22222'),  # Firebrick red
        'minimal_layout': True  # Very few text elements
    },
    
    # GQ Magazine - Men's fashion, bold and modern
    'GQ Magazine': {
        'font_masthead': 'Impact', 'font_main': 'Arial-Bold', 'font_body': 'Arial',
        'caps': True, 'align': 'left', 'bg': 'style_gq.png', 'mode': 'vogue_premium',
        'palette': HexColor('#FFFFFF'),
        'masthead_size': 140,
        'text_shadow': True,
        'floating_text': True,
        'accent_color': HexColor('#1E90FF'),  # Dodger blue
        'bold_headlines': True
    }
}


DEFAULT_STYLE_CONTENT = {
    'Neural Citadel': [
        {'title': "The Rise of Synthetic Consciousness", 'author': "Dr. A.I. Vance", 'category': "FUTURE", 'content': "..."},
        {'title': "Global Markets Embrace Neural Link", 'author': "Market Watch", 'category': "FINANCE", 'content': "..."},
        {'title': "Digital Art Revolution", 'author': "Pixel Master", 'category': "CULTURE", 'content': "..."},
        {'title': "The End of Sleep?", 'author': "Sleep Tech", 'category': "HEALTH", 'content': "..."}
    ],
    'The Tech': [
        {'title': "Quantum Computing Breaks Encryption", 'author': "Bit Lord", 'category': "CODE", 'content': "..."},
        {'title': "New Cyber-Deck Released", 'author': "Gear Head", 'category': "REVIEW", 'content': "..."},
        {'title': "AI Rights Bill Passes", 'author': "Legal Bot", 'category': "LAW", 'content': "..."},
        {'title': "Hacking the Mainframe", 'author': "Zero Cool", 'category': "SECURITY", 'content': "..."}
    ],
    'The Times': [
        {'title': "Historic Treaty Signed in Geneva", 'author': "H. Kissinger", 'category': "WORLD", 'content': "..."},
        {'title': "Economy Shows Signs of Recovery", 'author': "Econ Dept", 'category': "BUSINESS", 'content': "..."},
        {'title': "New Library Wing Opens", 'author': "Arch Digest", 'category': "LOCAL", 'content': "..."},
        {'title': "The Lost Letters of WWII", 'author': "Historian", 'category': "HISTORY", 'content': "..."}
    ],
    'The Minimal': [
        {'title': "Less Is More: Living With Void", 'author': "Mies V.", 'category': "DESIGN", 'content': "..."},
        {'title': "White Space in UI", 'author': "J. Ive", 'category': "TECH", 'content': "..."},
        {'title': "The Art of Silence", 'author': "Monk", 'category': "LIFE", 'content': "..."},
        {'title': "Pure Forms", 'author': "Abstract", 'category': "ART", 'content': "..."}
    ],
    'The Bold': [
        {'title': "LOUD NOISES!", 'author': "Brick T.", 'category': "ALERT", 'content': "..."},
        {'title': "WARNING: EXTREME WEATHER", 'author': "Met Office", 'category': "CLIMATE", 'content': "..."},
        {'title': "MARKET CRASH IMMINENT?", 'author': "Bear Bull", 'category': "MONEY", 'content': "..."},
        {'title': "DO NOT IGNORE THIS", 'author': "Editor", 'category': "OPINION", 'content': "..."}
    ],
    'The Elegant': [
        {'title': "Paris Fashion Week Highlights", 'author': "Vogue Ed.", 'category': "STYLE", 'content': "..."},
        {'title': "The Return of Silk", 'author': "Fabricio", 'category': "TRENDS", 'content': "..."},
        {'title': "Diamonds Are Forever", 'author': "De Beers", 'category': "LUXURY", 'content': "..."},
        {'title': "An Evening in Milan", 'author': "Traveler", 'category': "TRAVEL", 'content': "..."}
    ],
    'The Geo': [
        {'title': "Amazon Rainforest Secrets", 'author': "Explorer", 'category': "NATURE", 'content': "..."},
        {'title': "Saving the Great Barrier Reef", 'author': "Marine Bio", 'category': "OCEAN", 'content': "..."},
        {'title': "Hidden Tribes of Papua", 'author': "Anthro", 'category': "CULTURE", 'content': "..."},
        {'title': "Climate Change Realities", 'author': "Scientist", 'category': "PLANET", 'content': "..."}
    ],
    'The Star': [
        {'title': "WHO WORE IT BETTER?", 'author': "Fashion Police", 'category': "GOSSIP", 'content': "..."},
        {'title': "SHOCKING SCANDAL!", 'author': "Anon", 'category': "CELEB", 'content': "..."},
        {'title': "10 Tips for flawless skin", 'author': "Beauty Guru", 'category': "BEAUTY", 'content': "..."},
        {'title': "He said WHAT?!", 'author': "Insider", 'category': "DRAMA", 'content': "..."}
    ],
    'The Noir': [
        {'title': "Shadows in the Rain", 'author': "Det. Spade", 'category': "CRIME", 'content': "..."},
        {'title': "The Case of the Missing Ruby", 'author': "Holmes", 'category': "MYSTERY", 'content': "..."},
        {'title': "Midnight Confessions", 'author': "Stranger", 'category': "CITY", 'content': "..."},
        {'title': "Dark Alleys", 'author': "Walker", 'category': "LIFE", 'content': "..."}
    ],
    'The Pop': [
        {'title': "BANG! ZAP! POW!", 'author': "Stan Lee", 'category': "COMIC", 'content': "..."},
        {'title': "Top 10 Anime Betrayals", 'author': "Otaku", 'category': "LIST", 'content': "..."},
        {'title': "Video Game Awards", 'author': "Gamer", 'category': "GAMING", 'content': "..."},
        {'title': "Viral TikTok Trends", 'author': "Influencer", 'category': "SOCIAL", 'content': "..."}
    ],
    'The Corporate': [
        {'title': "Q4 Earnings Report", 'author': "CFO", 'category': "FINANCE", 'content': "..."},
        {'title': "Synergy in the Workplace", 'author': "HR Dept", 'category': "CAREER", 'content': "..."},
        {'title': "Mergers & Acquisitions", 'author': "CEO", 'category': "BIZ", 'content': "..."},
        {'title': "Stock Options 101", 'author': "Broker", 'category': "INVEST", 'content': "..."}
    ],
    'The Future': [
        {'title': "Mars Colony Established", 'author': "Elon", 'category': "SPACE", 'content': "..."},
        {'title': "Immortality Within Reach", 'author': "Futurist", 'category': "BIO", 'content': "..."},
        {'title': "Flying Cars Traffic Update", 'author': "Sky Patrol", 'category': "TRANS", 'content': "..."},
        {'title': "Robot President Elected", 'author': "VoteBot", 'category': "POLITICS", 'content': "..."}
    ],
    
    # Premium Vogue Styles
    'Vogue Classic': [
        {'title': "The Art of Elegance", 'author': "Anna Wintour", 'category': "FASHION", 'content': "..."},
        {'title': "Spring Collection Preview", 'author': "Vogue Paris", 'category': "RUNWAY", 'content': "..."},
        {'title': "Icons of Style", 'author': "Fashion Editor", 'category': "ICONS", 'content': "..."},
        {'title': "The New Minimalism", 'author': "Style Curator", 'category': "TRENDS", 'content': "..."}
    ],
    'Vogue Paris': [
        {'title': "L'Art de Vivre", 'author': "Parisian Editor", 'category': "LIFESTYLE", 'content': "..."},
        {'title': "Haute Couture Returns", 'author': "Dior", 'category': "COUTURE", 'content': "..."},
        {'title': "The French Way", 'author': "Coco Chanel", 'category': "STYLE", 'content': "..."},
        {'title': "Romance in Paris", 'author': "Traveler", 'category': "TRAVEL", 'content': "..."}
    ],
    'Vogue Noir': [
        {'title': "Dark Glamour", 'author': "Night Editor", 'category': "EDITORIAL", 'content': "..."},
        {'title': "Shadows and Light", 'author': "Photographer", 'category': "ART", 'content': "..."},
        {'title': "The Black Collection", 'author': "Designer", 'category': "FASHION", 'content': "..."},
        {'title': "Midnight Elegance", 'author': "Stylist", 'category': "LOOK", 'content': "..."}
    ],
    'Elle Style': [
        {'title': "Bold & Beautiful", 'author': "Elle Editor", 'category': "BEAUTY", 'content': "..."},
        {'title': "Color of the Season", 'author': "Trend Spotter", 'category': "TRENDS", 'content': "..."},
        {'title': "Power Dressing 2026", 'author': "Career Coach", 'category': "CAREER", 'content': "..."},
        {'title': "Summer Must-Haves", 'author': "Shopper", 'category': "SHOP", 'content': "..."}
    ],
    'Harpers Bazaar': [
        {'title': "Simply Iconic", 'author': "Bazaar Editor", 'category': "ICON", 'content': "..."},
        {'title': "Less is Luxury", 'author': "Minimalist", 'category': "DESIGN", 'content': "..."},
        {'title': "The Quiet Revolution", 'author': "Analyst", 'category': "CULTURE", 'content': "..."},
        {'title': "Timeless Pieces", 'author': "Curator", 'category': "STYLE", 'content': "..."}
    ],
    'GQ Magazine': [
        {'title': "The Modern Gentleman", 'author': "GQ Editor", 'category': "STYLE", 'content': "..."},
        {'title': "Power Moves", 'author': "Business", 'category': "SUCCESS", 'content': "..."},
        {'title': "Tech We Love", 'author': "Gadget Guru", 'category': "TECH", 'content': "..."},
        {'title': "Fitness Revolution", 'author': "Trainer", 'category': "HEALTH", 'content': "..."}
    ]
}


@register_template(
    name="magazine",
    keywords=["magazine", "glossy", "vibrant", "cover", "vogue", "fashion"],
    description="Vibrant magazine with 12+ substyles (The Tech, The Noir, The Star, etc.)",
    substyles=STYLES
)
class VibrantMagazine(NewspaperTemplate):
    def __init__(self, filename, size=A4, style_name=None):
        super().__init__(filename, size)
        # Select style (forced or random)
        if style_name and style_name in STYLES:
            self.style_name = style_name
        else:
            self.style_name = random.choice(list(STYLES.keys()))
            
        self.style = STYLES[self.style_name]
        print(f"Generating Magazine Style: {self.style_name}")
        
        # 1. FIXED COVER CONTENT (The "Font Page")
        # This ensures the first page always looks like the specific magazine style
        self.cover_articles = DEFAULT_STYLE_CONTENT.get(self.style_name, DEFAULT_STYLE_CONTENT['Neural Citadel'])
        
        # 2. DYNAMIC INNER CONTENT
        self.articles = []

    def build(self, articles=None):
        # We accept dynamic articles for the inner pages
        self.articles = articles or []
        super().build(self.articles)

    def _draw_text_block(self, c, x, y, text, font, size, bg_color=black, text_color=white, padding=4, alpha=1.0):
        c.saveState()
        width = c.stringWidth(text, font, size)
        height = size * 0.8
        c.setFillColor(bg_color)
        c.setFillAlpha(alpha)
        # Style specific shape?
        c.rect(x - padding, y - 2, width + 2*padding, height + padding*2, fill=1, stroke=0)
        c.setFillAlpha(1.0)
        c.setFillColor(text_color)
        c.setFont(font, size)
        c.drawString(x, y + 2, text)
        c.restoreState()
        return height + padding*2

    def _draw_barcode(self, c, x, y):
        """Draw a barcode element at the specified position."""
        c.saveState()
        w, h = 1.5 * inch, 0.5 * inch
        c.setFillColor(white)
        c.rect(x, y, w, h + 10, fill=1, stroke=0)
        c.setFillColor(black)
        c.rect(x + 5, y + 5, 1, h, fill=1, stroke=0)
        c.rect(x + w - 5, y + 5, 1, h, fill=1, stroke=0)
        curr_x = x + 10
        for _ in range(30):
            bar_w = random.choice([0.5, 1, 2])
            if curr_x + bar_w > x + w - 10:
                break
            c.rect(curr_x, y + 15, bar_w, h - 10, fill=1, stroke=0)
            curr_x += bar_w + random.choice([1, 2])
        c.setFont('Helvetica', 7)
        c.drawCentredString(x + w / 2, y + 2, "9 771234 567003")
        c.restoreState()

    def _draw_floating_text(self, c, x, y, text, font, size, color=white, shadow=True, shadow_color=black):
        """
        Draw text floating on image (Vogue-style) with optional shadow.
        No background box - just elegant floating text.
        """
        c.saveState()
        if shadow:
            # Draw shadow
            c.setFillColor(shadow_color)
            c.setFont(font, size)
            c.drawString(x + 2, y - 2, text)
        # Draw face
        c.setFillColor(color)
        c.setFont(font, size)
        c.drawString(x, y, text)
        c.restoreState()
        return size + 5  # Return height for stacking
    
    def _create_vogue_cover(self, c, doc):
        """
        Create a premium Vogue-style magazine cover.
        Features: Large masthead, floating text, full-bleed cover image, elegant typography.
        """
        c.saveState()
        
        # Get cover image: 1) Style bg, 2) Article image, 3) Dark fallback
        cover_image_path = None
        
        # First try: style's background image
        if self.style.get('bg'):
            style_bg = os.path.join(ASSET_DIR, self.style['bg'])
            if os.path.exists(style_bg):
                cover_image_path = style_bg
        
        # Fallback: use first fetched article's image
        if not cover_image_path and hasattr(self, 'articles') and self.articles:
            for art in self.articles:
                if art.get('image'):
                    cover_image_path = art['image']
                    break
        
        # Fallback: use cover_articles
        if not cover_image_path and self.cover_articles and self.cover_articles[0].get('image'):
            cover_image_path = self.cover_articles[0]['image']
        
        # Draw Cover Image (Full Bleed)
        if cover_image_path and os.path.exists(cover_image_path):
            try:
                img = ImageReader(cover_image_path)
                iw, ih = img.getSize()
                scale = max(self.width / iw, self.height / ih)
                new_w, new_h = iw * scale, ih * scale
                c.drawImage(cover_image_path, (self.width - new_w) / 2, (self.height - new_h) / 2, new_w, new_h)
                
                # Add dark overlay if specified
                if self.style.get('overlay_darkness', 0) > 0:
                    c.setFillColor(black)
                    c.setFillAlpha(self.style['overlay_darkness'])
                    c.rect(0, 0, self.width, self.height, fill=1, stroke=0)
                    c.setFillAlpha(1.0)
            except Exception as e:
                print(f"Cover image error: {e}")
                c.setFillColor(HexColor('#1a1a1a'))
                c.rect(0, 0, self.width, self.height, fill=1)
        else:
            # No image - dark elegant background
            c.setFillColor(HexColor('#1a1a1a'))
            c.rect(0, 0, self.width, self.height, fill=1)
        
        # Style settings
        text_color = self.style.get('palette', white)
        accent = self.style.get('accent_color', HexColor('#E60012'))
        font_mh = self.style['font_masthead']
        font_main = self.style['font_main']
        use_shadow = self.style.get('text_shadow', True)
        mh_size = self.style.get('masthead_size', 100)
        
        # =====================================================================
        # MASTHEAD (Large centered title)
        # =====================================================================
        masthead_y = self.height - 1.2 * inch
        masthead_text = "NEURAL CITADEL"
        
        # Calculate centered position with scaling
        natural_w = c.stringWidth(masthead_text, font_mh, mh_size)
        max_w = self.width - 1.0 * inch
        scale_x = min(1.0, max_w / natural_w)
        visual_w = natural_w * scale_x
        start_x = (self.width - visual_w) / 2
        
        # Draw masthead with shadow
        c.saveState()
        if use_shadow:
            c.translate(start_x + 3, masthead_y - 3)
            c.scale(scale_x, 1.0)
            c.setFillColor(black)
            c.setFont(font_mh, mh_size)
            c.drawString(0, 0, masthead_text)
            c.restoreState()
            c.saveState()
        
        c.translate(start_x, masthead_y)
        c.scale(scale_x, 1.0)
        c.setFillColor(text_color)
        c.setFont(font_mh, mh_size)
        c.drawString(0, 0, masthead_text)
        c.restoreState()
        
        # =====================================================================
        # TOP STRIP (Minimal)
        # =====================================================================
        c.setFillColor(text_color)
        c.setFont('Helvetica', 8)
        c.drawCentredString(self.width / 2, self.height - 0.3 * inch, 
                            f"JANUARY 2026  •  THE FUTURE ISSUE  •  $9.99")
        
        # =====================================================================
        # FLOATING HEADLINES (Vogue-style)
        # =====================================================================
        if self.cover_articles and len(self.cover_articles) > 0:
            # Main headline at bottom
            main_art = self.cover_articles[0]
            main_title = main_art['title'].upper() if self.style.get('caps', True) else main_art['title']
            
            # Split into lines if too long
            words = main_title.split()
            lines = []
            curr = []
            for w in words:
                curr.append(w)
                if len(" ".join(curr)) > 18:
                    lines.append(" ".join(curr))
                    curr = []
            if curr:
                lines.append(" ".join(curr))
            
            # Draw main headline at bottom
            bottom_y = 1.8 * inch
            main_font_size = 48
            
            for i, line in enumerate(lines[:3]):
                line_w = c.stringWidth(line, font_main, main_font_size)
                
                # Center or align based on style
                if self.style.get('align') == 'left':
                    x = 0.6 * inch
                elif self.style.get('align') == 'right':
                    x = self.width - 0.6 * inch - line_w
                else:
                    x = (self.width - line_w) / 2
                
                self._draw_floating_text(c, x, bottom_y + (len(lines) - 1 - i) * main_font_size * 1.1,
                                         line, font_main, main_font_size, text_color, use_shadow)
            
            # Sub-headlines on the side
            if not self.style.get('minimal_layout'):
                side_y = self.height - 2.8 * inch
                side_font_size = 22
                
                for art in self.cover_articles[1:4]:
                    title = art['title'].upper() if self.style.get('caps', True) else art['title']
                    # Truncate long titles
                    if len(title) > 25:
                        title = title[:22] + "..."
                    
                    if self.style.get('align') == 'right' or self.style.get('sidebar_teasers'):
                        x = self.width - 0.6 * inch - c.stringWidth(title, font_main, side_font_size)
                    else:
                        x = 0.6 * inch
                    
                    self._draw_floating_text(c, x, side_y, title, font_main, side_font_size, 
                                             accent, use_shadow)
                    
                    # Category/author line
                    meta = f"{art.get('category', 'FEATURE')} // {art.get('author', 'Staff')}"
                    c.setFont(self.style['font_body'], 9)
                    c.setFillColor(text_color)
                    c.drawString(x, side_y - 15, meta)
                    
                    side_y -= 0.7 * inch
        
        # Small barcode (optional, more subtle)
        c.saveState()
        c.setFillAlpha(0.8)
        self._draw_barcode(c, 0.4 * inch, 0.4 * inch)
        c.restoreState()
        
        c.restoreState()

    def _create_cover(self, c, doc):
        # Dispatch to premium or standard cover based on mode
        if self.style.get('mode') == 'vogue_premium':
            return self._create_vogue_cover(c, doc)
        
        # ====== ORIGINAL STANDARD COVER CODE BELOW ======
        c.saveState()
        
        # 1. IMAGE Logic
        # STRICTLY uses Style Background or a Fixed Cover Image. 
        # For now, we default to the style's background to ensure standard "Font Page" look.
        # If we want a specific cover image for the style, it should be in cover_articles[0]['image']
        
        cover_image_path = None
        # Check if the STATIC cover content has a specific image (e.g. for The Star's cover story)
        if self.cover_articles and self.cover_articles[0].get('image'):
             cover_image_path = self.cover_articles[0]['image']
        
        # Fallback to style default background
        if not cover_image_path:
            cover_image_path = os.path.join(ASSET_DIR, self.style['bg'])

        
        palette = {'primary': HexColor('#E60023'), 'pastel': white, 'pop': white, 'dark': black}
        
        if cover_image_path and os.path.exists(cover_image_path):
            try:
                img = ImageReader(cover_image_path)
                iw, ih = img.getSize()
                scale = max(self.width / iw, self.height / ih)
                new_w, new_h = iw*scale, ih*scale
                c.drawImage(cover_image_path, (self.width-new_w)/2, (self.height-new_h)/2, new_w, new_h)
                
                _, base_rgb = get_dominant_color(cover_image_path)
                palette = generate_palette(base_rgb)
            except Exception as e:
                print(f"Img Error: {e}")
                c.setFillColor(black); c.rect(0,0,self.width,self.height,fill=1)

        # Override Palette from Style?
        if 'palette' in self.style:
            palette['primary'] = self.style['palette']
            
        # 2. MASTHEAD
        masthead_y = self.height - 1.8 * inch
        mh_color = palette['primary'] if palette['primary'] != black else white
        text = "NEURAL CITADEL"
        font = self.style['font_masthead']
        
        # Improved Scaling & Alignment Logic
        # Use safer margins to ensure "show the whole"
        side_margin = 0.5 * inch
        max_width = self.width - (2 * side_margin) # width - 1.0 inch
        size = 130 # Target Size
        
        c.saveState()
        natural_w = c.stringWidth(text, font, size)
        
        # Scaling
        scale_x = min(1.0, max_width / natural_w)
        visual_w = natural_w * scale_x
        
        # Positioning based on Alignment
        # Center = True Center
        start_x = (self.width - visual_w) / 2.0 
        
        if self.style['align'] == 'left': 
            # Left aligned but slightly indented ("a little bit right")
            start_x = 0.75 * inch 
            # Re-check scaling with new constraint?
            # Safe width for Left Align: self.width - 0.75 - 0.5 = width - 1.25
            left_safe_width = self.width - 0.75 * inch - 0.5 * inch
            if visual_w > left_safe_width:
                scale_x = min(1.0, left_safe_width / natural_w)
                visual_w = natural_w * scale_x

        if self.style['align'] == 'right':
             # Right aligned but with padding
             end_x = self.width - 0.75 * inch
             start_x = end_x - visual_w
             # Checked by global max_width usually, but extra safe:
             right_safe_width = self.width - 0.75*inch - 0.5*inch
             if visual_w > right_safe_width:
                 scale_x = min(1.0, right_safe_width / natural_w)
                 visual_w = natural_w * scale_x
                 start_x = end_x - visual_w

        # Draw Shadow
        c.saveState()
        c.translate(start_x + 3, masthead_y - 3)
        c.scale(scale_x, 1.0)
        c.setFillColor(black)
        c.setFont(font, size)
        c.drawString(0, 0, text)
        c.restoreState()
        
        # Draw Face
        c.saveState()
        c.translate(start_x, masthead_y)
        c.scale(scale_x, 1.0)
        c.setFillColor(mh_color)
        c.setFont(font, size)
        c.drawString(0, 0, text)
        c.restoreState()
        c.restoreState()

        # TOP STRIP
        c.setFillColor(black)
        c.rect(0, self.height - 0.4*inch, self.width, 0.4*inch, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont('Helvetica-Bold', 9)
        c.drawRightString(self.width - 0.5*inch, self.height - 0.25*inch, f"IG: @light_up_my_world01  |  GH: RajTewari01  |  $5.99  |  STYLE: {self.style_name.upper()}")
        c.drawString(0.5*inch, self.height - 0.25*inch, "PUBLISHER: Biswadeep Tewari (Raj)")
        
        # DATELINE
        tag_y = masthead_y - 0.35 * inch
        # Center dateline usually
        self._draw_text_block(c, self.width/2 - 100, tag_y, " THE FUTURE ISSUE • JANUARY 2026 ", 'Helvetica-Bold', 10, bg_color=black, text_color=white)

        # 3. COVER CONTENT
        # Logic varies by mode slightly, but keeping block structure for consistency
        start_y = tag_y - 1.2 * inch
        
        if self.cover_articles and len(self.cover_articles) > 1:
            for i, art in enumerate(self.cover_articles[1:4]):
                # Dynamic X Position Logic
                title = art['title'].upper() if self.style['caps'] else art['title']
                
                # Word-based wrapping
                words = title.split()
                lines = []
                curr = []
                for w in words:
                    curr.append(w)
                    if len(" ".join(curr)) > 20: # Slightly relaxed char limit
                        lines.append(" ".join(curr))
                        curr = []
                if curr: lines.append(" ".join(curr))
                
                bg = black
                if i == 1: bg = palette['primary']
                
                for line in lines[:2]:
                    # Calculate Width First
                    font_name = self.style['font_main']
                    font_size = 26
                    text_w = c.stringWidth(line, font_name, font_size)
                    
                    # Calculate Start X based on Alignment
                    if self.style['align'] == 'right':
                        # Flush Right against margin
                        x_pos = self.width - 0.5*inch - text_w
                    elif self.style['align'] == 'left':
                        x_pos = 0.5 * inch
                    else: # Center
                        x_pos = (self.width - text_w) / 2.0
                        
                    h = self._draw_text_block(c, x_pos, start_y, line, font_name, font_size, bg_color=bg, text_color=white, alpha=0.9)
                    start_y -= (h + 3)
                
                teaser = f"{art.get('category','FEAT')} // {art.get('author','Staff')}"
                # Teaser Alignment
                tw = c.stringWidth(teaser, self.style['font_body'], 10)
                if self.style['align'] == 'right': tx = self.width - 0.5*inch - tw
                elif self.style['align'] == 'left': tx = 0.5 * inch
                else: tx = (self.width - tw) / 2.0
                
                self._draw_text_block(c, tx, start_y, teaser, self.style['font_body'], 10, bg_color=white, text_color=black, alpha=0.8)
                start_y -= 0.7 * inch

        # MAIN STORY
        if self.cover_articles:
            main_art = self.cover_articles[0]
            title = main_art['title'].upper() if self.style['caps'] else main_art['title']
            
            # Dynamic Vertical Position based on Alignment (Barcode Safety)
            if self.style['align'] == 'left':
                bottom_y = 2.8 * inch # Must clear barcode (Bottom-Left)
            elif self.style['align'] == 'center':
                bottom_y = 2.0 * inch # Moderate lift
            else: # Right Aligned
                bottom_y = 1.6 * inch # Can be low and sleek (Barcode is on Left)
            
            # Label
            label_text = " COVER STORY "
            label_w = c.stringWidth(label_text, 'Helvetica-Bold', 14)
            label_x = (self.width - label_w) / 2 # Default center
            if self.style['align'] == 'left': label_x = 0.5 * inch
            elif self.style['align'] == 'right': label_x = self.width - 0.5 * inch - label_w
            
            self._draw_text_block(c, label_x, bottom_y + 90, label_text, 'Helvetica-Bold', 14, bg_color=palette['primary'], text_color=white)
            
            # Sub-Headline Logic
            # Smart wrapping
            words = title.split()
            lines = []
            curr = []
            for w in words:
                curr.append(w)
                if len(" ".join(curr)) > 15: # Tight wrap for impact
                    lines.append(" ".join(curr))
                    curr = []
            if curr: lines.append(" ".join(curr))
            
            y_curr = bottom_y + 30
            base_size = 52
            font_name = self.style['font_masthead']
            
            for line in lines:
                # 1. Scale to fit
                font_size = base_size
                safe_width = self.width - 1.0 * inch # 0.5 margin each side
                
                text_w = c.stringWidth(line, font_name, font_size)
                if text_w > safe_width:
                    scale_factor = safe_width / text_w
                    font_size *= scale_factor
                    text_w = safe_width # It now fits exactly
                
                # 2. Align
                if self.style['align'] == 'left':
                    x = 0.5 * inch
                elif self.style['align'] == 'right':
                    x = self.width - 0.5 * inch - text_w
                else:
                    x = (self.width - text_w) / 2
                
                # Draw
                c.setFont(font_name, font_size)
                c.setFillColor(black)
                c.drawString(x+3, y_curr-3, line)
                c.setFillColor(white)
                c.drawString(x, y_curr, line)
                
                y_curr -= (font_size + 5) # Move down by line height

        # Barcode (Bottom Left)
        self._draw_barcode(c, 0.5*inch, 0.5*inch)
        c.restoreState()

    def _create_inner_header(self, c, doc):
        c.saveState()
        c.setFont('Times-Bold', 12)
        c.drawString(0.5*inch, self.height - 0.8*inch, "NEURAL CITADEL")
        c.drawRightString(self.width - 0.5*inch, self.height - 0.8*inch, "JANUARY 2026")
        c.setLineWidth(2)
        c.line(0.5*inch, self.height - 0.9*inch, self.width - 0.5*inch, self.height - 0.9*inch)
        c.restoreState()
        self._create_footer(c, doc)

    def setup_page_templates(self, doc):
        cover_frame = Frame(0, 0, 0, 0, id='cover') 
        margin = 0.5 * inch
        available_width = self.width - 2*margin
        col_gap = 0.2 * inch
        col_w = (available_width - 2*col_gap) / 3
        f1 = Frame(margin, margin, col_w, self.height - 2*inch, id='col1')
        f2 = Frame(margin + col_w + col_gap, margin, col_w, self.height - 2*inch, id='col2')
        f3 = Frame(margin + 2*col_w + 2*col_gap, margin, col_w, self.height - 2*inch, id='col3')
        doc.addPageTemplates([
            PageTemplate(id='Cover', frames=[cover_frame], onPage=self._create_cover),
            PageTemplate(id='Inner', frames=[f1, f2, f3], onPage=self._create_inner_header)
        ])

    def convert_articles_to_flowables(self, articles):
        story = []
        story.append(NextPageTemplate('Inner'))
        story.append(PageBreak())
        
        for article in articles:
            # Detect font based on content
            title_font = get_font_for_text(article.get('title', ''))
            body_font = get_font_for_text(article.get('content', ''))
            
            # Create styles with detected fonts
            inner_title = ParagraphStyle(name='H1', fontName=title_font, fontSize=20, leading=22, spaceAfter=8, textColor=black)
            inner_body = ParagraphStyle(name='Body', fontName=body_font, fontSize=9, leading=12, alignment=TA_JUSTIFY, spaceAfter=8)
            
            story.append(Paragraph(article['title'], inner_title))
            story.append(Paragraph(f"By {article.get('author','Staff')}", ParagraphStyle('auth', parent=inner_body, fontName=body_font, fontSize=8)))
            story.append(Spacer(1, 6))
            if article.get('image'):
                col_width = (self.width - 1.4 * inch) / 3
                img = self.get_image(article['image'], width=col_width)
                if img:
                    story.append(img)
                    story.append(Spacer(1, 6))
            story.append(Paragraph(article['content'], inner_body))
            story.append(Spacer(1, 12))
            story.append(Paragraph("***", ParagraphStyle('sep', alignment=TA_CENTER)))
            story.append(Spacer(1, 12))
        return story
