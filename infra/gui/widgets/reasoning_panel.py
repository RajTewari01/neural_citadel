"""
Reasoning Panel - Premium Center Display
=========================================

Minimalist reasoning display for center panel.
Only shows when reasoning is active.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QApplication, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QCursor, QPainter, QBrush, QColor

from infra.gui.theme import ThemeManager

# Theme colors
PINK = "#E1306C"


class PulsingDot(QWidget):
    """Animated pulsing dot."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(12, 12)
        self._opacity = 1.0
        self._growing = False
        self._timer = QTimer()
        self._timer.timeout.connect(self._animate)
    
    def start(self):
        self._timer.start(50)
    
    def stop(self):
        self._timer.stop()
    
    def _animate(self):
        if self._growing:
            self._opacity += 0.1
            if self._opacity >= 1.0:
                self._growing = False
        else:
            self._opacity -= 0.1
            if self._opacity <= 0.3:
                self._growing = True
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(PINK)
        color.setAlphaF(self._opacity)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(1, 1, 10, 10)


class ReasoningCenterPanel(QWidget):
    """Premium reasoning display for center panel."""
    
    cancelled = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._elapsed = 0
        self._response_text = ""
        self._setup_ui()
        self.hide()
    
    def _setup_ui(self):
        self.setStyleSheet("background-color: transparent;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 40, 50, 30)
        layout.setSpacing(25)
        
        # Top bar with thinking indicator and close button
        top_bar = QHBoxLayout()
        
        # Thinking indicator (small, no border)
        thinking_row = QHBoxLayout()
        thinking_row.setSpacing(10)
        
        self.pulsing_dot = PulsingDot()
        thinking_row.addWidget(self.pulsing_dot)
        
        self.status_label = QLabel("Thinking...")
        self.status_label.setStyleSheet(f"""
            color: {PINK};
            font-family: 'Segoe UI', Consolas;
            font-size: 14px;
            background: transparent;
            font-weight: bold;
        """)
        thinking_row.addWidget(self.status_label)
        
        self.timer_label = QLabel("0:00")
        # Style set in update_theme
        thinking_row.addWidget(self.timer_label)
        
        top_bar.addLayout(thinking_row)
        top_bar.addStretch()
        
        # Close button (Proper button style)
        self.close_btn = QPushButton("Close")
        self.close_btn.setFixedSize(70, 30)
        self.close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        # Style set in update_theme
        self.close_btn.clicked.connect(lambda: self.cancelled.emit())
        top_bar.addWidget(self.close_btn)
        
        layout.addLayout(top_bar)
        
        # Response area (center, scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
            }
            QScrollBar::handle:vertical {
                background: rgba(128, 128, 128, 0.3);
                border-radius: 3px;
            }
        """)
        
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Streaming text label (centered) - Use TextFormat for proper line breaks
        self.response_label = QLabel("")
        self.response_label.setWordWrap(True)
        self.response_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.response_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.response_label.setTextFormat(Qt.TextFormat.PlainText)  # Proper newline handling
        # Style set in update_theme
        content_layout.addWidget(self.response_label)
        content_layout.addStretch()
        
        scroll.setWidget(content)
        self.scroll = scroll
        layout.addWidget(scroll, stretch=1)
        
        # Footer with copy button
        footer = QHBoxLayout()
        footer.addStretch()
        
        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setFixedSize(85, 30)
        self.copy_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.copy_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #833AB4, stop:1 {PINK});
                color: white;
                border: none;
                border-radius: 15px;
                font-family: Consolas;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #9b4fc9, stop:1 #f04080);
            }}
        """)
        self.copy_btn.clicked.connect(self._copy_text)
        self.copy_btn.hide()
        footer.addWidget(self.copy_btn)
        
        layout.addLayout(footer)
        
        # Timer
        self._elapsed_timer = QTimer()
        self._elapsed_timer.timeout.connect(self._update_timer)
        
        # Initial theme update
        self.update_theme()
    
    def update_theme(self):
        """Update styles based on current theme."""
        theme = ThemeManager.get_theme()
        is_dark = theme.name == "dark"
        
        # Text colors - Light Red for Light Mode (user said #8B0000 looks brown)
        text_color = "#ffffff" if is_dark else "#FF5252"  # Light Red
        timer_color = "#888888" if is_dark else "#555555"
        
        # Background Colors
        bg_color = "#0a0a0a" if is_dark else "#fcfcfc"
        
        self.setStyleSheet(f"background-color: {bg_color};")
        
        # Timer style
        self.timer_label.setStyleSheet(f"""
            color: {timer_color};
            font-family: Consolas;
            font-size: 12px;
            background: transparent;
            margin-left: 15px;
        """)
        
        # Response text style - proper line height for readability
        self.response_label.setStyleSheet(f"""
            color: {text_color};
            font-family: 'Segoe UI', Consolas;
            font-size: 15px;
            line-height: 1.8;
            background: transparent;
            padding: 5px 0;
        """)
        
        # Close button style
        if is_dark:
            # User said "ok in dark mode"
            btn_bg = "#252525"          # Dark Grey
            btn_text = "#e0e0e0"        # Light text
            btn_hover = "#333333"       
            btn_pressed = "#404040"
        else:
            # User said "grey background and black text"
            btn_bg = "#c0c0c0"          # Visible Medium Grey
            btn_text = "#000000"        # Black Text
            btn_hover = "#b0b0b0"       
            btn_pressed = "#a0a0a0"
            
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {btn_bg};
                color: {btn_text};
                border: none;
                border-radius: 15px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
                font-weight: 600;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background-color: {btn_hover};
                color: {PINK};
            }}
            QPushButton:pressed {{
                background-color: {btn_pressed};
                color: {PINK};
            }}
        """)
    
    def _update_timer(self):
        self._elapsed += 1
        mins = self._elapsed // 60
        secs = self._elapsed % 60
        self.timer_label.setText(f"{mins}:{secs:02d}")
    
    def start(self):
        """Start reasoning display."""
        self.update_theme() # Ensure theme is current
        
        self._elapsed = 0
        self._response_text = ""
        
        # Determine status color based on theme
        theme = ThemeManager.get_theme()
        is_dark = theme.name == "dark"
        status_color = PINK if is_dark else "#FF5252"  # Light Red for Light Mode
        
        self.response_label.setText("")
        self.copy_btn.hide()
        self.status_label.setText("Thinking...")
        self.status_label.setStyleSheet(f"color: {status_color}; font-size: 14px; background: transparent; font-weight: bold;")
        self.timer_label.setText("0:00")
        
        self.pulsing_dot.start()
        self._elapsed_timer.start(1000)
        self.show()
    
    def on_think_start(self):
        self.status_label.setText("Reasoning...")
    
    def on_token(self, token: str):
        """Streaming token."""
        self._response_text += token
        self.response_label.setText(self._response_text + "▌")
        
        # Auto-scroll
        scrollbar = self.scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def on_think_end(self):
        self.status_label.setText("Answering...")
    
    def finish(self):
        """Complete."""
        self.pulsing_dot.stop()
        self._elapsed_timer.stop()
        
        # Determine status color based on theme
        theme = ThemeManager.get_theme()
        is_dark = theme.name == "dark"
        # Orange for completion indicator (visible in both modes)
        status_color = "#7CFC00" if is_dark else "#FF7043"  # Light Orange for Light Mode
        
        self.status_label.setText("Complete")
        self.status_label.setStyleSheet(f"color: {status_color}; font-size: 14px; background: transparent; font-weight: bold;")
        
        self.response_label.setText(self._response_text)
        self.copy_btn.show()
    
    def on_error(self, msg: str):
        self.pulsing_dot.stop()
        self._elapsed_timer.stop()
        
        self.status_label.setText("Error")
        self.status_label.setStyleSheet("color: #ff6666; font-size: 14px; background: transparent; font-weight: bold;")
        self.response_label.setText(f"Error: {msg}")
    
    def _copy_text(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self._response_text)
        self.copy_btn.setText("Copied!")
        QTimer.singleShot(1500, lambda: self.copy_btn.setText("Copy"))
    
    def reset(self):
        self._response_text = ""
        self.response_label.setText("")
        self.copy_btn.hide()
