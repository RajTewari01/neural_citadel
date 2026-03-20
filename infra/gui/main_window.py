"""
Main Window - V3 Refined
Supports light/dark mode themes
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from infra.gui.widgets.system_stats import SystemStatsWidget
from infra.gui.widgets.object_detect import ObjectDetectionWidget
from infra.gui.widgets.video_background import VideoBackgroundWidget
from infra.gui.widgets.chat import ChatWidget
from infra.gui.widgets.reasoning_panel import ReasoningCenterPanel
from infra.gui.widgets.code_panel import CodeCenterPanel
from infra.gui.widgets.hacking_panel import HackingCenterPanel
from infra.gui.widgets.writing_panel import WritingCenterPanel
from infra.gui.widgets.nsfw_writing_panel import NSFWWritingCenterPanel
from infra.gui.theme import ThemeManager


class NeuralCitadelWindow(QMainWindow):
    """V3 - Supports light/dark mode themes"""
    
    def __init__(self, mini_bar=None):
        super().__init__()
        self.mini_bar = mini_bar
        self.setWindowTitle("Neural Citadel - V3")
        self.setMinimumSize(1400, 800)
        
        # Set window icon
        from PyQt6.QtGui import QIcon
        from pathlib import Path
        icon_path = Path(__file__).parent.parent.parent / "assets" / "apps_assets" / "gui" / "neural_citadel.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Listen for theme changes
        ThemeManager.add_listener(self._on_theme_change)
        self._apply_theme()
        
        # Title animation state
        self._full_title = "NEURAL CITADEL"
        self._title_text = ""
        self._anim_phase = 0  # 0=type, 1=pause, 2=erase, 3=fast_type, 4=done
        self._anim_index = 0
        
        self._setup_ui()
        self._start_title_animation()
        
        # Connect mini bar signals
        if self.mini_bar:
            self.mini_bar.expand_requested.connect(self._restore_from_mini)
            self.mini_bar.message_sent.connect(self._handle_mini_message)
        
        # Connect voice manager at window level - ensures loading continues
        # even if settings dialog is closed
        self._connect_voice_manager()
    
    def _setup_ui(self):
        """Create the three-panel layout"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        
        # === LEFT PANEL ===
        left_panel = QWidget()
        left_panel.setObjectName("leftPanel")
        left_panel.setFixedWidth(320)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(12)
        
        # Header with settings button
        left_header = QHBoxLayout()
        left_header.setSpacing(8)
        
        left_title = QLabel("◆ SYSTEM MONITOR")
        left_title.setObjectName("panelTitle")
        left_header.addWidget(left_title)
        
        left_header.addStretch()
        
        # Settings button
        from PyQt6.QtGui import QCursor
        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setFixedSize(24, 24)
        self.settings_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.settings_btn.setToolTip("System Settings")
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666;
                border: 1px solid #333;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                border-color: #E1306C;
                color: #E1306C;
            }
        """)
        self.settings_btn.clicked.connect(self._show_settings_popup)
        left_header.addWidget(self.settings_btn)
        
        left_layout.addLayout(left_header)
        
        self.stats_widget = SystemStatsWidget()
        left_layout.addWidget(self.stats_widget)
        
        self.camera_widget = ObjectDetectionWidget()
        left_layout.addWidget(self.camera_widget, stretch=1)
        
        from PyQt6.QtWidgets import QStackedWidget
        from infra.gui.widgets.gallery_panel import GalleryPanel

        # === CENTER PANEL ===
        center_panel = QWidget()
        center_panel.setObjectName("centerPanel")
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(20, 20, 20, 20)
        center_layout.setSpacing(8)
        
        # Stack for switching views (Home vs Gallery)
        self.center_stack = QStackedWidget()
        center_layout.addWidget(self.center_stack)
        
        # --- View 1: Home (Original) ---
        self.home_view = QWidget()
        home_layout = QVBoxLayout(self.home_view)
        home_layout.setContentsMargins(0, 0, 0, 0)
        home_layout.setSpacing(8)
        
        self.title_label = QLabel("")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setFont(QFont("Consolas", 26, QFont.Weight.Bold))
        self.title_label.setObjectName("mainTitle")
        home_layout.addWidget(self.title_label)
        
        subtitle = QLabel("ARCHITECTURE OF THE MIND")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setObjectName("subtitle")
        home_layout.addWidget(subtitle)
        
        home_layout.addSpacing(10)
        
        self.video_widget = VideoBackgroundWidget()
        home_layout.addWidget(self.video_widget, stretch=1)
        
        # Credit footer
        credit = QLabel("Created by ━ BISWADEEP TEWARI (RAJ)")
        credit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credit.setStyleSheet("""
            color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #833AB4, stop:0.5 #E1306C, stop:1 #F77737);
            font-family: 'Segoe UI Light', 'Century Gothic', 'Trebuchet MS', sans-serif;
            font-size: 10px;
            font-weight: 300;
            font-style: italic;
            letter-spacing: 3px;
            padding: 10px;
            background: transparent;
        """)
        home_layout.addWidget(credit)
        
        self.center_stack.addWidget(self.home_view)
        
        # --- View 2: Gallery ---
        self.gallery_panel = GalleryPanel()
        self.gallery_panel.back_to_chat_requested.connect(self._restore_home_view)
        self.center_stack.addWidget(self.gallery_panel)
        
        # --- View 3: Reasoning ---
        self.reasoning_panel = ReasoningCenterPanel()
        self.reasoning_panel.cancelled.connect(self._on_reasoning_cancelled)
        self.center_stack.addWidget(self.reasoning_panel)
        
        # --- View 4: Code ---
        self.code_panel = CodeCenterPanel()
        self.code_panel.cancelled.connect(self._on_code_cancelled)
        self.center_stack.addWidget(self.code_panel)
        
        # --- View 5: Hacking ---
        self.hacking_panel = HackingCenterPanel()
        self.hacking_panel.cancelled.connect(self._on_hacking_cancelled)
        self.center_stack.addWidget(self.hacking_panel)
        
        # --- View 6: Writing ---
        self.writing_panel = WritingCenterPanel()
        self.writing_panel.cancelled.connect(self._on_writing_cancelled)
        self.writing_panel.persona_changed.connect(self._on_writing_persona_changed)
        self.writing_panel.history_cleared.connect(self._on_writing_history_cleared)
        self.center_stack.addWidget(self.writing_panel)
        
        # --- View 7: NSFW Writing ---
        self.nsfw_writing_panel = NSFWWritingCenterPanel()
        self.nsfw_writing_panel.cancelled.connect(self._on_nsfw_writing_cancelled)
        self.nsfw_writing_panel.persona_changed.connect(self._on_nsfw_writing_persona_changed)
        self.nsfw_writing_panel.history_cleared.connect(self._on_nsfw_writing_history_cleared)
        self.center_stack.addWidget(self.nsfw_writing_panel)
        
        # === RIGHT PANEL ===
        right_panel = QWidget()
        right_panel.setObjectName("rightPanel")
        right_panel.setFixedWidth(340)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(12)
        
        # Header row with title and theme toggle
        header_row = QHBoxLayout()
        right_title = QLabel("◆ AI INTERFACE")
        right_title.setObjectName("panelTitle")
        header_row.addWidget(right_title)
        header_row.addStretch()
        
        # Theme toggle button (top right)
        from PyQt6.QtGui import QCursor
        from infra.gui.theme import ThemeManager
        self.theme_btn = QPushButton("☀️")
        self.theme_btn.setFixedSize(28, 28)
        self.theme_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.theme_btn.setToolTip("Toggle light/dark mode")
        self.theme_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #833AB4, stop:0.5 #E1306C, stop:1 #F77737);
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #9b4fc9, stop:0.5 #f04080, stop:1 #ff9050);
            }
        """)
        self.theme_btn.clicked.connect(self._toggle_theme)
        header_row.addWidget(self.theme_btn)
        
        right_layout.addLayout(header_row)
        
        self.chat_widget = ChatWidget()
        self.chat_widget.mode_changed.connect(self._on_chat_mode_changed)
        # Connect reasoning signals to center panel
        self.chat_widget.reasoning_started.connect(self._on_reasoning_started)
        self.chat_widget.reasoning_token.connect(self.reasoning_panel.on_token)
        self.chat_widget.reasoning_think_start.connect(self.reasoning_panel.on_think_start)
        self.chat_widget.reasoning_think_end.connect(self.reasoning_panel.on_think_end)
        self.chat_widget.reasoning_finished.connect(self._on_reasoning_complete)
        self.chat_widget.reasoning_error.connect(self.reasoning_panel.on_error)
        # Connect code signals to center panel
        self.chat_widget.code_started.connect(self._on_code_started)
        self.chat_widget.code_token.connect(self.code_panel.on_token)
        self.chat_widget.code_finished.connect(self._on_code_complete)
        self.chat_widget.code_error.connect(self.code_panel.on_error)
        
        # Connect hacking signals to center panel
        self.chat_widget.hacking_started.connect(self._on_hacking_started)
        self.chat_widget.hacking_token.connect(self.hacking_panel.on_token)
        self.chat_widget.hacking_finished.connect(self._on_hacking_complete)
        self.chat_widget.hacking_error.connect(self.hacking_panel.on_error)
        
        # Connect writing signals to center panel
        self.chat_widget.writing_started.connect(self._on_writing_started)
        self.chat_widget.writing_token.connect(self.writing_panel.on_token)
        self.chat_widget.writing_finished.connect(self._on_writing_complete)
        self.chat_widget.writing_error.connect(self.writing_panel.on_error)
        self.chat_widget.writing_history_count.connect(self.writing_panel.update_history_count)
        
        # Connect NSFW writing signals to center panel
        self.chat_widget.nsfw_writing_started.connect(self._on_nsfw_writing_started)
        self.chat_widget.nsfw_writing_token.connect(self.nsfw_writing_panel.on_token)
        self.chat_widget.nsfw_writing_finished.connect(self._on_nsfw_writing_complete)
        self.chat_widget.nsfw_writing_error.connect(self.nsfw_writing_panel.on_error)
        
        # Connect engine status for loading progress
        self.chat_widget.writing_manager.engine_status.connect(
            lambda s: self.writing_panel.status_label.setText(s.upper())
        )
        
        right_layout.addWidget(self.chat_widget)
        
        main_layout.addWidget(left_panel)
        main_layout.addWidget(center_panel, stretch=1)
        main_layout.addWidget(right_panel)
    
    def _on_chat_mode_changed(self, mode: str):
        """Switch central view based on chat mode"""
        if mode == "Gallery":
            self.center_stack.setCurrentIndex(1)
            self.video_widget.pause()
        elif mode == "Reasoning":
            # Don't switch view yet - keep video visible
            # Only switch when user sends a message (reasoning_started signal)
            pass
        elif mode == "Code":
            # Don't switch view yet - show code panel when user sends message
            pass
        elif mode == "Hacking":
            # Don't switch view yet - show hacking panel when user sends message
            pass
        elif mode == "Writing":
            # Don't switch view yet - show writing panel when user sends message
            pass
        elif mode == "NSFW Stories":
            # Don't switch view yet - show NSFW panel when user sends message
            pass
        else:
            # Any other mode - show home/video
            self.center_stack.setCurrentIndex(0)
            self.video_widget.resume()
            # Hide panels if visible
            self.reasoning_panel.hide()
            self.code_panel.hide()
            self.hacking_panel.hide()
            self.writing_panel.hide()
            self.nsfw_writing_panel.hide()

    def _restore_home_view(self):
        """Switch back to home view from gallery"""
        self.center_stack.setCurrentIndex(0)
        self.video_widget.resume()
    
    def _on_reasoning_started(self):
        """Handle reasoning start from chat widget."""
        self.center_stack.setCurrentIndex(2)
        self.video_widget.pause()
        self.reasoning_panel.start()
    
    def _on_reasoning_complete(self, response: str):
        """Handle reasoning completion."""
        self.reasoning_panel.finish()
    
    def _on_reasoning_cancelled(self):
        """Handle reasoning cancellation - immediately unload and restore video."""
        # Hide reasoning panel
        self.reasoning_panel.hide()
        self.reasoning_panel.reset()
        
        # Restore video
        self.center_stack.setCurrentIndex(0)
        self.video_widget.resume()
        
        # Terminate reasoning subprocess immediately
        # Terminate reasoning subprocess immediately
        if hasattr(self.chat_widget, 'reasoning_manager'):
            self.chat_widget.reasoning_manager.terminate()
            self.chat_widget.reasoning_manager.clear_history()
        
        # Keep user in Reasoning mode
        self.chat_widget.input.setEnabled(True)
        self.chat_widget.send_btn.setEnabled(True)
    
    def _on_code_started(self):
        """Handle code generation start."""
        self.center_stack.setCurrentIndex(3)
        self.video_widget.pause()
        self.code_panel.start()
    
    def _on_code_complete(self, response: str):
        """Handle code generation completion."""
        self.code_panel.finish()
    
    
    def _on_code_cancelled(self):
        """Handle code cancellation - immediately unload and restore video."""
        # Hide code panel
        self.code_panel.hide()
        self.code_panel.reset()
        
        # Restore video
        self.center_stack.setCurrentIndex(0)
        self.video_widget.resume()
        
        # Terminate code subprocess
        if hasattr(self.chat_widget, 'code_manager'):
            self.chat_widget.code_manager.terminate()
        
        # Keep user in Code mode
        self.chat_widget.input.setEnabled(True)
        self.chat_widget.send_btn.setEnabled(True)

    def _on_hacking_started(self):
        """Handle hacking generation start."""
        self.center_stack.setCurrentIndex(4) # Check index! 0=Home, 1=Gallery, 2=Reasoning, 3=Code, 4=Hacking
        self.video_widget.pause()
        self.hacking_panel.start()
    
    def _on_hacking_complete(self, response: str):
        """Handle hacking generation completion."""
        self.hacking_panel.finish()
    
    def _on_hacking_cancelled(self):
        """Handle hacking cancellation."""
        self.hacking_panel.hide()
        self.hacking_panel.reset()
        
        self.center_stack.setCurrentIndex(0)
        self.video_widget.resume()
        
        if hasattr(self.chat_widget, 'hacking_manager'):
            self.chat_widget.hacking_manager.terminate()
        
        # DON'T reset mode - keep user in Hacking mode so they can try again
        # Just re-enable input
        self.chat_widget.input.setEnabled(True)
        self.chat_widget.send_btn.setEnabled(True)

    # Writing Mode handlers
    def _on_writing_started(self, prompt: str):
        """Handle writing start from chat widget."""
        # Sync persona/style from chat widget to panel
        if hasattr(self.chat_widget, 'writing_persona_combo'):
            persona = self.chat_widget.writing_persona_combo.currentData() or "therapist"
            style = self.chat_widget.writing_style_combo.currentData() or "supportive"
            self.writing_panel.set_persona(persona, style)
        
        self.center_stack.setCurrentWidget(self.writing_panel)
        self.video_widget.pause()
        self.writing_panel.start(user_prompt=prompt)
    
    def _on_writing_complete(self, response: str):
        """Handle writing generation completion."""
        self.writing_panel.finish()
    
    def _on_writing_cancelled(self):
        """Handle writing cancellation."""
        self.writing_panel.hide()
        self.writing_panel.reset()
        
        self.center_stack.setCurrentIndex(0)
        self.video_widget.resume()
        
        if hasattr(self.chat_widget, 'writing_manager'):
            self.chat_widget.writing_manager.terminate()
        
        # Keep user in Writing mode
        self.chat_widget.input.setEnabled(True)
        self.chat_widget.send_btn.setEnabled(True)
    
    def _on_writing_persona_changed(self, persona: str, style: str):
        """Handle persona/style change from writing panel."""
        if hasattr(self.chat_widget, 'writing_manager'):
            self.chat_widget.writing_manager.set_persona(persona, style)
    
    def _on_writing_history_cleared(self):
        """Handle history clear from writing panel."""
        if hasattr(self.chat_widget, 'writing_manager'):
            self.chat_widget.writing_manager.clear_history()

    # NSFW Writing Mode handlers
    def _on_nsfw_writing_started(self, prompt: str, persona: str, style: str):
        """Handle NSFW writing start from chat widget."""
        # Sync persona/style from signal to panel
        self.nsfw_writing_panel.set_persona(persona, style)
        
        self.center_stack.setCurrentWidget(self.nsfw_writing_panel)
        self.video_widget.pause()
        self.nsfw_writing_panel.start_streaming()
    
    def _on_nsfw_writing_complete(self, response: str):
        """Handle NSFW writing generation completion."""
        self.nsfw_writing_panel.finish()
    
    def _on_nsfw_writing_cancelled(self):
        """Handle NSFW writing cancellation."""
        self.nsfw_writing_panel.hide()
        self.nsfw_writing_panel.reset()
        
        self.center_stack.setCurrentIndex(0)
        self.video_widget.resume()
        
        if hasattr(self.chat_widget, 'nsfw_writing_manager'):
            self.chat_widget.nsfw_writing_manager.terminate()
        
        self.chat_widget.input.setEnabled(True)
        self.chat_widget.send_btn.setEnabled(True)
    
    def _on_nsfw_writing_persona_changed(self, persona: str, style: str):
        """Handle persona/style change from NSFW writing panel."""
        if hasattr(self.chat_widget, 'nsfw_writing_manager'):
            self.chat_widget.nsfw_writing_manager.set_persona(persona, style)
    
    def _on_nsfw_writing_history_cleared(self):
        """Handle history clear from NSFW writing panel."""
        if hasattr(self.chat_widget, 'nsfw_writing_manager'):
            self.chat_widget.nsfw_writing_manager.clear_history()

    
    def _get_stylesheet(self) -> str:
        """Generate stylesheet based on current theme"""
        theme = ThemeManager.get_theme()
        is_dark = theme.name == "dark"
        
        # Light mode uses premium gradient backgrounds, dark mode uses solid
        if is_dark:
            panel_bg = f"background-color: {theme.bg_panel};"
            main_bg = f"background-color: {theme.bg_dark};"
            panel_border = f"border: 1px solid {theme.border_color};"
            title_style = f"color: {theme.accent_2};"
            subtitle_color = "#666666"
        else:
            # Premium light mode - Glassmorphism with rose gold accents
            panel_bg = """background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(255, 245, 250, 0.98),
                stop:0.3 rgba(250, 240, 255, 0.95),
                stop:0.7 rgba(255, 235, 245, 0.95),
                stop:1 rgba(245, 235, 255, 0.98));"""
            main_bg = """background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(250, 245, 255, 1),
                stop:0.5 rgba(255, 248, 252, 1),
                stop:1 rgba(248, 245, 255, 1));"""
            panel_border = """border: 1px solid rgba(200, 180, 220, 0.4);"""
            title_style = """color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #B76E9B, stop:0.5 #9B6EB7, stop:1 #6E9BB7);"""
            subtitle_color = "#9988AA"
        
        return f"""
            QMainWindow {{
                {main_bg}
            }}
            #leftPanel, #rightPanel {{
                {panel_bg}
                {panel_border}
                border-radius: 20px;
            }}
            #centerPanel {{
                background-color: {theme.bg_dark if is_dark else '#ffffff'};
                border: {'2px' if is_dark else '1px'} solid;
                border-color: {'qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 ' + theme.accent_1 + ', stop:0.5 ' + theme.accent_2 + ', stop:1 ' + theme.accent_3 + ')' if is_dark else 'rgba(200, 180, 220, 0.3)'};
                border-radius: 20px;
            }}
            #panelTitle {{
                {title_style}
                font-family: 'Segoe UI', Consolas;
                font-size: 12px;
                font-weight: {'bold' if is_dark else '600'};
                padding-bottom: 8px;
                border-bottom: 1px solid {theme.border_color if is_dark else 'rgba(180, 160, 200, 0.3)'};
                letter-spacing: {'0' if is_dark else '1px'};
            }}
            #mainTitle {{
                color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {theme.accent_1}, stop:0.5 {theme.accent_2}, stop:1 {theme.accent_3});
                background: transparent;
            }}
            #subtitle {{
                color: {subtitle_color};
                font-size: 11px;
                letter-spacing: {'3px' if is_dark else '4px'};
                background: transparent;
                font-weight: {'normal' if is_dark else '300'};
            }}
            QLabel {{
                color: {theme.text_primary};
                background: transparent;
            }}
            QWidget {{
                background: transparent;
            }}
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollArea > QWidget > QWidget {{
                background: transparent;
            }}
            QPushButton {{
                border-radius: {'4px' if is_dark else '8px'};
            }}
        """
    
    def _apply_theme(self):
        """Apply current theme styles"""
        self.setStyleSheet(self._get_stylesheet())
    
    def _on_theme_change(self, theme):
        """Handle theme change notification"""
        self._apply_theme()
        
        # Update theme button icon
        if hasattr(self, 'theme_btn'):
            self.theme_btn.setText("☀️" if theme.name == "dark" else "🌙")
            
        # Update chat widget specific styling (for inputs)
        if hasattr(self, 'chat_widget'):
            self.chat_widget.update_theme()
            
        # Update Reasoning Panel (Fix for stuck dark mode styles)
        if hasattr(self, 'reasoning_panel'):
            self.reasoning_panel.update_theme()
    
    def _toggle_theme(self):
        """Toggle between light and dark mode"""
        ThemeManager.toggle_theme()
    
    def _start_title_animation(self):
        """Start the ChatGPT-style typing animation with smooth timing"""
        self._anim_timer = QTimer()
        self._anim_timer.timeout.connect(self._animate_title)
        self._anim_timer.start(60)  # Smoother typing speed (was 80)
    
    def _animate_title(self):
        """Animate title: type slowly -> pause -> erase -> type fast -> stay"""
        if self._anim_phase == 0:  # Type slowly
            if self._anim_index < len(self._full_title):
                self._anim_index += 1
                self._title_text = self._full_title[:self._anim_index]
                self.title_label.setText(self._title_text + "▌")
            else:
                self._anim_phase = 1
                self._anim_timer.setInterval(800)  # Pause
        
        elif self._anim_phase == 1:  # Pause then start erasing
            self._anim_phase = 2
            self._anim_timer.setInterval(30)  # Fast erase
        
        elif self._anim_phase == 2:  # Erase quickly
            if self._anim_index > 0:
                self._anim_index -= 1
                self._title_text = self._full_title[:self._anim_index]
                self.title_label.setText(self._title_text + "▌")
            else:
                self._anim_phase = 3
                self._anim_timer.setInterval(25)  # Super fast type
        
        elif self._anim_phase == 3:  # Type fast
            if self._anim_index < len(self._full_title):
                self._anim_index += 1
                self._title_text = self._full_title[:self._anim_index]
                self.title_label.setText(self._title_text + "▌")
            else:
                self._anim_phase = 4
                self._anim_timer.stop()
                self.title_label.setText(self._full_title)  # Final, no cursor
    
    def changeEvent(self, event):
        """Show mini bar when minimized or hidden"""
        from PyQt6.QtCore import QEvent
        if event.type() == QEvent.Type.WindowStateChange:
            if self.windowState() & Qt.WindowState.WindowMinimized:
                if self.mini_bar:
                    self.mini_bar.show()
        super().changeEvent(event)
    
    def hideEvent(self, event):
        """Show mini bar immediately when window is hidden"""
        # Only show mini bar if we're not in the process of restoring
        if self.mini_bar and not getattr(self, '_restoring', False):
            self.mini_bar.show()
        super().hideEvent(event)

    def _show_settings_popup(self):
        """Show settings popup to manually load/unload models."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar, QHBoxLayout, QGraphicsDropShadowEffect
        from PyQt6.QtCore import QProcess
        from PyQt6.QtGui import QColor
        
        theme = ThemeManager.get_theme()
        is_dark = theme.name == "dark"
        
        dlg = QDialog(self)
        dlg.setWindowTitle("System Settings")
        dlg.setFixedSize(300, 420)
        dlg.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        
        # Theme-aware styling with glowing border
        if is_dark:
            dlg.setStyleSheet("""
                QDialog {
                    background-color: #1a1a1a;
                    border: 2px solid;
                    border-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #833AB4, stop:0.5 #E1306C, stop:1 #F77737);
                    border-radius: 16px;
                }
                QLabel { color: #ddd; font-family: 'Segoe UI', Consolas; }
            """)
        else:
            dlg.setStyleSheet("""
                QDialog {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 rgba(255, 250, 255, 0.98),
                        stop:1 rgba(250, 245, 255, 0.98));
                    border: 2px solid;
                    border-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #B76E9B, stop:0.5 #9B6EB7, stop:1 #6E9BB7);
                    border-radius: 16px;
                }
                QLabel { color: #4a3545; font-family: 'Segoe UI', Consolas; }
            """)
        
        # Add glow effect
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(25)
        glow.setColor(QColor(theme.accent_2) if is_dark else QColor("#B76E9B"))
        glow.setOffset(0, 0)
        dlg.setGraphicsEffect(glow)
        
        layout = QVBoxLayout(dlg)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("System Settings")
        title.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {theme.accent_2 if is_dark else '#9B6EB7'};")
        layout.addWidget(title)
        
        layout.addSpacing(5)
        
        # Description
        desc = QLabel("Manage AI services manually.\nUnload to free memory.")
        desc.setStyleSheet(f"color: {'#888' if is_dark else '#887799'}; font-size: 10px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        layout.addSpacing(10)
        
        # Status Label
        status_lbl = QLabel("Image Captioner: Not Loaded")
        status_lbl.setStyleSheet(f"color: {'#aaa' if is_dark else '#776688'}; font-size: 11px;")
        layout.addWidget(status_lbl)
        
        # Progress Bar (Pulse)
        progress = QProgressBar()
        progress.setFixedHeight(4)
        progress.setTextVisible(False)
        progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {'#333' if is_dark else '#e8e0f0'};
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {'#833AB4' if is_dark else '#B76E9B'}, 
                    stop:1 {'#F77737' if is_dark else '#6E9BB7'});
                border-radius: 2px;
            }}
        """)
        progress.hide()
        layout.addWidget(progress)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        load_btn = QPushButton("Load Model")
        load_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        load_btn.setFixedHeight(32)
        if is_dark:
            load_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2a2a2a;
                    color: white;
                    border: 1px solid #444;
                    border-radius: 8px;
                    font-family: 'Segoe UI', Consolas;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #333; 
                    border-color: #833AB4;
                }
            """)
        else:
            load_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(180, 160, 200, 0.3),
                        stop:1 rgba(160, 180, 200, 0.3));
                    color: #5a4a6a;
                    border: 1px solid rgba(180, 160, 200, 0.5);
                    border-radius: 8px;
                    font-family: 'Segoe UI', Consolas;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(180, 160, 200, 0.5),
                        stop:1 rgba(160, 180, 200, 0.5));
                    border-color: #9B6EB7;
                }
            """)
        
        unload_btn = QPushButton("Unload")
        unload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        unload_btn.setFixedHeight(32)
        if is_dark:
            unload_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3a1a1a;
                    color: #ff6666;
                    border: 1px solid #802020;
                    border-radius: 8px;
                    font-family: 'Segoe UI', Consolas;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #4a1a1a;
                    border-color: #ff4444;
                }
            """)
        else:
            unload_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 200, 200, 0.4);
                    color: #995555;
                    border: 1px solid rgba(200, 150, 150, 0.5);
                    border-radius: 8px;
                    font-family: 'Segoe UI', Consolas;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: rgba(255, 180, 180, 0.5);
                    border-color: #cc6666;
                }
            """)
        unload_btn.hide()
        
        btn_layout.addWidget(load_btn)
        btn_layout.addWidget(unload_btn)
        layout.addLayout(btn_layout)
        
        # ========== VOICE INPUT SECTION ==========
        layout.addSpacing(15)
        
        # Voice Status Label (same style as Image Captioner)
        voice_status_lbl = QLabel("Voice Input: Not Loaded")
        voice_status_lbl.setStyleSheet(f"color: {'#aaa' if is_dark else '#776688'}; font-size: 11px;")
        layout.addWidget(voice_status_lbl)
        
        # Voice Progress Bar
        voice_progress = QProgressBar()
        voice_progress.setFixedHeight(4)
        voice_progress.setTextVisible(False)
        voice_progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {'#333' if is_dark else '#e8e0f0'};
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {'#833AB4' if is_dark else '#B76E9B'}, 
                    stop:1 {'#F77737' if is_dark else '#6E9BB7'});
                border-radius: 2px;
            }}
        """)
        voice_progress.hide()
        layout.addWidget(voice_progress)
        
        # Voice Buttons
        voice_btn_layout = QHBoxLayout()
        voice_btn_layout.setSpacing(10)
        
        voice_load_btn = QPushButton("Load Model")
        voice_load_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        voice_load_btn.setFixedHeight(32)
        if is_dark:
            voice_load_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2a2a2a;
                    color: white;
                    border: 1px solid #444;
                    border-radius: 8px;
                    font-family: 'Segoe UI', Consolas;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #333; 
                    border-color: #833AB4;
                }
            """)
        else:
            voice_load_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(180, 160, 200, 0.3),
                        stop:1 rgba(160, 180, 200, 0.3));
                    color: #5a4a6a;
                    border: 1px solid rgba(180, 160, 200, 0.5);
                    border-radius: 8px;
                    font-family: 'Segoe UI', Consolas;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(180, 160, 200, 0.5),
                        stop:1 rgba(160, 180, 200, 0.5));
                    border-color: #9B6EB7;
                }
            """)
        
        voice_unload_btn = QPushButton("Unload")
        voice_unload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        voice_unload_btn.setFixedHeight(32)
        if is_dark:
            voice_unload_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3a1a1a;
                    color: #ff6666;
                    border: 1px solid #802020;
                    border-radius: 8px;
                    font-family: 'Segoe UI', Consolas;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #4a1a1a;
                    border-color: #ff4444;
                }
            """)
        else:
            voice_unload_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 200, 200, 0.4);
                    color: #995555;
                    border: 1px solid rgba(200, 150, 150, 0.5);
                    border-radius: 8px;
                    font-family: 'Segoe UI', Consolas;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: rgba(255, 180, 180, 0.5);
                    border-color: #cc6666;
                }
            """)
        voice_unload_btn.hide()
        
        voice_btn_layout.addWidget(voice_load_btn)
        voice_btn_layout.addWidget(voice_unload_btn)
        layout.addLayout(voice_btn_layout)
        
        # Voice Manager integration
        from infra.gui.widgets.voice_worker import get_voice_manager
        voice_manager = get_voice_manager()
        
        # Check initial voice state
        if voice_manager.is_loaded:
            voice_status_lbl.setText("Voice Input: Ready 🟢")
            voice_status_lbl.setStyleSheet("color: #4a8a4a; font-size: 11px;")
            voice_load_btn.hide()
            voice_unload_btn.show()
        elif voice_manager.process and voice_manager.process.state() == QProcess.ProcessState.Running:
            # Process is running but not ready yet - show loading state
            voice_status_lbl.setText("Loading Whisper model...")
            voice_status_lbl.setStyleSheet("color: #F77737; font-size: 11px;")
            voice_load_btn.setEnabled(False)
            voice_load_btn.setText("Loading...")
            voice_progress.show()
            voice_progress.setRange(0, 0)
        
        # Voice Logic
        def on_voice_load():
            voice_load_btn.setEnabled(False)
            voice_load_btn.setText("Loading...")
            voice_progress.show()
            voice_progress.setRange(0, 0)
            voice_status_lbl.setText("Loading Whisper model...")
            voice_status_lbl.setStyleSheet("color: #F77737; font-size: 11px;")
            voice_manager.load_model()
        
        def on_voice_ready():
            try:
                voice_progress.hide()
                voice_status_lbl.setText("Voice Input: Ready 🟢")
                voice_status_lbl.setStyleSheet("color: #4a8a4a; font-size: 11px;")
                voice_load_btn.hide()
                voice_unload_btn.show()
                voice_load_btn.setEnabled(True)
                voice_load_btn.setText("Load Model")
                # Show mic buttons in chat
                if hasattr(self, 'chat_widget'):
                    self.chat_widget.show_mic_button()
            except RuntimeError:
                pass
        
        def on_voice_error(msg):
            try:
                voice_progress.hide()
                voice_status_lbl.setText(f"Error: {msg[:30]}...")
                voice_status_lbl.setStyleSheet("color: #ff6666; font-size: 11px;")
                voice_load_btn.setEnabled(True)
                voice_load_btn.setText("Load Model")
            except RuntimeError:
                pass
        
        def on_voice_unload():
            voice_manager.unload_model()
            try:
                voice_status_lbl.setText("Voice Input: Unloaded ⚪")
                voice_status_lbl.setStyleSheet(f"color: {'#aaa' if is_dark else '#776688'}; font-size: 11px;")
                voice_unload_btn.hide()
                voice_load_btn.show()
                # Hide mic buttons in chat
                if hasattr(self, 'chat_widget'):
                    self.chat_widget.hide_mic_button()
            except RuntimeError:
                pass
        
        voice_load_btn.clicked.connect(on_voice_load)
        voice_unload_btn.clicked.connect(on_voice_unload)
        
        # Connect voice manager signals for this dialog
        # These handlers fail gracefully if dialog is closed
        def safe_on_ready():
            try:
                # Check if widgets still exist by accessing a property
                _ = voice_progress.isVisible()
                on_voice_ready()
            except (RuntimeError, AttributeError):
                # Dialog was closed, but model still loaded successfully
                pass
        
        def safe_on_error(msg):
            try:
                _ = voice_progress.isVisible()
                on_voice_error(msg)
            except (RuntimeError, AttributeError):
                pass
        
        voice_manager.ready.connect(safe_on_ready)
        voice_manager.error.connect(safe_on_error)
        
        # ========== END VOICE INPUT SECTION ==========
        
        layout.addStretch()
        
        # Close Button
        close_btn = QPushButton("Close")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("background: transparent; color: #666; border: none; font-size: 11px;")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn)
        
        # Check initial state
        is_running = False
        if hasattr(self.camera_widget, 'caption_process') and self.camera_widget.caption_process.state() == QProcess.ProcessState.Running:
            is_running = True
            status_lbl.setText("Image Captioner: Ready 🟢")
            status_lbl.setStyleSheet("color: #4a8a4a; font-size: 11px;")
            load_btn.hide()
            unload_btn.show()
        
        # Logic
        def on_load():
            load_btn.setEnabled(False)
            load_btn.setText("Loading...")
            progress.show()
            progress.setRange(0, 0)  # Pulse
            status_lbl.setText("Initializing Service...")
            status_lbl.setStyleSheet("color: #F77737; font-size: 11px;")
            
            self.camera_widget.ai_service_ready.connect(on_success)
            self.camera_widget.load_ai_service()
            
        def on_success():
            # Check if dialog is still valid
            try:
                if not progress.isVisible() and not load_btn.isEnabled(): # Basic check
                    pass
            except RuntimeError:
                return # Dialog deleted

            try:
                progress.hide()
                status_lbl.setText("Image Captioner: Ready 🟢")
                status_lbl.setStyleSheet("color: #4a8a4a; font-size: 11px;")
                
                load_btn.hide()
                unload_btn.show()
                
                # Reset load button logic for next time
                load_btn.setEnabled(True)
                load_btn.setText("Load Model")
            except RuntimeError:
                pass # UI elements deleted
            
            cleanup_signals()

        def cleanup_signals():
            try:
                self.camera_widget.ai_service_ready.disconnect(on_success)
            except:
                pass
        
        dlg.finished.connect(cleanup_signals)

        def on_unload():
            self.camera_widget.unload_ai_service()
            try:
                status_lbl.setText("Image Captioner: Unloaded ⚪")
                status_lbl.setStyleSheet("color: #aaa; font-size: 11px;")
                unload_btn.hide()
                load_btn.show()
            except RuntimeError:
                pass

        load_btn.clicked.connect(on_load)
        unload_btn.clicked.connect(on_unload)
        
        # Position near the mouse/button
        pos = self.settings_btn.mapToGlobal(self.settings_btn.rect().bottomLeft())
        dlg.move(pos)
        
        dlg.exec()
    
    def _restore_from_mini(self):
        """Restore main window from mini bar"""
        self._restoring = True  # Prevent hideEvent from showing mini bar
        if self.mini_bar:
            self.mini_bar.hide()
        self.showNormal()
        self.activateWindow()
        self.raise_()
        # Resume video playback
        self.video_widget.resume()
        self._restoring = False
    
    def _handle_mini_message(self, message: str):
        """Handle message sent from mini bar"""
        self.chat_widget._add_bubble("User", message, True)
        # Trigger response (simplified)
        if self.mini_bar:
            self.mini_bar.set_response("Processing...")
    
    def _connect_voice_manager(self):
        """Connect voice manager signals at window level for persistent loading."""
        try:
            from infra.gui.widgets.voice_worker import get_voice_manager
            voice_manager = get_voice_manager()
            
            def on_voice_ready_persistent():
                """Show mic button when voice model loads, regardless of dialog state."""
                if hasattr(self, 'chat_widget'):
                    self.chat_widget.show_mic_button()
            
            # Connect ready signal - this persists for window lifetime
            voice_manager.ready.connect(on_voice_ready_persistent)
        except Exception:
            pass  # Voice module not available
    
    def closeEvent(self, event):
        """Show mini bar when main window is closed, don't exit"""
        self.camera_widget.stop()
        self.video_widget.stop()
        if self.mini_bar:
            self.mini_bar.show()
            self.hide()  # Hide instead of close
            event.ignore()  # Don't actually close
        else:
            event.accept()
