"""
Image Popup Window
==================

Popup window to display generated images.
Shows the image in a window with title bar and close button.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QCursor, QFont

# Instagram colors
PURPLE = "#833AB4"
PINK = "#E1306C"
ORANGE = "#F77737"


class ImagePopup(QDialog):
    """
    Popup window to display a generated image.
    Opens when image generation is complete.
    """
    
    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self._setup_ui()
    
    def _setup_ui(self):
        # Regular dialog with title (not frameless for visibility)
        self.setWindowTitle("🎨 Generated Image")
        self.setModal(False)
        
        # Dark themed styling
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #0a0a0f;
            }}
            QLabel {{
                color: #cccccc;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Image display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Load and display image
        import os
        if os.path.exists(self.image_path):
            pixmap = QPixmap(self.image_path)
            if not pixmap.isNull():
                # Scale to fit screen while maintaining aspect ratio
                max_size = QSize(800, 600)
                scaled = pixmap.scaled(
                    max_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.image_label.setPixmap(scaled)
                self.resize(scaled.width() + 32, scaled.height() + 100)
            else:
                self.image_label.setText("Failed to load image")
                self.image_label.setStyleSheet("color: #aa5555;")
        else:
            self.image_label.setText(f"Image not found:\n{self.image_path}")
            self.image_label.setStyleSheet("color: #aa5555;")
        
        layout.addWidget(self.image_label)
        
        # Path label
        path_label = QLabel(f"📁 {self.image_path}")
        path_label.setStyleSheet("color: #666; font-size: 10px; font-family: Consolas;")
        path_label.setWordWrap(True)
        layout.addWidget(path_label)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {PINK};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-family: Consolas;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {PURPLE};
            }}
        """)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)


def show_image_popup(image_path: str, parent=None):
    """Show an image popup window."""
    popup = ImagePopup(image_path, parent)
    popup.exec()
