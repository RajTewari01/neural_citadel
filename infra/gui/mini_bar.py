"""
Mini Floating Bar - Neural Citadel
Collapsible bar: starts as listening orb, expands on click
Supports light/dark mode themes with smooth animations
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel, QGraphicsOpacityEffect,
    QStyleOptionButton, QStyle
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QPropertyAnimation, QEasingCurve, QSize, QRect, QParallelAnimationGroup, QTimer, QRectF
from PyQt6.QtGui import QCursor, QPainter, QPen, QColor

from infra.gui.theme import ThemeManager, DARK_THEME, LIGHT_THEME
import math


class SpinnerButton(QPushButton):
    """Button with circular spinning arc animation for processing state."""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._spinning = False
        self._angle = 0
        self._spinner_timer = QTimer()
        self._spinner_timer.timeout.connect(self._update_spin)
        self._arc_color = QColor("#ffffff")
        self._arc_width = 3
        self._arc_length = 90
    
    def start_spinner(self):
        self._spinning = True
        self._angle = 0
        self._spinner_timer.start(30)
        self.update()
    
    def stop_spinner(self):
        self._spinning = False
        self._spinner_timer.stop()
        self.update()
    
    def is_spinning(self):
        return self._spinning
    
    def _update_spin(self):
        self._angle = (self._angle + 15) % 360
        self.update()
    
    def paintEvent(self, event):
        if self._spinning:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            opt = QStyleOptionButton()
            self.initStyleOption(opt)
            opt.text = ""
            self.style().drawControl(QStyle.ControlElement.CE_PushButton, opt, painter, self)
            
            padding = 5
            rect = QRectF(padding, padding, self.width() - padding * 2, self.height() - padding * 2)
            
            pen = QPen(self._arc_color)
            pen.setWidth(self._arc_width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            
            start_angle = int(self._angle * 16)
            span_angle = int(self._arc_length * 16)
            painter.drawArc(rect, start_angle, span_angle)
            
            painter.end()
        else:
            super().paintEvent(event)


class MiniFloatingBar(QWidget):
    """Collapsible floating bar - starts as listening orb, expands on click"""
    
    expand_requested = pyqtSignal()
    message_sent = pyqtSignal(str)
    
    # Sizes
    COLLAPSED_SIZE = (60, 60)
    EXPANDED_SIZE = (450, 50)
    
    def __init__(self):
        super().__init__()
        
        # Premium Gradient Animation - Initialize BEFORE setup_ui
        self.gradient_angle = 0
        self.gradient_timer = QTimer()
        self.gradient_timer.timeout.connect(self._animate_orb)
        self.gradient_timer.start(30)  # Faster 33fps animation
        
        self.drag_pos = None
        self.is_expanded = False
        self.is_listening = False
        
        # Voice state: "idle", "recording", or "processing"
        self._voice_state = "idle"
        
        self._setup_window()
        self._setup_collapsed_ui()
        self._setup_expanded_ui()
        self._show_collapsed()
        
        # Listen for theme changes
        ThemeManager.add_listener(self._on_theme_change)
    
    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(*self.COLLAPSED_SIZE)
        
        # Position at bottom center
        screen = self.screen().geometry()
        self.move(
            (screen.width() - self.COLLAPSED_SIZE[0]) // 2,
            screen.height() - 100
        )
    
    def _setup_collapsed_ui(self):
        """Small orb for listening mode"""
        self.collapsed_widget = QWidget(self)
        self.collapsed_widget.setGeometry(0, 0, *self.COLLAPSED_SIZE)
        self.collapsed_widget.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        collapsed_layout = QHBoxLayout(self.collapsed_widget)
        collapsed_layout.setContentsMargins(0, 0, 0, 0)
        
        self.orb_icon = QLabel("")
        self.orb_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.orb_icon.setStyleSheet("background: transparent; border: none;")
        collapsed_layout.addWidget(self.orb_icon)
        
        self.collapsed_widget.mousePressEvent = self._on_collapsed_click
        self._apply_collapsed_theme()
    
    def _setup_expanded_ui(self):
        """Full mini bar"""
        self.expanded_widget = QWidget(self)
        self.expanded_widget.setGeometry(0, 0, *self.EXPANDED_SIZE)
        
        layout = QHBoxLayout(self.expanded_widget)
        layout.setContentsMargins(15, 5, 10, 5)
        layout.setSpacing(10)
        
        # Collapse button (back to orb) - also shows voice gradient
        self.collapse_btn = QPushButton("◀")
        self.collapse_btn.setFixedSize(32, 32)
        self.collapse_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.collapse_btn.setToolTip("Collapse to listening mode")
        self.collapse_btn.clicked.connect(self._collapse)
        layout.addWidget(self.collapse_btn)
        
        # Voice gradient animation timer for collapse button
        self._gradient_timer = QTimer()
        self._gradient_timer.timeout.connect(self._animate_collapse_gradient)
        self._gradient_pulse = 0
        
        # Input field
        self.input = QLineEdit()
        self.input.setPlaceholderText("Ask Neural Citadel...")
        self.input.returnPressed.connect(self._send_message)
        layout.addWidget(self.input, stretch=1)
        
        # Mic button with spinner capability
        self.mic_btn = SpinnerButton("🎤")
        self.mic_btn.setFixedSize(32, 32)
        self.mic_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.mic_btn.setToolTip("Voice input")
        self.mic_btn.clicked.connect(self._toggle_voice)
        layout.addWidget(self.mic_btn)
        
        # Send button (Updated Icon)
        self.send_btn = QPushButton("➤")
        self.send_btn.setFixedSize(32, 32)
        self.send_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.send_btn.clicked.connect(self._send_message)
        layout.addWidget(self.send_btn)
        
        # Expand to main window button
        self.expand_btn = QPushButton("◻") # Standard Maximise Square
        self.expand_btn.setFixedSize(32, 32)
        self.expand_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.expand_btn.setToolTip("Expand to full window")
        self.expand_btn.clicked.connect(self._expand_to_main)
        layout.addWidget(self.expand_btn)
        
        # Exit button
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(32, 32)
        self.close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.close_btn.setToolTip("Exit application")
        self.close_btn.clicked.connect(self._exit_app)
        layout.addWidget(self.close_btn)
        
        self.expanded_widget.hide()
        self._apply_expanded_theme()
    
    def _apply_collapsed_theme(self):
        """Apply theme to collapsed orb (initial static state)"""
        # Actual styling handled by _animate_orb
        self._animate_orb()

    def _animate_orb(self):
        """Rotate gradient for premium live-like effect"""
        if self.is_expanded:
            return
            
        # Use a time-based counter for smoother organic motion
        self.gradient_angle = (self.gradient_angle + 6) % 3600 
        t = self.gradient_angle * 0.05
        
        # Lissajous-like chaotic motion (Tighter containment)
        fx = 0.5 + 0.15 * math.cos(t * 0.7) 
        fy = 0.5 + 0.15 * math.sin(t * 1.1)
        
        # Breathing radius (pulsing size)
        radius = 0.65 + 0.05 * math.sin(t * 2.0)
        
        theme = ThemeManager.get_theme()
        is_dark = theme.name == "dark"
        
        if is_dark:
            # Siri Dark: Deepest Blacks/Blues with a sharp glowing core
            stops = "stop:0 rgba(255, 255, 255, 0.95), stop:0.1 rgba(0, 255, 255, 0.9), stop:0.25 rgba(0, 0, 255, 0.6), stop:0.5 rgba(120, 0, 200, 0.4), stop:0.75 rgba(40, 0, 80, 0.1), stop:1 rgba(0, 0, 0, 0.0)"
            bg_base = "#000000"
        else:
            # Light Mode: Vibrant Iridescent Pearl
            stops = "stop:0 rgba(255, 255, 255, 1.0), stop:0.15 rgba(0, 180, 255, 0.8), stop:0.35 rgba(255, 100, 150, 0.7), stop:0.6 rgba(150, 100, 255, 0.5), stop:0.85 rgba(200, 200, 220, 0.2), stop:1 rgba(255, 255, 255, 0.0)"
            bg_base = "#FFFFFF"
            
        self.collapsed_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_base};
                background-image: none;
                background: qradialgradient(cx:0.5, cy:0.5, radius: {radius:.2f}, fx:{fx:.2f}, fy:{fy:.2f}, {stops});
                border: none;
                border-radius: 30px;
            }}
        """)
    
    def _apply_expanded_theme(self):
        """Apply theme to expanded bar"""
        theme = ThemeManager.get_theme()
        
        self.expanded_widget.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {theme.bar_gradient_start},
                    stop:0.5 {theme.bar_gradient_mid},
                    stop:1 {theme.bar_gradient_end});
                border: none;
                border-radius: 25px;
            }}
        """)
        
        # Collapse button
        self.collapse_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.1);
                color: {theme.bar_text};
                border: none;
                border-radius: 16px;
                font-size: 14px;
                font-weight: bold;
                padding-bottom: 2px; /* Visual centering */
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.2);
            }}
        """)
        
        # Input field
        self.input.setStyleSheet(f"""
            QLineEdit {{
                background: {theme.bar_input_bg};
                border: none;
                border-radius: 15px;
                color: {theme.bar_text};
                font-family: Consolas;
                font-size: 13px;
                padding: 8px 15px;
            }}
            QLineEdit::placeholder {{
                color: {'#888' if theme.name == 'dark' else '#666'};
            }}
        """)
        
        # Mic button
        self.mic_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.1);
                color: {theme.bar_text};
                border: none;
                border-radius: 16px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.2);
                color: #ffffff;
            }}
        """)
        
        # Send button - Gradient Circle
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {theme.accent_1}, stop:1 {theme.accent_2});
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 14px;
                font-weight: bold;
                padding-left: 2px; /* Center optical alignment */
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """)
        
        # Expand button
        self.expand_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.1);
                color: {theme.bar_text};
                border: none;
                border-radius: 16px;
                font-size: 18px;
                font-weight: bold;
                padding-bottom: 2px; /* Visual centering */
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.2);
                color: #ffffff;
            }}
        """)
        
        # Close button - always reddish
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 100, 100, 0.3);
                color: #c55;
                border: none;
                border-radius: 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 100, 100, 0.5);
                color: #f66;
            }
        """)
    
    def _on_theme_change(self, theme):
        """Handle theme change"""
        self._apply_collapsed_theme()
        self._apply_expanded_theme()
    
    def _toggle_theme(self):
        """Toggle between light and dark mode"""
        ThemeManager.toggle_theme()
    
    def _show_collapsed(self, animated=True):
        """Show collapsed orb mode with optional animation"""
        if not animated:
            self.is_expanded = False
            self.expanded_widget.hide()
            self.collapsed_widget.show()
            self.setFixedSize(*self.COLLAPSED_SIZE)
            screen = self.screen().geometry()
            self.move(
                (screen.width() - self.COLLAPSED_SIZE[0]) // 2,
                screen.height() - 100
            )
            return
        
        self.is_expanded = False
        screen = self.screen().geometry()
        target_x = (screen.width() - self.COLLAPSED_SIZE[0]) // 2
        target_y = screen.height() - 100
        
        # Create animation group for smooth transition
        self.collapse_anim = QParallelAnimationGroup()
        
        # Geometry animation (size + position)
        geom_anim = QPropertyAnimation(self, b"geometry")
        geom_anim.setDuration(250)
        geom_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        geom_anim.setStartValue(self.geometry())
        geom_anim.setEndValue(QRect(target_x, target_y, *self.COLLAPSED_SIZE))
        self.collapse_anim.addAnimation(geom_anim)
        
        # Fade out expanded widget
        self.expanded_opacity = QGraphicsOpacityEffect()
        self.expanded_widget.setGraphicsEffect(self.expanded_opacity)
        fade_out = QPropertyAnimation(self.expanded_opacity, b"opacity")
        fade_out.setDuration(150)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        self.collapse_anim.addAnimation(fade_out)
        
        def on_collapse_finished():
            self.expanded_widget.hide()
            self.expanded_widget.setGraphicsEffect(None)
            self.collapsed_widget.show()
            self.setFixedSize(*self.COLLAPSED_SIZE)
        
        self.collapse_anim.finished.connect(on_collapse_finished)
        self.collapse_anim.start()
    
    def _show_expanded(self, animated=True):
        """Show expanded bar mode with optional animation"""
        if not animated:
            self.is_expanded = True
            self.collapsed_widget.hide()
            self.expanded_widget.show()
            self.setFixedSize(*self.EXPANDED_SIZE)
            screen = self.screen().geometry()
            self.move(
                (screen.width() - self.EXPANDED_SIZE[0]) // 2,
                screen.height() - 100
            )
            self.input.setFocus()
            # Auto-start listening as requested
            self._start_listening()
            return
        
        self.is_expanded = True
        self.collapsed_widget.hide()
        self.expanded_widget.show()
        
        screen = self.screen().geometry()
        target_x = (screen.width() - self.EXPANDED_SIZE[0]) // 2
        target_y = screen.height() - 100
        
        # Set initial size for animation
        self.setFixedSize(*self.EXPANDED_SIZE)
        
        # Create animation group
        self.expand_anim = QParallelAnimationGroup()
        
        # Geometry animation
        geom_anim = QPropertyAnimation(self, b"geometry")
        geom_anim.setDuration(250)
        geom_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        geom_anim.setStartValue(self.geometry())
        geom_anim.setEndValue(QRect(target_x, target_y, *self.EXPANDED_SIZE))
        self.expand_anim.addAnimation(geom_anim)
        
        # Fade in expanded widget
        self.expanded_opacity = QGraphicsOpacityEffect()
        self.expanded_widget.setGraphicsEffect(self.expanded_opacity)
        fade_in = QPropertyAnimation(self.expanded_opacity, b"opacity")
        fade_in.setDuration(200)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        self.expand_anim.addAnimation(fade_in)
        
        def on_expand_finished():
            self.expanded_widget.setGraphicsEffect(None)
            self.input.setFocus()
        
        self.expand_anim.finished.connect(on_expand_finished)
        self.expand_anim.start()
    
    def _on_collapsed_click(self, event):
        """Handle click on collapsed orb"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._show_expanded()
    
    def _collapse(self):
        """Collapse back to orb"""
        self._show_collapsed()
    
    def _send_message(self):
        msg = self.input.text().strip()
        if msg:
            self.message_sent.emit(msg)
            self.input.clear()
    
    def _expand_to_main(self):
        """Expand to main window"""
        self.hide()
        self.expand_requested.emit()
    
    def _exit_app(self):
        """Fully exit the application"""
        from PyQt6.QtWidgets import QApplication
        QApplication.instance().quit()
    
    def _toggle_voice(self):
        """Toggle voice recording with VoiceManager integration."""
        from infra.gui.widgets.voice_worker import get_voice_manager
        voice_manager = get_voice_manager()
        
        # Check if model is loaded
        if not voice_manager.is_loaded:
            self.input.setPlaceholderText("Load Voice Model in Settings first")
            return
        
        if self._voice_state == "recording":
            # Stop recording → processing
            voice_manager.stop_listening()
        else:
            # Start recording
            self._voice_state = "recording"
            self.is_listening = True
            self.input.setPlaceholderText("🎤 Listening...")
            
            # Start pulsing gradient animation on collapse button
            self._gradient_timer.start(40)  # Fast pulsing
            
            voice_manager.start_listening()
            
            # Connect signals (disconnect first to avoid duplicates)
            try:
                voice_manager.transcription.disconnect(self._on_voice_transcription)
                voice_manager.processing.disconnect(self._on_voice_processing)
                voice_manager.stopped.disconnect(self._on_voice_stopped)
                voice_manager.error.disconnect(self._on_voice_error)
            except:
                pass
            
            voice_manager.transcription.connect(self._on_voice_transcription)
            voice_manager.processing.connect(self._on_voice_processing)
            voice_manager.stopped.connect(self._on_voice_stopped)
            voice_manager.error.connect(self._on_voice_error)
    
    def _on_voice_processing(self):
        """Called when VoiceManager starts processing audio."""
        self._voice_state = "processing"
        self.input.setPlaceholderText("Processing...")
        self.mic_btn.start_spinner()
        # Stop gradient animation during processing
        self._gradient_timer.stop()
        self._reset_collapse_btn_style()
    
    def _on_voice_stopped(self):
        """Called when recording/processing stops."""
        self._voice_state = "idle"
        self.is_listening = False
        self.mic_btn.stop_spinner()
        self.mic_btn.setText("🎤")
        self.input.setPlaceholderText("Ask Neural Citadel...")
        # Stop gradient animation
        self._gradient_timer.stop()
        self._reset_collapse_btn_style()
    
    def _on_voice_transcription(self, text: str):
        """Handle transcription result - put text in input field."""
        self._on_voice_stopped()
        if text.strip():
            self.input.setText(text.strip())
            self.input.setFocus()
    
    def _animate_collapse_gradient(self):
        """Animate the collapse button with pulsing gradient effect."""
        self._gradient_pulse = (self._gradient_pulse + 1) % 360
        t = self._gradient_pulse * 0.1
        
        # Breathing effect for opacity/intensity
        intensity = 0.6 + 0.4 * math.sin(t * 2.0)
        
        if self._voice_state == "recording":
            # Lime green pulsing gradient
            r1, g1, b1 = 50, int(255 * intensity), 100
            r2, g2, b2 = 0, int(200 * intensity), 50
        else:
            # Red/orange pulsing gradient (idle)
            r1, g1, b1 = int(255 * intensity), 80, 50
            r2, g2, b2 = int(200 * intensity), 50, 50
        
        self.collapse_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgb({r1}, {g1}, {b1}),
                    stop:1 rgb({r2}, {g2}, {b2}));
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 14px;
                font-weight: bold;
            }}
        """)
    
    def _reset_collapse_btn_style(self):
        """Reset collapse button to default theme style."""
        theme = ThemeManager.get_theme()
        self.collapse_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.1);
                color: {theme.bar_text};
                border: none;
                border-radius: 16px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.2);
            }}
        """)
    
    def _on_voice_result_from_manager(self, text: str):
        """Handle successful voice transcription from VoiceManager"""
        self._stop_listening()
        if text.strip():
            self.input.setText(text.strip())
            self._show_expanded()
            self.input.setFocus()
    
    def _on_voice_result(self, text: str):
        """Handle successful voice recognition (legacy)"""
        self._stop_listening()
        self.input.setText(text)
        self._show_expanded()
        self.input.setFocus()
    
    def _on_voice_error(self, error: str):
        """Handle voice recognition error"""
        self._stop_listening()
        self.input.setPlaceholderText("Voice error...")
    
    def set_response(self, text: str):
        """Show AI response briefly in the input as placeholder"""
        self.input.setPlaceholderText(f"AI: {text[:50]}...")
    
    # Drag functionality
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_pos:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        self.drag_pos = None


