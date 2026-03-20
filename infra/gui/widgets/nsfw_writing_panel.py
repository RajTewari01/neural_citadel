"""
NSFW Writing Panel - Premium Center Display for NSFW Writing Mode
==================================================================
Sleek text-based rain with premium red/pink theme matching hacking panel layout.
Has TERMINATE button, model selector, proper status bar.
"""

import re
import random
import math
import uuid
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QTextEdit, QPushButton, QFrame,
    QSizePolicy, QComboBox, QApplication, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QCursor, QPainter, QBrush, QColor, QFont, QTextCursor

from infra.gui.theme import ThemeManager

# NSFW Theme Colors
FIRE_RED = "#FF3366"
FIRE_ORANGE = "#FF6B35"
DARK_RED = "#8B0000"
HEART_PINK = "#FF6B9D"
BLACK_BG = "#000000"  # Pure black

# NSFW Personas and Styles
NSFW_PERSONAS = {
    "erotica": {
        "name": "Erotica Writer",
        "styles": ["romance", "explicit", "fantasy", "taboo"],
        "style_names": ["Romance", "Explicit", "Fantasy", "Taboo"],
    },
    "roleplay": {
        "name": "Roleplay Partner", 
        "styles": ["romantic", "dominant", "submissive", "scenario"],
        "style_names": ["Romantic", "Dominant", "Submissive", "Scenario"],
    }
}

# Sleek rain characters (like Matrix - letters, numbers, symbols)
RAIN_CHARS = list("abcdefghijklmnopqrstuvwxyz0123456789@#$%&*+-=<>?!~")


