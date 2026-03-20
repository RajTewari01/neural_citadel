
from reportlab.platypus import Flowable
from reportlab.lib.colors import white, black
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

class ImageWithTextOverlay(Flowable):
    def __init__(self, img_path, width, text, font_name='Helvetica-Bold', font_size=24):
        Flowable.__init__(self)
        self.img_path = img_path
        self.width = width
        self.text = text
        self.font_name = font_name
        self.font_size = font_size
        
        try:
            self.img = ImageReader(img_path)
            iw, ih = self.img.getSize()
            aspect = ih / float(iw)
            self.height = width * aspect
        except:
            self.img = None
            self.height = 0

    def draw(self):
        if not self.img:
            return

        # Draw Image
        self.canv.drawImage(self.img_path, 0, 0, width=self.width, height=self.height)
        
        # Draw Text Overlay
        # Centered, with stroke for visibility ("changing colors" effect)
        self.canv.saveState()
        self.canv.setFont(self.font_name, self.font_size)
        
        # Basic wrapping for very long titles (simple implementation)
        # We'll just draw it centered at the bottom third for visibility
        y_pos = self.height / 2.0
        
        # Manual Outline/Shadow Effect for "Visible in any part"
        # We draw a thick black outline/shadow behind the white text
        offsets = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1),
            (-2, -2), (2, 2) # Extra depth
        ]
        
        self.canv.setFillColor(black)
        for ox, oy in offsets:
             self.canv.drawCentredString(self.width / 2.0 + ox, y_pos + oy, self.text)
        
        # Draw main white text
        self.canv.setFillColor(white)
        self.canv.drawCentredString(self.width / 2.0, y_pos, self.text)
        
        self.canv.restoreState()
