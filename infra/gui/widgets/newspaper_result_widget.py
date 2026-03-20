
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QCursor
import os

class NewspaperResultWidget(QFrame):
    """
    Chat bubble widget for Newspaper generation result.
    Shows success message, path, and action buttons.
    """
    
    def __init__(self, pdf_path: str):
        super().__init__()
        self.pdf_path = pdf_path
        self._setup_ui()
        
    def _setup_ui(self):
        # Interactive bubble styling
        # Matches AI bubble gradient (blue/violet)
        self.setStyleSheet("""
            NewspaperResultWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a3e, stop:0.5 #2d1b4e, stop:1 #1e3a5f);
                border: 1px solid #3d3d6b;
                border-radius: 12px;
                margin-right: 40px;
            }
            QLabel {
                color: #e0e0e0;
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 6px;
                color: #fff;
                padding: 6px 12px;
                font-family: Consolas;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.05);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(10)
        
        # Header
        header = QHBoxLayout()
        icon = QLabel("📰 ✅")
        icon.setStyleSheet("font-size: 16px;")
        header.addWidget(icon)
        
        title = QLabel("Newspaper Generated")
        title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        # Path
        self.path_label = QLabel(self.pdf_path)
        self.path_label.setStyleSheet("color: #888; font-size: 11px; font-family: Consolas;")
        self.path_label.setWordWrap(True)
        layout.addWidget(self.path_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        self.copy_btn = QPushButton("📋 Copy Path")
        self.copy_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.copy_btn.clicked.connect(self._copy_path)
        btn_layout.addWidget(self.copy_btn)
        
        self.open_btn = QPushButton("📂 Open PDF")
        self.open_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.open_btn.clicked.connect(self._open_pdf)
        btn_layout.addWidget(self.open_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
    def _copy_path(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.pdf_path)
        self.copy_btn.setText("✓ Copied!")
        QTimer.singleShot(2000, lambda: self.copy_btn.setText("📋 Copy Path"))
        
    def _open_pdf(self):
        if os.path.exists(self.pdf_path):
            os.startfile(self.pdf_path)
