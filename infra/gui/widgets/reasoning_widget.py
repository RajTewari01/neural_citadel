"""
Reasoning Widget - Premium ChatGPT-like Streaming Display
==========================================================

Center-screen overlay widget for reasoning mode.
Features:
- Animated thinking indicator
- Live token streaming
- Collapsible <think> block
- Timer and cancel button
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPainter, QLinearGradient, QCursor

# Instagram gradient colors
PURPLE = "#833AB4"
PINK = "#E1306C"
ORANGE = "#F77737"


class ThinkingBlock(QFrame):
    """Collapsible thinking block with premium styling."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_expanded = False
        self._content = ""
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet("""
            ThinkingBlock {
                background: rgba(131, 58, 180, 0.15);
                border: 1px solid rgba(131, 58, 180, 0.4);
                border-radius: 12px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)
        
        # Header
        header = QHBoxLayout()
        
        self.toggle_btn = QPushButton("💭 Thinking...")
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #B38BDB;
                font-family: Consolas;
                font-size: 12px;
                font-weight: bold;
                text-align: left;
                padding: 4px;
            }
            QPushButton:hover {
                color: #D4A5FF;
            }
        """)
        self.toggle_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.toggle_btn.clicked.connect(self._toggle)
        header.addWidget(self.toggle_btn)
        
        header.addStretch()
        
        self.expand_icon = QLabel("▼")
        self.expand_icon.setStyleSheet("color: #B38BDB; font-size: 10px;")
        header.addWidget(self.expand_icon)
        
        layout.addLayout(header)
        
        # Content (hidden by default)
        self.content_label = QLabel()
        self.content_label.setWordWrap(True)
        self.content_label.setStyleSheet("""
            QLabel {
                color: #C4A6E2;
                font-family: Consolas;
                font-size: 11px;
                padding: 8px;
                background: rgba(0, 0, 0, 0.2);
                border-radius: 8px;
            }
        """)
        self.content_label.hide()
        layout.addWidget(self.content_label)
    
    def _toggle(self):
        self._is_expanded = not self._is_expanded
        self.content_label.setVisible(self._is_expanded)
        self.expand_icon.setText("▲" if self._is_expanded else "▼")
        self.toggle_btn.setText("💭 Thinking" if self._is_expanded else "💭 Thinking...")
    
    def add_token(self, token: str):
        self._content += token
        self.content_label.setText(self._content)
    
    def finish(self):
        self.toggle_btn.setText(f"💭 Thinking ({len(self._content)} chars)")
    
    def clear(self):
        self._content = ""
        self.content_label.setText("")


