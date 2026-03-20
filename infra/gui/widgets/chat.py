"""
Chat Widget - V3
Gradient bubbles: Instagram gradient for user, black gradient for AI
Pop-up model selector above input
Image generation integration with subprocess
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea, QFrame, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QPoint, QTimer, QRectF
from PyQt6.QtGui import QFont, QCursor, QAction, QPixmap, QPainter, QPen, QColor

from infra.gui.theme import ThemeManager
from .image_gen_panel import ImageGenPanel
from .image_worker import ImageWorker
from .progress_widget import GeneratingWidget
from .image_popup import ImagePopup
from .movie_panel import MoviePanel
from .newspaper_panel import NewspaperPanel
from .movie_worker import MovieWorker
from .download_progress import DownloadProgressWidget, MoviePlayPopup, InlineVideoPlayer
from .qr_panel import QRPanel
from .qr_worker import QRWorker
from .newspaper_result_widget import NewspaperResultWidget
from .reasoning_worker import ReasoningManager
from .reasoning_widget import ReasoningWidget


class SpinnerButton(QPushButton):
    """Button that can show a circular spinning arc when processing."""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._spinning = False
        self._angle = 0
        self._spinner_timer = QTimer()
        self._spinner_timer.timeout.connect(self._update_spin)
        self._arc_color = QColor("#ffffff")
        self._arc_width = 3
        self._arc_length = 90  # degrees
    
    def start_spinner(self):
        """Start the spinning animation."""
        self._spinning = True
        self._angle = 0
        self._spinner_timer.start(30)  # ~33 fps for smooth spin
        self.update()
    
    def stop_spinner(self):
        """Stop the spinning animation."""
        self._spinning = False
        self._spinner_timer.stop()
        self.update()
    
    def is_spinning(self):
        return self._spinning
    
    def _update_spin(self):
        """Update the spin angle."""
        self._angle = (self._angle + 15) % 360
        self.update()
    
    def paintEvent(self, event):
        """Override paint to draw spinning arc when active."""
        if self._spinning:
            # When spinning, draw ONLY the button background and spinner (NO text/emoji)
            from PyQt6.QtWidgets import QStyleOptionButton, QStyle
            
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Draw button background only (no text)
            opt = QStyleOptionButton()
            self.initStyleOption(opt)
            opt.text = ""  # Clear text so emoji doesn't show
            self.style().drawControl(QStyle.ControlElement.CE_PushButton, opt, painter, self)
            
            # Calculate arc bounds (centered, with padding)
            padding = 6
            rect = QRectF(padding, padding, 
                         self.width() - padding * 2, 
                         self.height() - padding * 2)
            
            # Draw spinning arc
            pen = QPen(self._arc_color)
            pen.setWidth(self._arc_width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            
            # Draw arc: start angle and span angle (in 1/16th of a degree)
            start_angle = int(self._angle * 16)
            span_angle = int(self._arc_length * 16)
            painter.drawArc(rect, start_angle, span_angle)
            
            painter.end()
        else:
            # Normal button rendering with text/emoji
            super().paintEvent(event)


# Instagram colors
PURPLE = "#833AB4"
PINK = "#E1306C"
ORANGE = "#F77737"

# Model options
MODEL_OPTIONS = [
    ("💬", "Chat", "General conversation"),
    ("🧠", "Reasoning", "Deep thinking & analysis"),
    ("🎨", "Image Generation", "Create images from text"),
    ("🎬", "Movie Downloader", "Download videos & movies"),
    ("📱", "QR Studio", "Generate styled QR codes"),
    ("💻", "Code", "Programming assistance"),
    ("💀", "Hacking", "Offensive security tools"),
    ("✍️", "Writing", "Creative writing & personas"),
    ("🔥", "NSFW Stories", "Adult creative fiction"),
    ("🔍", "Search", "Web search & research"),
    ("📄", "Document", "Analyze documents"),
    ("---", "---", "---"),  # Separator
    ("🎤", "Auto-Listen", "Voice input mode"),
]


class ChatBubble(QFrame):
    """Chat bubble with gradient styling - theme aware"""
    
    def __init__(self, sender: str, message: str, is_user: bool = False):
        super().__init__()
        
        from datetime import datetime
        
        theme = ThemeManager.get_theme()
        is_dark = theme.name == "dark"
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)
        
        # Header row with sender and timestamp
        header = QHBoxLayout()
        header.setSpacing(8)
        
        # Sender label
        sender_label = QLabel(sender)
        if is_user:
            sender_color = "#ffffff"
        else:
            sender_color = "#888888" if is_dark else "#666666"
        sender_label.setStyleSheet(f"""
            color: {sender_color};
            font-size: 10px;
            font-family: Consolas;
            font-weight: bold;
        """)
        header.addWidget(sender_label)
        
        header.addStretch()
        
        # Timestamp
        time_str = datetime.now().strftime("%I:%M %p")
        time_label = QLabel(time_str)
        time_color = "#aaaaaa" if is_user else "#666666"
        time_label.setStyleSheet(f"""
            color: {time_color};
            font-size: 9px;
            font-family: Consolas;
        """)
        header.addWidget(time_label)
        
        layout.addLayout(header)
        
        # Message
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        if is_user:
            msg_color = "#ffffff"
        else:
            msg_color = "#cccccc" if is_dark else "#4a3535"
        msg_label.setStyleSheet(f"""
            color: {msg_color};
            font-size: 12px;
            font-family: Consolas;
        """)
        layout.addWidget(msg_label)
        
        # Style the bubble
        if is_user:
            # Instagram gradient for user (same in both modes)
            self.setStyleSheet(f"""
                ChatBubble {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 {PURPLE}, stop:0.5 {PINK}, stop:1 {ORANGE});
                    border: none;
                    border-radius: 16px;
                    margin-left: 30px;
                }}
            """)
        else:
            # AI bubble - different for dark/light
            if is_dark:
                self.setStyleSheet("""
                    ChatBubble {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                            stop:0 #1a1a3e, stop:0.5 #2d1b4e, stop:1 #1e3a5f);
                        border: 1px solid #3d3d6b;
                        border-radius: 16px;
                        margin-right: 30px;
                    }
                """)
            else:
                # Light mode - soft lavender/pink gradient
                self.setStyleSheet("""
                    ChatBubble {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                            stop:0 #E8D8F0, stop:0.5 #F0E0E8, stop:1 #F8E8E8);
                        border: 1px solid #D8C0D0;
                        border-radius: 16px;
                        margin-right: 30px;
                    }
                """)


class ImageBubble(QFrame):
    """Chat bubble that displays a generated image inline"""
    
    def __init__(self, image_path: str):
        super().__init__()
        
        from datetime import datetime
        import os
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(8)
        
        # Header with title and time
        header = QHBoxLayout()
        
        title = QLabel("🎨 IMAGE")
        title.setStyleSheet(f"color: {PINK}; font-size: 10px; font-family: Consolas; font-weight: bold;")
        header.addWidget(title)
        
        header.addStretch()
        
        time_str = datetime.now().strftime("%I:%M %p")
        time_label = QLabel(time_str)
        time_label.setStyleSheet("color: #666; font-size: 9px; font-family: Consolas;")
        header.addWidget(time_label)
        
        layout.addLayout(header)
        
        # Image display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # Scale to fit in bubble (max 300px wide)
                scaled = pixmap.scaledToWidth(300, Qt.TransformationMode.SmoothTransformation)
                self.image_label.setPixmap(scaled)
                self.image_path = image_path
                self.image_label.mousePressEvent = self._on_image_click
            else:
                self.image_label.setText("Failed to load image")
                self.image_label.setStyleSheet("color: #aa5555;")
        else:
            self.image_label.setText(f"Image not found:\n{image_path}")
            self.image_label.setStyleSheet("color: #aa5555;")
        
        layout.addWidget(self.image_label)
        
        # Path label
        path_label = QLabel(f"📁 {image_path}")
        path_label.setStyleSheet("color: #666; font-size: 9px; font-family: Consolas;")
        path_label.setWordWrap(True)
        layout.addWidget(path_label)
        
        # Style the bubble
        self.setStyleSheet("""
            ImageBubble {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a3e, stop:0.5 #2d1b4e, stop:1 #1e3a5f);
                border: 1px solid #3d3d6b;
                border-radius: 16px;
                margin-right: 30px;
            }
        """)
    
    def _on_image_click(self, event):
        """Open full image in popup when clicked."""
        if hasattr(self, 'image_path'):
            popup = ImagePopup(self.image_path, self.window())
            popup.exec()


class ChatWorker(QThread):
    """Background worker for AI responses"""
    finished = pyqtSignal(str)
    
    def __init__(self, message: str, model: str = "Chat"):
        super().__init__()
        self.message = message
        self.model = model
    
    def run(self):
        import time
        time.sleep(0.5)
        response = f"[{self.model}] Analysis complete.\nLaunching protocols."
        self.finished.emit(response)


class ModelSelectorButton(QPushButton):
    """Button that shows current model and opens popup menu"""
    
    model_changed = pyqtSignal(str, str)  # icon, name
    auto_listen_requested = pyqtSignal()  # Signal for voice input
    
    def __init__(self):
        super().__init__()
        self.current_icon = "💬"
        self.current_model = "Chat"
        self._setup_ui()
    
    def _setup_ui(self):
        self.setFixedHeight(32)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._update_display()
        self.clicked.connect(self._show_popup)
    
    def _update_display(self):
        self.setText(f"{self.current_icon} {self.current_model} ▾")
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(131, 58, 180, 0.3), stop:1 rgba(225, 48, 108, 0.3));
                color: #ffffff;
                border: 1px solid #3a3a3a;
                border-radius: 16px;
                padding: 6px 14px;
                font-family: Consolas;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(131, 58, 180, 0.5), stop:1 rgba(225, 48, 108, 0.5));
                border-color: {PINK};
            }}
        """)
    
    def _show_popup(self):
        """Show the model selector popup."""
        from .model_selector import ModelSelectorPopup
        
        self.popup = ModelSelectorPopup(self)
        self.popup.model_selected.connect(self._select_model)
        self.popup.auto_listen_requested.connect(self._trigger_auto_listen)
        
        # Position popup above the button, ensuring it stays on screen
        button_global = self.mapToGlobal(QPoint(0, 0))
        popup_height = self.popup.sizeHint().height()
        
        # Calculate y position - popup above button, but not off-screen
        y_pos = button_global.y() - popup_height - 5
        min_y = 50  # Keep at least 50px from top of screen
        y_pos = max(y_pos, min_y)
        
        pos = QPoint(button_global.x(), y_pos)
        self.popup.move(pos)
        self.popup.show()
    
    def _select_model(self, icon: str, name: str):
        self.current_icon = icon
        self.current_model = name
        self._update_display()
        self.model_changed.emit(icon, name)
    
    def _trigger_auto_listen(self):
        """Emit signal to start voice input"""
        self.auto_listen_requested.emit()


