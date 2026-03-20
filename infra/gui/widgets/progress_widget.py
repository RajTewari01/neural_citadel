"""
Animated Progress Widget
========================

Pulsing progress bar for image generation status.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QFont


# Instagram colors
PURPLE = "#833AB4"
PINK = "#E1306C"
ORANGE = "#F77737"


class PulsingProgressBar(QFrame):
    """Animated pulsing progress bar with Instagram gradient."""
    
    def __init__(self):
        super().__init__()
        self.setFixedHeight(6)
        self.setMinimumWidth(200)
        
        self._position = 0.0  # 0 to 1, position of the pulse
        self._pulse_width = 0.3  # Width of the pulse (30% of bar)
        
        # Animation timer
        self._timer = QTimer()
        self._timer.timeout.connect(self._animate)
        
        self.setStyleSheet("""
            PulsingProgressBar {
                background-color: #1a1a1a;
                border-radius: 3px;
            }
        """)
    
    def start(self):
        """Start the pulsing animation."""
        self._timer.start(60)  # ~16fps (reduced from 33fps to prevent lag)
    
    def stop(self):
        """Stop the pulsing animation."""
        self._timer.stop()
        self._position = 0.0
        self.update()
    
    def _animate(self):
        """Update pulse position."""
        self._position += 0.04  # Larger step to compensate for lower FPS
        if self._position > 1.0 + self._pulse_width:
            self._position = -self._pulse_width
        self.update()
    
    def paintEvent(self, event):
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # Draw the pulsing gradient
        pulse_start = int(self._position * w)
        pulse_end = int((self._position + self._pulse_width) * w)
        
        # Create gradient for the pulse
        gradient = QLinearGradient(pulse_start, 0, pulse_end, 0)
        gradient.setColorAt(0.0, QColor(0, 0, 0, 0))
        gradient.setColorAt(0.3, QColor(PURPLE))
        gradient.setColorAt(0.5, QColor(PINK))
        gradient.setColorAt(0.7, QColor(ORANGE))
        gradient.setColorAt(1.0, QColor(0, 0, 0, 0))
        
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, w, h, 3, 3)


class GeneratingWidget(QFrame):
    """
    Widget showing generating status with pulsing progress bar.
    Used in chat during image generation.
    """
    
    def __init__(self, model_name: str = "", title: str = ""):
        super().__init__()
        self._elapsed_seconds = 0
        self._setup_ui(model_name, title)
    
    def _setup_ui(self, model_name: str, title: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)
        
        # Header with title and elapsed time
        header = QHBoxLayout()
        
        # Title
        display_title = title if title else "🎨 Generating Image..."
        title_label = QLabel(display_title)
        title_label.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {PINK};")
        header.addWidget(title_label)
        
        header.addStretch()
        
        # Elapsed time
        self.time_label = QLabel("0s")
        self.time_label.setStyleSheet(f"color: {ORANGE}; font-size: 11px; font-family: Consolas; font-weight: bold;")
        header.addWidget(self.time_label)
        
        layout.addLayout(header)
        
        # Model info
        if model_name:
            model_label = QLabel(f"Model: {model_name}")
            model_label.setStyleSheet("color: #888; font-size: 10px; font-family: Consolas;")
            layout.addWidget(model_label)
        
        # Status label
        self.status_label = QLabel("Loading model...")
        self.status_label.setStyleSheet("color: #666; font-size: 10px; font-family: Consolas;")
        layout.addWidget(self.status_label)
        
        # Pulsing progress bar
        self.progress_bar = PulsingProgressBar()
        layout.addWidget(self.progress_bar)
        
        # Style the frame
        self.setStyleSheet("""
            GeneratingWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a3e, stop:0.5 #2d1b4e, stop:1 #1e3a5f);
                border: 1px solid #3d3d6b;
                border-radius: 16px;
                margin-right: 30px;
            }
        """)
        
        # Start animation and timer
        self.progress_bar.start()
        
        # Elapsed time timer - use self as parent for proper event loop
        self._elapsed_timer = QTimer(self)
        self._elapsed_timer.timeout.connect(self._update_elapsed)
        self._elapsed_timer.start(1000)  # Update every second
    
    def _update_elapsed(self):
        """Update elapsed time display."""
        self._elapsed_seconds += 1
        if self._elapsed_seconds < 60:
            self.time_label.setText(f"{self._elapsed_seconds}s")
        else:
            mins = self._elapsed_seconds // 60
            secs = self._elapsed_seconds % 60
            self.time_label.setText(f"{mins}m {secs}s")
    
    def set_status(self, status: str):
        """Update the status text."""
        self.status_label.setText(status)
    
    def finish(self):
        """Stop animation when done."""
        self.progress_bar.stop()
        if hasattr(self, '_elapsed_timer'):
            self._elapsed_timer.stop()
