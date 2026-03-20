"""
Video Background Widget - Native QtMultimedia
Hardware accelerated for zero-lag playback
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import QUrl, QTimer, Qt

import os
import sys
from pathlib import Path

# Import path from centralized config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from configs.paths import GUI_VIDEO_PATH
from infra.gui.theme import ThemeManager


class VideoBackgroundWidget(QWidget):
    """Looping video background using native QMediaPlayer"""
    
    # Default video path from centralized config
    DEFAULT_VIDEO = str(GUI_VIDEO_PATH)
    
    def __init__(self, video_path: str = None):
        super().__init__()
        self.video_path = video_path or self.DEFAULT_VIDEO
        self.player = None
        self.video_widget = None
        
        self._setup_ui()
        
        if self.video_path and os.path.exists(self.video_path):
            self._load_video(self.video_path)
        else:
            self._show_placeholder()
            
        # Listen for theme changes
        ThemeManager.add_listener(self._on_theme_change)
        self._on_theme_change(ThemeManager.get_theme())
    
    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Native Video Widget
        self.video_widget = QVideoWidget()
        self.video_widget.setAspectRatioMode(Qt.AspectRatioMode.IgnoreAspectRatio)
        self.layout.addWidget(self.video_widget)
        
        # Placeholder (hidden initially)
        self.placeholder = QLabel()
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.hide()
        self.layout.addWidget(self.placeholder)
        
        # Initialize Player
        self.player = QMediaPlayer()
        self.player.setVideoOutput(self.video_widget)
        
        # Set Infinite Loop
        self.player.setLoops(QMediaPlayer.Loops.Infinite)
        
        # Handle errors and status changes
        self.player.errorOccurred.connect(self._handle_error)
        self.player.mediaStatusChanged.connect(self._on_status_changed)
        
        self._recovery_timer = QTimer()
        self._recovery_timer.timeout.connect(self._check_playback)
        self._recovery_timer.start(500)  # Check every 500ms for quick recovery
    
    def _on_theme_change(self, theme):
        """Update background styling based on theme."""
        if theme.name == "light":
            # Premium Light Blue + Light Pink Gradient
            style = """
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #E0F7FA, stop:1 #FCE4EC);
            """
        else:
            # Deep Black for Dark Mode
            style = "background-color: #000000;"
            
        self.setStyleSheet(f"VideoBackgroundWidget {{ {style} }}")
        
        # Ensure video widget is transparent so gradient shows if video hasn't loaded
        # Note: QVideoWidget paints over background when video plays
        if self.video_widget:
            self.video_widget.setStyleSheet(f"background-color: {'transparent' if theme.name == 'light' else '#000000'};")
    
    def _load_video(self, path: str):
        """Load and play video"""
        self.placeholder.hide()
        self.video_widget.show()
        
        url = QUrl.fromLocalFile(path)
        self.player.setSource(url)
        self.player.play()
    
    def _show_placeholder(self):
        """Show placeholder text"""
        if self.player:
            self.player.stop()
        
        self.video_widget.hide()
        self.placeholder.show()
        
        self.placeholder.setText("🎬 No Video Found")
        self.placeholder.setStyleSheet("""
            background-color: #000000;
            color: #444;
            font-size: 14px;
            font-family: Consolas;
            border: 2px dashed #333;
            border-radius: 8px;
        """)
    
    def _handle_error(self):
        error_msg = self.player.errorString()
        print(f"Video Error: {error_msg}")
        self._show_placeholder()
        self.placeholder.setText(f"⚠ Video Error\n{error_msg}")
    
    def set_video(self, path: str):
        if os.path.exists(path):
            self._load_video(path)
        else:
            self._show_placeholder()
    
    def stop(self):
        if self.player:
            self.player.stop()
    
    def pause(self):
        """Pause video playback"""
        if self.player:
            self.player.pause()
    
    def resume(self):
        """Resume video playback"""
        if self.player:
            self.player.play()
    
    def _on_status_changed(self, status):
        """Handle media status changes to recover from stalls."""
        from PyQt6.QtMultimedia import QMediaPlayer
        
        # If video ended but should be looping, restart it
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if self.video_path and os.path.exists(self.video_path):
                self.player.setPosition(0)
                self.player.play()
        
        # If video is stalled or invalid, try to reload
        elif status in (QMediaPlayer.MediaStatus.StalledMedia, 
                        QMediaPlayer.MediaStatus.InvalidMedia):
            print(f"Video stalled/invalid, attempting recovery...")
            if self.video_path and os.path.exists(self.video_path):
                QTimer.singleShot(500, lambda: self._load_video(self.video_path))
    
    def _check_playback(self):
        """Periodic check to ensure video is still playing."""
        from PyQt6.QtMultimedia import QMediaPlayer
        
        if not self.player or not self.video_path:
            return
        
        # If playback stopped but should be playing, restart
        state = self.player.playbackState()
        if state == QMediaPlayer.PlaybackState.StoppedState:
            print(f"[MainVideo] Video stopped unexpectedly, restarting...")
            if os.path.exists(self.video_path):
                self.player.setPosition(0)
                self.player.play()
        elif state == QMediaPlayer.PlaybackState.PausedState:
            print(f"[MainVideo] Video paused unexpectedly, resuming...")
            self.player.play()
