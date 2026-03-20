"""
Newspaper Publisher Panel
=========================

Panel for generating PDF newspapers from RSS feeds.
Uses subprocess to run runner.py in global venv.
"""

import os
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QFrame, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QProcess
from PyQt6.QtGui import QFont, QCursor

from infra.gui.theme import ThemeManager

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Instagram colors
PURPLE = "#833AB4"
PINK = "#E1306C"
ORANGE = "#F77737"

# Categories & Styles
REGIONS = ["INDIA", "USA", "GLOBAL"]
STYLES = ["Classic", "Modern", "Magazine"]
MAGAZINE_SUBSTYLES = [
    # Original Styles
    "Neural Citadel",
    "The Tech",
    "The Times",
    "The Minimal",
    "The Bold",
    "The Elegant",
    "The Geo",
    "The Star",
    "The Noir",
    "The Pop",
    "The Corporate",
    "The Future",
    # Premium Vogue Styles
    "Vogue Classic",
    "Vogue Paris",
    "Vogue Noir",
    "Elle Style",
    "Harpers Bazaar",
    "GQ Magazine"
]

# Languages (Popular ones)
LANGUAGES = [
    "English",
    "Hindi", 
    "Bengali",
    "Spanish",
    "French",
    "German",
    "Japanese",
    "Chinese",
    "Korean",
    "Russian",
    "Portuguese",
    "Arabic",
    "Tamil",
    "Telugu",
    "Gujarati",
    "Punjabi",
    "Filipino",
    "Vietnamese",
    "Thai",
    "Indonesian"
]


