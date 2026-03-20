"""
Writing Panel - Premium Center Display for Writing Mode
=======================================================
Themed rain effects per persona with light/dark mode support.
Native Widget implementation with persona/style selectors.
"""

import re
import uuid
import random
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QApplication, QFileDialog, QTextEdit, QFrame,
    QSizePolicy, QComboBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QCursor, QPainter, QBrush, QColor, QFont

from infra.gui.theme import ThemeManager

# Persona configurations with colors
PERSONAS = {
    "reddit": {
        "name": "📖 Reddit Stories",
        "styles": ["dramatic", "wholesome", "horror", "revenge"],
        "style_names": ["🎭 Dramatic", "💕 Wholesome", "👻 Horror", "⚔️ Revenge"],
        "colors": {"dark": "#FF6B35", "light": "#E85D04"},  # Orange
        "rain_chars": ["STORY", "DRAMA", "PLOT", "TWIST", "OMG", "THEN", "...", "WOW"]
    },
    "therapist": {
        "name": "🧠 Therapist",
        "styles": ["supportive", "cbt", "motivational", "mindfulness"],
        "style_names": ["💝 Supportive", "🧩 CBT", "💪 Motivational", "🧘 Mindfulness"],
        "colors": {"dark": "#FF69B4", "light": "#DB7093"},  # Pink
        "rain_chars": ["♥", "♡", "💕", "✿", "❀", "∞", "☮", "✧", "💗", "♥"]
    },
    "teacher": {
        "name": "📚 Teacher",
        "styles": ["eli5", "academic", "socratic", "practical"],
        "style_names": ["👶 ELI5", "🎓 Academic", "🤔 Socratic", "🔧 Practical"],
        "colors": {"dark": "#4FC3F7", "light": "#0288D1"},  # Blue
        "rain_chars": ["π", "∑", "√", "∞", "±", "×", "÷", "=", "α", "β", "Δ", "%"]
    },
    "poet": {
        "name": "✍️ Poet",
        "styles": ["romantic", "gothic", "haiku", "epic"],
        "style_names": ["💘 Romantic", "🌑 Gothic", "🍃 Haiku", "⚔️ Epic"],
        "colors": {"dark": "#BA68C8", "light": "#7B1FA2"},  # Purple
        "rain_chars": ["✨", "⭐", "✦", "✧", "★", "✴", "✵", "❋", "✶", "・"]
    }
}


