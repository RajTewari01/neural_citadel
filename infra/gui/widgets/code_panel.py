"""
Code Panel - Premium Center Display for Code Mode
==================================================

Native Widget implementation for perfect styling (Rounded corners, Shadows).
Replaces HTML rendering.
"""

import html
import re
import uuid
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QApplication, QFileDialog, QTextEdit, QFrame,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QUrl, QSize
from PyQt6.QtGui import QCursor, QDesktopServices, QPainter, QBrush, QColor, QFont

from infra.gui.theme import ThemeManager

# Theme colors
GREEN = "#7CFC00"
RED = "#DC143C"
PINK = "#E1306C"


class PulsingDot(QWidget):
    """Animated pulsing dot."""
    def __init__(self, color="#7CFC00", parent=None):
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
        color = "#e0e0e0" if is_dark else "#333333"
        self.setStyleSheet(f"color: {color}; font-family: Consolas; font-size: 14px; border: none;")


class CodeBlockWidget(QFrame):
    """Premium Card Widget for a Code Block."""
    def __init__(self, language="CODE", code="", parent=None):
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
        self.header.setFixedHeight(28) # Fixed height for sleek header
        self.header_layout = QHBoxLayout(self.header)
        # Sleeker margins
        self.header_layout.setContentsMargins(12, 0, 12, 0) # Zero vertical margin as height is fixed
        
        self.lang_label = QLabel(self.language.upper())
        # Initial small size
        self.lang_label.setStyleSheet("font-weight: bold; font-family: Consolas; font-size: 10px;")
        
        self.copy_btn = QPushButton("📋 COPY")
        self.copy_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.copy_btn.clicked.connect(self._copy_content)
        
        self.header_layout.addWidget(self.lang_label)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.copy_btn)
        
        self.main_layout.addWidget(self.header)
        
        # Code Content (Auto-resizing text edit)
        self.code_edit = QTextEdit()
        self.code_edit.setReadOnly(True)
        self.code_edit.setFrameStyle(QFrame.Shape.NoFrame)
        # Force scrollbars off to ensure widget expands
        self.code_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.code_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.code_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap) 
        self.code_edit.setText(self.full_code)
        
        # Font
        font = QFont("Consolas", 10) 
        self.code_edit.setFont(font)
        
        self.main_layout.addWidget(self.code_edit)
        
        # Explicitly set minimal height initially
        self.code_edit.setFixedHeight(25)
        
        # Adjust height based on content
        self._adjust_height()

    def set_content(self, code):
        """Update code content and resize."""
        if code is None:
            code = ""
        # Clean the code to remove excess whitespace that causes "huge" startup
        clean_code = code.strip()
        if self.full_code != clean_code:
            self.full_code = clean_code
            self.code_edit.setPlainText(clean_code) 
            self._adjust_height()
            
    def _adjust_height(self):
        try:
            # Manual height calculation to completely bypass QDocument layout quirks
            # Since we use NoWrap, height is strictly (lines * line_height) + padding
            
            fm = self.code_edit.fontMetrics()
            line_height = fm.lineSpacing()
            
            # Count lines strictly from the clean code
            # If code is empty, count as 0 lines for calculation
            if not self.full_code:
                lines = 0
            else:
                lines = self.full_code.count('\n') + 1
                
            # Content height
            content_height = lines * line_height
            
            # Start SMALL. If lines=0 or 1, we want ALMOST NOTHING visible (just header + tiny slit)
            if lines <= 1:
                target_h = 25 # Minimum height constraint
            else:
                target_h = content_height + 15
            
            # Safety caps
            if target_h > 5000:
                target_h = 5000
                
            self.code_edit.setFixedHeight(int(target_h))
        except Exception:
            pass 
    
    def resizeEvent(self, event):
        """Handle resize to adjust height for wrapping."""
        super().resizeEvent(event)
        self._adjust_height()

    def _copy_content(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.full_code)
        orig_text = self.copy_btn.text()
        self.copy_btn.setText("COPIED!")
        QTimer.singleShot(1500, lambda: self.copy_btn.setText(orig_text))

    def update_theme(self, is_dark):
        # Colors based on user request (Unified bg, High contrast outline)
        if is_dark:
            bg_color = "#1e1e1e"
            curr_bg = bg_color
            fg_color = "#7CFC00"
            border_color = "#ffffff" # White outline
            header_fg = "#e0e0e0"
        else:
            bg_color = "#fafafa"
            curr_bg = bg_color
            fg_color = "#DC143C"
            border_color = "#000000" # Black outline
            header_fg = "#000000"
            
        # Frame Style (Rounded + Shadow + Border)
        self.setStyleSheet(f"""
            CodeBlockWidget {{
                background-color: {curr_bg};
                border: 2px solid {border_color};
                border-radius: 12px;
            }}
        """)
        
        # Header Style
        self.header.setStyleSheet(f"""
            QFrame {{
                background-color: {curr_bg};
                border-bottom: 1px solid rgba(128,128,128,0.3);
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }}
        """)
        # Explicitly set font size here to prevent overriding resetting it
        self.lang_label.setStyleSheet(f"color: {header_fg}; font-weight: bold; border: none; background: transparent; font-size: 10px;")
        
        self.copy_btn.setStyleSheet(f"""
            QPushButton {{
                color: {header_fg}; border: none; background: transparent; font-weight: bold; font-size: 10px;
            }}
            QPushButton:hover {{ color: #888; }}
        """)
        
        # Code Edit Style
        # Set margins to 0 to remove internal padding gaps
        self.code_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {curr_bg};
                color: {fg_color};
                border: none;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
                padding: 5px; /* Minimal padding */
            }}
        """)
        
        # Set document margin for tighter fit
        self.code_edit.document().setDocumentMargin(0)
        
        self._adjust_height()


class CodeCenterPanel(QWidget):
    """Premium code display for center panel."""
    
    cancelled = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._elapsed = 0
        self._code_text = ""
        self._blocks_data = [] # List of (type, content, lang)
        self._setup_ui()
        ThemeManager.add_listener(self._on_theme_changed)
        self.hide()
    
    def _on_theme_changed(self, theme):
        """Callback for theme changes."""
        self._update_theme()
        
    def reset(self):
        """Reset panel state (stop animations/timers)."""
        self.pulsing_dot.stop()
        self._elapsed_timer.stop()
        self.hide()
        
    def _setup_ui(self):
        # Main Layout (Full Width)
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QHBoxLayout()
        header.setContentsMargins(15, 10, 15, 5) # Close vertical spacing
        
        status_layout = QHBoxLayout()
        status_layout.setSpacing(10) # Add requested space between dot and text
        self.pulsing_dot = PulsingDot()
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-family: Consolas; font-size: 14px;")
        status_layout.addWidget(self.pulsing_dot)
        status_layout.addWidget(self.status_label)
        header.addLayout(status_layout)
        
        self.timer_label = QLabel("0:00")
        self.timer_label.setStyleSheet("color: #888; font-family: Consolas; margin-left: 10px;")
        header.addWidget(self.timer_label)
        
        header.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.setFixedSize(60, 28)
        self.close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.close_btn.clicked.connect(self.cancelled.emit)
        header.addWidget(self.close_btn)
        
        layout.addLayout(header)
        
        # Content Area: Scroll Area containing a VBox of widgets
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.scroll_content = QWidget()
        self.content_layout = QVBoxLayout(self.scroll_content)
        self.content_layout.setSpacing(25) # Gap between blocks
        self.content_layout.setContentsMargins(20, 10, 20, 20)
        self.content_layout.addStretch() # Push content up
        
        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area, stretch=1)
        
        # Footer
        footer = QHBoxLayout()
        footer.setSpacing(15) # Add spacing between buttons
        footer.setContentsMargins(0, 5, 15, 15)
        footer.addStretch()
        
        self.copy_btn = QPushButton("Copy All")
        self.copy_btn.setFixedSize(100, 30)
        self.copy_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.copy_btn.clicked.connect(self._copy_all_code)
        self.copy_btn.hide()
        footer.addWidget(self.copy_btn)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.setFixedSize(80, 30)
        self.save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.save_btn.clicked.connect(self._save_code)
        self.save_btn.hide()
        footer.addWidget(self.save_btn)
        
        layout.addLayout(footer)
        
        self._elapsed_timer = QTimer()
        self._elapsed_timer.timeout.connect(self._update_timer)
        self._update_theme()

    def start(self):
        """Start code generation display."""
        self._code_text = ""
        self._blocks_data = [] # Reset data
        
        # Clear existing widgets (except stretch)
        while self.content_layout.count() > 1:
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        self._update_theme()
        
        self.pulsing_dot.update_color(self._get_accent_color())
        self.status_label.setText("Generating...")
        self.timer_label.setText("0:00")
        self.copy_btn.hide()
        self.save_btn.hide()
        
        self.pulsing_dot.start()
        self._elapsed_timer.start(1000)
        self.show()
        self._elapsed = 0
    
    def on_token(self, token: str):
        self._code_text += token
        self._reconcile_content()
        
        # Scroll to bottom
        scrollbar = self.scroll_area.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())
            
    def _reconcile_content(self):
        """Parse full text and update widgets."""
        # Simple Markdown Splitter with cleanup
        parts = re.split(r"(```[a-zA-Z0-9_\-\.\+]*\n.*?```|```[a-zA-Z0-9_\-\.\+]*\n.*$)", self._code_text, flags=re.DOTALL)
        
        valid_parts = [p for p in parts if p.strip()] # Filter out empty/whitespace-only parts to prevent gaps
        
        current_widget_idx = 0
        
        for part in valid_parts:
            # Determine type
            is_code = part.startswith("```")
            content = part
            lang = "CODE"
            
            if is_code:
                lines = part.split('\n')
                lang_line = lines[0].strip('`').strip()
                if lang_line: 
                    lang = lang_line
                
                if part.strip().endswith("```") and len(lines) > 1:
                     content = "\n".join(lines[1:-1])
                else:
                     content = "\n".join(lines[1:])
            
            # Clean content strictly to prevent huge boxes
            content = content.strip()
            
            # Reuse/Create Widget Logic
            widget = None
            if current_widget_idx < self.content_layout.count() - 1:
                item = self.content_layout.itemAt(current_widget_idx)
                if item and item.widget():
                    widget = item.widget()
            
            if widget:
                if is_code and isinstance(widget, CodeBlockWidget):
                    widget.set_content(content) 
                elif not is_code and isinstance(widget, TextSectionWidget):
                    widget.setText(content)
                else:
                    self._clear_from(current_widget_idx)
                    widget = None
            
            if widget is None:
                if is_code:
                    widget = CodeBlockWidget(language=lang, code=content)
                else:
                    widget = TextSectionWidget(text=content)
                
                widget.update_theme(ThemeManager.get_theme().name == "dark")
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
        self.status_label.setText("Complete")
        self.copy_btn.show()
        self.save_btn.show()

    def on_error(self, msg: str):
        self.pulsing_dot.stop()
        self._elapsed_timer.stop()
        self.status_label.setText("Error")
        self.status_label.setStyleSheet("color: #ff6666; font-family: Consolas; font-size: 14px;")
        
        # Add error widget
        error_widget = TextSectionWidget(f"Error: {msg}")
        error_widget.setStyleSheet("color: #ff6666; font-family: Consolas; font-size: 14px;")
        self.content_layout.insertWidget(self.content_layout.count()-1, error_widget)

    def _update_timer(self):
        self._elapsed += 1
        mins = self._elapsed // 60
        secs = self._elapsed % 60
        self.timer_label.setText(f"{mins}:{secs:02d}")
    
    def _get_accent_color(self):
        theme = ThemeManager.get_theme()
        return GREEN if theme.name == "dark" else RED

    def _update_theme(self):
        theme = ThemeManager.get_theme()
        is_dark = theme.name == "dark"
        
        # Main Background
        bg_color = "rgba(0, 0, 0, 0.95)" if is_dark else "rgba(255, 255, 255, 0.95)"
        self.setStyleSheet(f"background-color: {bg_color};")
        
        # Status
        accent = self._get_accent_color()
        self.status_label.setStyleSheet(f"color: {accent}; font-family: Consolas; font-size: 14px;")
        self.pulsing_dot.update_color(accent)
        
        # Scroll Area Scrollbar Style
        # (Assuming dark means dark scrollbar)
        
        # Update Content Widgets
        for i in range(self.content_layout.count()):
            item = self.content_layout.itemAt(i)
            if item and item.widget():
                if hasattr(item.widget(), "update_theme"):
                    item.widget().update_theme(is_dark)

        # Buttons
        btn_bg = "rgba(128, 128, 128, 0.1)"
        btn_hover = "rgba(128, 128, 128, 0.2)"
        
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {btn_bg};
                color: #888;
                border: none;
                border-radius: 14px;
                font-family: Consolas;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: rgba(255, 100, 100, 0.2);
                color: #ff6666;
            }}
        """)
        
        self.copy_btn.setStyleSheet(f"""
            QPushButton {{
                background: {btn_bg};
                color: {accent};
                border: 1px solid {accent};
                border-radius: 15px;
                font-family: Consolas;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: {btn_hover};
            }}
        """)
        
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #833AB4, stop:1 {PINK});
                color: white;
                border: none;
                border-radius: 15px;
                font-family: Consolas;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #9b4fc9, stop:1 #f04080);
            }}
        """)

    def _extract_code(self) -> str:
        """Extract code blocks from full text."""
        matches = re.findall(r"```(?:\w+)?\n(.*?)```", self._code_text, re.DOTALL)
        if matches:
            return "\n\n".join(matches).strip()
        return self._code_text.strip()
    
    def _copy_all_code(self):
        code_to_copy = self._extract_code()
        clipboard = QApplication.clipboard()
        clipboard.setText(code_to_copy)
        self.copy_btn.setText("Copied!")
        QTimer.singleShot(1500, lambda: self.copy_btn.setText("Copy All"))
    
    def _save_code(self):
        code_to_save = self._extract_code()
        ext = ".txt" # Simple detection or use old logic if needed. 
        # Re-implementing detection briefly:
        if "def " in code_to_save: ext = ".py"
        elif "function " in code_to_save: ext = ".js"
        
        default_name = f"code_{uuid.uuid4().hex[:8]}{ext}"
        filepath, _ = QFileDialog.getSaveFileName(self, "Save Code", str(Path.home() / "Desktop" / default_name), f"Code Files (*{ext});;All Files (*)")
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(code_to_save)
