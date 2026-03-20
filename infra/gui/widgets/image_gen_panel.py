"""
Image Generation Panel
======================

UI panel for selecting image generation model and settings.
Shows only when Image Generation mode is selected.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QPushButton, QRadioButton, QButtonGroup,
    QFrame, QToolTip, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QCursor, QFont

from .image_models import IMAGE_MODELS, ASPECT_RATIOS, get_model_by_name
from infra.gui.theme import ThemeManager


# Instagram colors
PURPLE = "#833AB4"
PINK = "#E1306C"
ORANGE = "#F77737"


class ImageGenPanel(QWidget):
    """
    Panel for image generation settings.
    Appears below chat input when Image Gen mode is selected.
    """
    
    generate_requested = pyqtSignal(str, str, str, str, object)  # prompt, pipeline, type, aspect, seed (int or None)
    
    def __init__(self):
        super().__init__()
        self.setObjectName("ImageGenPanel")
        self._setup_ui()
        self.hide()  # Hidden by default
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        
        # Header
        self.header = QLabel("🎨 IMAGE GENERATION")
        self.header.setObjectName("header")
        self.header.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        layout.addWidget(self.header)
        
        # Model selector row
        model_row = QHBoxLayout()
        model_row.setSpacing(8)
        
        self.model_label = QLabel("Model:")
        model_row.addWidget(self.model_label)
        
        self.model_combo = QComboBox()
        self.model_combo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # Populate models
        for display_name, pipeline, type_name, icon, desc in IMAGE_MODELS:
            self.model_combo.addItem(f"{icon} {display_name}", (pipeline, type_name, desc))
            
        model_row.addWidget(self.model_combo, stretch=1)
        
        # Info button
        self.info_btn = QPushButton("ⓘ")
        self.info_btn.setFixedSize(24, 24)
        self.info_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.info_btn.clicked.connect(self._show_model_info)
        model_row.addWidget(self.info_btn)
        
        layout.addLayout(model_row)
        
        # Aspect ratio row
        aspect_row = QHBoxLayout()
        aspect_row.setSpacing(8)
        
        self.aspect_label = QLabel("Aspect:")
        aspect_row.addWidget(self.aspect_label)
        
        self.aspect_group = QButtonGroup(self)
        self.radios = []
        
        for i, (name, value, tooltip) in enumerate(ASPECT_RATIOS):
            radio = QRadioButton(name)
            radio.setProperty("aspect_value", value)
            radio.setToolTip(tooltip)
            radio.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.aspect_group.addButton(radio, i)
            aspect_row.addWidget(radio)
            self.radios.append(radio)
            
            if i == 0:  # Default to portrait
                radio.setChecked(True)
        
        aspect_row.addStretch()
        layout.addLayout(aspect_row)
        
        # Seed row
        seed_row = QHBoxLayout()
        seed_row.setSpacing(8)
        
        self.seed_label = QLabel("Seed:")
        seed_row.addWidget(self.seed_label)
        
        self.seed_input = QLineEdit()
        self.seed_input.setPlaceholderText("Auto")
        self.seed_input.setFixedWidth(80)
        seed_row.addWidget(self.seed_input)
        
        seed_row.addStretch()
        layout.addLayout(seed_row)
        
        # Initial Styling
        self.update_theme()

    def update_theme(self):
        """Update styles based on current theme."""
        theme = ThemeManager.get_theme()
        is_dark = theme.name == "dark"
        
        if is_dark:
            bg_color = "rgba(20, 15, 25, 0.95)"
            border_color = "#2a2a3a"
            text_color = "#ffffff"
            label_color = "#888"
            input_bg = "#1a1a1a"
            input_border = "#333"
            radio_unchecked = "#333"
            combo_hover = PINK
        else:
            bg_color = "rgba(255, 255, 255, 0.95)"
            border_color = "#e0e0e0"
            text_color = "#000000"
            label_color = "#666"
            input_bg = "#f8f9fa"
            input_border = "#ddd"
            radio_unchecked = "#ddd"
            combo_hover = "#9B6EB7"

        self.setStyleSheet(f"""
            QWidget#ImageGenPanel {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 12px;
            }}
            QLabel {{
                color: {label_color};
                font-family: Consolas;
                font-size: 11px;
            }}
            QLabel#header {{
                color: {PINK};
                font-family: Consolas;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
        """)

        # Combo Box Style
        self.model_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {input_bg};
                color: {text_color};
                border: 1px solid {input_border};
                border-radius: 6px;
                padding: 6px 10px;
                font-family: Consolas;
                font-size: 11px;
            }}
            QComboBox:hover {{
                border-color: {combo_hover};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {input_bg};
                color: {text_color};
                border: 1px solid {input_border};
                selection-background-color: {PINK};
                selection-color: white;
            }}
        """)

        # Info Button Style
        self.info_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {label_color};
                border: 1px solid {input_border};
                border-radius: 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                color: {PINK};
                border-color: {PINK};
            }}
        """)

        # Seed Input Style
        self.seed_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {input_bg};
                color: {text_color};
                border: 1px solid {input_border};
                border-radius: 6px;
                padding: 4px 8px;
                font-family: Consolas;
                font-size: 11px;
            }}
            QLineEdit:focus {{
                border-color: {PINK};
            }}
        """)

        # Radio Button Style
        radio_style = f"""
            QRadioButton {{
                color: {label_color};
                font-size: 11px;
                font-family: Consolas;
                spacing: 6px;
            }}
            QRadioButton:hover {{
                color: {PINK};
            }}
            QRadioButton::indicator {{
                width: 14px;
                height: 14px;
                border: 1px solid {input_border};
                border-radius: 8px;
                background: {input_bg};
            }}
            QRadioButton::indicator:checked {{
                background: {PINK};
                border: 1px solid {PINK};
            }}
            QRadioButton::indicator:unchecked {{
                background: {radio_unchecked};
            }}
        """
        for radio in self.radios:
            radio.setStyleSheet(radio_style)
    
    def _show_model_info(self):
        """Show tooltip with model description."""
        idx = self.model_combo.currentIndex()
        if idx >= 0:
            data = self.model_combo.itemData(idx)
            if data and len(data) >= 3:
                desc = data[2]
                pos = self.info_btn.mapToGlobal(QPoint(0, -30))
                QToolTip.showText(pos, desc, self.info_btn)
    
    def get_current_model(self):
        """Get current model selection."""
        idx = self.model_combo.currentIndex()
        if idx >= 0:
            data = self.model_combo.itemData(idx)
            return data[0], data[1]  # pipeline, type
        return None, None
    
    def get_aspect_ratio(self):
        """Get selected aspect ratio."""
        checked = self.aspect_group.checkedButton()
        if checked:
            return checked.property("aspect_value")
        return "portrait"
    
    def get_seed(self):
        """Get seed value or None if auto."""
        text = self.seed_input.text().strip()
        if text and text.isdigit():
            return int(text)
        return None
    
    def request_generation(self, prompt: str):
        """Emit generate request with current settings."""
        pipeline, type_name = self.get_current_model()
        aspect = self.get_aspect_ratio()
        seed = self.get_seed()
        self.generate_requested.emit(prompt, pipeline, type_name or "", aspect, seed)