class ChatWidget(QWidget):
    """Chat interface with gradient bubbles and model selector"""
    mode_changed = pyqtSignal(str)  # For global layout switching
    # Reasoning signals
    reasoning_started = pyqtSignal()
    reasoning_token = pyqtSignal(str)
    reasoning_think_start = pyqtSignal()
    reasoning_think_end = pyqtSignal()
    reasoning_finished = pyqtSignal(str)
    reasoning_error = pyqtSignal(str)
    # Code signals
    code_started = pyqtSignal()
    code_token = pyqtSignal(str)
    code_finished = pyqtSignal(str)
    code_error = pyqtSignal(str)
    # Hacking signals
    hacking_started = pyqtSignal()
    hacking_token = pyqtSignal(str)
    hacking_finished = pyqtSignal(str)
    hacking_error = pyqtSignal(str)
    # Writing signals
    writing_started = pyqtSignal(str)  # Emits the user prompt
    writing_token = pyqtSignal(str)
    writing_finished = pyqtSignal(str)
    writing_error = pyqtSignal(str)
    writing_history_count = pyqtSignal(int)
    # NSFW Writing signals
    nsfw_writing_started = pyqtSignal(str, str, str)  # Emits prompt, persona, style
    nsfw_writing_token = pyqtSignal(str)
    nsfw_writing_finished = pyqtSignal(str)
    nsfw_writing_error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.current_model = "Chat"
        self.reasoning_manager = ReasoningManager()
        # Import CodeManager here to avoid circular imports
        from infra.gui.widgets.code_worker import CodeManager
        self.code_manager = CodeManager()
        # Import HackingManager
        from infra.gui.widgets.hacking_worker import HackingManager
        self.hacking_manager = HackingManager()
        # Import WritingManager
        from infra.gui.widgets.writing_worker import WritingManager
        self.writing_manager = WritingManager()
        # Import NSFWWritingManager
        from infra.gui.widgets.nsfw_writing_worker import NSFWWritingManager
        self.nsfw_writing_manager = NSFWWritingManager()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll area for messages
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidgetResizable(True)
        # Scrollbar styling is handled in update_theme()
        
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setSpacing(12)
        self.messages_layout.setContentsMargins(5, 5, 5, 5)
        self.messages_layout.addStretch()
        
        self.scroll.setWidget(self.messages_container)
        layout.addWidget(self.scroll, stretch=1)
        
        # Model selector row (above input)
        model_row = QHBoxLayout()
        model_row.setContentsMargins(0, 4, 0, 4)
        
        self.model_selector = ModelSelectorButton()
        self.model_selector.model_changed.connect(self._on_model_changed)
        self.model_selector.auto_listen_requested.connect(self._start_listening)
        model_row.addWidget(self.model_selector)
        
        # Initialize listening state
        self.is_listening = False
        
        model_row.addStretch()
        
        # Quick mode indicators
        self.mode_label = QLabel("Ready")
        self.mode_label.setStyleSheet(f"""
            color: #555;
            font-size: 10px;
            font-family: Consolas;
        """)
        model_row.addWidget(self.mode_label)
        
        layout.addLayout(model_row)
        
        # Image Generation Panel (hidden by default)
        self.image_gen_panel = ImageGenPanel()
        self.image_gen_panel.generate_requested.connect(self._on_image_generate)
        layout.addWidget(self.image_gen_panel)
        
        # Movie Downloader Panel (hidden by default)
        self.movie_panel = MoviePanel()
        self.movie_panel.youtube_requested.connect(self._on_youtube_download)
        self.movie_panel.torrent_requested.connect(self._on_torrent_search)
        self.movie_panel.torrent_download_requested.connect(self._on_torrent_download_magnet)
        self.movie_panel.scan_requested.connect(self._on_scan_downloads)
        self.movie_panel.subtitle_requested.connect(self._on_subtitle_generate)
        self.movie_panel.hide()
        layout.addWidget(self.movie_panel)
        
        # QR Studio Panel (hidden by default)
        self.qr_panel = QRPanel()
        self.qr_panel.generate_requested.connect(self._on_qr_generate)
        self.qr_panel.hide()
        layout.addWidget(self.qr_panel)
        
        # Newspaper Panel (hidden by default)
        self.newspaper_panel = NewspaperPanel()
        self.newspaper_panel.back_btn.clicked.connect(lambda: self._on_model_changed("💬", "Chat"))
        self.newspaper_panel.generation_started.connect(self._on_newspaper_start)
        self.newspaper_panel.generation_progress.connect(self._on_newspaper_progress)
        self.newspaper_panel.generation_complete.connect(self._on_newspaper_complete)
        self.newspaper_panel.hide()
        layout.addWidget(self.newspaper_panel)
        
        # Code model selector (hidden by default, shown when in Code mode)
        self.code_model_row = QHBoxLayout()
        self.code_model_row.setSpacing(8)
        
        self.code_model_label = QLabel("Coder Model:")
        self.code_model_row.addWidget(self.code_model_label)
        
        from PyQt6.QtWidgets import QComboBox
        self.code_model_combo = QComboBox()
        self.code_model_combo.addItem("DeepSeek (Master)", "deepseek")
        self.code_model_combo.addItem("Qwen (Efficient)", "qwen")
        self.code_model_combo.setFixedWidth(150)
        self.code_model_row.addWidget(self.code_model_combo)
        self.code_model_row.addStretch()
        
        # Container widget for the row (to easily show/hide)
        self.code_model_widget = QWidget()
        self.code_model_widget.setLayout(self.code_model_row)
        self.code_model_widget.hide()
        layout.addWidget(self.code_model_widget)
        
        # Writing mode persona/style selector (hidden by default)
        self.writing_selector_row = QHBoxLayout()
        self.writing_selector_row.setSpacing(8)
        
        # Persona dropdown
        self.writing_persona_label = QLabel("Persona:")
        self.writing_selector_row.addWidget(self.writing_persona_label)
        
        self.writing_persona_combo = QComboBox()
        self.writing_persona_combo.addItem("📖 Reddit Stories", "reddit")
        self.writing_persona_combo.addItem("🧠 Therapist", "therapist")
        self.writing_persona_combo.addItem("📚 Teacher", "teacher")
        self.writing_persona_combo.addItem("✍️ Poet", "poet")
        self.writing_persona_combo.setCurrentIndex(1)  # Therapist default
        self.writing_persona_combo.currentIndexChanged.connect(self._on_writing_persona_changed)
        self.writing_persona_combo.setFixedWidth(140)
        self.writing_selector_row.addWidget(self.writing_persona_combo)
        
        # Style dropdown
        self.writing_style_label = QLabel("Style:")
        self.writing_selector_row.addWidget(self.writing_style_label)
        
        self.writing_style_combo = QComboBox()
        self._update_writing_styles()  # Populate based on current persona
        self.writing_style_combo.currentIndexChanged.connect(self._on_writing_style_changed)
        self.writing_style_combo.setFixedWidth(130)
        self.writing_selector_row.addWidget(self.writing_style_combo)
        
        self.writing_selector_row.addStretch()
        
        # Container widget
        self.writing_selector_widget = QWidget()
        self.writing_selector_widget.setLayout(self.writing_selector_row)
        self.writing_selector_widget.hide()
        layout.addWidget(self.writing_selector_widget)
        
        # NSFW Writing mode persona/style selector (hidden by default)
        self.nsfw_selector_row = QHBoxLayout()
        self.nsfw_selector_row.setSpacing(8)
        
        # Persona dropdown
        self.nsfw_persona_label = QLabel("Persona:")
        self.nsfw_selector_row.addWidget(self.nsfw_persona_label)
        
        self.nsfw_persona_combo = QComboBox()
        self.nsfw_persona_combo.addItem("🔥 Erotica Writer", "erotica")
        self.nsfw_persona_combo.addItem("🎭 Roleplay Partner", "roleplay")
        self.nsfw_persona_combo.setCurrentIndex(0)
        self.nsfw_persona_combo.currentIndexChanged.connect(self._on_nsfw_persona_changed)
        self.nsfw_persona_combo.setFixedWidth(150)
        self.nsfw_selector_row.addWidget(self.nsfw_persona_combo)
        
        # Style dropdown
        self.nsfw_style_label = QLabel("Style:")
        self.nsfw_selector_row.addWidget(self.nsfw_style_label)
        
        self.nsfw_style_combo = QComboBox()
        self._update_nsfw_styles()
        self.nsfw_style_combo.currentIndexChanged.connect(self._on_nsfw_style_changed)
        self.nsfw_style_combo.setFixedWidth(130)
        self.nsfw_selector_row.addWidget(self.nsfw_style_combo)
        
        self.nsfw_selector_row.addStretch()
        
        # Container widget
        self.nsfw_selector_widget = QWidget()
        self.nsfw_selector_widget.setLayout(self.nsfw_selector_row)
        self.nsfw_selector_widget.hide()
        layout.addWidget(self.nsfw_selector_widget)
        
        # Input area
        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)
        
        theme = ThemeManager.get_theme()
        is_dark = theme.name == "dark"
        
        # Mic button with spinner (hidden by default, shown when VoiceManager loaded)
        self.mic_btn = SpinnerButton("🎤")
        self.mic_btn.setFixedSize(44, 44)
        self.mic_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.mic_btn.setToolTip("Voice input")
        self.mic_btn.clicked.connect(self._toggle_voice_input)
        self.mic_btn.hide()  # Hidden until model loaded via Settings
        input_layout.addWidget(self.mic_btn)
        
        self.input = QLineEdit()
        self.input.setPlaceholderText("Type a message...")
        self.input.returnPressed.connect(self._send_message)
        input_layout.addWidget(self.input)
        
        self.send_btn = QPushButton("➤")
        self.send_btn.setFixedSize(44, 44)
        self.send_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.send_btn.clicked.connect(self._send_message)
        input_layout.addWidget(self.send_btn)
        
        layout.addLayout(input_layout)
        
        # Recording overlay (shown during voice input)
        self.recording_widget = QWidget()
        self.recording_widget.setFixedHeight(50)
        recording_layout = QHBoxLayout(self.recording_widget)
        recording_layout.setContentsMargins(10, 5, 10, 5)
        recording_layout.setSpacing(10)
        
        self.recording_icon = QLabel("🎤")
        self.recording_icon.setStyleSheet("font-size: 18px;")
        recording_layout.addWidget(self.recording_icon)
        
        self.recording_label = QLabel("Recording...")
        self.recording_label.setStyleSheet(f"color: {'#ff6666' if is_dark else '#cc4444'}; font-size: 13px; font-family: Consolas;")
        recording_layout.addWidget(self.recording_label)
        
        recording_layout.addStretch()
        
        self.recording_timer_label = QLabel("0:00")
        self.recording_timer_label.setStyleSheet(f"color: {'#aaa' if is_dark else '#666'}; font-size: 12px; font-family: Consolas;")
        recording_layout.addWidget(self.recording_timer_label)
        
        self.stop_recording_btn = QPushButton("⏹")
        self.stop_recording_btn.setFixedSize(32, 32)
        self.stop_recording_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.stop_recording_btn.setToolTip("Stop & transcribe")
        self.stop_recording_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff4444;
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #ff6666; }
        """)
        self.stop_recording_btn.clicked.connect(self._stop_voice_input)
        recording_layout.addWidget(self.stop_recording_btn)
        
        # Pause button
        self.pause_recording_btn = QPushButton("⏸")
        self.pause_recording_btn.setFixedSize(32, 32)
        self.pause_recording_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.pause_recording_btn.setToolTip("Pause recording")
        self.pause_recording_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffa500;
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #ffb733; }
        """)
        self.pause_recording_btn.clicked.connect(self._pause_voice_input)
        recording_layout.addWidget(self.pause_recording_btn)
        
        self.cancel_recording_btn = QPushButton("←")
        self.cancel_recording_btn.setFixedSize(32, 32)
        self.cancel_recording_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.cancel_recording_btn.setToolTip("Cancel")
        self.cancel_recording_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666;
                border: 1px solid #444;
                border-radius: 16px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #333; color: #aaa; border-color: #666; }
        """)
        self.cancel_recording_btn.clicked.connect(self._cancel_voice_input)
        recording_layout.addWidget(self.cancel_recording_btn)
        
        self.recording_widget.hide()
        layout.addWidget(self.recording_widget)
        
        # Transcription preview (shown after voice transcription with Send/Delete options)
        self.transcription_preview = QWidget()
        self.transcription_preview.setFixedHeight(50)
        preview_layout = QHBoxLayout(self.transcription_preview)
        preview_layout.setContentsMargins(10, 5, 10, 5)
        preview_layout.setSpacing(8)
        
        self.preview_text = QLabel("")
        self.preview_text.setStyleSheet(f"color: {'#ddd' if is_dark else '#444'}; font-size: 12px; font-family: Consolas;")
        self.preview_text.setWordWrap(False)
        preview_layout.addWidget(self.preview_text, stretch=1)
        
        # Send button (green checkmark)
        self.preview_send_btn = QPushButton("➤")
        self.preview_send_btn.setFixedSize(36, 36)
        self.preview_send_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.preview_send_btn.setToolTip("Send message")
        self.preview_send_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #28a745, stop:1 #20c997);
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 16px;
            }
            QPushButton:hover { background: #34ce57; }
        """)
        self.preview_send_btn.clicked.connect(self._send_transcription)
        preview_layout.addWidget(self.preview_send_btn)
        
        # Delete button (red trash)
        self.preview_delete_btn = QPushButton("🗑️")
        self.preview_delete_btn.setFixedSize(36, 36)
        self.preview_delete_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.preview_delete_btn.setToolTip("Discard")
        self.preview_delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #e4606d; }
        """)
        self.preview_delete_btn.clicked.connect(self._discard_transcription)
        preview_layout.addWidget(self.preview_delete_btn)
        
        self.transcription_preview.hide()
        layout.addWidget(self.transcription_preview)
        
        # Store transcription text for send
        self._pending_transcription = ""
        
        # Recording timer
        self._recording_timer = QTimer()
        self._recording_timer.timeout.connect(self._update_recording_time)
        
        # Add initial messages
        self._add_bubble("AI CORE", "Welcome to Neural Citadel.\nHow can I assist you?", False)
        self._add_bubble("User", "Initialize systems.", True)
        self._add_bubble("AI CORE", "All systems operational.\nReady for commands.", False)
        
        # Initial styling call
        self.update_theme()

    def update_theme(self):
        """Update widget styling based on current theme."""
        theme = ThemeManager.get_theme()
        is_dark = theme.name == "dark"
        
        # Determine accent color for code mode (Green for Dark, Red for Light)
        # Note: We import colors locally or rely on hex codes to avoid circular imports if needed
        green_accent = "#7CFC00"
        red_accent = "#DC143C"  # Crimson red for visibility on white
        accent = green_accent if is_dark else red_accent
        
        # Update Code Model Selector Styling
        self.code_model_label.setStyleSheet(f"color: {accent}; font-family: Consolas; font-size: 11px;")
        
        bg_rgba = "rgba(124, 252, 0, 0.1)" if is_dark else "rgba(220, 20, 60, 0.1)"
        border_color = "#3a7a3a" if is_dark else "#a03030"
        
        self.code_model_combo.setStyleSheet(f"""
            QComboBox {{
                background: {bg_rgba};
                color: {accent};
                border: 1px solid {border_color};
                border-radius: 10px;
                padding: 4px 8px;
                font-family: Consolas;
                font-size: 10px;
            }}
            QComboBox::drop-down {{ border: none; width: 16px; }}
            QComboBox QAbstractItemView {{
                background: {"#1a1a1a" if is_dark else "#f0f0f0"};
                color: {accent};
                selection-background-color: {"#2a5a2a" if is_dark else "#e0e0e0"};
            }}
        """)

        if is_dark:
            self.input.setStyleSheet("""
                QLineEdit {
                    background-color: #0a0a0a;
                    color: #ffffff;
                    border: 1px solid #2a2a2a;
                    border-radius: 20px;
                    padding: 12px 18px;
                    font-family: Consolas;
                    font-size: 12px;
                }
                QLineEdit:focus {
                    border-color: #E1306C;
                }
            """)
            self.scroll.setStyleSheet("""
                QScrollArea { background-color: transparent; border: none; }
                QScrollBar:vertical { background-color: #000000; width: 6px; border-radius: 3px; }
                QScrollBar::handle:vertical { background-color: #333333; border-radius: 3px; }
            """)
        else:
            self.input.setStyleSheet("""
                QLineEdit {
                    background-color: #FFFFFF;
                    color: #000000;
                    border: 1px solid rgba(200, 180, 220, 0.5);
                    border-radius: 20px;
                    padding: 12px 18px;
                    font-family: 'Segoe UI', Consolas;
                    font-size: 12px;
                    font-weight: 500;
                }
                QLineEdit:focus {
                    border: 1px solid #9B6EB7;
                }
                QLineEdit::placeholder {
                    color: #888;
                }
            """)
            self.scroll.setStyleSheet("""
                QScrollArea { background-color: transparent; border: none; }
                QScrollBar:vertical { background-color: rgba(240, 240, 245, 0.5); width: 6px; border-radius: 3px; }
                QScrollBar::handle:vertical { background-color: rgba(180, 160, 200, 0.5); border-radius: 3px; }
            """)
        
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {PURPLE}, stop:0.5 {PINK}, stop:1 {ORANGE});
                color: white;
                border: none;
                border-radius: 22px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #9b4fc9, stop:0.5 #f04080, stop:1 #ff9050);
            }}
        """)
        
        # Propagate to panels
        if hasattr(self, 'image_gen_panel'):
            self.image_gen_panel.update_theme()
        if hasattr(self, 'movie_panel'):
            self.movie_panel.update_theme()
        if hasattr(self, 'qr_panel'):
            self.qr_panel.update_theme()
    

    def _on_model_changed(self, icon: str, name: str):
        # Check if switching away from Reasoning mode - always show warning
        if self.current_model == "Reasoning" and name != "Reasoning":
            # Show warning if there's history or reasoning is active
            if self.reasoning_manager.has_history() or self.reasoning_manager.is_active:
                if not self._show_reasoning_warning():
                    return  # User cancelled
            # Terminate reasoning subprocess
            self.reasoning_manager.terminate()
            self.reasoning_manager.clear_history()
        
        # Check if switching away from Code mode
        if self.current_model == "Code" and name != "Code":
            if self.code_manager.is_active:
                if not self._show_code_warning():
                    return  # User cancelled
            self.code_manager.terminate()
        
        # Check if switching away from Hacking mode - cleanup VRAM
        if self.current_model == "Hacking" and name != "Hacking":
            if self.hacking_manager.is_active:
                # No warning needed, just terminate
                pass
            self.hacking_manager.terminate()
        
        # Check if switching away from Writing mode - cleanup VRAM and clear history
        if self.current_model == "Writing" and name != "Writing":
            self.writing_manager.terminate()
            self.writing_manager.clear_history()
        
        self.current_model = name
        self.mode_label.setText(f"Mode: {name}")
        self.mode_label.setStyleSheet(f"color: {PINK}; font-size: 10px; font-family: Consolas;")
        
        # Emit signal for main window
        self.mode_changed.emit(name)
        
        # Hide all panels first
        self.image_gen_panel.hide()
        self.movie_panel.hide()
        self.qr_panel.hide()
        self.newspaper_panel.hide()
        self.code_model_widget.hide()  # Hide code model selector by default
        self.writing_selector_widget.hide()  # Hide writing selector by default
        self.nsfw_selector_widget.hide()  # Hide NSFW selector by default
        
        # Show/hide panels based on mode
        if name == "Image Generation":
            self.image_gen_panel.show()
            self.input.setPlaceholderText("Describe the image you want to generate...")
        elif name == "Movie Downloader":
            self.movie_panel.show()
            self.input.setPlaceholderText("Use the panel above to download...")
        elif name == "QR Studio":
            self.qr_panel.show()
            self.input.setPlaceholderText("Use the panel above to generate QR codes...")
        elif name == "Newspaper":
            self.newspaper_panel.show()
            self.input.setPlaceholderText("Generate a newspaper from live RSS feeds...")
        elif name == "Reasoning":
            self.input.setPlaceholderText("Ask a math or logic question...")
        elif name == "Code":
            self.code_model_widget.show()  # Show model selector
            self.input.setPlaceholderText("Describe the code you want...")
        elif name == "Hacking":
            self.input.setPlaceholderText("Enter exploit command...")
        elif name == "Writing":
            self.writing_selector_widget.show()  # Show persona/style selector
            self.input.setPlaceholderText("What would you like me to write?")
        elif name == "NSFW Stories":
            self.nsfw_selector_widget.show()  # Show NSFW persona/style selector
            self.input.setPlaceholderText("What would you like me to write?")
        else:
            self.input.setPlaceholderText("Type a message...")
    
    def _show_reasoning_warning(self) -> bool:
        """Show warning dialog when switching away from Reasoning mode."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
        
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        dialog.setFixedSize(340, 160)
        
        # Main container
        from PyQt6.QtWidgets import QFrame
        container = QFrame(dialog)
        container.setGeometry(0, 0, 340, 160)
        container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a3e, stop:0.5 #2d1b4e, stop:1 #1e3a5f);
                border: 2px solid #F77737;
                border-radius: 20px;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(25, 25, 25, 20)
        layout.setSpacing(15)
        
        # Warning message
        msg = QLabel("Clear reasoning history?\n\nSwitching modes will stop the model and clear memory.")
        msg.setWordWrap(True)
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setStyleSheet("color: #ffffff; font-family: Consolas; font-size: 13px; border: none;")
        layout.addWidget(msg)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        stay_btn = QPushButton("Stay")
        stay_btn.setFixedSize(100, 36)
        stay_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        stay_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #833AB4, stop:1 #E1306C);
                color: white; border: none; border-radius: 18px;
                font-family: Consolas; font-weight: bold;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #9945C4, stop:1 #F1407C); }
        """)
        stay_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(stay_btn)
        
        switch_btn = QPushButton("Switch Anyway")
        switch_btn.setFixedSize(120, 36)
        switch_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        switch_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.1);
                color: #888; border: 1px solid #555; border-radius: 18px;
                font-family: Consolas;
            }
            QPushButton:hover { background: rgba(255,255,255,0.2); color: #aaa; }
        """)
        switch_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(switch_btn)
        
        layout.addLayout(btn_layout)
        
        # Center dialog on screen
        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().geometry()
        dialog.move(
            (screen.width() - dialog.width()) // 2,
            (screen.height() - dialog.height()) // 2
        )
        
        # Shake animation
        shake = QPropertyAnimation(dialog, b"pos")
        shake.setDuration(50)
        shake.setLoopCount(4)
        pos = dialog.pos()
        shake.setKeyValueAt(0, pos)
        shake.setKeyValueAt(0.25, QPoint(pos.x() - 5, pos.y()))
        shake.setKeyValueAt(0.75, QPoint(pos.x() + 5, pos.y()))
        shake.setKeyValueAt(1, pos)
        shake.start()
        
        return dialog.exec() == QDialog.DialogCode.Accepted
    
    def _add_bubble(self, sender: str, message: str, is_user: bool):
        bubble = ChatBubble(sender, message, is_user)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)
    
    def _send_message(self):
        message = self.input.text().strip()
        if not message:
            return
        
        self._add_bubble("User", message, True)
        self.input.clear()
        
        # Handle Image Generation mode differently
        if self.current_model == "Image Generation":
            self.image_gen_panel.request_generation(message)
            return
        
        # Handle Reasoning mode
        if self.current_model == "Reasoning":
            self._start_reasoning(message)
            return
        
        # Handle Code mode
        if self.current_model == "Code":
            self._start_coding(message)
            return
            
        # Handle Hacking mode
        if self.current_model == "Hacking":
            self._start_hacking(message)
            return
        
        # Handle Writing mode
        if self.current_model == "Writing":
            self._start_writing(message)
            return
        
        # Handle NSFW Stories mode
        if self.current_model == "NSFW Stories":
            self._start_nsfw_writing(message)
            return
        
        # Regular chat processing
        self.input.setEnabled(False)
        self.send_btn.setEnabled(False)
        
        self.worker = ChatWorker(message, self.current_model)
        self.worker.finished.connect(self._on_response)
        self.worker.start()
    
    def _start_reasoning(self, prompt: str):
        """Start reasoning with DeepSeek R1."""
        # Add generating status to chat
        self._add_bubble("AI CORE", "🧠 Generating...", False)
        
        # Start worker
        worker = self.reasoning_manager.start_reasoning(prompt)
        
        # Connect worker signals to ChatWidget signals (for main_window)
        worker.loaded.connect(lambda: print("[Reasoning] Model loaded"))
        worker.think_start.connect(self.reasoning_think_start.emit)
        worker.token.connect(self.reasoning_token.emit)
        worker.think_end.connect(self.reasoning_think_end.emit)
        worker.finished.connect(lambda resp: self._on_reasoning_finished(prompt, resp))
        worker.error.connect(self._on_reasoning_error)
        
        # Emit started signal to main window
        self.reasoning_started.emit()
        
        self.input.setEnabled(False)
        self.send_btn.setEnabled(False)
        
        worker.start()
    
    def _on_reasoning_finished(self, prompt: str, response: str):
        """Handle reasoning completion."""
        self.reasoning_manager.add_to_history(prompt, response)
        self.reasoning_finished.emit(response)
        
        self.input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.input.setFocus()
    
    def _on_reasoning_error(self, error: str):
        """Handle reasoning error."""
        self.reasoning_error.emit(error)
        self._add_bubble("AI CORE", f"Reasoning error: {error}", False)
        
        self.input.setEnabled(True)
        self.send_btn.setEnabled(True)
    
    def _start_coding(self, prompt: str):
        """Start code generation."""
        # Get selected model from dropdown
        model = self.code_model_combo.currentData()
        if not model:
            model = "deepseek"  # Fallback
        
        # Add generating status to chat (green themed)
        model_name = "DeepSeek" if model == "deepseek" else "Qwen"
        self._add_bubble("AI CORE", f"Generating code with {model_name}...", False)
        
        # Start worker
        worker = self.code_manager.start_coding(prompt, model)
        
        # Connect worker signals
        worker.loaded.connect(lambda: print("[Code] Model loaded"))
        worker.token.connect(self.code_token.emit)
        worker.finished.connect(self._on_code_finished)
        worker.error.connect(self._on_code_error)
        
        # Emit started signal
        self.code_started.emit()
        
        self.input.setEnabled(False)
        self.send_btn.setEnabled(False)
        
        worker.start()

    def _start_hacking(self, prompt: str):
        """Start hacking mode generation."""
        # Add generating status to chat
        self._add_bubble("AI CORE", "💀 INITIATING EXPLOIT...", False)
        
        # Start worker
        worker = self.hacking_manager.start_hacking(prompt)
        
        # Connect worker signals
        worker.loaded.connect(lambda: print("[Hacking] Model loaded"))
        worker.token.connect(self.hacking_token.emit)
        worker.finished.connect(self._on_hacking_finished)
        worker.error.connect(self._on_hacking_error)
        
        # Emit started signal
        self.hacking_started.emit()
        
        self.input.setEnabled(False)
        self.send_btn.setEnabled(False)
        
        # ACTUALLY START THE WORKER!
        worker.start()

    def _on_hacking_finished(self, response: str):
        """Handle hacking completion."""
        self.hacking_finished.emit(response)
        self.input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.input.setFocus()
        
        # Terminate manager immediately as no history needed
        # self.hacking_manager.terminate() 
        # Wait, keeping it active allows faster subsequent requests? 
        # Code mode keeps it active. Let's keep it active.

    def _on_hacking_error(self, error: str):
        """Handle hacking error."""
        self.hacking_error.emit(error)
        self._add_bubble("AI CORE", f"BREACH FAILED: {error}", False)
        self.input.setEnabled(True)
        self.send_btn.setEnabled(True)

    def _start_writing(self, prompt: str):
        """Start writing mode generation."""
        # Add generating status to chat
        self._add_bubble("AI CORE", "✍️ COMPOSING...", False)
        
        # Emit started signal with prompt FIRST so panel shows immediately
        self.writing_started.emit(prompt)
        
        self.input.setEnabled(False)
        self.send_btn.setEnabled(False)
        
        # Start worker (may be None if engine starting async)
        worker = self.writing_manager.start_writing(prompt)
        
        if worker is None:
            # Engine is starting async - connect to ready signal
            self.writing_manager.engine_ready.connect(self._on_writing_engine_ready)
            self.writing_manager.engine_error.connect(self._on_writing_error)
            return
        
        # Engine was already ready, start worker immediately
        self._connect_and_start_worker(worker)
    
    def _on_writing_engine_ready(self):
        """Called when engine finishes async startup."""
        # Disconnect signal
        try:
            self.writing_manager.engine_ready.disconnect(self._on_writing_engine_ready)
        except:
            pass
        
        # Get the worker that was created after engine ready
        worker = self.writing_manager.get_current_worker()
        if worker:
            self._connect_and_start_worker(worker)
    
    def _connect_and_start_worker(self, worker):
        """Connect signals and start the worker."""
        worker.token.connect(self.writing_token.emit)
        worker.finished.connect(self._on_writing_finished)
        worker.error.connect(self._on_writing_error)
        worker.start()
    
    def _on_writing_finished(self, response: str):
        """Handle writing completion."""
        self.writing_manager.add_response(response)
        self.writing_history_count.emit(self.writing_manager.get_history_count())
        self.writing_finished.emit(response)
        self.input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.input.setFocus()
    
    def _on_writing_error(self, error: str):
        """Handle writing error."""
        self.writing_error.emit(error)
        self._add_bubble("AI CORE", f"WRITING FAILED: {error}", False)
        self.input.setEnabled(True)
        self.send_btn.setEnabled(True)
    
    def _start_nsfw_writing(self, prompt: str):
        """Start NSFW writing mode generation."""
        # Add generating status to chat
        self._add_bubble("AI CORE", "🔥 GENERATING...", False)
        
        # Get current selection
        persona = self.nsfw_persona_combo.currentData() or "erotica"
        style = self.nsfw_style_combo.currentData() or "romance"
        
        # Emit started signal with prompt AND selection so panel updates
        self.nsfw_writing_started.emit(prompt, persona, style)
        
        # Don't disable input/send button - allow user to interrupt/queue
        # self.input.setEnabled(False)
        # self.send_btn.setEnabled(False)
        
        # Start worker (may be None if engine starting async)
        worker = self.nsfw_writing_manager.start_writing(prompt)
        
        if worker is None:
            # Engine is starting async - connect to ready signal
            self.nsfw_writing_manager.engine_ready.connect(self._on_nsfw_writing_engine_ready)
            self.nsfw_writing_manager.engine_error.connect(self._on_nsfw_writing_error)
            return
        
        # Engine was already ready, start worker immediately
        self._connect_and_start_nsfw_worker(worker)
    
    def _on_nsfw_writing_engine_ready(self):
        """Called when NSFW engine finishes async startup."""
        try:
            self.nsfw_writing_manager.engine_ready.disconnect(self._on_nsfw_writing_engine_ready)
        except:
            pass
        
        worker = self.nsfw_writing_manager.get_current_worker()
        if worker:
            self._connect_and_start_nsfw_worker(worker)
    
    def _connect_and_start_nsfw_worker(self, worker):
        """Connect signals and start the NSFW worker."""
        worker.token.connect(self.nsfw_writing_token.emit)
        worker.finished.connect(self._on_nsfw_writing_finished)
        worker.error.connect(self._on_nsfw_writing_error)
        worker.start()
    
    def _on_nsfw_writing_finished(self, response: str):
        """Handle NSFW writing completion."""
        self.nsfw_writing_manager.add_response(response)
        self.nsfw_writing_finished.emit(response)
        self.input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.input.setFocus()
    
    def _on_nsfw_writing_error(self, error: str):
        """Handle NSFW writing error."""
        self.nsfw_writing_error.emit(error)
        self._add_bubble("AI CORE", f"NSFW GENERATION FAILED: {error}", False)
        self.input.setEnabled(True)
        self.send_btn.setEnabled(True)

    # Writing style definitions
    WRITING_STYLES = {
        "reddit": [("🎭 Dramatic", "dramatic"), ("💕 Wholesome", "wholesome"), ("👻 Horror", "horror"), ("⚔️ Revenge", "revenge")],
        "therapist": [("💝 Supportive", "supportive"), ("🧩 CBT", "cbt"), ("💪 Motivational", "motivational"), ("🧘 Mindfulness", "mindfulness")],
        "teacher": [("👶 ELI5", "eli5"), ("🎓 Academic", "academic"), ("🤔 Socratic", "socratic"), ("🔧 Practical", "practical")],
        "poet": [("💘 Romantic", "romantic"), ("🌑 Gothic", "gothic"), ("🍃 Haiku", "haiku"), ("⚔️ Epic", "epic")]
    }
    
    def _update_writing_styles(self):
        """Update style combo based on current persona."""
        persona = self.writing_persona_combo.currentData() or "therapist"
        styles = self.WRITING_STYLES.get(persona, self.WRITING_STYLES["therapist"])
        
        self.writing_style_combo.blockSignals(True)
        self.writing_style_combo.clear()
        for label, value in styles:
            self.writing_style_combo.addItem(label, value)
        self.writing_style_combo.blockSignals(False)
        
        # Update manager
        style = self.writing_style_combo.currentData() or styles[0][1]
        self.writing_manager.set_persona(persona, style)
    
    def _on_writing_persona_changed(self, index):
        """Handle persona dropdown change."""
        self._update_writing_styles()
    
    def _on_writing_style_changed(self, index):
        """Handle style dropdown change."""
        persona = self.writing_persona_combo.currentData() or "therapist"
        style = self.writing_style_combo.currentData()
        if style:
            self.writing_manager.set_persona(persona, style)

    # NSFW Writing style definitions
    NSFW_STYLES = {
        "erotica": [("💕 Romance", "romance"), ("🔥 Explicit", "explicit"), ("✨ Fantasy", "fantasy"), ("⛓️ Taboo", "taboo")],
        "roleplay": [("💘 Romantic", "romantic"), ("👑 Dominant", "dominant"), ("🦋 Submissive", "submissive"), ("🎬 Scenario", "scenario")]
    }
    
    def _update_nsfw_styles(self):
        """Update NSFW style combo based on current persona."""
        persona = self.nsfw_persona_combo.currentData() or "erotica"
        styles = self.NSFW_STYLES.get(persona, self.NSFW_STYLES["erotica"])
        
        self.nsfw_style_combo.blockSignals(True)
        self.nsfw_style_combo.clear()
        for label, value in styles:
            self.nsfw_style_combo.addItem(label, value)
        self.nsfw_style_combo.blockSignals(False)
        
        # Update manager
        style = self.nsfw_style_combo.currentData() or styles[0][1]
        self.nsfw_writing_manager.set_persona(persona, style)
    
    def _on_nsfw_persona_changed(self, index):
        """Handle NSFW persona dropdown change."""
        self._update_nsfw_styles()
    
    def _on_nsfw_style_changed(self, index):
        """Handle NSFW style dropdown change."""
        persona = self.nsfw_persona_combo.currentData() or "erotica"
        style = self.nsfw_style_combo.currentData()
        if style:
            self.nsfw_writing_manager.set_persona(persona, style)
    
    def _on_code_finished(self, response: str):
        """Handle code generation completion."""
        self.code_finished.emit(response)
        
        self.input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.input.setFocus()
    
    def _on_code_error(self, error: str):
        """Handle code generation error."""
        self.code_error.emit(error)
        self._add_bubble("AI CORE", f"Code error: {error}", False)
        
        self.input.setEnabled(True)
        self.send_btn.setEnabled(True)
    
    def _show_code_warning(self) -> bool:
        """Show warning when switching away from active Code mode."""
        from PyQt6.QtWidgets import QDialog, QFrame
        from PyQt6.QtCore import QPropertyAnimation, QPoint
        from PyQt6.QtGui import QGuiApplication
        
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        dialog.setFixedSize(340, 140)
        
        container = QFrame(dialog)
        container.setGeometry(0, 0, 340, 140)
        container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a3a1e, stop:0.5 #2d4e1b, stop:1 #1e5f3a);
                border: 2px solid #7CFC00;
                border-radius: 20px;
            }
            QLabel { border: none; background: transparent; }
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(15)
        
        msg = QLabel("Stop code generation?\n\nThis will unload the model.")
        msg.setWordWrap(True)
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setStyleSheet("color: #ffffff; font-family: Consolas; font-size: 13px; border: none;")
        layout.addWidget(msg)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        stay_btn = QPushButton("Stay")
        stay_btn.setFixedSize(100, 36)
        stay_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        stay_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2a5a2a, stop:1 #3a7a3a);
                color: #7CFC00;
                border: none;
                border-radius: 18px;
                font-family: Consolas;
                font-size: 12px;
            }
            QPushButton:hover { background: #4a9a4a; }
        """)
        stay_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(stay_btn)
        
        switch_btn = QPushButton("Switch Anyway")
        switch_btn.setFixedSize(120, 36)
        switch_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        switch_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.1);
                color: #888;
                border: 1px solid #555;
                border-radius: 18px;
                font-family: Consolas;
                font-size: 12px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.2); color: #aaa; }
        """)
        switch_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(switch_btn)
        
        layout.addLayout(btn_layout)
        
        # Center dialog on screen
        screen = QGuiApplication.primaryScreen().geometry()
        dialog.move(
            (screen.width() - dialog.width()) // 2,
            (screen.height() - dialog.height()) // 2
        )
        
        return dialog.exec() == QDialog.DialogCode.Accepted
    
    def _on_response(self, response: str):
        self._add_bubble("AI CORE", response, False)
        self.input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.input.setFocus()
    
    def _on_image_generate(self, prompt: str, pipeline: str, type_name: str, aspect: str, seed: int = None):
        """Handle image generation request from panel."""
        # Add animated generating widget
        model_name = f"{pipeline}" + (f" ({type_name})" if type_name else "")
        self.generating_widget = GeneratingWidget(model_name)
        self.generating_widget.set_status(f"Prompt: {prompt[:40]}...")
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, self.generating_widget)
        
        # Disable input during generation
        self.input.setEnabled(False)
        self.send_btn.setEnabled(False)
        self.mode_label.setText("🎨 Generating...")
        self.mode_label.setStyleSheet(f"color: {ORANGE}; font-size: 10px; font-family: Consolas;")
        
        # Start background worker
        self.image_worker = ImageWorker(prompt, pipeline, type_name if type_name else None, aspect, seed)
        self.image_worker.progress.connect(self._on_image_progress)
        self.image_worker.finished.connect(self._on_image_finished)
        self.image_worker.error.connect(self._on_image_error)
        self.image_worker.start()
    
    def _on_image_progress(self, message: str):
        """Update progress display."""
        if hasattr(self, 'generating_widget'):
            # Update the generating widget status
            if len(message) > 40:
                message = message[:40] + "..."
            self.generating_widget.set_status(message)
    
    def _on_image_finished(self, path: str):
        """Handle successful image generation."""
        # Remove generating widget
        if hasattr(self, 'generating_widget'):
            self.generating_widget.finish()
            self.generating_widget.deleteLater()
        
        self.input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.mode_label.setText("Mode: Image Generation")
        self.mode_label.setStyleSheet(f"color: {PINK}; font-size: 10px; font-family: Consolas;")
        self.input.setFocus()
        
        # Show image inline in chat with copy button
        if path and path != "Generation complete":
            import os
            # Clean up path (remove quotes, whitespace)
            clean_path = path.strip().strip('"').strip("'")
            
            try:
                # Add image result with copy button
                self._add_image_result(clean_path)
                
                # Also show popup with the full image
                if os.path.exists(clean_path):
                    self.image_popup = ImagePopup(clean_path, self.window())
                    # Center on screen
                    screen = self.screen().geometry()
                    x = (screen.width() - 820) // 2
                    y = (screen.height() - 620) // 2
                    self.image_popup.move(x, y)
                    self.image_popup.show()
                    self.image_popup.raise_()
                    self.image_popup.activateWindow()
            except Exception as e:
                print(f"[ERROR] Failed to create image bubble: {e}")
                self._add_bubble("🎨 IMAGE", f"✅ Image generated!\n📁 {clean_path}", False)
        else:
            # Path not found, just show text
            self._add_bubble("🎨 IMAGE", "✅ Image generated! (Path not captured)", False)
    
    def _on_image_error(self, error: str):
        """Handle image generation error."""
        # Remove generating widget
        if hasattr(self, 'generating_widget'):
            self.generating_widget.finish()
            self.generating_widget.deleteLater()
        
        self._add_bubble("🎨 IMAGE", f"❌ Error: {error}", False)
        self.input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.mode_label.setText("Mode: Image Generation")
        self.mode_label.setStyleSheet("color: #aa5555; font-size: 10px; font-family: Consolas;")
        self.input.setFocus()
    
    # =========================================================================
    # MOVIE DOWNLOADER HANDLERS
    # =========================================================================
    
    def _on_youtube_download(self, url: str, quality: str, download_playlist: bool = False):
        """Handle YouTube download request with progress widget."""
        playlist_msg = " (Playlist)" if download_playlist else ""
        self._add_bubble("User", f"📺 Download{playlist_msg}: {url}\nQuality: {quality}", True)
        
        self.movie_panel.set_enabled(False)
        self.mode_label.setText("📺 Downloading...")
        self.mode_label.setStyleSheet(f"color: {ORANGE}; font-size: 10px; font-family: Consolas;")
        
        # Create progress widget
        title = "Downloading Playlist..." if download_playlist else "Downloading Video..."
        self._download_progress = DownloadProgressWidget(title)
        self._download_progress.canceled.connect(self._cancel_download)
        self._add_widget_to_chat(self._download_progress)
        
        # Store URL for reference
        self._current_url = url
        
        # Start download
        self.movie_worker = MovieWorker("youtube", url=url, quality=quality, playlist=download_playlist)
        self.movie_worker.progress.connect(self._on_download_progress)
        self.movie_worker.finished.connect(self._on_youtube_finished)
        self.movie_worker.error.connect(self._on_download_error)
        self.movie_worker.start()
    
    def _on_youtube_finished(self, message: str):
        """Handle YouTube download completion with inline video player."""
        if hasattr(self, '_download_progress') and self._download_progress:
            self._download_progress.set_complete(True)
        
        self.movie_panel.set_enabled(True)
        self.mode_label.setText("Mode: Movie Downloader")
        self.mode_label.setStyleSheet(f"color: {PINK}; font-size: 10px; font-family: Consolas;")
        
        # Find downloaded file and show inline video player
        try:
            import sys
            import re
            sys.path.insert(0, str(__file__).split('infra')[0])
            from configs.paths import MOVIE_DOWNLOAD_DIR
            
            # Find the most recent MERGED video file
            # Exclude: .part, .f1., .f2., .f140., .m4a, .webm (intermediate files)
            files = sorted(MOVIE_DOWNLOAD_DIR.glob('*.mp4'), key=lambda f: f.stat().st_mtime, reverse=True)
            
            for f in files:
                # Skip intermediate format files (e.g., video.f1.mp4, video.f140.m4a)
                if re.search(r'\.f\d+\.', f.name):
                    continue
                # Skip partial downloads
                if f.name.endswith('.part'):
                    continue
                # Found valid merged video
                print(f"[InlinePlayer] Selected file: {f}")
                video_player = InlineVideoPlayer(str(f), self)
                self._add_widget_to_chat(video_player)
                break
        except Exception as e:
            print(f"Error showing video player: {e}")
    
    def _on_torrent_search(self, query: str, limit: int):
        """Handle torrent search request (non-interactive)."""
        self._add_bubble("User", f"🏴‍☠️ Search: {query} (limit: {limit})", True)
        self._add_bubble("🎬 MOVIE", "⏳ Searching torrents...", False)
        
        self.movie_panel.set_enabled(False)
        self.mode_label.setText("🎬 Searching...")
        self.mode_label.setStyleSheet(f"color: {ORANGE}; font-size: 10px; font-family: Consolas;")
        
        # Use non-interactive torrent-search command
        self.movie_worker = MovieWorker("torrent-search", query=query, limit=limit)
        self.movie_worker.progress.connect(self._on_movie_progress)
        self.movie_worker.search_results.connect(self._on_torrent_results)
        self.movie_worker.finished.connect(self._on_movie_finished)
        self.movie_worker.error.connect(self._on_movie_error)
        self.movie_worker.start()
    
    def _on_torrent_results(self, results: list):
        """Handle received torrent search results."""
        if results:
            self._add_bubble("🎬 MOVIE", f"✅ Found {len(results)} results\nSelect one to download:", False)
            self.movie_panel.display_torrent_results(results)
        else:
            self._add_bubble("🎬 MOVIE", "❌ No results found", False)
        self.movie_panel.set_enabled(True)
    
    def _on_torrent_download_magnet(self, magnet: str):
        """Handle download by magnet link with progress widget."""
        short_magnet = magnet[:60] + "..." if len(magnet) > 60 else magnet
        self._add_bubble("User", f"📥 Download: {short_magnet}", True)
        
        self.movie_panel.set_enabled(False)
        self.mode_label.setText("🎬 Downloading...")
        self.mode_label.setStyleSheet(f"color: {ORANGE}; font-size: 10px; font-family: Consolas;")
        
        # Create progress widget
        self._download_progress = DownloadProgressWidget("Downloading Movie...", show_phases=False)
        self._download_progress.canceled.connect(self._cancel_download)
        self._add_widget_to_chat(self._download_progress)
        
        # Store magnet for potential file lookup
        self._current_magnet = magnet
        
        # Use torrent-download command (auto-scans after download)
        self.movie_worker = MovieWorker("torrent-download", magnet=magnet)
        self.movie_worker.progress.connect(self._on_download_progress)
        self.movie_worker.finished.connect(self._on_download_finished)
        self.movie_worker.error.connect(self._on_download_error)
        self.movie_worker.scan_complete.connect(self._on_scan_result)
        self.movie_worker.start()
    
    def _on_download_progress(self, message: str):
        """Update download progress widget."""
        if hasattr(self, '_download_progress') and self._download_progress:
            self._download_progress.update_progress(message)
    
    def _on_download_finished(self, message: str):
        """Handle download completion with inline video player."""
        if hasattr(self, '_download_progress') and self._download_progress:
            self._download_progress.set_complete(True)
        
        self.movie_panel.set_enabled(True)
        self.mode_label.setText("Mode: Movie Downloader")
        self.mode_label.setStyleSheet(f"color: {PINK}; font-size: 10px; font-family: Consolas;")
        
        # Find downloaded file and show inline video player
        try:
            import sys
            sys.path.insert(0, str(__file__).split('infra')[0])
            from configs.paths import TORRENT_DOWNLOAD_DIR
            # Find the most recent video file
            video_exts = {'.mp4', '.mkv', '.avi', '.mov', '.webm'}
            files = sorted(TORRENT_DOWNLOAD_DIR.glob('*.*'), key=lambda f: f.stat().st_mtime, reverse=True)
            video_files = [f for f in files if f.suffix.lower() in video_exts and not f.name.endswith('.aria2')]
            if video_files:
                video_player = InlineVideoPlayer(str(video_files[0]), self)
                self._add_widget_to_chat(video_player)
        except Exception as e:
            print(f"Error showing video player: {e}")
    
    def _on_download_error(self, error: str):
        """Handle download error."""
        if hasattr(self, '_download_progress') and self._download_progress:
            self._download_progress.set_complete(False)
        
        self._add_bubble("🎬 MOVIE", f"❌ Error: {error}", False)
        self.movie_panel.set_enabled(True)
        self.mode_label.setText("Mode: Movie Downloader")
        self.mode_label.setStyleSheet("color: #aa5555; font-size: 10px; font-family: Consolas;")
    
    def _cancel_download(self):
        """Cancel current download."""
        if hasattr(self, 'movie_worker') and self.movie_worker:
            self.movie_worker.stop()
        self._add_bubble("🎬 MOVIE", "⏹️ Download canceled", False)
        self.movie_panel.set_enabled(True)
        self.mode_label.setText("Mode: Movie Downloader")
    
    def _add_widget_to_chat(self, widget):
        """Add a widget directly to the chat scroll area."""
        # Insert before the stretch
        count = self.messages_layout.count()
        self.messages_layout.insertWidget(count - 1, widget)
        # Scroll to bottom
        QTimer.singleShot(100, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        ))
    
    def _on_scan_result(self, scan_data: dict):
        """Handle scan result after download."""
        score = scan_data.get("total_risk_score", 0)
        level = scan_data.get("risk_level", "UNKNOWN")
        files = scan_data.get("files_scanned", 0)
        
        # Color-coded display
        if score < 20:
            color = "#33cc33"  # Green
            icon = "✅"
        elif score < 50:
            color = "#ffcc00"  # Yellow
            icon = "⚠️"
        else:
            color = "#ff3333"  # Red
            icon = "🚨"
        
        msg = f"{icon} Security Scan: {level}\nRisk Score: {score}/100\nFiles scanned: {files}"
        self._add_bubble("🛡️ SCAN", msg, False)
    
    def _on_scan_downloads(self):
        """Handle malware scan request."""
        self._add_bubble("User", "🛡️ Scan downloads for malware", True)
        self._start_movie_operation("scan")
    
    def _on_subtitle_generate(self, file_path: str, lang: str, task: str, model: str):
        """Handle subtitle generation request."""
        import os
        self._add_bubble("User", f"📝 Generate subtitles\n📁 {os.path.basename(file_path)}\nLang: {lang} | Model: {model}", True)
        self._start_movie_operation("subtitle", file=file_path, lang=lang, task=task, model=model)
    
    def _on_newspaper_start(self, msg: str):
        """Handle newspaper generation start."""
        # Add animated generating widget
        self.newspaper_generating_widget = GeneratingWidget("", title="📰 Generating Newspaper...")
        self.newspaper_generating_widget.set_status(msg)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, self.newspaper_generating_widget)
        
        # Scroll to bottom
        QTimer.singleShot(100, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        ))
        
        self.mode_label.setText("📰 Generating...")
        self.mode_label.setStyleSheet(f"color: {ORANGE}; font-size: 10px; font-family: Consolas;")

    def _on_newspaper_progress(self, msg: str):
        """Update pulsing widget with live CLI output."""
        if hasattr(self, 'newspaper_generating_widget'):
            # Truncate if too long to keep UI clean
            if len(msg) > 60:
                msg = msg[:57] + "..."
            self.newspaper_generating_widget.set_status(msg)

    def _on_newspaper_complete(self, path: str):
        """Handle newspaper generation complete."""
        # Remove generating widget
        if hasattr(self, 'newspaper_generating_widget'):
            self.newspaper_generating_widget.finish()
            self.newspaper_generating_widget.deleteLater()
            del self.newspaper_generating_widget
        
        self.mode_label.setText("Mode: Newspaper")
        self.mode_label.setStyleSheet(f"color: {PINK}; font-size: 10px; font-family: Consolas;")
        
        # Show result widget
        result_widget = NewspaperResultWidget(path)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, result_widget)
        
        # Scroll to bottom
        QTimer.singleShot(100, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        ))
    
    def _start_movie_operation(self, command: str, **kwargs):
        """Start a movie operation in background."""
        self.movie_panel.set_enabled(False)
        self.mode_label.setText(f"🎬 Running {command}...")
        self.mode_label.setStyleSheet(f"color: {ORANGE}; font-size: 10px; font-family: Consolas;")
        
        # Create progress bubble
        self._add_bubble("🎬 MOVIE", f"⏳ Starting {command}...", False)
        
        self.movie_worker = MovieWorker(command, **kwargs)
        self.movie_worker.progress.connect(self._on_movie_progress)
        self.movie_worker.finished.connect(self._on_movie_finished)
        self.movie_worker.error.connect(self._on_movie_error)
        self.movie_worker.start()
    
    def _on_movie_progress(self, message: str):
        """Handle movie operation progress."""
        # Update mode label with latest status
        if len(message) > 50:
            message = message[:47] + "..."
        self.mode_label.setText(f"🎬 {message}")
    
    def _on_movie_finished(self, message: str):
        """Handle movie operation completion."""
        self._add_bubble("🎬 MOVIE", message, False)
        self.movie_panel.set_enabled(True)
        self.mode_label.setText("Mode: Movie Downloader")
        self.mode_label.setStyleSheet(f"color: {PINK}; font-size: 10px; font-family: Consolas;")
    
    def _on_movie_error(self, error: str):
        """Handle movie operation error."""
        self._add_bubble("🎬 MOVIE", f"❌ Error: {error}", False)
        self.movie_panel.set_enabled(True)
        self.mode_label.setText("Mode: Movie Downloader")
        self.mode_label.setStyleSheet("color: #aa5555; font-size: 10px; font-family: Consolas;")
    
    def _toggle_listening(self):
        """Toggle voice input mode"""
        if self.is_listening:
            self._stop_listening()
        else:
            self._start_listening()
    
    def _start_listening(self):
        """Start listening for voice input"""
        self.is_listening = True
        self.model_selector.setText("🔴 Listening...")
        self.mode_label.setText("🎤 Speak now...")
        self.mode_label.setStyleSheet(f"color: {PINK}; font-size: 10px; font-family: Consolas;")
        
        # Start voice recognition in background
        class VoiceWorker(QThread):
            finished = pyqtSignal(str)
            error = pyqtSignal(str)
            
            def run(self):
                try:
                    import speech_recognition as sr
                    recognizer = sr.Recognizer()
                    with sr.Microphone() as source:
                        recognizer.adjust_for_ambient_noise(source, duration=0.3)
                        audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    
                    text = recognizer.recognize_google(audio)
                    self.finished.emit(text)
                except Exception as e:
                    self.error.emit(str(e))
        
        self.voice_worker = VoiceWorker()
        self.voice_worker.finished.connect(self._on_voice_result)
        self.voice_worker.error.connect(self._on_voice_error)
        self.voice_worker.start()
    
    def _stop_listening(self):
        """Stop listening state"""
        self.is_listening = False
        self.model_selector._update_display()  # Restore button text
        self.mode_label.setText(f"Mode: {self.current_model}")
        self.mode_label.setStyleSheet(f"color: {PINK}; font-size: 10px; font-family: Consolas;")
    
    def _on_voice_result(self, text: str):
        """Handle successful voice recognition"""
        self._stop_listening()
        self.input.setText(text)
        self.input.setFocus()
    
    def _on_voice_error(self, error: str):
        """Handle voice recognition error"""
        self._stop_listening()
        self.mode_label.setText(f"Voice error")
        self.mode_label.setStyleSheet("color: #aa5555; font-size: 10px; font-family: Consolas;")
    
    # =========================================================================
    # QR STUDIO HANDLERS
    # =========================================================================
    
    def _on_qr_generate(self, handler: str, data: dict, mode: str, auto_mode: bool,
                        colors: list, mask: str, drawer: str, logo_path: str, prompt: str):
        """Handle QR generation request from panel."""
        import json
        from PyQt6.QtCore import QTimer
        import time
        
        # Format data for display
        data_preview = json.dumps(data)
        if len(data_preview) > 50:
            data_preview = data_preview[:47] + "..."
        
        # Mode display string
        if mode == "svg":
            mode_str = "SVG"
        elif mode == "creative":
            mode_str = f"✨ Creative AI"
            if prompt:
                mode_str += f" ({prompt[:20]}...)" if len(prompt) > 20 else f" ({prompt})"
        else:
            mode_str = "Gradient Auto" if auto_mode else "Gradient Manual"
        
        self._add_bubble("User", f"📱 Generate QR ({handler})\n{data_preview}\nMode: {mode_str}", True)
        
        # Disable panel during generation
        self.qr_panel.set_enabled(False)
        self.mode_label.setText("📱 Generating QR...")
        self.mode_label.setStyleSheet(f"color: {ORANGE}; font-size: 10px; font-family: Consolas;")
        
        # Create progress bubble
        # Create progress bubble or widget
        if mode == "creative":
            # Use animated widget for creative mode
            title = "✨ Creative AI QR"
            model_info = f"Prompt: {prompt[:30]}..." if len(prompt) > 30 else f"Prompt: {prompt}"
            self.qr_generating_widget = GeneratingWidget(model_info, title=title)
            self.qr_generating_widget.set_status("Initializing diffusion model... (this may take 2-5 minutes)")
            self.messages_layout.insertWidget(self.messages_layout.count() - 1, self.qr_generating_widget)
            
            # Scroll to bottom
            QTimer.singleShot(100, lambda: self.scroll.verticalScrollBar().setValue(
                self.scroll.verticalScrollBar().maximum()
            ))
            
            # Start timer for pulsing mode label
            self._qr_start_time = time.time()
            self._qr_timer_pulse = 0
            self._qr_timer = QTimer()
            self._qr_timer.timeout.connect(self._update_qr_timer)
            self._qr_timer.start(1000)  # Update every second
        else:
            self._add_bubble("📱 QR STUDIO", "⏳ Generating QR code...", False)
            self._qr_timer = None
        
        # Start worker
        self.qr_worker = QRWorker(
            handler=handler,
            data=data,
            mode=mode,
            auto_mode=auto_mode,
            colors=colors,
            mask=mask,
            drawer=drawer,
            logo_path=logo_path,
            prompt=prompt
        )
        self.qr_worker.progress.connect(self._on_qr_progress)
        self.qr_worker.finished.connect(self._on_qr_finished)
        self.qr_worker.error.connect(self._on_qr_error)
        self.qr_worker.start()
    
    # _update_qr_timer deleted
    
    def _update_qr_timer(self):
        """Update the pulsing timer display for diffusion."""
        import time
        elapsed = int(time.time() - self._qr_start_time)
        minutes = elapsed // 60
        seconds = elapsed % 60
        
        # Pulsing animation
        self._qr_timer_pulse = (self._qr_timer_pulse + 1) % 4
        pulse_chars = ["⠋", "⠙", "⠹", "⠸"]
        pulse = pulse_chars[self._qr_timer_pulse]
        
        self.mode_label.setText(f"✨ {pulse} AI Generating... {minutes}m {seconds:02d}s")
        self.mode_label.setStyleSheet(f"color: {PURPLE}; font-size: 10px; font-family: Consolas;")
    
    def _on_qr_progress(self, message: str):
        """Handle QR generation progress."""
        if len(message) > 50:
            message = message[:47] + "..."
        self.mode_label.setText(f"📱 {message}")
        
        # Update widget if it exists
        if hasattr(self, 'qr_generating_widget'):
            self.qr_generating_widget.set_status(message)
    
    def _on_qr_finished(self, path: str):
        """Handle successful QR generation."""
        # Stop timer if running
        if hasattr(self, '_qr_timer') and self._qr_timer:
            self._qr_timer.stop()
            self._qr_timer = None
            
        # Remove generating widget
        if hasattr(self, 'qr_generating_widget'):
            self.qr_generating_widget.finish()
            self.qr_generating_widget.deleteLater()
            del self.qr_generating_widget
        
        self.qr_panel.set_enabled(True)
        self.mode_label.setText("Mode: QR Studio")
        self.mode_label.setStyleSheet(f"color: {PINK}; font-size: 10px; font-family: Consolas;")
        
        # Check if it's an image (PNG) or SVG
        if path and (path.endswith('.png') or path.endswith('.svg')):
            import os
            clean_path = path.strip().strip('"').strip("'")
            
            if os.path.exists(clean_path) and clean_path.endswith('.png'):
                # Show PNG inline with copy button
                self._add_qr_result(clean_path, is_png=True)
            elif clean_path.endswith('.svg'):
                # SVG - show path with copy button
                self._add_qr_result(clean_path, is_png=False)
            else:
                # Unknown - show text with path
                self._add_bubble("📱 QR STUDIO", f"✅ QR Generated!\n📁 {clean_path}", False)
        else:
            self._add_bubble("📱 QR STUDIO", f"✅ QR Generated!\n{path}", False)
    
    def _add_qr_result(self, qr_path: str, is_png: bool = True):
        """Add QR result with inline image (PNG) and copyable path."""
        from PyQt6.QtWidgets import QApplication
        import os
        
        # Create a bubble with QR display and copy functionality
        bubble = QFrame()
        bubble.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a3e, stop:0.5 #2d1b4e, stop:1 #1e3a5f);
                border: 1px solid #3d3d6b;
                border-radius: 16px;
                margin-right: 30px;
            }
        """)
        
        layout = QVBoxLayout(bubble)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(8)
        
        # Header
        file_type = "PNG" if is_png else "SVG"
        header = QLabel(f"📱 QR STUDIO - {file_type} Generated ✅")
        header.setStyleSheet(f"color: {PINK}; font-size: 10px; font-family: Consolas; font-weight: bold;")
        layout.addWidget(header)
        
        # Show inline image for PNG
        if is_png and os.path.exists(qr_path):
            try:
                from PyQt6.QtGui import QPixmap
                img_label = QLabel()
                pixmap = QPixmap(qr_path)
                scaled = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                img_label.setPixmap(scaled)
                img_label.setStyleSheet("border: none; margin: 4px 0;")
                img_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                # Click to show popup
                img_label.mousePressEvent = lambda e: self._show_qr_popup(qr_path)
                layout.addWidget(img_label)
            except Exception:
                pass
        
        # Path display
        path_label = QLabel(f"📁 {os.path.basename(qr_path)}")
        path_label.setStyleSheet("color: #aaa; font-size: 9px; font-family: Consolas;")
        path_label.setWordWrap(True)
        path_label.setToolTip(qr_path)
        layout.addWidget(path_label)
        
        # Button row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        
        # Copy button
        copy_btn = QPushButton("📋 Copy Path")
        copy_btn.setFixedSize(100, 26)
        copy_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background: {PURPLE};
                color: white;
                border: none;
                border-radius: 13px;
                font-family: Consolas;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background: {PINK};
            }}
        """)
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(qr_path))
        btn_row.addWidget(copy_btn)
        
        btn_row.addStretch()
        layout.addLayout(btn_row)
        
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)
        self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())
    
    def _show_qr_popup(self, path: str):
        """Show QR image in popup."""
        popup = ImagePopup(path, self.window())
        screen = self.screen().geometry()
        x = (screen.width() - 420) // 2
        y = (screen.height() - 420) // 2
        popup.move(x, y)
        popup.show()
    
    def _on_qr_error(self, error: str):
        """Handle QR generation error."""
        # Stop timer if running
        if hasattr(self, '_qr_timer') and self._qr_timer:
            self._qr_timer.stop()
            self._qr_timer = None
            
        # Remove generating widget
        if hasattr(self, 'qr_generating_widget'):
            self.qr_generating_widget.finish()
            self.qr_generating_widget.deleteLater()
            del self.qr_generating_widget
        
        self.qr_panel.set_enabled(True)
        self.mode_label.setText("Mode: QR Studio")
        self.mode_label.setStyleSheet("color: #aa5555; font-size: 10px; font-family: Consolas;")
        
        self._add_bubble("📱 QR STUDIO", f"❌ Error: {error}", False)
    
    def _add_image_result(self, image_path: str):
        """Add image result with inline preview and copy path button."""
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QPixmap
        import os
        
        # Create a bubble
        bubble = QFrame()
        bubble.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a3e, stop:0.5 #2d1b4e, stop:1 #1e3a5f);
                border: 1px solid #3d3d6b;
                border-radius: 16px;
                margin-right: 30px;
            }
        """)
        
        layout = QVBoxLayout(bubble)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(8)
        
        # Header
        header = QLabel("🎨 IMAGE - Generated ✅")
        header.setStyleSheet(f"color: {PINK}; font-size: 11px; font-family: Consolas; font-weight: bold;")
        layout.addWidget(header)
        
        # Show inline image
        if os.path.exists(image_path):
            try:
                img_label = QLabel()
                pixmap = QPixmap(image_path)
                # Scale to fit while maintaining aspect ratio
                scaled = pixmap.scaled(280, 280, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                img_label.setPixmap(scaled)
                img_label.setStyleSheet("border: none; margin: 4px 0;")
                img_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                # Click to show popup
                img_label.mousePressEvent = lambda e: self._show_image_popup(image_path)
                layout.addWidget(img_label)
            except Exception:
                pass
        
        # Path display
        path_label = QLabel(f"📁 {os.path.basename(image_path)}")
        path_label.setStyleSheet("color: #aaa; font-size: 10px; font-family: Consolas;")
        path_label.setWordWrap(True)
        path_label.setToolTip(image_path)
        layout.addWidget(path_label)
        
        # Button row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        
        # Copy button
        copy_btn = QPushButton("📋 Copy Path")
        copy_btn.setFixedSize(100, 28)
        copy_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background: {PURPLE};
                color: white;
                border: none;
                border-radius: 14px;
                font-family: Consolas;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background: {PINK};
            }}
        """)
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(image_path))
        btn_row.addWidget(copy_btn)
        
        btn_row.addStretch()
        layout.addLayout(btn_row)
        
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)
        self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())
    
    def _show_image_popup(self, path: str):
        """Show image in popup."""
        popup = ImagePopup(path, self.window())
        screen = self.screen().geometry()
        x = (screen.width() - 820) // 2
        y = (screen.height() - 620) // 2
        popup.move(x, y)
        popup.show()
    
    # ============ VOICE INPUT METHODS ============
    
    def show_mic_button(self):
        """Show mic button when voice model is loaded."""
        self.mic_btn.show()
        self._apply_mic_button_style()
    
    def hide_mic_button(self):
        """Hide mic button when voice model is unloaded."""
        self.mic_btn.hide()
        self._stop_voice_recording_ui()
    
    def _apply_mic_button_style(self):
        """Apply Instagram gradient style to mic button."""
        self.mic_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {PURPLE}, stop:0.5 {PINK}, stop:1 {ORANGE});
                color: white;
                border: none;
                border-radius: 22px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #9b4fc9, stop:0.5 #f04080, stop:1 #ff9050);
            }}
        """)
    
    def _toggle_voice_input(self):
        """Toggle voice input on/off."""
        from infra.gui.widgets.voice_worker import get_voice_manager
        voice_manager = get_voice_manager()
        
        if voice_manager.is_listening:
            voice_manager.stop_listening()
        else:
            self._start_voice_recording_ui()
            voice_manager.start_listening()
            
            # Connect signals (one-time per recording)
            try:
                voice_manager.transcription.disconnect(self._on_voice_transcription)
            except:
                pass
            try:
                voice_manager.stopped.disconnect(self._stop_voice_recording_ui)
            except:
                pass
            try:
                voice_manager.error.disconnect(self._on_voice_error)
            except:
                pass
            try:
                voice_manager.processing.disconnect(self._show_processing_ui)
            except:
                pass
            
            voice_manager.transcription.connect(self._on_voice_transcription)
            voice_manager.stopped.connect(self._stop_voice_recording_ui)
            voice_manager.error.connect(self._on_voice_error)
            voice_manager.processing.connect(self._show_processing_ui)
    
    def _start_voice_recording_ui(self):
        """Show recording UI."""
        self.recording_widget.show()
        self.input.hide()
        self.send_btn.hide()
        self.mic_btn.hide()
        
        self._recording_seconds = 0
        self._processing_dots = 0
        self._is_processing = False
        self.recording_label.setText("Recording...")
        self.recording_timer_label.setText("0:00")
        self._recording_timer.start(1000)
    
    def _show_processing_ui(self):
        """Show processing animation during transcription - mic button stays in place."""
        self._is_processing = True
        self._recording_timer.stop()
        
        # Hide recording overlay
        self.recording_widget.hide()
        if hasattr(self, 'transcription_preview'):
            self.transcription_preview.hide()
        
        # Keep layout intact! Show input and send but disable them
        self.input.show()
        self.input.setEnabled(False)
        self.input.setPlaceholderText("Processing...")
        self.send_btn.show()
        self.send_btn.setEnabled(False)
        
        # Start spinner in the mic button (stays in its original position)
        self.mic_btn.start_spinner()
        self.mic_btn.show()
    
    def _animate_processing(self):
        """Placeholder - animation handled by SpinnerButton now."""
        pass
    
    def _stop_voice_recording_ui(self):
        """Hide recording UI, restore input."""
        self._recording_timer.stop()
        # Stop processing animation if running
        if hasattr(self, '_processing_timer'):
            self._processing_timer.stop()
        
        # Stop mic button spinner and restore emoji
        self.mic_btn.stop_spinner()
        self.mic_btn.setText("🎤")
        
        # Re-enable input field and send button
        self.input.setEnabled(True)
        self.input.setPlaceholderText("Type a message...")
        self.send_btn.setEnabled(True)
        
        # Reset UI elements
        self._is_paused = False
        self.recording_icon.setText("🎤")
        self.pause_recording_btn.setText("⏸")
        self.stop_recording_btn.show()
        self.pause_recording_btn.show()
        self.cancel_recording_btn.show()
        self.recording_widget.hide()
        self.input.show()
        self.send_btn.show()
        self.mic_btn.show()
    
    def _stop_voice_input(self):
        """Manual stop button pressed."""
        from infra.gui.widgets.voice_worker import get_voice_manager
        get_voice_manager().stop_listening()
    
    def _cancel_voice_input(self):
        """Cancel recording without processing - discard the audio."""
        from infra.gui.widgets.voice_worker import get_voice_manager
        voice_manager = get_voice_manager()
        voice_manager.cancel_listening()  # Cancel without processing
        self._stop_voice_recording_ui()
        # Also hide any preview
        if hasattr(self, 'transcription_preview'):
            self.transcription_preview.hide()
    
    def _pause_voice_input(self):
        """Pause/Resume recording."""
        if hasattr(self, '_is_paused') and self._is_paused:
            # Resume
            self._is_paused = False
            self.pause_recording_btn.setText("⏸")
            self.pause_recording_btn.setToolTip("Pause recording")
            self.recording_label.setText("Recording...")
            self._recording_timer.start(1000)
        else:
            # Pause
            self._is_paused = True
            self.pause_recording_btn.setText("▶")
            self.pause_recording_btn.setToolTip("Resume recording")
            self.recording_label.setText("Paused")
            self._recording_timer.stop()
    
    def _update_recording_time(self):
        """Update recording timer display."""
        self._recording_seconds += 1
        mins = self._recording_seconds // 60
        secs = self._recording_seconds % 60
        self.recording_timer_label.setText(f"{mins}:{secs:02d}")
    
    def _on_voice_transcription(self, text: str):
        """Handle transcription result - put text directly in input field."""
        self._stop_voice_recording_ui()
        
        if text.strip():
            # Put text directly in input field - no preview needed
            self.input.setText(text.strip())
            self.input.setFocus()
    
    def _send_transcription(self):
        """Send the transcribed text as a message."""
        if self._pending_transcription:
            self.input.setText(self._pending_transcription)
            self._pending_transcription = ""
            self.transcription_preview.hide()
            self.input.show()
            self.send_btn.show()
            self.mic_btn.show()
            self._send_message()
    
    def _discard_transcription(self):
        """Discard the transcription and restore input."""
        self._pending_transcription = ""
        self.transcription_preview.hide()
        self.input.show()
        self.send_btn.show()
        self.mic_btn.show()
        self.input.setFocus()
    
    def _on_voice_error(self, error: str):
        """Handle voice input error."""
        self._stop_voice_recording_ui()
        print(f"[Voice Error]: {error}")


