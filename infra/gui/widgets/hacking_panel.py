"""
Hacking Panel - Premium Center Display for Hacking Mode
======================================================
Deep Cyan (Matrix) Theme
Native Widget implementation.
"""

import re
import uuid
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QApplication, QFileDialog, QTextEdit, QFrame,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QCursor, QPainter, QBrush, QColor, QFont

from infra.gui.theme import ThemeManager

# Matrix/Cyberpunk Colors
CYAN = "#00E5FF" # Deep Hacker Cyan
DARK_CYAN = "#008B8B"
BLACK_BG = "#000000"
RED = "#FF0000" # For errors

import random

# Matrix characters (mix of katakana, numbers, symbols)
MATRIX_CHARS = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%^&*(){}[]|:;<>?!~`アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン")


class MatrixRainWidget(QWidget):
    """Matrix-style falling characters effect."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setMinimumHeight(80)
        
        # Column state: list of (y_position, speed, chars_list)
        self._columns = []
        self._col_width = 14
        self._char_height = 16
        self._is_running = False
        
        self._timer = QTimer()
        self._timer.timeout.connect(self._animate)
        self._color = CYAN
    
    def set_color(self, color):
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
        """Initialize column data based on widget width."""
        self._columns = []
        num_cols = max(1, self.width() // self._col_width)
        
        for i in range(num_cols):
            # Random start position (some start offscreen for staggered effect)
            y = random.randint(-200, 0)
            speed = random.uniform(2, 8)
            # Generate a list of random characters for this column
            chars = [random.choice(MATRIX_CHARS) for _ in range(20)]
            self._columns.append([y, speed, chars])
    
    def _animate(self):
        """Update positions and redraw."""
        h = self.height()
        
        for col in self._columns:
            col[0] += col[1]  # y += speed
            
            # Reset when column moves past bottom
            if col[0] > h + 200:
                col[0] = random.randint(-200, -50)
                col[1] = random.uniform(2, 8)
                col[2] = [random.choice(MATRIX_CHARS) for _ in range(20)]
            
            # Randomly mutate some characters
            if random.random() < 0.1:
                idx = random.randint(0, len(col[2]) - 1)
                col[2][idx] = random.choice(MATRIX_CHARS)
        
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
                
                # Only draw if visible
                if 0 <= char_y <= self.height():
                    # Fade effect: first char is bright, others fade
                    if j == 0:
                        alpha = 255  # Head is brightest
                        color = QColor("#FFFFFF")  # White head
                    else:
                        alpha = max(30, 255 - j * 25)
                        color = QColor(base_color)
                    
                    color.setAlpha(alpha)
                    painter.setPen(color)
                    painter.drawText(int(x), int(char_y), char)


class PulsingDot(QWidget):
    """Animated pulsing dot."""
    def __init__(self, color="#00E5FF", parent=None):
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


class TextSectionWidget(QLabel):
    """Widget for regular text explanation."""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setWordWrap(True)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setContentsMargins(5, 5, 5, 5)
    
    def update_theme(self, is_dark):
        if is_dark:
            color = CYAN 
        else:
            color = "#006666"  # Dark teal for light mode
        self.setStyleSheet(f"color: {color}; font-family: Consolas; font-size: 14px; border: none;")


class HackingBlockWidget(QFrame):
    """Premium Card Widget for Hacking Code."""
    def __init__(self, language="HACK", code="", parent=None):
        super().__init__(parent)
        self.language = language
        self.full_code = code
        self._setup_ui()
        
    def _setup_ui(self):
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        self.header = QFrame()
        self.header.setFixedHeight(28)
        self.header_layout = QHBoxLayout(self.header)
        self.header_layout.setContentsMargins(12, 0, 12, 0)
        
        self.lang_label = QLabel(self.language.upper())
        self.lang_label.setStyleSheet("font-weight: bold; font-family: Consolas; font-size: 10px;")
        
        self.copy_btn = QPushButton("📋 COPY")
        self.copy_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.copy_btn.clicked.connect(self._copy_content)
        
        self.header_layout.addWidget(self.lang_label)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.copy_btn)
        
        self.main_layout.addWidget(self.header)
        
        # Code Content
        self.code_edit = QTextEdit()
        self.code_edit.setReadOnly(True)
        self.code_edit.setFrameStyle(QFrame.Shape.NoFrame)
        self.code_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.code_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.code_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap) 
        self.code_edit.setText(self.full_code)
        
        font = QFont("Consolas", 10) 
        self.code_edit.setFont(font)
        
        self.main_layout.addWidget(self.code_edit)
        
        self.code_edit.setFixedHeight(25)
        self._adjust_height()

    def set_content(self, code):
        """Update code content and resize."""
        if code is None: code = ""
        clean_code = code.strip()
        if self.full_code != clean_code:
            self.full_code = clean_code
            self.code_edit.setPlainText(clean_code) 
            self._adjust_height()
            
    def _adjust_height(self):
        try:
            fm = self.code_edit.fontMetrics()
            line_height = fm.lineSpacing()
            
            if not self.full_code:
                lines = 0
            else:
                lines = self.full_code.count('\n') + 1
                
            content_height = lines * line_height
            
            if lines <= 1:
                target_h = 25
            else:
                target_h = content_height + 15
            
            if target_h > 5000: target_h = 5000
                
            self.code_edit.setFixedHeight(int(target_h))
        except Exception:
            pass 
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._adjust_height()

    def _copy_content(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.full_code)
        orig_text = self.copy_btn.text()
        self.copy_btn.setText("COPIED!")
        QTimer.singleShot(1500, lambda: self.copy_btn.setText(orig_text))

    def update_theme(self, is_dark):
        if is_dark:
            # Dark Mode: Matrix/Hacker aesthetic
            curr_bg = "#0a0a0a"
            fg_color = CYAN
            border_color = CYAN
            header_fg = CYAN
        else:
            # Light Mode: Premium teal on light background
            curr_bg = "#f0ffff"  # Azure/light cyan
            fg_color = "#006666"  # Dark teal
            border_color = "#008B8B"  # Darker teal border
            header_fg = "#006666"
            
        self.setStyleSheet(f"""
            HackingBlockWidget {{
                background-color: {curr_bg};
                border: 2px solid {border_color};
                border-radius: 12px;
            }}
        """)
        
        self.header.setStyleSheet(f"""
            QFrame {{
                background-color: {curr_bg};
                border-bottom: 1px solid {'rgba(0, 229, 255, 0.3)' if is_dark else 'rgba(0, 139, 139, 0.3)'};
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }}
        """)
        
        self.lang_label.setStyleSheet(f"color: {header_fg}; font-weight: bold; border: none; background: transparent; font-size: 10px;")
        
        self.copy_btn.setStyleSheet(f"""
            QPushButton {{
                color: {header_fg}; border: none; background: transparent; font-weight: bold; font-size: 10px;
            }}
            QPushButton:hover {{ color: {'#fff' if is_dark else '#004444'}; }}
        """)
        
        self.code_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {curr_bg};
                color: {fg_color};
                border: none;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
                padding: 5px; 
            }}
        """)
        
        self.code_edit.document().setDocumentMargin(0)
        self._adjust_height()


class HackingCenterPanel(QFrame):
    """Premium hacking display for center panel."""
    
    cancelled = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HackingPanel")
        self._elapsed = 0
        self._code_text = ""
        self._blocks_data = [] 
        self._setup_ui()
        ThemeManager.add_listener(self._on_theme_changed)
        self.hide()
    
    def _on_theme_changed(self, theme):
        self._update_theme()
        
    def reset(self):
        """Reset panel state."""
        self.pulsing_dot.stop()
        self._elapsed_timer.stop()
        self.matrix_rain.stop()
        self.hide()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Matrix Rain Background (decorative header banner)
        self.matrix_rain = MatrixRainWidget()
        self.matrix_rain.setFixedHeight(80)
        layout.addWidget(self.matrix_rain)
        
        # Header (overlays on top of matrix rain via styling)
        header = QHBoxLayout()
        header.setContentsMargins(15, 10, 15, 5)
        
        status_layout = QHBoxLayout()
        status_layout.setSpacing(10) 
        self.pulsing_dot = PulsingDot(color=CYAN)
        self.status_label = QLabel("SYSTEM READY")
        self.status_label.setStyleSheet(f"color: {CYAN}; font-family: Consolas; font-size: 14px; letter-spacing: 1px;")
        status_layout.addWidget(self.pulsing_dot)
        status_layout.addWidget(self.status_label)
        header.addLayout(status_layout)
        
        self.timer_label = QLabel("0:00")
        self.timer_label.setStyleSheet(f"color: {DARK_CYAN}; font-family: Consolas; margin-left: 10px;")
        header.addWidget(self.timer_label)
        
        header.addStretch()
        
        self.close_btn = QPushButton("TERMINATE")
        self.close_btn.setFixedSize(80, 28)
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
        self.content_layout.setSpacing(25)
        self.content_layout.setContentsMargins(20, 10, 20, 20)
        self.content_layout.addStretch()
        
        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area, stretch=1)
        
        # Footer
        footer = QHBoxLayout()
        footer.setSpacing(15) 
        footer.setContentsMargins(0, 5, 15, 15)
        footer.addStretch()
        
        self.copy_btn = QPushButton("EXTRACT ALL")
        self.copy_btn.setFixedSize(120, 30)
        self.copy_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.copy_btn.clicked.connect(self._copy_all_code)
        self.copy_btn.hide()
        footer.addWidget(self.copy_btn)
        
        self.save_btn = QPushButton("SAVE LOOT")
        self.save_btn.setFixedSize(100, 30)
        self.save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.save_btn.clicked.connect(self._save_code)
        self.save_btn.hide()
        footer.addWidget(self.save_btn)
        
        layout.addLayout(footer)
        
        self._elapsed_timer = QTimer()
        self._elapsed_timer.timeout.connect(self._update_timer)
        self._update_theme()

    def start(self):
        """Start display."""
        self._code_text = ""
        self._blocks_data = [] 
        
        while self.content_layout.count() > 1:
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        self._update_theme()
        
        self.pulsing_dot.update_color(CYAN)
        self.status_label.setText("INFILTRATING...")
        self.timer_label.setText("0:00")
        self.copy_btn.hide()
        self.save_btn.hide()
        
        self.pulsing_dot.start()
        self._elapsed_timer.start(1000)
        self.matrix_rain.start()  # Start Matrix Rain!
        self.show()
        self._elapsed = 0
    
    def on_token(self, token: str):
        self._code_text += token
        self._reconcile_content()
        
        scrollbar = self.scroll_area.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())
            
    def _reconcile_content(self):
        parts = re.split(r"(```[a-zA-Z0-9_\-\.\+]*\n.*?```|```[a-zA-Z0-9_\-\.\+]*\n.*$)", self._code_text, flags=re.DOTALL)
        valid_parts = [p for p in parts if p.strip()] 
        
        current_widget_idx = 0
        
        for part in valid_parts:
            is_code = part.startswith("```")
            content = part
            lang = "PAYLOAD"
            
            if is_code:
                lines = part.split('\n')
                lang_line = lines[0].strip('`').strip()
                if lang_line: lang = lang_line
                
                if part.strip().endswith("```") and len(lines) > 1:
                     content = "\n".join(lines[1:-1])
                else:
                     content = "\n".join(lines[1:])
            
            content = content.strip()
            
            widget = None
            if current_widget_idx < self.content_layout.count() - 1:
                item = self.content_layout.itemAt(current_widget_idx)
                if item and item.widget():
                    widget = item.widget()
            
            if widget:
                if is_code and isinstance(widget, HackingBlockWidget):
                    widget.set_content(content) 
                elif not is_code and isinstance(widget, TextSectionWidget):
                    widget.setText(content)
                else:
                    self._clear_from(current_widget_idx)
                    widget = None
            
            if widget is None:
                if is_code:
                    widget = HackingBlockWidget(language=lang, code=content)
                else:
                    widget = TextSectionWidget(text=content)
                
                widget.update_theme(True) # Force dark theme
                self.content_layout.insertWidget(self.content_layout.count() - 1, widget)
            
            current_widget_idx += 1

    def _clear_from(self, idx):
        while self.content_layout.count() - 1 > idx:
            item = self.content_layout.takeAt(idx)
            if item.widget():
                item.widget().deleteLater()

    def on_finished(self):
        self.finish()

    def finish(self):
        self.pulsing_dot.stop()
        self._elapsed_timer.stop()
        self.status_label.setText("ACCESS GRANTED")
        self.copy_btn.show()
        self.save_btn.show()

    def on_error(self, msg: str):
        self.pulsing_dot.stop()
        self._elapsed_timer.stop()
        self.status_label.setText("BREACH FAILED")
        self.status_label.setStyleSheet(f"color: {RED}; font-family: Consolas; font-size: 14px;")
        
        error_widget = TextSectionWidget(f"Error: {msg}")
        error_widget.setStyleSheet(f"color: {RED}; font-family: Consolas; font-size: 14px;")
        self.content_layout.insertWidget(self.content_layout.count()-1, error_widget)
        
    def _update_timer(self):
        self._elapsed += 1
        mins = self._elapsed // 60
        secs = self._elapsed % 60
        self.timer_label.setText(f"{mins}:{secs:02d}")
    
    def _update_theme(self):
        theme = ThemeManager.get_theme()
        is_dark = theme.name == "dark"
        
        if is_dark:
            # Dark Mode: Matrix/Hacker Aesthetic - Cyan on Black
            bg_color = "rgba(0, 0, 0, 0.95)"
            border_color = CYAN
            status_color = CYAN
            timer_color = DARK_CYAN
            btn_bg = "rgba(0, 229, 255, 0.1)"
            btn_hover = "rgba(0, 229, 255, 0.2)"
            btn_border = DARK_CYAN
            btn_text = CYAN
        else:
            # Light Mode: Premium Teal/Cyan on white
            bg_color = "rgba(240, 255, 255, 0.98)"  # Light cyan tint
            border_color = "#008B8B"  # Darker teal
            status_color = "#006666"  # Dark teal text
            timer_color = "#008B8B"
            btn_bg = "rgba(0, 139, 139, 0.1)"
            btn_hover = "rgba(0, 139, 139, 0.2)"
            btn_border = "#008B8B"
            btn_text = "#006666"
        
        self.setStyleSheet(f"""
            #HackingPanel {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 12px;
            }}
        """)
        
        # Update Matrix Rain color
        self.matrix_rain.set_color(status_color)
        
        self.status_label.setStyleSheet(f"color: {status_color}; font-family: Consolas; font-size: 14px; letter-spacing: 1px;")
        self.timer_label.setStyleSheet(f"color: {timer_color}; font-family: Consolas; margin-left: 10px;")
        self.pulsing_dot.update_color(status_color)
        
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
                color: {'#fff' if is_dark else '#004444'};
            }}
        """)
        
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
        
        if is_dark:
            self.save_btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {DARK_CYAN}, stop:1 {CYAN});
                    color: black;
                    font-weight: bold;
                    border: none;
                    border-radius: 15px;
                    font-family: Consolas;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {CYAN}, stop:1 #fff);
                }}
            """)
        else:
            self.save_btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #008B8B, stop:1 #20B2AA);
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 15px;
                    font-family: Consolas;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #20B2AA, stop:1 #40E0D0);
                }}
            """)
        
        # Update child widgets
        for i in range(self.content_layout.count() - 1):
            item = self.content_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if hasattr(widget, 'update_theme'):
                    widget.update_theme(is_dark)

    def _extract_code(self) -> str:
        matches = re.findall(r"```(?:\w+)?\n(.*?)```", self._code_text, re.DOTALL)
        if matches: return "\n\n".join(matches).strip()
        return self._code_text.strip()
    
    def _copy_all_code(self):
        code_to_copy = self._extract_code()
        clipboard = QApplication.clipboard()
        clipboard.setText(code_to_copy)
        self.copy_btn.setText("EXTRACTED!")
        QTimer.singleShot(1500, lambda: self.copy_btn.setText("EXTRACT ALL"))
    
    def _save_code(self):
        code_to_save = self._extract_code()
        ext = ".txt"
        if "def " in code_to_save: ext = ".py"
        elif "function " in code_to_save: ext = ".js"
        
        default_name = f"loot_{uuid.uuid4().hex[:8]}{ext}"
        filepath, _ = QFileDialog.getSaveFileName(self, "Save Loot", str(Path.home() / "Desktop" / default_name), f"Code Files (*{ext});;All Files (*)")
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(code_to_save)
