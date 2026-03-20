"""
Model Selector Popup
====================

Custom popup with search and scrollable list for model selection.
Supports 200+ models with fixed Auto-listen at bottom.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QScrollArea, QWidget, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor, QFont

# Instagram colors
PURPLE = "#833AB4"
PINK = "#E1306C"
ORANGE = "#F77737"

# Model options (expandable for 200+ models)
MODEL_OPTIONS = [
    ("💬", "Chat", "General conversation"),
    ("🧠", "Reasoning", "Deep thinking & analysis"),
    ("🎨", "Image Generation", "Create images from text"),
    ("🎬", "Movie Downloader", "Download videos & movies"),
    ("📰", "Newspaper", "Generate PDF newspapers"),
    ("📂", "Gallery", "View generated & downloaded media"),
    ("📱", "QR Studio", "Generate styled QR codes"),
    ("💻", "Code", "Programming assistance"),
    ("💀", "Hacking", "Offensive security tools"),
    ("✍️", "Writing", "Creative writing & personas"),
    ("🔥", "NSFW Stories", "Adult creative fiction"),
    ("🔍", "Search", "Web search & research"),
    ("📄", "Document", "Analyze documents"),
]


class ModelItem(QFrame):
    """Single model item in the list."""
    
    clicked = pyqtSignal(str, str)  # icon, name
    
    def __init__(self, icon: str, name: str, desc: str, is_dark: bool = True):
        super().__init__()
        self.icon = icon
        self.name = name
        self.desc = desc
        self._is_dark = is_dark
        self._setup_ui()
    
    def _setup_ui(self):
        self.setObjectName("modelItem")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)
        
        icon_label = QLabel(self.icon)
        icon_label.setStyleSheet("font-size: 13px; background: transparent; border: none;")
        layout.addWidget(icon_label)
        
        name_label = QLabel(self.name)
        if self._is_dark:
            name_label.setStyleSheet("color: #e0e0e0; font-size: 11px; font-family: 'Segoe UI', sans-serif; background: transparent; border: none;")
        else:
            name_label.setStyleSheet("color: #444; font-size: 11px; font-family: 'Segoe UI', sans-serif; font-weight: 500; background: transparent; border: none;")
        layout.addWidget(name_label)
        
        layout.addStretch()
        
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        if self._is_dark:
            self.setStyleSheet(f"""
                QFrame#modelItem {{
                    background-color: transparent;
                    border-radius: 6px;
                    border: none;
                }}
                QFrame#modelItem:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(131, 58, 180, 0.4), stop:1 rgba(225, 48, 108, 0.4));
                }}
            """)
        else:
            self.setStyleSheet("""
                QFrame#modelItem {
                    background-color: transparent;
                    border-radius: 6px;
                    border: none;
                }
                QFrame#modelItem:hover {
                    background-color: rgba(0, 0, 0, 0.05);
                }
            """)
        

    
    def mousePressEvent(self, event):
        self.clicked.emit(self.icon, self.name)


class ModelSelectorPopup(QDialog):
    """
    Custom popup with search and scrollable model list.
    Auto-listen stays fixed at the bottom.
    """
    
    model_selected = pyqtSignal(str, str)  # icon, name
    auto_listen_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(240)
        self.setMaximumHeight(360)
        
        # Get current theme
        from infra.gui.theme import ThemeManager
        theme = ThemeManager.get_theme()
        is_dark = theme.name == "dark"
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Container with theme-aware styling
        container = QFrame()
        container.setObjectName("popupContainer")
        
        # Sleek premium styling
        if is_dark:
            container.setStyleSheet("""
                QFrame#popupContainer {
                    background-color: rgba(15, 15, 20, 0.98);
                    border: 1px solid rgba(80, 80, 100, 0.5);
                    border-radius: 16px;
                }
            """)
        else:
            container.setStyleSheet("""
                QFrame#popupContainer {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 rgba(255, 255, 255, 0.98),
                        stop:1 rgba(245, 240, 250, 0.98));
                    border: 1px solid rgba(200, 190, 210, 0.5);
                    border-radius: 16px;
                }
            """)
            
        # Add drop shadow for depth
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 5)
        container.setGraphicsEffect(shadow)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(12, 12, 12, 12)
        container_layout.setSpacing(8)
        
        # Search input - theme-aware & sleek
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        if is_dark:
            self.search_input.setStyleSheet(f"""
                QLineEdit {{
                    background-color: rgba(30, 30, 40, 0.6);
                    color: #fff;
                    border: 1px solid rgba(255,255,255,0.08);
                    border-radius: 8px;
                    padding: 8px 12px;
                    font-family: 'Segoe UI', sans-serif;
                    font-size: 13px;
                }}
                QLineEdit:focus {{
                    border: 1px solid {PINK};
                    background-color: rgba(40, 40, 50, 0.8);
                }}
            """)
        else:
            self.search_input.setStyleSheet("""
                QLineEdit {
                    background-color: rgba(240, 240, 245, 0.6);
                    color: #333;
                    border: 1px solid rgba(0,0,0,0.05);
                    border-radius: 8px;
                    padding: 8px 12px;
                    font-family: 'Segoe UI', sans-serif;
                    font-size: 13px;
                }
                QLineEdit:focus {
                    border: 1px solid #9B6EB7;
                    background-color: #fff;
                }
            """)
        self.search_input.textChanged.connect(self._filter_models)
        container_layout.addWidget(self.search_input)
        
        # Store theme for model items
        self._is_dark = is_dark
        
        # Scrollable model list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: transparent;
                width: 4px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #833AB4, stop:1 #E1306C);
                border-radius: 2px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)
        
        self.model_container = QWidget()
        self.model_layout = QVBoxLayout(self.model_container)
        self.model_layout.setContentsMargins(0, 2, 0, 2)
        self.model_layout.setSpacing(1)
        
        # Add model items
        self.model_items = []
        for icon, name, desc in MODEL_OPTIONS:
            item = ModelItem(icon, name, desc, is_dark=self._is_dark)
            item.clicked.connect(self._on_model_clicked)
            self.model_items.append(item)
            self.model_layout.addWidget(item)
        
        self.model_layout.addStretch()
        scroll.setWidget(self.model_container)
        container_layout.addWidget(scroll)
        
        # Separator - subtle gradient line
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #833AB4, stop:0.5 #E1306C, stop:1 #F77737); margin: 4px 8px;")
        container_layout.addWidget(sep)
        
        # Fixed Auto-listen at bottom - sleeker
        auto_listen = QFrame()
        auto_listen_layout = QHBoxLayout(auto_listen)
        auto_listen_layout.setContentsMargins(10, 6, 10, 6)
        
        mic_label = QLabel("🎤")
        mic_label.setStyleSheet("font-size: 14px;")
        auto_listen_layout.addWidget(mic_label)
        
        listen_text = QLabel("Auto-Listen")
        # Ensure deep red color for visibility in light mode
        text_color = "#e0e0e0" if is_dark else "#b71c1c" 
        listen_text.setStyleSheet(f"color: {text_color}; font-size: 11px; font-family: Consolas; font-weight: bold;")
        auto_listen_layout.addWidget(listen_text)
        
        auto_listen_layout.addStretch()
        
        auto_listen.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        auto_listen.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border-radius: 6px;
            }
            QFrame:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #F77737, stop:0.5 #E1306C, stop:1 #833AB4);
            }
        """)
        auto_listen.mousePressEvent = lambda e: self._trigger_auto_listen()
        container_layout.addWidget(auto_listen)
        
        layout.addWidget(container)
    
    def _filter_models(self, text: str):
        """Filter model list based on search text."""
        text = text.lower()
        for item in self.model_items:
            visible = text in item.name.lower() or text in item.icon
            item.setVisible(visible)
    
    def _on_model_clicked(self, icon: str, name: str):
        """Handle model selection."""
        self.model_selected.emit(icon, name)
        self.close()
    
    def _trigger_auto_listen(self):
        """Trigger auto-listen mode."""
        self.auto_listen_requested.emit()
        self.close()