class ThemedRainWidget(QWidget):
    """Themed falling characters/symbols effect that changes per persona."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setMinimumHeight(80)
        
        self._columns = []
        self._col_width = 20
        self._char_height = 18
        self._is_running = False
        
        self._timer = QTimer()
        self._timer.timeout.connect(self._animate)
        
        self._color = "#FF69B4"
        self._chars = ["♥", "♡", "💕"]
        self._persona = "therapist"
    
    def set_persona(self, persona: str, is_dark: bool):
        """Update rain theme based on persona."""
        self._persona = persona
        config = PERSONAS.get(persona, PERSONAS["therapist"])
        self._color = config["colors"]["dark" if is_dark else "light"]
        self._chars = config["rain_chars"]
        self.update()
    
    def start(self):
        if not self._is_running:
            self._is_running = True
            self._init_columns()
            self._timer.start(60)
    
    def stop(self):
        self._is_running = False
        self._timer.stop()
    
    def _init_columns(self):
        self._columns = []
        num_cols = max(1, self.width() // self._col_width)
        
        for i in range(num_cols):
            y = random.randint(-150, 0)
            speed = random.uniform(1.5, 5)
            chars = [random.choice(self._chars) for _ in range(12)]
            self._columns.append([y, speed, chars])
    
    def _animate(self):
        h = self.height()
        
        for col in self._columns:
            col[0] += col[1]
            
            if col[0] > h + 150:
                col[0] = random.randint(-150, -30)
                col[1] = random.uniform(1.5, 5)
                col[2] = [random.choice(self._chars) for _ in range(12)]
            
            if random.random() < 0.08:
                idx = random.randint(0, len(col[2]) - 1)
                col[2][idx] = random.choice(self._chars)
        
        self.update()
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._is_running:
            self._init_columns()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        font = QFont("Segoe UI Emoji", 12)
        painter.setFont(font)
        
        base_color = QColor(self._color)
        
        for i, (y, speed, chars) in enumerate(self._columns):
            x = i * self._col_width + 5
            
            for j, char in enumerate(chars):
                char_y = y + j * self._char_height
                
                if 0 <= char_y <= self.height():
                    if j == 0:
                        alpha = 255
                        color = QColor("#FFFFFF")
                    else:
                        alpha = max(30, 255 - j * 30)
                        color = QColor(base_color)
                    
                    color.setAlpha(alpha)
                    painter.setPen(color)
                    painter.drawText(int(x), int(char_y), char)


class PulsingDot(QWidget):
    """Animated pulsing dot."""
    def __init__(self, color="#FF69B4", parent=None):
        super().__init__(parent)
        self.setFixedSize(12, 12)
        self._color = color
        self._opacity = 1.0
        self._growing = False
        self._timer = QTimer()
        self._timer.timeout.connect(self._animate)
    
    def update_color(self, color):
        self._color = color
        self.update()
    
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
        color = QColor(self._color)
        color.setAlphaF(self._opacity)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(1, 1, 10, 10)


class TextBlockWidget(QLabel):
    """Widget for text content."""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setWordWrap(True)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setContentsMargins(5, 5, 5, 5)
    
    def update_theme(self, color):
        self.setStyleSheet(f"color: {color}; font-family: 'Georgia', serif; font-size: 14px; line-height: 1.6; border: none;")


class WritingCenterPanel(QFrame):
    """Premium writing display for center panel with persona selection."""
    
    cancelled = pyqtSignal()
    persona_changed = pyqtSignal(str, str)  # persona, style
    history_cleared = pyqtSignal()  # emitted when clear button clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("WritingPanel")
        self._elapsed = 0
        self._text = ""
        self._current_persona = "therapist"
        self._current_style = "supportive"
        self._setup_ui()
        ThemeManager.add_listener(self._on_theme_changed)
        self.hide()
    
    def _on_theme_changed(self, theme):
        self._update_theme()
    
    def reset(self):
        """Reset panel state."""
        self.pulsing_dot.stop()
        self._elapsed_timer.stop()
        self.themed_rain.stop()
        self.hide()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Rain banner at top (fixed height 80px)
        self.themed_rain = ThemedRainWidget()
        self.themed_rain.setFixedHeight(80)
        layout.addWidget(self.themed_rain)
        
        # Simplified Header row
        header = QHBoxLayout()
        header.setContentsMargins(20, 12, 20, 12)
        header.setSpacing(20)
        
        # Persona label (read-only display, selection is in chat widget)
        self.persona_label = QLabel("🧠 Therapist • Supportive")
        self.persona_label.setFixedHeight(30)
        header.addWidget(self.persona_label)
        
        header.addStretch()
        
        # Status with dot
        status_layout = QHBoxLayout()
        status_layout.setSpacing(8)
        self.pulsing_dot = PulsingDot()
        self.status_label = QLabel("READY")
        status_layout.addWidget(self.pulsing_dot)
        status_layout.addWidget(self.status_label)
        header.addLayout(status_layout)
        
        # Timer
        self.timer_label = QLabel("0:00")
        header.addWidget(self.timer_label)
        
        # History indicator
        self.history_label = QLabel("📝 0")
        self.history_label.setToolTip("Conversation history")
        header.addWidget(self.history_label)
        
        # STOP button
        self.close_btn = QPushButton("STOP")
        self.close_btn.setFixedSize(70, 30)
        self.close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.close_btn.clicked.connect(self.cancelled.emit)
        header.addWidget(self.close_btn)
        
        layout.addLayout(header)
        
        # Content
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.scroll_content = QWidget()
        self.content_layout = QVBoxLayout(self.scroll_content)
        self.content_layout.setSpacing(15)
        self.content_layout.setContentsMargins(20, 10, 20, 20)
        self.content_layout.addStretch()
        
        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area, stretch=1)
        
        # Footer
        footer = QHBoxLayout()
        footer.setSpacing(15)
        footer.setContentsMargins(20, 10, 20, 15)
        
        self.clear_history_btn = QPushButton("🗑️ Clear")
        self.clear_history_btn.setFixedSize(90, 32)
        self.clear_history_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.clear_history_btn.clicked.connect(self._on_clear_history)
        footer.addWidget(self.clear_history_btn)
        
        footer.addStretch()
        
        self.copy_btn = QPushButton("📋 Copy")
        self.copy_btn.setFixedSize(90, 32)
        self.copy_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.copy_btn.clicked.connect(self._copy_all)
        self.copy_btn.hide()
        footer.addWidget(self.copy_btn)
        
        self.save_btn = QPushButton("💾 Save")
        self.save_btn.setFixedSize(90, 32)
        self.save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.save_btn.clicked.connect(self._save)
        self.save_btn.hide()
        footer.addWidget(self.save_btn)
        
        layout.addLayout(footer)
        
        self._elapsed_timer = QTimer()
        self._elapsed_timer.timeout.connect(self._update_timer)
        self._update_theme()
    
    def _on_clear_history(self):
        """Clear conversation from panel and emit signal for manager."""
        self.clear_conversation()
        self.update_history_count(0)
        self.history_cleared.emit()
    
    def get_persona_style(self):
        """Get current persona and style."""
        return self._current_persona, self._current_style
    
    def set_persona(self, persona: str, style: str):
        """Set persona and style from external source (chat widget)."""
        self._current_persona = persona
        self._current_style = style
        
        # Update the display label
        config = PERSONAS.get(persona, PERSONAS["therapist"])
        persona_name = config["name"]
        
        # Get style name
        style_idx = config["styles"].index(style) if style in config["styles"] else 0
        style_name = config["style_names"][style_idx]
        
        self.persona_label.setText(f"{persona_name} • {style_name}")
        
        # Update theme (including rain)
        self._update_theme()
    
    def update_history_count(self, count: int):
        """Update history indicator."""
        self.history_label.setText(f"📝 {count}")
    
    def start(self, user_prompt: str = None):
        """Start display for a new message (appends to existing conversation)."""
        self._text = ""  # Current response text
        
        # Don't clear existing content - append instead
        # Add a user prompt bubble if provided
        if user_prompt:
            self._add_message_block("You", user_prompt, is_user=True)
        
        # Add an empty AI response block that will be filled
        self._current_response_widget = TextBlockWidget()
        config = PERSONAS.get(self._current_persona, PERSONAS["therapist"])
        theme = ThemeManager.get_theme()
        is_dark = theme.name == "dark"
        self._current_response_widget.update_theme(config["colors"]["dark" if is_dark else "light"])
        self.content_layout.insertWidget(self.content_layout.count() - 1, self._current_response_widget)
        
        self._update_theme()
        
        self.status_label.setText("WRITING...")
        self.timer_label.setText("0:00")
        self.copy_btn.hide()
        self.save_btn.hide()
        
        self.pulsing_dot.start()
        self._elapsed_timer.start(1000)
        self.themed_rain.start()
        
        self.show()
        self._elapsed = 0
        
        # Scroll to bottom
        scrollbar = self.scroll_area.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())
    
    def _add_message_block(self, sender: str, text: str, is_user: bool = False):
        """Add a message block to the conversation."""
        theme = ThemeManager.get_theme()
        is_dark = theme.name == "dark"
        config = PERSONAS.get(self._current_persona, PERSONAS["therapist"])
        color = config["colors"]["dark" if is_dark else "light"]
        
        if is_user:
            # User message - right-aligned chat bubble
            row = QHBoxLayout()
            row.setContentsMargins(0, 5, 0, 10)
            
            row.addStretch()  # Push to right
            
            bubble = QLabel(text)
            bubble.setWordWrap(True)
            bubble.setMaximumWidth(400)
            bubble.setStyleSheet(f"""
                QLabel {{
                    color: #FFFFFF;
                    font-family: 'Segoe UI';
                    font-size: 13px;
                    padding: 10px 15px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                stop:0 #FF6B9D, stop:1 #C85A9D);
                    border-radius: 15px;
                    border-top-right-radius: 5px;
                }}
            """)
            row.addWidget(bubble)
            
            # Create container widget for the row
            container = QWidget()
            container.setLayout(row)
            self.content_layout.insertWidget(self.content_layout.count() - 1, container)
        else:
            # AI message - left-aligned, full width
            block = QWidget()
            block_layout = QVBoxLayout(block)
            block_layout.setContentsMargins(0, 5, 0, 10)
            block_layout.setSpacing(4)
            
            sender_label = QLabel(sender)
            sender_label.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold;")
            block_layout.addWidget(sender_label)
            
            text_widget = TextBlockWidget(text)
            text_widget.update_theme(color)
            block_layout.addWidget(text_widget)
            
            self.content_layout.insertWidget(self.content_layout.count() - 1, block)
    
    def clear_conversation(self):
        """Clear all conversation content (for Clear History button)."""
        while self.content_layout.count() > 1:
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._text = ""
        self._current_response_widget = None
    
    def on_token(self, token: str):
        self._text += token
        
        # Update current response widget
        if hasattr(self, '_current_response_widget') and self._current_response_widget:
            self._current_response_widget.setText(self._text)
        
        scrollbar = self.scroll_area.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())
    
    def on_finished(self):
        self.finish()
    
    def finish(self):
        self.pulsing_dot.stop()
        self._elapsed_timer.stop()
        self.status_label.setText("COMPLETE")
        self.copy_btn.show()
        self.save_btn.show()
    
    def on_error(self, msg: str):
        self.pulsing_dot.stop()
        self._elapsed_timer.stop()
        self.status_label.setText("ERROR")
        
        error_widget = TextBlockWidget(f"Error: {msg}")
        error_widget.setStyleSheet("color: #FF4444; font-family: Consolas;")
        self.content_layout.insertWidget(self.content_layout.count()-1, error_widget)
    
    def _update_timer(self):
        self._elapsed += 1
        mins = self._elapsed // 60
        secs = self._elapsed % 60
        self.timer_label.setText(f"{mins}:{secs:02d}")
    
    def _update_theme(self):
        theme = ThemeManager.get_theme()
        is_dark = theme.name == "dark"
        config = PERSONAS.get(self._current_persona, PERSONAS["therapist"])
        color = config["colors"]["dark" if is_dark else "light"]
        
        # Update rain
        self.themed_rain.set_persona(self._current_persona, is_dark)
        
        if is_dark:
            bg_color = "rgba(0, 0, 0, 0.98)"  # Pure black
            text_color = "#EEEEEE"
        else:
            bg_color = "rgba(255, 255, 255, 0.98)"  # Pure white
            text_color = "#333333"
        
        self.setStyleSheet(f"""
            #WritingPanel {{
                background-color: {bg_color};
                border: 2px solid {color};
                border-radius: 12px;
            }}
        """)
        
        self.status_label.setStyleSheet(f"color: {color}; font-family: Consolas; font-size: 13px;")
        self.timer_label.setStyleSheet(f"color: {color}; font-family: Consolas; margin-left: 10px;")
        self.history_label.setStyleSheet(f"color: {color}; font-family: Consolas; font-size: 11px;")
        self.pulsing_dot.update_color(color)
        
        # Persona label styling
        self.persona_label.setStyleSheet(f"""
            color: {color};
            font-family: 'Segoe UI';
            font-size: 14px;
            font-weight: bold;
            padding: 5px 15px;
            background: {'rgba(30, 30, 30, 0.8)' if is_dark else 'rgba(245, 245, 245, 0.9)'};
            border: 1px solid {color};
            border-radius: 15px;
        """)
        
        btn_style = f"""
            QPushButton {{
                background: {'rgba(255,255,255,0.1)' if is_dark else 'rgba(0,0,0,0.05)'};
                color: {color};
                border: 1px solid {color};
                border-radius: 14px;
                font-family: 'Segoe UI';
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: {'rgba(255,255,255,0.2)' if is_dark else 'rgba(0,0,0,0.1)'};
            }}
        """
        self.close_btn.setStyleSheet(btn_style)
        self.copy_btn.setStyleSheet(btn_style)
        self.save_btn.setStyleSheet(btn_style)
        self.clear_history_btn.setStyleSheet(btn_style)
    
    def _copy_all(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self._text)
        self.copy_btn.setText("Copied!")
        QTimer.singleShot(1500, lambda: self.copy_btn.setText("📋 Copy All"))
    
    def _save(self):
        default_name = f"writing_{self._current_persona}_{uuid.uuid4().hex[:6]}.txt"
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Writing", 
            str(Path.home() / "Desktop" / default_name),
            "Text Files (*.txt);;All Files (*)"
        )
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self._text)
