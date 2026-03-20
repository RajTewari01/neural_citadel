"""
Movie Downloader Panel
======================

Panel for movie downloader operations with input fields
for different operation types.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QComboBox, QFrame, QFileDialog,
    QCheckBox, QScrollArea, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor
from infra.gui.theme import ThemeManager

# Instagram colors
PURPLE = "#833AB4"
PINK = "#E1306C"
ORANGE = "#F77737"


class MoviePanel(QFrame):
    """
    Panel for movie downloader operations.
    Shows different inputs based on operation type.
    """
    
    # Signals
    youtube_requested = pyqtSignal(str, str, bool)  # url, quality, download_playlist
    torrent_requested = pyqtSignal(str, int)      # query, limit
    torrent_download_requested = pyqtSignal(str)  # magnet link
    scan_requested = pyqtSignal()                 # no args
    subtitle_requested = pyqtSignal(str, str, str, str)  # file, lang, task, model
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MoviePanel")
        self._current_mode = "youtube"
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        
        # Header
        header = QHBoxLayout()
        
        self.title_label = QLabel("🎬 MOVIE DOWNLOADER")
        self.title_label.setObjectName("title")
        self.title_label.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        header.addWidget(self.title_label)
        
        header.addStretch()
        
        # Close button
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.close_btn.clicked.connect(self.hide)
        header.addWidget(self.close_btn)
        
        layout.addLayout(header)
        
        # Operation selector
        op_layout = QHBoxLayout()
        op_label = QLabel("Operation:")
        op_layout.addWidget(op_label)
        
        self.op_combo = QComboBox()
        self.op_combo.addItems([
            "🎬 Any Video Download",
            "🏴‍☠️ Torrent Search",
            "🛡️ Scan Downloads",
            "📝 Generate Subtitles"
        ])
        self.op_combo.currentIndexChanged.connect(self._on_operation_changed)
        op_layout.addWidget(self.op_combo, 1)
        
        layout.addLayout(op_layout)
        
        # YouTube section
        self.youtube_section = QWidget()
        yt_layout = QVBoxLayout(self.youtube_section)
        yt_layout.setContentsMargins(0, 0, 0, 0)
        yt_layout.setSpacing(8)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter Video URL (YouTube, Vimeo, etc.)...")
        yt_layout.addWidget(self.url_input)
        
        quality_layout = QHBoxLayout()
        quality_label = QLabel("Quality:")
        quality_layout.addWidget(quality_label)
        
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["best", "4k", "1080p", "720p", "480p"])
        quality_layout.addWidget(self.quality_combo)
        
        quality_layout.addSpacing(15)
        
        # Playlist checkbox
        self.playlist_check = QCheckBox("Download Playlist")
        self.playlist_check.setToolTip("Enable to download entire playlist instead of single video")
        quality_layout.addWidget(self.playlist_check)
        
        quality_layout.addStretch()
        
        yt_layout.addLayout(quality_layout)
        layout.addWidget(self.youtube_section)
        
        # Torrent section
        self.torrent_section = QWidget()
        tor_layout = QVBoxLayout(self.torrent_section)
        tor_layout.setContentsMargins(0, 0, 0, 0)
        tor_layout.setSpacing(8)
        
        # Search row
        search_row = QHBoxLayout()
        
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Enter movie name to search...")
        search_row.addWidget(self.query_input, 1)
        
        # Limit selector
        limit_label = QLabel("Limit:")
        search_row.addWidget(limit_label)
        
        self.limit_combo = QComboBox()
        self.limit_combo.addItems(["5", "10", "15", "20"])
        self.limit_combo.setCurrentText("10")
        self.limit_combo.setFixedWidth(60)
        search_row.addWidget(self.limit_combo)
        
        tor_layout.addLayout(search_row)
        
        # Results list (scrollable)
        self.torrent_results_area = QScrollArea()
        self.torrent_results_area.setWidgetResizable(True)
        self.torrent_results_area.setMaximumHeight(160)
        
        self.torrent_results_list = QListWidget()
        self.torrent_results_list.itemDoubleClicked.connect(self._on_result_double_click)
        self.torrent_results_area.setWidget(self.torrent_results_list)
        self.torrent_results_area.hide()  # Hidden until search
        tor_layout.addWidget(self.torrent_results_area)
        
        # Action buttons row
        self.torrent_actions = QWidget()
        actions_layout = QHBoxLayout(self.torrent_actions)
        actions_layout.setContentsMargins(0, 6, 0, 0)
        actions_layout.setSpacing(10)
        
        # Selection input
        self.selection_input = QLineEdit()
        self.selection_input.setPlaceholderText("#")
        self.selection_input.setFixedWidth(50)
        actions_layout.addWidget(self.selection_input)
        
        # Download button
        self.download_btn = QPushButton("↓ Download")
        self.download_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.download_btn.setFixedHeight(32)
        self.download_btn.clicked.connect(self._on_download_selected)
        actions_layout.addWidget(self.download_btn)
        
        actions_layout.addStretch()
        
        # Cancel button
        self.cancel_btn = QPushButton("✕")
        self.cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.cancel_btn.setFixedSize(32, 32)
        self.cancel_btn.setToolTip("Cancel and clear results")
        self.cancel_btn.clicked.connect(self._clear_results)
        actions_layout.addWidget(self.cancel_btn)
        
        self.torrent_actions.hide()  # Hidden until search
        tor_layout.addWidget(self.torrent_actions)
        
        # Store results data
        self._torrent_results = []
        
        layout.addWidget(self.torrent_section)
        self.torrent_section.hide()
        
        # Scan section
        self.scan_section = QWidget()
        scan_layout = QVBoxLayout(self.scan_section)
        scan_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scan_info = QLabel("🛡️ Scans your downloads folder for malware")
        scan_layout.addWidget(self.scan_info)
        
        layout.addWidget(self.scan_section)
        self.scan_section.hide()
        
        # Subtitle section
        self.subtitle_section = QWidget()
        sub_layout = QVBoxLayout(self.subtitle_section)
        sub_layout.setContentsMargins(0, 0, 0, 0)
        sub_layout.setSpacing(8)
        
        # File picker
        file_layout = QHBoxLayout()
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("Select video file...")
        file_layout.addWidget(self.file_input, 1)
        
        self.browse_btn = QPushButton("📁")
        self.browse_btn.setFixedSize(32, 32)
        self.browse_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(self.browse_btn)
        
        sub_layout.addLayout(file_layout)
        
        # Options row
        opts_layout = QHBoxLayout()
        
        lang_label = QLabel("Lang:")
        opts_layout.addWidget(lang_label)
        
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["en", "bn", "hi", "es", "fr", "de", "ja", "ko", "zh"])
        opts_layout.addWidget(self.lang_combo)
        
        opts_layout.addSpacing(10)
        
        model_label = QLabel("Model:")
        opts_layout.addWidget(model_label)
        
        self.model_combo = QComboBox()
        self.model_combo.addItems(["small", "tiny", "base", "medium"])
        opts_layout.addWidget(self.model_combo)
        
        opts_layout.addStretch()
        sub_layout.addLayout(opts_layout)
        
        layout.addWidget(self.subtitle_section)
        self.subtitle_section.hide()
        
        # Run button
        self.run_btn = QPushButton("▶ Run")
        self.run_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.run_btn.clicked.connect(self._on_run)
        layout.addWidget(self.run_btn)
        
        # Initial Styling
        self.update_theme()
    
    def update_theme(self):
        """Update styles based on current theme."""
        theme = ThemeManager.get_theme()
        is_dark = theme.name == "dark"
        print(f"[MoviePanel] update_theme: is_dark={is_dark}, theme={theme.name}")
        
        if is_dark:
            bg_color = "#0a0a0f"
            border_color = "#333"
            text_color = "#ffffff"
            text_secondary = "#888"
            input_bg = "#1a1a2e"
            input_border = "#333"
            combo_sel = PINK
            res_bg = "#0a0a0f"
            res_hover = "#1a1a2e"
            
            close_color = "#666"
            close_border = "#333"
            
            checkbox_border = "#555"
            checkbox_unchecked = "#1a1a1a"
        else:
            bg_color = "rgba(255, 255, 255, 0.95)"
            border_color = "#e0e0e0"
            text_color = "#000000"
            text_secondary = "#666"
            input_bg = "#f8f9fa"
            input_border = "#ddd"
            combo_sel = "#9B6EB7"
            res_bg = "#ffffff"
            res_hover = "#f0f0f5"
            
            close_color = "#888"
            close_border = "#ddd"
            
            checkbox_border = "#ddd"
            checkbox_unchecked = "#fff"

        # Global Styles
        self.setStyleSheet(f"""
            QFrame#MoviePanel {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 12px;
            }}
            QLabel {{
                color: {text_secondary};
                font-family: Consolas;
                font-size: 11px;
            }}
            QLabel#title {{
                color: {ORANGE};
                font-size: 10px;
                font-weight: bold;
            }}
            QLineEdit {{
                background-color: {input_bg};
                color: {text_color};
                border: 1px solid {input_border};
                border-radius: 8px;
                padding: 10px;
                font-family: Consolas;
                font-size: 11px;
            }}
            QLineEdit:focus {{
                border-color: {PINK};
            }}
            QComboBox {{
                background-color: {input_bg};
                color: {text_color};
                border: 1px solid {input_border};
                border-radius: 6px;
                padding: 6px 10px;
                font-family: Consolas;
                font-size: 11px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {input_bg};
                color: {text_color};
                border: 1px solid {input_border};
                selection-background-color: {combo_sel};
                selection-color: white;
            }}
        """)
        
        # Close Button
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {close_color};
                border: 1px solid {close_border};
                border-radius: 12px;
            }}
            QPushButton:hover {{
                color: #ff5555;
                border-color: #ff5555;
            }}
        """)
        
        # Checkbox
        self.playlist_check.setStyleSheet(f"""
            QCheckBox {{
                color: {text_secondary};
                font-size: 10px;
                font-family: Consolas;
            }}
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
            }}
            QCheckBox::indicator:unchecked {{
                border: 1px solid {checkbox_border};
                background: {checkbox_unchecked};
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                border: 1px solid #833AB4;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #833AB4, stop:1 #E1306C);
                border-radius: 3px;
            }}
        """)
        
        # Torrent Results
        self.torrent_results_area.setStyleSheet(f"""
            QScrollArea {{
                background: {res_bg};
                border: 1px solid {input_border};
                border-radius: 6px;
            }}
            QScrollBar:vertical {{
                background: {input_bg};
                width: 8px;
            }}
            QScrollBar::handle:vertical {{
                background: {text_secondary};
                border-radius: 4px;
            }}
        """)
        
        self.torrent_results_list.setStyleSheet(f"""
            QListWidget {{
                background: {res_bg};
                color: {text_color};
                border: none;
                font-family: Consolas;
                font-size: 11px;
            }}
            QListWidget::item {{
                padding: 6px;
                border-bottom: 1px solid {input_border};
            }}
            QListWidget::item:selected {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(131, 58, 180, 0.5), stop:1 rgba(225, 48, 108, 0.5));
                color: white;
            }}
            QListWidget::item:hover {{
                background-color: {res_hover};
            }}
        """)
        
        # Download Button
        self.download_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {PURPLE}, stop:1 {PINK});
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-family: Consolas;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {PINK}, stop:1 {ORANGE});
            }}
        """)
        
        # Cancel Button (Always red-ish, but maybe clearer in light mode?)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #cc3333, stop:0.5 #aa2222, stop:1 #882222);
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ff4444, stop:0.5 #cc3333, stop:1 #aa2222);
            }
        """)

        # Browse Button
        self.browse_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {PURPLE};
                color: white;
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {PINK};
            }}
        """)

        # Run Button
        self.run_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {PURPLE}, stop:0.5 {PINK}, stop:1 {ORANGE});
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-family: Consolas;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {ORANGE}, stop:0.5 {PINK}, stop:1 {PURPLE});
            }}
            QPushButton:disabled {{
                background: #333;
                color: #666;
            }}
        """)
    
    def _on_operation_changed(self, index):
        # Hide all sections
        self.youtube_section.hide()
        self.torrent_section.hide()
        self.scan_section.hide()
        self.subtitle_section.hide()
        
        # Show selected section
        if index == 0:  # YouTube
            self.youtube_section.show()
            self._current_mode = "youtube"
        elif index == 1:  # Torrent
            self.torrent_section.show()
            self._current_mode = "torrent"
        elif index == 2:  # Scan
            self.scan_section.show()
            self._current_mode = "scan"
        elif index == 3:  # Subtitle
            self.subtitle_section.show()
            self._current_mode = "subtitle"
    
    def _browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            "",
            "Video Files (*.mp4 *.mkv *.avi *.mov *.webm);;All Files (*)"
        )
        if file_path:
            self.file_input.setText(file_path)
    
    def _on_run(self):
        if self._current_mode == "youtube":
            url = self.url_input.text().strip()
            quality = self.quality_combo.currentText()
            download_playlist = self.playlist_check.isChecked()
            if url:
                self.youtube_requested.emit(url, quality, download_playlist)
        
        elif self._current_mode == "torrent":
            query = self.query_input.text().strip()
            limit = int(self.limit_combo.currentText())
            if query:
                self.torrent_requested.emit(query, limit)
        
        elif self._current_mode == "scan":
            self.scan_requested.emit()
        
        elif self._current_mode == "subtitle":
            file_path = self.file_input.text().strip()
            lang = self.lang_combo.currentText()
            task = "transcribe"  # Could add translate option
            model = self.model_combo.currentText()
            if file_path:
                self.subtitle_requested.emit(file_path, lang, task, model)
    
    def set_enabled(self, enabled: bool):
        """Enable/disable all inputs."""
        self.run_btn.setEnabled(enabled)
        self.url_input.setEnabled(enabled)
        self.query_input.setEnabled(enabled)
        self.file_input.setEnabled(enabled)
    
    def display_torrent_results(self, results: list):
        """Display search results in the list."""
        self._torrent_results = results
        self.torrent_results_list.clear()
        
        for r in results:
            idx = r.get("index", 0)
            name = r.get("name", "Unknown")
            # Truncate name if too long
            if len(name) > 55:
                name = name[:52] + "..."
            seeds = r.get("seeders", 0)
            size = r.get("size", "?")
            source = r.get("source", "?")
            
            # Multi-line format:
            # [1] Movie.Name.Here
            #     💾 1.5 GB  🌱 123  [TPB]
            text = f"[{idx}] {name}\n     💾 {size}  🌱 {seeds}  [{source}]"
            self.torrent_results_list.addItem(text)
        
        # Show results area and actions
        self.torrent_results_area.show()
        self.torrent_actions.show()
        self.selection_input.clear()
        self.selection_input.setFocus()
    
    def _on_result_double_click(self, item):
        """Handle double-click on a result - start download."""
        row = self.torrent_results_list.row(item)
        if 0 <= row < len(self._torrent_results):
            self._download_result(row)
    
    def _on_download_selected(self):
        """Handle download button click."""
        # Try from text input first, then from selection
        text = self.selection_input.text().strip()
        if text.isdigit():
            idx = int(text) - 1  # Convert to 0-indexed
            if 0 <= idx < len(self._torrent_results):
                self._download_result(idx)
                return
        
        # Try from list selection
        selected = self.torrent_results_list.currentRow()
        if 0 <= selected < len(self._torrent_results):
            self._download_result(selected)
    
    def _download_result(self, index: int):
        """Initiate download for a specific result."""
        if index < 0 or index >= len(self._torrent_results):
            return
        
        result = self._torrent_results[index]
        magnet = result.get("magnet", "")
        info_hash = result.get("info_hash", "")
        
        # Use magnet if available, otherwise use info hash
        if magnet:
            self.torrent_download_requested.emit(magnet)
        elif info_hash:
            self.torrent_download_requested.emit(info_hash)
    
    def _clear_results(self):
        """Clear search results and hide results area."""
        self._torrent_results = []
        self.torrent_results_list.clear()
        self.torrent_results_area.hide()
        self.torrent_actions.hide()
        self.selection_input.clear()