class NewspaperPanel(QFrame):
    """
    Panel for newspaper generation.
    """
    
    # Signals
    generation_complete = pyqtSignal(str)  # output_path
    generation_started = pyqtSignal(str)   # message (for chat bubble)
    generation_progress = pyqtSignal(str)  # live stdout progress
    close_requested = pyqtSignal()         # Signal to close/hide panel
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("NewspaperPanel")
        self._process = None
        self._timer = QTimer()
        self._elapsed = 0
        self._output_path = None
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 15)
        layout.setSpacing(10)
        
        # Header - Compact & Sleek
        header = QHBoxLayout()
        header.setSpacing(8)
        
        self.title_label = QLabel("📰 Newspaper")
        self.title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #ccc;")
        header.addWidget(self.title_label)
        
        header.addStretch()
        
        # Back button - Premium & Solid
        self.back_btn = QPushButton("Back")
        self.back_btn.setFixedSize(70, 32)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                color: #e0e0e0;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-color: rgba(255, 255, 255, 0.4);
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.05);
            }
        """)
        self.back_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        header.addWidget(self.back_btn)
        
        layout.addLayout(header)
        
        # Thin separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: rgba(255,255,255,0.05);")
        layout.addWidget(sep)
        
        # Controls Section
        controls = QVBoxLayout()
        controls.setSpacing(12)
        
        # Region
        region_row = QHBoxLayout()
        region_label = QLabel("Region:")
        region_label.setFixedWidth(80)
        region_row.addWidget(region_label)
        
        self.region_combo = QComboBox()
        self.region_combo.addItems(REGIONS)
        self.region_combo.setCurrentText("INDIA")
        region_row.addWidget(self.region_combo, 1)
        controls.addLayout(region_row)
        
        # Style
        style_row = QHBoxLayout()
        style_label = QLabel("Style:")
        style_label.setFixedWidth(80)
        style_row.addWidget(style_label)
        
        self.style_combo = QComboBox()
        self.style_combo.addItems(STYLES)
        self.style_combo.currentTextChanged.connect(self._on_style_changed)
        style_row.addWidget(self.style_combo, 1)
        controls.addLayout(style_row)
        
        # Substyle (for Magazine)
        self.substyle_row = QHBoxLayout()
        substyle_label = QLabel("Substyle:")
        substyle_label.setFixedWidth(80)
        self.substyle_row.addWidget(substyle_label)
        
        self.substyle_combo = QComboBox()
        self.substyle_combo.addItems(MAGAZINE_SUBSTYLES)
        self.substyle_row.addWidget(self.substyle_combo, 1)
        
        self.substyle_widget = QWidget()
        self.substyle_widget.setLayout(self.substyle_row)
        self.substyle_widget.hide()
        controls.addWidget(self.substyle_widget)
        
        # Language
        lang_row = QHBoxLayout()
        lang_label = QLabel("Language:")
        lang_label.setFixedWidth(80)
        lang_row.addWidget(lang_label)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(LANGUAGES)
        self.language_combo.setCurrentText("English")
        lang_row.addWidget(self.language_combo, 1)
        controls.addLayout(lang_row)
        
        # Translation Mode
        mode_row = QHBoxLayout()
        mode_label = QLabel("Mode:")
        mode_label.setFixedWidth(80)
        mode_row.addWidget(mode_label)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Online (Fast)", "Offline (NLLB)"])
        self.mode_combo.setCurrentText("Online (Fast)")
        mode_row.addWidget(self.mode_combo, 1)
        controls.addLayout(mode_row)
        
        layout.addLayout(controls)
        
        # Generate Button
        self.generate_btn = QPushButton("🚀 Generate Newspaper")
        self.generate_btn.setFixedHeight(48)
        self.generate_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.generate_btn.clicked.connect(self._start_generation)
        layout.addWidget(self.generate_btn)
        
        # Loading Section (Hidden by default)
        self.loading_widget = QWidget()
        loading_layout = QHBoxLayout(self.loading_widget)
        loading_layout.setContentsMargins(0, 10, 0, 10)
        
        self.pulse_label = QLabel("●")
        self.pulse_label.setStyleSheet(f"color: {PINK}; font-size: 24px;")
        loading_layout.addWidget(self.pulse_label)
        
        self.status_label = QLabel("Generating...")
        self.status_label.setStyleSheet("font-size: 14px;")
        loading_layout.addWidget(self.status_label)
        
        loading_layout.addStretch()
        
        self.timer_label = QLabel("⏱ 0s")
        self.timer_label.setStyleSheet("font-size: 14px; color: #888;")
        loading_layout.addWidget(self.timer_label)
        
        self.loading_widget.hide()
        layout.addWidget(self.loading_widget)
        
        # Result Section (Hidden by default)
        self.result_widget = QWidget()
        result_layout = QVBoxLayout(self.result_widget)
        result_layout.setContentsMargins(0, 10, 0, 10)
        
        result_header = QHBoxLayout()
        self.result_icon = QLabel("✅")
        self.result_icon.setStyleSheet("font-size: 20px;")
        result_header.addWidget(self.result_icon)
        
        self.result_label = QLabel("PDF Generated!")
        self.result_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        result_header.addWidget(self.result_label)
        result_header.addStretch()
        result_layout.addLayout(result_header)
        
        # Path row
        path_row = QHBoxLayout()
        self.path_label = QLabel("")
        self.path_label.setStyleSheet("font-size: 11px; color: #888;")
        self.path_label.setWordWrap(True)
        path_row.addWidget(self.path_label, 1)
        
        self.copy_btn = QPushButton("📋 Copy")
        self.copy_btn.setFixedSize(70, 28)
        self.copy_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.copy_btn.clicked.connect(self._copy_path)
        path_row.addWidget(self.copy_btn)
        
        self.open_btn = QPushButton("📂 Open")
        self.open_btn.setFixedSize(70, 28)
        self.open_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.open_btn.clicked.connect(self._open_pdf)
        path_row.addWidget(self.open_btn)
        
        result_layout.addLayout(path_row)
        
        self.result_widget.hide()
        layout.addWidget(self.result_widget)
        
        layout.addStretch()
        
        self._update_theme()
    
    def _connect_signals(self):
        ThemeManager.add_listener(self._update_theme)
        self._timer.timeout.connect(self._update_timer)
        self.back_btn.clicked.connect(self.close_requested.emit)
    
    def _on_style_changed(self, style):
        if style == "Magazine":
            self.substyle_widget.show()
        else:
            self.substyle_widget.hide()
    
    def _start_generation(self):
        # Hide result, show loading
        self.result_widget.hide()
        self.loading_widget.show()
        self.generate_btn.setEnabled(False)
        
        # Start timer
        self._elapsed = 0
        self.timer_label.setText("⏱ 0s")
        self._timer.start(1000)
        
        # Start pulse animation
        self._pulse_state = True
        self._pulse_timer = QTimer()
        self._pulse_timer.timeout.connect(self._animate_pulse)
        self._pulse_timer.start(500)
        
        # Build command - Use GLOBAL Python (not pyqt_venv)
        # The global Python has newspaper_publisher dependencies
        GLOBAL_PYTHON = r"C:\Program Files\Python310\python.exe"
        
        region = self.region_combo.currentText()
        style = self.style_combo.currentText()
        language = self.language_combo.currentText()
        mode = "online" if "Online" in self.mode_combo.currentText() else "offline"
        
        cmd = [
            GLOBAL_PYTHON,
            "-u",  # Unbuffered output - ensures print() appears immediately
            str(PROJECT_ROOT / "apps" / "newspaper_publisher" / "runner.py"),
            "--category", region,
            "--style", style,
            "--language", language,
            f"--{mode}"
            
        ]
        
        if style == "Magazine":
            substyle = self.substyle_combo.currentText()
            cmd.extend(["--substyle", substyle])
        
        # Emit started signal for chat bubble
        msg = f"Started generating {style} newspaper for {region} in {language}..."
        if style == "Magazine":
            msg = f"Started generating {style} ({substyle}) newspaper for {region} in {language}..."
        self.generation_started.emit(msg)

        print(f"[NewspaperPanel] Running: {' '.join(cmd)}")
        
        # Run subprocess
        self._process = QProcess()
        self._process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._process.readyReadStandardOutput.connect(self._on_output)
        self._process.finished.connect(self._on_finished)
        self._process.start(cmd[0], cmd[1:])
    
    def _animate_pulse(self):
        self._pulse_state = not self._pulse_state
        color = PINK if self._pulse_state else "#555"
        self.pulse_label.setStyleSheet(f"color: {color}; font-size: 24px;")
    
    def _update_timer(self):
        self._elapsed += 1
        self.timer_label.setText(f"⏱ {self._elapsed}s")
    
    def _on_output(self):
        # FIX: Safe decoding for Windows output
        output = self._process.readAllStandardOutput().data().decode('utf-8', errors='replace')
        print(output, end="")
        
        # Try to extract PDF path from output
        for line in output.split("\n"):
            clean_line = line.strip()
            if not clean_line:
                continue
            
            # Emit progress for chat bubble
            self.generation_progress.emit(clean_line)
            
            # Show live progress in the panel UI
            if len(clean_line) > 60:
                self.status_label.setText(clean_line[:57] + "...")
            else:
                self.status_label.setText(clean_line)
            
            if "Path:" in line:
                # Format: "   Path: D:\...\file.pdf"
                path_part = line.split("Path:")[-1].strip()
                self._output_path = path_part
            elif "-> Output:" in line:
                # Format: "   -> Output: D:\...\file.pdf"
                path_part = line.split("-> Output:")[-1].strip()
                self._output_path = path_part
            elif line.strip().endswith(".pdf") and (":\\" in line or "/" in line):
                 # Strict check for absolute paths
                 self._output_path = line.strip()
    
    def _on_finished(self, exit_code, exit_status):
        # Stop timers
        self._timer.stop()
        self._pulse_timer.stop()
        
        # Hide loading
        self.loading_widget.hide()
        self.generate_btn.setEnabled(True)
        
        # Try to find latest PDF if we missed the path
        if not self._output_path:
            try:
                # Check default output directory
                output_dir = PROJECT_ROOT / "assets" / "generated" / "newspaper"
                if output_dir.exists():
                    files = [f for f in output_dir.iterdir() if f.suffix == '.pdf']
                    if files:
                        # Find newest file created in the last 2 minutes
                        newest = max(files, key=os.path.getctime)
                        if time.time() - os.path.getctime(newest) < 120:
                            self._output_path = newest
            except: pass

        # Success if we have a path, even if exit_code != 0 (warnings)
        if self._output_path and os.path.exists(self._output_path):
            # Emit result only (UI handled in chat)
            self.generation_complete.emit(self._output_path)
            self.status_label.setText(f"✓ Generated: {os.path.basename(self._output_path)}")
        else:
            self.status_label.setText("❌ Generation failed")
            self.loading_widget.show()
    
    def _copy_path(self):
        if self._output_path:
            clipboard = QApplication.clipboard()
            clipboard.setText(self._output_path)
            self.copy_btn.setText("✓ Copied!")
            QTimer.singleShot(2000, lambda: self.copy_btn.setText("📋 Copy"))
    
    def _open_pdf(self):
        if self._output_path and os.path.exists(self._output_path):
            os.startfile(self._output_path)
    
    def _update_theme(self, theme=None):
        if theme is None:
            theme = ThemeManager.get_theme()
        is_dark = theme.name == "dark"
        
        print(f"[NewspaperPanel] update_theme: is_dark={is_dark}, theme={theme.name}")
        
        bg = "#121212" if is_dark else "#f5f5f7"
        text = "#ffffff" if is_dark else "#000000"
        border = "rgba(255,255,255,0.1)" if is_dark else "rgba(0,0,0,0.1)"
        
        self.setStyleSheet(f"""
            QFrame#NewspaperPanel {{
                background-color: {bg};
                border-radius: 12px;
            }}
            QLabel {{
                color: {text};
            }}
            QComboBox {{
                background-color: {'#2a2a2a' if is_dark else '#ffffff'};
                color: {text};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 8px 12px;
                min-height: 20px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {'#2a2a2a' if is_dark else '#ffffff'};
                color: {text};
                selection-background-color: {PINK};
            }}
            QPushButton {{
                background-color: {'rgba(255,255,255,0.1)' if is_dark else '#e0e0e0'};
                color: {text};
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: rgba(225, 48, 108, 0.3);
            }}
            QPushButton#generate_btn {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {PURPLE}, stop:0.5 {PINK}, stop:1 {ORANGE});
                color: white;
                font-weight: bold;
                font-size: 14px;
            }}
        """)
        
        self.generate_btn.setObjectName("generate_btn")
