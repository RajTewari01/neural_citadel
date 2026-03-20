"""
Movie Download Progress Widget
==============================

Progress bar with percentage and elapsed time for movie downloads.
Also includes movie play popup for completed downloads.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QPushButton, QProgressBar, QDialog, QSlider
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, QUrl
from PyQt6.QtGui import QFont, QCursor
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
import os
import subprocess
import sys

# Instagram colors
PURPLE = "#833AB4"
PINK = "#E1306C"
ORANGE = "#F77737"


class DownloadProgressWidget(QFrame):
    """
    Download progress widget with percentage bar and elapsed time.
    Parses aria2c output for progress updates.
    """
    
    canceled = pyqtSignal()
    
    def __init__(self, title: str = "Downloading...", show_phases: bool = True):
        super().__init__()
        self._elapsed_seconds = 0
        self._percentage = 0
        self._download_speed = ""
        self._show_phases = show_phases  # Only for YouTube (video+audio+merge)
        # Phase tracking for video/audio/merge
        self._current_phase = "init"  # init, video, audio, merge, complete
        self._video_progress = 0
        self._audio_progress = 0
        self._setup_ui(title)
    
    def _setup_ui(self, title: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)
        
        # Header row
        header = QHBoxLayout()
        
        # Title with download icon
        self.title_label = QLabel(f"📥 {title}")
        self.title_label.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        self.title_label.setStyleSheet(f"color: {PINK};")
        header.addWidget(self.title_label)
        
        header.addStretch()
        
        # Elapsed time
        self.time_label = QLabel("0s")
        self.time_label.setStyleSheet(f"color: {ORANGE}; font-size: 11px; font-family: Consolas; font-weight: bold;")
        header.addWidget(self.time_label)
        
        layout.addLayout(header)
        
        # Phase indicators row - only for YouTube (video+audio+merge)
        if self._show_phases:
            phase_row = QHBoxLayout()
            phase_row.setSpacing(4)
            
            # Video phase
            self.video_dot = QLabel("●")
            self.video_dot.setStyleSheet("color: #333; font-size: 8px;")
            phase_row.addWidget(self.video_dot)
            self.video_label = QLabel("Video")
            self.video_label.setStyleSheet("color: #555; font-size: 9px; font-family: Consolas;")
            phase_row.addWidget(self.video_label)
            
            arrow1 = QLabel("→")
            arrow1.setStyleSheet("color: #444; font-size: 9px;")
            phase_row.addWidget(arrow1)
            
            # Audio phase
            self.audio_dot = QLabel("●")
            self.audio_dot.setStyleSheet("color: #333; font-size: 8px;")
            phase_row.addWidget(self.audio_dot)
            self.audio_label = QLabel("Audio")
            self.audio_label.setStyleSheet("color: #555; font-size: 9px; font-family: Consolas;")
            phase_row.addWidget(self.audio_label)
            
            arrow2 = QLabel("→")
            arrow2.setStyleSheet("color: #444; font-size: 9px;")
            phase_row.addWidget(arrow2)
            
            # Merge phase
            self.merge_dot = QLabel("●")
            self.merge_dot.setStyleSheet("color: #333; font-size: 8px;")
            phase_row.addWidget(self.merge_dot)
            self.merge_label = QLabel("Merge")
            self.merge_label.setStyleSheet("color: #555; font-size: 9px; font-family: Consolas;")
            phase_row.addWidget(self.merge_label)
            
            phase_row.addStretch()
            layout.addLayout(phase_row)
        
        # Status label (filename/status)
        self.status_label = QLabel("Starting download...")
        self.status_label.setStyleSheet("color: #888; font-size: 10px; font-family: Consolas;")
        layout.addWidget(self.status_label)
        
        # Progress bar row
        progress_row = QHBoxLayout()
        progress_row.setSpacing(8)
        
        # Progress bar with gradient style
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #1a1a1a;
                border: none;
                border-radius: 6px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {PURPLE}, stop:0.5 {PINK}, stop:1 {ORANGE});
                border-radius: 6px;
            }}
        """)
        progress_row.addWidget(self.progress_bar, 1)
        
        # Percentage label
        self.percent_label = QLabel("0%")
        self.percent_label.setStyleSheet(f"color: {PINK}; font-size: 11px; font-family: Consolas; font-weight: bold;")
        self.percent_label.setFixedWidth(40)
        progress_row.addWidget(self.percent_label)
        
        layout.addLayout(progress_row)
        
        # Speed label
        self.speed_label = QLabel("Speed: --")
        self.speed_label.setStyleSheet("color: #666; font-size: 9px; font-family: Consolas;")
        layout.addWidget(self.speed_label)
        
        # Cancel button - modern minimal design
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedHeight(28)
        self.cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.cancel_btn.setToolTip("Cancel download")
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 80, 80, 0.15);
                color: #ff6b6b;
                border: 1px solid rgba(255, 80, 80, 0.3);
                border-radius: 14px;
                padding: 4px 16px;
                font-size: 11px;
                font-weight: 500;
                font-family: Consolas;
            }}
            QPushButton:hover {{
                background: rgba(255, 80, 80, 0.3);
                border: 1px solid rgba(255, 80, 80, 0.5);
                color: #ff8888;
            }}
            QPushButton:pressed {{
                background: rgba(255, 80, 80, 0.4);
            }}
        """)
        self.cancel_btn.clicked.connect(lambda: self.canceled.emit())
        btn_row.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_row)
        
        # Frame styling
        self.setStyleSheet("""
            DownloadProgressWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a3e, stop:0.5 #2d1b4e, stop:1 #1e3a5f);
                border: 1px solid #3d3d6b;
                border-radius: 16px;
            }
        """)
        
        # Start elapsed timer
        self._elapsed_timer = QTimer(self)
        self._elapsed_timer.timeout.connect(self._update_elapsed)
        self._elapsed_timer.start(1000)
    
    def _update_elapsed(self):
        """Update elapsed time display."""
        self._elapsed_seconds += 1
        if self._elapsed_seconds < 60:
            self.time_label.setText(f"{self._elapsed_seconds}s")
        else:
            mins = self._elapsed_seconds // 60
            secs = self._elapsed_seconds % 60
            self.time_label.setText(f"{mins}m {secs}s")
    
    def update_progress(self, message: str):
        """Parse aria2c/yt-dlp output and update progress with phase detection."""
        progress_updated = False
        
        # Phase detection based on output messages
        message_lower = message.lower()
        
        # Detect video download phase (f1, f2 are common format IDs, or "video" in destination)
        if "destination:" in message_lower and ("f1" in message_lower or "video" in message_lower or ".mp4" in message_lower):
            if self._current_phase != "video":
                self._set_phase("video")
        
        # Detect audio download phase
        elif "destination:" in message_lower and ("f2" in message_lower or "audio" in message_lower or ".m4a" in message_lower or ".webm" in message_lower):
            if self._current_phase != "audio":
                self._set_phase("audio")
        
        # Detect merge phase (.temp extension or Merging/muxing message)
        elif ".temp" in message or "Merging" in message or "muxing" in message_lower:
            if self._current_phase != "merge":
                self._set_phase("merge")
        
        # Try to parse aria2c progress format
        # Example with percentage: [#abc123 2.5MiB/10MiB(25%) CN:20 DL:500KiB/s]
        if "[#" in message and "]" in message:
            try:
                # Extract percentage if available
                if "(" in message and "%" in message:
                    pct_str = message.split("(")[1].split("%")[0]
                    pct = int(float(pct_str))
                    
                    # Scale percentage based on phase
                    if self._current_phase == "video":
                        self._video_progress = pct
                        self._percentage = int(pct * 0.45)  # 0-45%
                    elif self._current_phase == "audio":
                        self._audio_progress = pct
                        self._percentage = 45 + int(pct * 0.45)  # 45-90%
                    else:
                        self._percentage = pct
                    
                    self.progress_bar.setValue(self._percentage)
                    self.percent_label.setText(f"{self._percentage}%")
                    progress_updated = True
                
                # Extract bytes progress
                elif "/" in message and "B" in message:
                    import re
                    match = re.search(r'(\d+\.?\d*\s*[KMGT]?i?B)/(\d+\.?\d*\s*[KMGT]?i?B)', message)
                    if match:
                        current = match.group(1)
                        total = match.group(2)
                        phase_text = {"video": "📹", "audio": "🔊", "merge": "🔗"}.get(self._current_phase, "")
                        self.status_label.setText(f"{phase_text} {current} / {total}")
                        progress_updated = True
                
                # Extract speed
                if "DL:" in message:
                    speed_match = message.split("DL:")[1].split("]")[0].split()[0]
                    if speed_match and speed_match != "0B":
                        self.speed_label.setText(f"Speed: {speed_match}")
            except:
                pass
        
        # Parse yt-dlp progress format
        elif "[download]" in message and "%" in message:
            try:
                parts = message.split()
                for i, p in enumerate(parts):
                    if "%" in p:
                        pct_str = p.replace("%", "").strip()
                        pct = int(float(pct_str))
                        
                        # Scale percentage based on phase
                        if self._current_phase == "video":
                            self._video_progress = pct
                            self._percentage = int(pct * 0.45)
                        elif self._current_phase == "audio":
                            self._audio_progress = pct
                            self._percentage = 45 + int(pct * 0.45)
                        else:
                            self._percentage = pct
                        
                        self.progress_bar.setValue(self._percentage)
                        self.percent_label.setText(f"{self._percentage}%")
                        progress_updated = True
                        break
                
                if "at" in message and "/s" in message:
                    for i, p in enumerate(parts):
                        if p == "at" and i + 1 < len(parts):
                            speed = parts[i + 1]
                            self.speed_label.setText(f"Speed: {speed}")
                            break
            except:
                pass
        
        # Parse ffmpeg/merger progress
        elif "frame=" in message or "size=" in message or ".temp" in message:
            self._set_phase("merge")
            self.status_label.setText("🔗 Merging video and audio...")
            if self._percentage < 90:
                self._percentage = 90
            self._percentage = min(self._percentage + 1, 99)
            self.progress_bar.setValue(self._percentage)
            self.percent_label.setText(f"{self._percentage}%")
            progress_updated = True
        
        # Update status with truncated message
        if not progress_updated:
            if len(message) > 60:
                message = message[:57] + "..."
            self.status_label.setText(message)
    
    def _set_phase(self, phase: str):
        """Update the current phase and visual indicators."""
        if not self._show_phases:
            return
        self._current_phase = phase
        
        # Reset all to inactive
        inactive_dot = "color: #333; font-size: 8px;"
        inactive_label = "color: #555; font-size: 9px; font-family: Consolas;"
        
        self.video_dot.setStyleSheet(inactive_dot)
        self.video_label.setStyleSheet(inactive_label)
        self.audio_dot.setStyleSheet(inactive_dot)
        self.audio_label.setStyleSheet(inactive_label)
        self.merge_dot.setStyleSheet(inactive_dot)
        self.merge_label.setStyleSheet(inactive_label)
        
        # Highlight active phase
        active_dot = f"color: {PINK}; font-size: 10px;"
        active_label = f"color: {PINK}; font-size: 9px; font-family: Consolas; font-weight: bold;"
        complete_dot = f"color: {PURPLE}; font-size: 8px;"
        complete_label = f"color: {PURPLE}; font-size: 9px; font-family: Consolas;"
        
        if phase == "video":
            self.video_dot.setStyleSheet(active_dot)
            self.video_label.setStyleSheet(active_label)
        elif phase == "audio":
            self.video_dot.setStyleSheet(complete_dot)
            self.video_label.setStyleSheet(complete_label)
            self.audio_dot.setStyleSheet(active_dot)
            self.audio_label.setStyleSheet(active_label)
        elif phase == "merge":
            self.video_dot.setStyleSheet(complete_dot)
            self.video_label.setStyleSheet(complete_label)
            self.audio_dot.setStyleSheet(complete_dot)
            self.audio_label.setStyleSheet(complete_label)
            self.merge_dot.setStyleSheet(active_dot)
            self.merge_label.setStyleSheet(active_label)
        elif phase == "complete":
            self.video_dot.setStyleSheet(complete_dot)
            self.video_label.setStyleSheet(complete_label)
            self.audio_dot.setStyleSheet(complete_dot)
            self.audio_label.setStyleSheet(complete_label)
            self.merge_dot.setStyleSheet(complete_dot)
            self.merge_label.setStyleSheet(complete_label)
    
    def set_complete(self, success: bool = True):
        """Mark download as complete."""
        self._elapsed_timer.stop()
        self.cancel_btn.hide()
        
        if success:
            self._set_phase("complete")
            self.title_label.setText("✅ Download Complete!")
            self.title_label.setStyleSheet(f"color: #33cc33;")
            self.progress_bar.setValue(100)
            self.percent_label.setText("100%")
        else:
            self.title_label.setText("❌ Download Failed")
            self.title_label.setStyleSheet(f"color: #ff4444;")


class MoviePlayPopup(QDialog):
    """
    Popup dialog to play a downloaded movie.
    """
    
    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle("Download Complete")
        self.setFixedSize(350, 180)
        self.setModal(True)
        
        # Dark theme
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #0a0a0f;
                border: 2px solid {PURPLE};
                border-radius: 16px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Success message
        title = QLabel("✅ Download Complete!")
        title.setFont(QFont("Consolas", 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {PINK};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # File name
        filename = os.path.basename(self.file_path)
        if len(filename) > 40:
            filename = filename[:37] + "..."
        file_label = QLabel(f"📁 {filename}")
        file_label.setStyleSheet("color: #888; font-size: 11px; font-family: Consolas;")
        file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        file_label.setWordWrap(True)
        layout.addWidget(file_label)
        
        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        
        # Play button
        play_btn = QPushButton("▶ Play")
        play_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        play_btn.setFixedHeight(36)
        play_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {PURPLE}, stop:1 {PINK});
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                font-family: Consolas;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {PINK}, stop:1 {ORANGE});
            }}
        """)
        play_btn.clicked.connect(self._play_movie)
        btn_row.addWidget(play_btn)
        
        # Open folder button
        folder_btn = QPushButton("📂 Folder")
        folder_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        folder_btn.setFixedHeight(36)
        folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                font-family: Consolas;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #444;
            }
        """)
        folder_btn.clicked.connect(self._open_folder)
        btn_row.addWidget(folder_btn)
        
        # Close button - modern minimal design
        close_btn = QPushButton("✕")
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.setFixedSize(36, 36)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 80, 80, 0.15);
                color: #ff6b6b;
                border: 1px solid rgba(255, 80, 80, 0.3);
                border-radius: 18px;
                font-size: 14px;
                font-weight: 500;
                font-family: Consolas;
            }
            QPushButton:hover {
                background: rgba(255, 80, 80, 0.3);
                border: 1px solid rgba(255, 80, 80, 0.5);
                color: #ff8888;
            }
            QPushButton:pressed {
                background: rgba(255, 80, 80, 0.4);
            }
        """)
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)
        
        layout.addLayout(btn_row)
    
    def _play_movie(self):
        """Open the movie with default player."""
        try:
            if sys.platform == 'win32':
                os.startfile(self.file_path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', self.file_path])
            else:
                subprocess.run(['xdg-open', self.file_path])
            self.close()
        except Exception as e:
            print(f"Error opening file: {e}")
    
    def _open_folder(self):
        """Open the folder containing the movie."""
        try:
            folder = os.path.dirname(self.file_path)
            if sys.platform == 'win32':
                os.startfile(folder)
            elif sys.platform == 'darwin':
                subprocess.run(['open', folder])
            else:
                subprocess.run(['xdg-open', folder])
            self.close()
        except Exception as e:
            print(f"Error opening folder: {e}")


class InlineVideoPlayer(QFrame):
    """
    Inline video player widget for playing downloaded videos in chat.
    Uses PyQt6 multimedia for embedded video playback.
    """
    
    closed = pyqtSignal()
    
    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self._is_playing = False
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        # Header with filename and close button
        header = QHBoxLayout()
        
        filename = os.path.basename(self.file_path)
        if len(filename) > 40:
            filename = filename[:37] + "..."
        title = QLabel(f"🎬 {filename}")
        title.setStyleSheet(f"color: {PINK}; font-size: 11px; font-family: Consolas; font-weight: bold;")
        header.addWidget(title)
        
        header.addStretch()
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 80, 80, 0.15);
                color: #ff6b6b;
                border: 1px solid rgba(255, 80, 80, 0.3);
                border-radius: 12px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: rgba(255, 80, 80, 0.3);
            }
        """)
        close_btn.clicked.connect(self._on_close)
        header.addWidget(close_btn)
        
        layout.addLayout(header)
        
        # Video widget - needs proper sizing for video to render
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(400, 225)  # 16:9 aspect ratio
        self.video_widget.setStyleSheet("background: #111; border-radius: 8px;")
        layout.addWidget(self.video_widget)
        
        # Media player setup
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(1.0)  # Full volume
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        
        # Connect signals BEFORE setting source
        self.media_player.positionChanged.connect(self._on_position_changed)
        self.media_player.durationChanged.connect(self._on_duration_changed)
        self.media_player.errorOccurred.connect(self._on_error)
        self.media_player.mediaStatusChanged.connect(self._on_media_status)
        
        # Delay source loading to ensure widget is rendered
        QTimer.singleShot(200, self._load_video)
        
        # Progress slider - high precision for responsive seeking
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setRange(0, 1000)  # High precision for smooth seeking
        self.progress_slider.setTracking(True)  # Update position while dragging
        self.progress_slider.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.progress_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: #1a1a1a;
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {PINK};
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
                border: 2px solid rgba(255, 255, 255, 0.3);
            }}
            QSlider::handle:horizontal:hover {{
                background: {ORANGE};
                border: 2px solid rgba(255, 255, 255, 0.5);
            }}
            QSlider::sub-page:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {PURPLE}, stop:1 {PINK});
                border-radius: 3px;
            }}
        """)
        self.progress_slider.sliderMoved.connect(self._on_slider_moved)
        self.progress_slider.sliderPressed.connect(self._on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self._on_slider_released)
        layout.addWidget(self.progress_slider)
        
        # Track if user is dragging
        self._user_dragging = False
        
        # Controls row
        controls = QHBoxLayout()
        controls.setSpacing(8)
        
        # Play/Pause button
        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(36, 36)
        self.play_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.play_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {PURPLE}, stop:1 {PINK});
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {PINK}, stop:1 {ORANGE});
            }}
        """)
        self.play_btn.clicked.connect(self._toggle_play)
        controls.addWidget(self.play_btn)
        
        # Time label
        self.time_label = QLabel("0:00 / 0:00")
        self.time_label.setStyleSheet("color: #888; font-size: 10px; font-family: Consolas;")
        controls.addWidget(self.time_label)
        
        controls.addStretch()
        
        # Open externally button
        external_btn = QPushButton("🔗")
        external_btn.setFixedSize(28, 28)
        external_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        external_btn.setToolTip("Open in default player")
        external_btn.setStyleSheet("""
            QPushButton {
                background: rgba(100, 100, 100, 0.2);
                color: #888;
                border: 1px solid rgba(100, 100, 100, 0.3);
                border-radius: 14px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: rgba(100, 100, 100, 0.3);
                color: #aaa;
            }
        """)
        external_btn.clicked.connect(self._open_external)
        controls.addWidget(external_btn)
        
        layout.addLayout(controls)
        
        # Frame styling
        self.setStyleSheet("""
            InlineVideoPlayer {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a3e, stop:0.5 #2d1b4e, stop:1 #1e3a5f);
                border: 1px solid #3d3d6b;
                border-radius: 12px;
            }
        """)
    
    def _load_video(self):
        """Load video after widget is visible."""
        print(f"[InlinePlayer] Loading video: {self.file_path}")
        print(f"[InlinePlayer] File exists: {os.path.exists(self.file_path)}")
        self.media_player.setSource(QUrl.fromLocalFile(self.file_path))
        # Force widget to update
        self.video_widget.show()
        self.video_widget.update()
        print(f"[InlinePlayer] Video widget size: {self.video_widget.size()}")
    
    def _on_error(self, error, error_string):
        """Handle media player errors."""
        print(f"[InlinePlayer] ERROR: {error} - {error_string}")
    
    def _on_media_status(self, status):
        """Handle media status changes."""
        from PyQt6.QtMultimedia import QMediaPlayer
        from PyQt6.QtCore import QTimer
        
        status_name = str(status).split('.')[-1]
        print(f"[InlinePlayer] Media status: {status_name}")
        
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            # Video is ready - ensure widget is showing
            print(f"[InlinePlayer] Video loaded! Duration: {self.media_player.duration()}ms")
            print(f"[InlinePlayer] Has video: {self.media_player.hasVideo()}")
            self.video_widget.show()
            self.video_widget.repaint()
            
            # Note: On Windows, you may need to minimize/maximize to fix video rendering
            # This is a known D3D11 limitation with multiple video players
    
    def _toggle_play(self):
        if self._is_playing:
            self.media_player.pause()
            self.play_btn.setText("▶")
        else:
            self.media_player.play()
            self.play_btn.setText("⏸")
        self._is_playing = not self._is_playing
    
    def _on_position_changed(self, position):
        # Don't update slider if user is dragging
        if self._user_dragging:
            return
        
        if self.media_player.duration() > 0:
            value = int((position / self.media_player.duration()) * 1000)
            self.progress_slider.blockSignals(True)
            self.progress_slider.setValue(value)
            self.progress_slider.blockSignals(False)
            
            # Update time label
            pos_mins = position // 60000
            pos_secs = (position % 60000) // 1000
            dur_mins = self.media_player.duration() // 60000
            dur_secs = (self.media_player.duration() % 60000) // 1000
            self.time_label.setText(f"{pos_mins}:{pos_secs:02d} / {dur_mins}:{dur_secs:02d}")
    
    def _on_duration_changed(self, duration):
        dur_mins = duration // 60000
        dur_secs = (duration % 60000) // 1000
        self.time_label.setText(f"0:00 / {dur_mins}:{dur_secs:02d}")
    
    def _on_slider_pressed(self):
        """User started dragging slider."""
        self._user_dragging = True
    
    def _on_slider_released(self):
        """User released slider - seek to position."""
        self._user_dragging = False
        value = self.progress_slider.value()
        position = int((value / 1000) * self.media_player.duration())
        self.media_player.setPosition(position)
    
    def _on_slider_moved(self, value):
        """Live update while dragging for responsive feedback."""
        position = int((value / 1000) * self.media_player.duration())
        self.media_player.setPosition(position)
        
        # Update time label in real-time
        pos_mins = position // 60000
        pos_secs = (position % 60000) // 1000
        dur_mins = self.media_player.duration() // 60000
        dur_secs = (self.media_player.duration() % 60000) // 1000
        self.time_label.setText(f"{pos_mins}:{pos_secs:02d} / {dur_mins}:{dur_secs:02d}")
    
    def _open_external(self):
        try:
            if sys.platform == 'win32':
                os.startfile(self.file_path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', self.file_path])
            else:
                subprocess.run(['xdg-open', self.file_path])
        except Exception as e:
            print(f"Error opening file: {e}")
    
    def _on_close(self):
        self.media_player.stop()
        self.closed.emit()
        self.deleteLater()
    
    def stop(self):
        """Stop playback and clean up."""
        self.media_player.stop()