class AnswerBlock(QFrame):
    """Premium answer display block."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._content = ""
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet("""
            AnswerBlock {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(131, 58, 180, 0.1),
                    stop:0.5 rgba(225, 48, 108, 0.1),
                    stop:1 rgba(247, 119, 55, 0.1));
                border: 1px solid rgba(225, 48, 108, 0.3);
                border-radius: 12px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        # Header
        header = QLabel("✨ Answer")
        header.setStyleSheet(f"""
            QLabel {{
                color: {PINK};
                font-family: Consolas;
                font-size: 13px;
                font-weight: bold;
            }}
        """)
        layout.addWidget(header)
        
        # Content with cursor
        self.content_label = QLabel()
        self.content_label.setWordWrap(True)
        self.content_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-family: Consolas;
                font-size: 14px;
                line-height: 1.5;
            }
        """)
        layout.addWidget(self.content_label)
        
        # Blinking cursor
        self._cursor_visible = True
        self._cursor_timer = QTimer()
        self._cursor_timer.timeout.connect(self._blink_cursor)
    
    def start_streaming(self):
        self._cursor_timer.start(500)
        self._update_display()
    
    def stop_streaming(self):
        self._cursor_timer.stop()
        self._cursor_visible = False
        self._update_display()
    
    def _blink_cursor(self):
        self._cursor_visible = not self._cursor_visible
        self._update_display()
    
    def _update_display(self):
        cursor = "▌" if self._cursor_visible else ""
        self.content_label.setText(self._content + cursor)
    
    def add_token(self, token: str):
        self._content += token
        self._update_display()
    
    def clear(self):
        self._content = ""
        self.content_label.setText("")


class ReasoningWidget(QWidget):
    """
    Center-screen reasoning display overlay.
    
    Signals:
        cancelled: User cancelled reasoning
    """
    
    cancelled = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._elapsed_seconds = 0
        self._in_think_block = False
        self._setup_ui()
        self._setup_timer()
    
    def _setup_ui(self):
        self.setStyleSheet("""
            ReasoningWidget {
                background: rgba(10, 10, 20, 0.95);
                border: 2px solid;
                border-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #833AB4, stop:0.5 #E1306C, stop:1 #F77737);
                border-radius: 20px;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)
        
        # Header row
        header = QHBoxLayout()
        
        # Pulsing brain icon
        self.brain_label = QLabel("🧠")
        self.brain_label.setStyleSheet("font-size: 24px;")
        header.addWidget(self.brain_label)
        
        # Status
        self.status_label = QLabel("Thinking...")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {PURPLE};
                font-family: Consolas;
                font-size: 16px;
                font-weight: bold;
            }}
        """)
        header.addWidget(self.status_label)
        
        header.addStretch()
        
        # Timer
        self.timer_label = QLabel("0:00")
        self.timer_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-family: Consolas;
                font-size: 12px;
            }
        """)
        header.addWidget(self.timer_label)
        
        # Cancel button
        self.cancel_btn = QPushButton("✕")
        self.cancel_btn.setFixedSize(28, 28)
        self.cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 14px;
                color: #888;
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(255, 100, 100, 0.3);
                color: #ff6666;
            }
        """)
        self.cancel_btn.clicked.connect(self._on_cancel)
        header.addWidget(self.cancel_btn)
        
        main_layout.addLayout(header)
        
        # Scroll area for content
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
                background: rgba(255, 255, 255, 0.2);
                border-radius: 3px;
            }
        """)
        
        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(12)
        
        # Thinking block
        self.thinking_block = ThinkingBlock()
        self.thinking_block.hide()
        self.content_layout.addWidget(self.thinking_block)
        
        # Answer block
        self.answer_block = AnswerBlock()
        self.content_layout.addWidget(self.answer_block)
        
        self.content_layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
        # Pulse animation for brain
        self._pulse_timer = QTimer()
        self._pulse_timer.timeout.connect(self._pulse_brain)
        self._pulse_state = 0
    
    def _setup_timer(self):
        self._elapsed_timer = QTimer()
        self._elapsed_timer.timeout.connect(self._update_timer)
    
    def _update_timer(self):
        self._elapsed_seconds += 1
        mins = self._elapsed_seconds // 60
        secs = self._elapsed_seconds % 60
        self.timer_label.setText(f"{mins}:{secs:02d}")
    
    def _pulse_brain(self):
        emojis = ["🧠", "💭", "✨", "💡"]
        self._pulse_state = (self._pulse_state + 1) % len(emojis)
        self.brain_label.setText(emojis[self._pulse_state])
    
    def start(self):
        """Start the reasoning display."""
        self._elapsed_seconds = 0
        self._elapsed_timer.start(1000)
        self._pulse_timer.start(300)
        self.thinking_block.clear()
        self.thinking_block.hide()
        self.answer_block.clear()
        self.answer_block.start_streaming()
        self.status_label.setText("Thinking...")
        self.show()
    
    def on_think_start(self):
        """Handle entering think block."""
        self._in_think_block = True
        self.thinking_block.show()
        self.status_label.setText("Reasoning...")
    
    def on_token(self, token: str):
        """Handle incoming token."""
        if self._in_think_block:
            self.thinking_block.add_token(token)
        else:
            self.answer_block.add_token(token)
    
    def on_think_end(self):
        """Handle exiting think block."""
        self._in_think_block = False
        self.thinking_block.finish()
        self.status_label.setText("Answering...")
    
    def finish(self):
        """Finish reasoning display."""
        self._elapsed_timer.stop()
        self._pulse_timer.stop()
        self.brain_label.setText("✅")
        self.status_label.setText("Complete")
        self.answer_block.stop_streaming()
    
    def on_error(self, msg: str):
        """Handle error."""
        self._elapsed_timer.stop()
        self._pulse_timer.stop()
        self.brain_label.setText("❌")
        self.status_label.setText("Error")
        self.status_label.setStyleSheet("color: #ff6666; font-size: 16px; font-weight: bold;")
        self.answer_block.stop_streaming()
    
    def _on_cancel(self):
        """Handle cancel button click."""
        self._elapsed_timer.stop()
        self._pulse_timer.stop()
        self.cancelled.emit()
    
    def reset(self):
        """Reset widget for new query."""
        self.thinking_block.clear()
        self.thinking_block.hide()
        self.answer_block.clear()
        self._in_think_block = False
        self.status_label.setStyleSheet(f"color: {PURPLE}; font-size: 16px; font-weight: bold;")