class FireRainWidget(QWidget):
    """Sleek Matrix-style falling characters with red/pink glow."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setMinimumHeight(80)
        
        self._columns = []
        self._col_width = 14  # Narrower for text
        self._char_height = 16
        self._is_running = False
        
        self._timer = QTimer()
        self._timer.timeout.connect(self._animate)
        self._color = FIRE_RED
    
    def set_color(self, color, glow=None):
        self._color = color
        self.update()
    
    def start(self):
        if not self._is_running:
            self._is_running = True
            self._init_columns()
            self._timer.start(50)  # 20 FPS
    
    def stop(self):
        self._is_running = False
        self._timer.stop()
    
    def _init_columns(self):
        self._columns = []
        num_cols = max(1, self.width() // self._col_width)
        
        for i in range(num_cols):
            y = random.randint(-200, 0)
            speed = random.uniform(2, 8)
            chars = [random.choice(RAIN_CHARS) for _ in range(20)]
            self._columns.append([y, speed, chars])
    
    def _animate(self):
        h = self.height()
        
        for col in self._columns:
            col[0] += col[1]  # y += speed
            
            if col[0] > h + 200:
                col[0] = random.randint(-200, -50)
                col[1] = random.uniform(2, 8)
                col[2] = [random.choice(RAIN_CHARS) for _ in range(20)]
            
            # Randomly mutate some characters
            if random.random() < 0.1:
                idx = random.randint(0, len(col[2]) - 1)
                col[2][idx] = random.choice(RAIN_CHARS)
        
        self.update()
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._is_running:
            self._init_columns()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        font = QFont("Consolas", 10)
        font.setBold(True)
        painter.setFont(font)
        
        base_color = QColor(self._color)
        
        for i, (y, speed, chars) in enumerate(self._columns):
            x = i * self._col_width + 5
            
            for j, char in enumerate(chars):
                char_y = y + j * self._char_height
                
                if 0 <= char_y <= self.height():
                    if j == 0:
                        # Head is bright white/pink
                        alpha = 255
                        color = QColor("#FFFFFF")
                    else:
                        # Trail fades
                        alpha = max(30, 255 - j * 25)
                        color = QColor(base_color)
                    
                    color.setAlpha(alpha)
                    painter.setPen(color)
                    painter.drawText(int(x), int(char_y), char)


class PulsingDot(QWidget):
    """Animated pulsing dot."""
    def __init__(self, color="#FF3366", parent=None):
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


class NSFWWritingCenterPanel(QFrame):
    """Premium NSFW writing display matching hacking panel layout."""
    
    cancelled = pyqtSignal()
    persona_changed = pyqtSignal(str, str)  # persona, style
    history_cleared = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("NSFWPanel")
        self._current_persona = "erotica"
        self._current_style = "romance"
        self._response_text = ""
        self._elapsed = 0
        self._setup_ui()
        ThemeManager.add_listener(self._on_theme_changed)
        self.hide()
    
    def _on_theme_changed(self, theme):
        self._update_theme()
    
    def reset(self):
        """Reset panel state."""
        self.pulsing_dot.stop()
        self._elapsed_timer.stop()
        self.fire_rain.stop()
        self._response_text = ""
        self.result_text.setPlainText("")
        self.timer_label.setText("0:00")
        self.hide()
    
    def set_persona(self, persona: str, style: str):
        """Set persona and style from external source."""
        for i in range(self.persona_combo.count()):
            if self.persona_combo.itemData(i) == persona:
                self.persona_combo.setCurrentIndex(i)
                break
        
        persona_config = NSFW_PERSONAS.get(persona, {})
        styles = persona_config.get("styles", [])
        if style in styles:
            self.style_combo.setCurrentIndex(styles.index(style))
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Fire Rain Header Banner (like Matrix Rain)
        self.fire_rain = FireRainWidget()
        self.fire_rain.setFixedHeight(80)
        layout.addWidget(self.fire_rain)
        
        # Header Bar (status, timer, persona selectors, terminate)
        header = QHBoxLayout()
        header.setContentsMargins(15, 10, 15, 5)
        header.setSpacing(12)
        
        # Status Layout
        status_layout = QHBoxLayout()
        status_layout.setSpacing(8)
        
        self.pulsing_dot = PulsingDot(color=FIRE_RED)
        self.status_label = QLabel("READY")
        status_layout.addWidget(self.pulsing_dot)
        status_layout.addWidget(self.status_label)
        header.addLayout(status_layout)
        
        self.timer_label = QLabel("0:00")
        header.addWidget(self.timer_label)
        
        header.addStretch()
        
        # Model/Persona Selectors
        self.persona_combo = QComboBox()
        for key, config in NSFW_PERSONAS.items():
            self.persona_combo.addItem(config["name"], key)
        self.persona_combo.setFixedHeight(28)
        self.persona_combo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.persona_combo.currentIndexChanged.connect(self._on_persona_changed)
        header.addWidget(self.persona_combo)
        
        self.style_combo = QComboBox()
        self._update_styles()
        self.style_combo.setFixedHeight(28)
        self.style_combo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.style_combo.currentIndexChanged.connect(self._on_style_changed)
        header.addWidget(self.style_combo)
        
        # TERMINATE Button
        self.close_btn = QPushButton("TERMINATE")
        self.close_btn.setFixedSize(90, 28)
        self.close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.close_btn.clicked.connect(self.cancelled.emit)
        header.addWidget(self.close_btn)
        
        layout.addLayout(header)
        
        # Content Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.scroll_content = QWidget()
        content_layout = QVBoxLayout(self.scroll_content)
        content_layout.setContentsMargins(20, 10, 20, 20)
        content_layout.setSpacing(10)
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setFrameStyle(QFrame.Shape.NoFrame)
        self.result_text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.result_text.setFont(QFont("Segoe UI", 12))
        content_layout.addWidget(self.result_text)
        
        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area, stretch=1)
        
        # Footer (action buttons)
        footer = QHBoxLayout()
        footer.setSpacing(12)
        footer.setContentsMargins(15, 5, 15, 15)
        
        # Clear History (left side)
        self.clear_btn = QPushButton("🗑️ CLEAR STORY")
        self.clear_btn.setFixedSize(120, 30)
        self.clear_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.clear_btn.clicked.connect(self.clear_conversation)
        footer.addWidget(self.clear_btn)
        
        footer.addStretch()
        
        # Copy and Save (right side)
        self.copy_btn = QPushButton("📋 COPY")
        self.copy_btn.setFixedSize(90, 30)
        self.copy_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.copy_btn.clicked.connect(self._copy_all)
        self.copy_btn.hide()
        footer.addWidget(self.copy_btn)
        
        self.save_btn = QPushButton("💾 SAVE")
        self.save_btn.setFixedSize(90, 30)
        self.save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.save_btn.clicked.connect(self._save)
        self.save_btn.hide()
        footer.addWidget(self.save_btn)
        
        layout.addLayout(footer)
        
        # Timer
        self._elapsed_timer = QTimer()
        self._elapsed_timer.timeout.connect(self._update_timer)
        
        self._update_theme()
    
    def _on_persona_changed(self, index):
        persona_key = self.persona_combo.itemData(index)
        if persona_key != self._current_persona:
            self._current_persona = persona_key
            self._update_styles()
            self.persona_changed.emit(self._current_persona, self._current_style)
    
    def _on_style_changed(self, index):
        if index >= 0:
            persona_config = NSFW_PERSONAS.get(self._current_persona, {})
            styles = persona_config.get("styles", [])
            if index < len(styles):
                self._current_style = styles[index]
                self.persona_changed.emit(self._current_persona, self._current_style)
    
    def _update_styles(self):
        self.style_combo.blockSignals(True)
        self.style_combo.clear()
        
        persona_config = NSFW_PERSONAS.get(self._current_persona, {})
        style_names = persona_config.get("style_names", [])
        styles = persona_config.get("styles", [])
        
        for name in style_names:
            self.style_combo.addItem(name)
        
        if styles:
            self._current_style = styles[0]
        
        self.style_combo.blockSignals(False)
    
    def start_streaming(self):
        """Called when generation starts."""
        # Append separator if there's existing text
        if self._response_text:
            self._response_text += "\n\n"
            cursor = self.result_text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertText("\n\n")
            
        self._elapsed = 0
        # Don't clear result_text, just update status
        self.timer_label.setText("0:00")
        self.status_label.setText("GENERATING...")
        self.copy_btn.hide()
        self.save_btn.hide()
        
        self.pulsing_dot.start()
        self._elapsed_timer.start(1000)
        self.fire_rain.start()
        self._update_theme()
        self.show()
        
        # Force scroll to bottom on start
        QTimer.singleShot(100, lambda: self._scroll_to_bottom())

    def _scroll_to_bottom(self):
        scrollbar = self.scroll_area.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())
    
    def on_token(self, token: str):
        """Receive streaming token."""
        # Check if already at bottom BEFORE adding text
        scrollbar = self.scroll_area.verticalScrollBar()
        was_at_bottom = True
        if scrollbar:
            # Consider "at bottom" if within 50 pixels
            was_at_bottom = scrollbar.value() >= (scrollbar.maximum() - 50)
            
        self._response_text += token
        # Use insertText to avoid resetting scroll position
        cursor = self.result_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(token)
        
        # If we were at bottom, keep scrolling
        if was_at_bottom:
             QTimer.singleShot(10, lambda: self._scroll_to_bottom())
    
    def on_finished(self):
        """Called when generation is done."""
        self.finish()
    
    def finish(self):
        self.pulsing_dot.stop()
        self._elapsed_timer.stop()
        self.status_label.setText("COMPLETE")
        self.copy_btn.show()
        self.save_btn.show()
    
    def on_error(self, msg: str):
        """Handle error."""
        self.pulsing_dot.stop()
        self._elapsed_timer.stop()
        self.status_label.setText("ERROR")
        self.result_text.setPlainText(f"❌ Error: {msg}")
    
    def clear_conversation(self):
        """Clear story history."""
        self.history_cleared.emit()
        self._response_text = ""
        self.result_text.setPlainText("")
    
    def _update_timer(self):
        self._elapsed += 1
        mins = self._elapsed // 60
        secs = self._elapsed % 60
        self.timer_label.setText(f"{mins}:{secs:02d}")
    
    def _update_theme(self):
        theme = ThemeManager.get_theme()
        is_dark = theme.name == "dark"
        
        if is_dark:
            # Dark Mode: Sleek red/pink on pure BLACK
            bg_color = "rgba(0, 0, 0, 0.98)"
            border_color = FIRE_RED
            status_color = FIRE_RED
            timer_color = HEART_PINK
            btn_bg = "rgba(255, 51, 102, 0.1)"
            btn_hover = "rgba(255, 51, 102, 0.2)"
            btn_border = DARK_RED
            btn_text = FIRE_RED
            text_color = "#FFE0E8"
        else:
            # Light Mode: Elegant rose
            bg_color = "rgba(255, 245, 248, 0.98)"
            border_color = "#C2185B"
            status_color = "#C2185B"
            timer_color = "#E91E63"
            btn_bg = "rgba(194, 24, 91, 0.08)"
            btn_hover = "rgba(194, 24, 91, 0.15)"
            btn_border = "#E91E63"
            btn_text = "#C2185B"
            text_color = "#4A0E1F"
        
        self.setStyleSheet(f"""
            #NSFWPanel {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 12px;
            }}
        """)
        
        self.fire_rain.set_color(status_color, timer_color)
        
        self.status_label.setStyleSheet(f"color: {status_color}; font-family: Consolas; font-size: 14px; letter-spacing: 1px;")
        self.timer_label.setStyleSheet(f"color: {timer_color}; font-family: Consolas; margin-left: 10px;")
        self.pulsing_dot.update_color(status_color)
        
        # Combo boxes - clean, no ugly squares
        combo_style = f"""
            QComboBox {{
                background: {btn_bg};
                color: {btn_text};
                border: 1px solid {btn_border};
                border-radius: 14px;
                padding: 4px 12px;
                font-family: Consolas;
                font-size: 11px;
                min-width: 100px;
            }}
            QComboBox:hover {{
                background: {btn_hover};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background: {'#1A0010' if is_dark else '#FFF5F8'};
                color: {btn_text};
                selection-background-color: {btn_hover};
                border: 1px solid {btn_border};
                border-radius: 6px;
            }}
        """
        self.persona_combo.setStyleSheet(combo_style)
        self.style_combo.setStyleSheet(combo_style)
        
        # TERMINATE button
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {btn_bg};
                color: {btn_text};
                border: 1px solid {btn_border};
                border-radius: 14px;
                font-family: Consolas;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: {btn_hover};
                color: {'#fff' if is_dark else '#8B0000'};
            }}
        """)
        
        # Clear button
        self.clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: {btn_bg};
                color: {btn_text};
                border: 1px solid {btn_border};
                border-radius: 15px;
                font-family: Consolas;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: {btn_hover};
            }}
        """)
        
        # Copy button
        self.copy_btn.setStyleSheet(f"""
            QPushButton {{
                background: {btn_bg};
                color: {btn_text};
                border: 1px solid {border_color};
                border-radius: 15px;
                font-family: Consolas;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: {btn_hover};
            }}
        """)
        
        # Save button with gradient
        if is_dark:
            self.save_btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {DARK_RED}, stop:1 {FIRE_RED});
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 15px;
                    font-family: Consolas;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {FIRE_RED}, stop:1 {FIRE_ORANGE});
                }}
            """)
        else:
            self.save_btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #C2185B, stop:1 #E91E63);
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 15px;
                    font-family: Consolas;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #E91E63, stop:1 #F48FB1);
                }}
            """)
        
        # Result text area
        self.result_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                color: {text_color};
                border: none;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                line-height: 1.6;
            }}
        """)
        
        # Scroll area
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 6px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {status_color}50;
                border-radius: 3px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)
        
        self.scroll_content.setStyleSheet("background: transparent;")
    
    def _copy_all(self):
        """Copy all text to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self._response_text)
        self.copy_btn.setText("COPIED!")
        QTimer.singleShot(1500, lambda: self.copy_btn.setText("📋 COPY"))
    
    def _save(self):
        """Save to file."""
        from datetime import datetime
        default_name = f"nsfw_story_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Story", str(Path.home() / "Desktop" / default_name), "Text Files (*.txt)"
        )
        
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self._response_text)
