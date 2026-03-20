"""
Object Detection Widget - V3
Simple toggle switch at bottom corner
Smooth fade transitions for camera start/stop
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGraphicsOpacityEffect
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QProcess
from PyQt6.QtGui import QImage, QPixmap, QFont

import cv2
import numpy as np
import sys
from pathlib import Path

# MediaPipe import with fallback
HAS_MEDIAPIPE = False
mp_hands = None
mp_draw = None

try:
    import mediapipe as mp
    if hasattr(mp, 'solutions') and hasattr(mp.solutions, 'hands'):
        mp_hands = mp.solutions.hands
        mp_draw = mp.solutions.drawing_utils
        HAS_MEDIAPIPE = True
except:
    pass

# Instagram colors
PURPLE = "#833AB4"
PINK = "#E1306C"
ORANGE = "#F77737"

from infra.gui.theme import ThemeManager


class CameraInitWorker(QThread):
    """Background worker to initialize camera faster"""
    finished = pyqtSignal(object, bool)  # cap, success
    
    def __init__(self, camera_index: int):
        super().__init__()
        self.camera_index = camera_index
    
    def run(self):
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)  # DirectShow for faster init on Windows
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimal buffer for less lag
        success = cap.isOpened()
        self.finished.emit(cap, success)


class CameraFrameWorker(QThread):
    """Background worker for continuous frame capture - prevents UI blocking"""
    frame_ready = pyqtSignal(object)  # QImage
    
    def __init__(self, cap, hands=None):
        super().__init__()
        self.cap = cap
        self.hands = hands
        self.running = True
    
    def run(self):
        while self.running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                continue
            
            frame = cv2.flip(frame, 1)
            
            # Hand detection (if available)
            if self.hands:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.hands.process(rgb)
                
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        mp_draw.draw_landmarks(
                            frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                            mp_draw.DrawingSpec(color=(131, 58, 180), thickness=2),
                            mp_draw.DrawingSpec(color=(225, 48, 108), thickness=1)
                        )
            
            # Convert to QImage
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qt_image = QImage(rgb.data.tobytes(), w, h, ch * w, QImage.Format.Format_RGB888)
            
            self.frame_ready.emit(qt_image)
            self.msleep(30)  # ~33fps, prevents CPU overload
    
    def stop(self):
        self.running = False


class ObjectDetectionWidget(QWidget):
    """Camera widget with simple toggle at bottom - theme aware"""
    
    ai_service_ready = pyqtSignal()
    ai_service_error = pyqtSignal(str)
    
    def __init__(self, camera_index: int = 0):
        super().__init__()
        self.camera_index = camera_index
        self.cap = None
        self.running = False
        self.camera_on = False
        
        self._setup_ui()
        self._setup_detector()
        
        # Listen for theme changes
        ThemeManager.add_listener(self._on_theme_change)

    def load_ai_service(self):
        """Public method to manually trigger AI service loading."""
        if hasattr(self, 'caption_process') and self.caption_process.state() == QProcess.ProcessState.Running:
            self.ai_service_ready.emit()
            return
            
        self._ensure_service_running()

    def unload_ai_service(self):
        """Public method to unload AI service and free resources."""
        if hasattr(self, 'caption_process'):
            print("[Camera] Stopping BLIP Service...", file=sys.stderr)
            self.caption_process.terminate()
            self.caption_process.waitForFinished(1000)
            if self.caption_process.state() == QProcess.ProcessState.Running:
                self.caption_process.kill()
            del self.caption_process
            
        if hasattr(self, 'ai_caption_timer'):
            self.ai_caption_timer.stop()
            
        # Update UI if camera running
        if self.ai_describe_on:
            self.ai_describe_on = False
            self._update_ai_toggle_style()
            if hasattr(self, 'caption_label'):
                self.caption_label.hide()
                
        self.status.setText("● LIVE")
        self.status.setStyleSheet(f"color: {PINK}; font-size: 10px; font-family: Consolas; font-weight: bold;")

    def _on_theme_change(self, theme):
        """Refresh display when theme changes"""
        self._update_ai_toggle_style()
        if not self.camera_on:
            self._show_off_state()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        # Header row
        header = QHBoxLayout()
        title = QLabel("◆ CAMERA")
        title.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {PINK};")
        header.addWidget(title)
        header.addStretch()
        
        # AI Describe toggle - elegant small toggle
        self.ai_describe_on = False
        self.ai_toggle = QPushButton("🔮 AI")
        self.ai_toggle.setFixedSize(48, 22)
        self.ai_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ai_toggle.setToolTip("Toggle AI auto-describe (Load model first)")
        self.ai_toggle.setEnabled(False)  # Disabled until model loads and warms up
        self.ai_toggle.clicked.connect(self._toggle_ai_describe)
        self._update_ai_toggle_style()
        header.addWidget(self.ai_toggle)
        
        layout.addLayout(header)
        
        # Camera display area
        self.display = QLabel()
        self.display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.display.setMinimumSize(280, 180)
        self._show_off_state()
        layout.addWidget(self.display, stretch=1)
        
        # Bottom row with toggle
        bottom = QHBoxLayout()
        bottom.setSpacing(8)
        
        # Status text
        self.status = QLabel("Camera off")
        self.status.setStyleSheet("color: #666; font-size: 10px; font-family: Consolas;")
        bottom.addWidget(self.status)
        
        bottom.addStretch()
        
        # Simple toggle button
        self.toggle_btn = QPushButton("Start Camera")
        self.toggle_btn.setFixedHeight(28)
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.clicked.connect(self._toggle_camera)
        self._update_button_style()
        bottom.addWidget(self.toggle_btn)
        
        layout.addLayout(bottom)
    
    def _update_button_style(self):
        if self.camera_on:
            self.toggle_btn.setText("■ Stop")
            self.toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #cc3333;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 0 12px;
                    font-size: 10px;
                    font-family: Consolas;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #dd4444;
                }
            """)
        else:
            self.toggle_btn.setText("▶ Start")
            self.toggle_btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {PURPLE}, stop:1 {PINK});
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 0 12px;
                    font-size: 10px;
                    font-family: Consolas;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #9b4fc9, stop:1 #f04080);
                }}
            """)
    
    def _show_off_state(self):
        theme = ThemeManager.get_theme()
        is_dark = theme.name == "dark"
        bg_color = "#0a0a0a" if is_dark else "#F8E8E8"
        border_color = "#1a1a1a" if is_dark else "#E8D0D0"
        icon_color = "#333" if is_dark else "#999"
        
        self.display.setText("📷")
        self.display.setStyleSheet(f"""
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: 8px;
            color: {icon_color};
            font-size: 40px;
        """)
    
    def _toggle_camera(self):
        if self.camera_on:
            self._stop_camera()
        else:
            self._start_camera()
    
    def _setup_detector(self):
        if HAS_MEDIAPIPE and mp_hands:
            self.hands = mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=2,
                min_detection_confidence=0.5
            )
        else:
            self.hands = None
    
    def _start_camera(self):
        theme = ThemeManager.get_theme()
        is_dark = theme.name == "dark"
        bg_color = "#0a0a0a" if is_dark else "#F8E8E8"
        border_color = "#1a1a1a" if is_dark else "#E8D0D0"
        
        # Show loading state
        self.status.setText("● Starting...")
        self.status.setStyleSheet(f"color: {ORANGE}; font-size: 10px; font-family: Consolas;")
        self.toggle_btn.setEnabled(False)
        
        self.display.setText("⏳")
        self.display.setStyleSheet(f"""
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: 8px;
            color: #E1306C;
            font-size: 40px;
        """)
        
        # Initialize camera in background thread
        self.cam_worker = CameraInitWorker(self.camera_index)
        self.cam_worker.finished.connect(self._on_camera_ready)
        self.cam_worker.start()
    
    def _on_camera_ready(self, cap, success: bool):
        """Called when camera initialization completes"""
        self.toggle_btn.setEnabled(True)
        
        if not success:
            self.status.setText("Camera unavailable")
            self.status.setStyleSheet("color: #aa5555; font-size: 10px; font-family: Consolas;")
            self._show_off_state()
            return
        
        self.cap = cap
        self.camera_on = True
        self.running = True
        self._update_button_style()
        self.status.setText("● LIVE")
        self.status.setStyleSheet(f"color: {PINK}; font-size: 10px; font-family: Consolas; font-weight: bold;")
        
        self.display.setStyleSheet("""
            background-color: #000;
            border: 1px solid #1a1a1a;
            border-radius: 8px;
        """)
        
        # Smooth fade-in effect for camera feed
        self.display_opacity = QGraphicsOpacityEffect()
        self.display.setGraphicsEffect(self.display_opacity)
        self.display_opacity.setOpacity(0)
        
        self.fade_in_anim = QPropertyAnimation(self.display_opacity, b"opacity")
        self.fade_in_anim.setDuration(300)
        self.fade_in_anim.setStartValue(0.0)
        self.fade_in_anim.setEndValue(1.0)
        self.fade_in_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fade_in_anim.finished.connect(lambda: self.display.setGraphicsEffect(None))
        self.fade_in_anim.start()
        
        # Start background frame worker (no UI blocking!)
        self.frame_worker = CameraFrameWorker(self.cap, self.hands)
        self.frame_worker.frame_ready.connect(self._on_frame_ready)
        self.frame_worker.start()

        # If AI was enabled before camera started, kick off the loop now
        if self.ai_describe_on:
            self._ensure_service_running()
            self._capture_for_caption()
            self.status.setText("● LIVE + AI")
            self.status.setStyleSheet(f"color: {ORANGE}; font-size: 10px; font-family: Consolas; font-weight: bold;")
    
    def _on_frame_ready(self, qt_image):
        """Update display with frame from background thread"""
        if not self.running:
            return
        scaled = qt_image.scaled(
            self.display.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        self.display.setPixmap(QPixmap.fromImage(scaled))
    
    def _stop_camera(self):
        self.running = False
        self.camera_on = False
        
        # Hide caption overlay
        if hasattr(self, 'caption_label'):
            self.caption_label.hide()
        
        # Clean up temp image file
        import tempfile
        import os
        temp_path = os.path.join(tempfile.gettempdir(), "neural_citadel_cam_frame.jpg")
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                print("[Camera] Cleaned up temp file", file=sys.stderr)
            except:
                pass
        
        # Stop background frame worker
        if hasattr(self, 'frame_worker'):
            self.frame_worker.stop()
            self.frame_worker.wait(500)  # Wait up to 500ms for thread to finish
        
        # Smooth fade-out effect
        self.display_opacity = QGraphicsOpacityEffect()
        self.display.setGraphicsEffect(self.display_opacity)
        
        self.fade_out_anim = QPropertyAnimation(self.display_opacity, b"opacity")
        self.fade_out_anim.setDuration(200)
        self.fade_out_anim.setStartValue(1.0)
        self.fade_out_anim.setEndValue(0.0)
        self.fade_out_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        def on_fade_out_finished():
            self.display.setGraphicsEffect(None)
            if self.cap:
                self.cap.release()
                self.cap = None
            self._update_button_style()
            self._show_off_state()
            self.status.setText("Camera off")
            self.status.setStyleSheet("color: #666; font-size: 10px; font-family: Consolas;")
        
        self.fade_out_anim.finished.connect(on_fade_out_finished)
        self.fade_out_anim.start()
    
    def stop(self):
        self._stop_camera()
    
    def _update_ai_toggle_style(self):
        """Update AI toggle button style based on state."""
        if self.ai_describe_on:
            self.ai_toggle.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {PURPLE}, stop:0.5 {PINK}, stop:1 {ORANGE});
                    color: white;
                    border: none;
                    border-radius: 10px;
                    font-size: 9px;
                    font-weight: bold;
                }}
            """)
        else:
            theme = ThemeManager.get_theme()
            if theme.name == "light":
                # Light mode: Glassy styling (Subtle transparent gray)
                self.ai_toggle.setStyleSheet(f"""
                    QPushButton {{
                        background-color: rgba(0, 0, 0, 0.05);
                        color: #666;
                        border: 1px solid rgba(0, 0, 0, 0.1);
                        border-radius: 10px;
                        font-size: 9px;
                    }}
                    QPushButton:hover {{
                        background-color: rgba(225, 48, 108, 0.1);
                        border-color: {PINK};
                        color: {PINK};
                    }}
                """)
            else:
                # Dark mode: Premium Glassy styling (No solid black box)
                self.ai_toggle.setStyleSheet(f"""
                    QPushButton {{
                        background-color: rgba(255, 255, 255, 0.08);
                        color: #bbb;
                        border: 1px solid rgba(255, 255, 255, 0.15);
                        border-radius: 10px;
                        font-size: 9px;
                    }}
                    QPushButton:hover {{
                        background-color: rgba(131, 58, 180, 0.2);
                        border-color: {PURPLE};
                        color: white;
                    }}
                """)
    
    def _toggle_ai_describe(self):
        """Toggle AI auto-describe feature."""
        self.ai_describe_on = not self.ai_describe_on
        self._update_ai_toggle_style()
        
        if self.ai_describe_on and self.camera_on:
            # Start AI service if not running
            self._ensure_service_running()
            
            # Start loop
            self._capture_for_caption()
            
            self.status.setText("● LIVE + AI")
            self.status.setStyleSheet(f"color: {ORANGE}; font-size: 10px; font-family: Consolas; font-weight: bold;")
        else:
            if self.camera_on:
                self.status.setText("● LIVE")
                self.status.setStyleSheet(f"color: {PINK}; font-size: 10px; font-family: Consolas; font-weight: bold;")
            
            # Clear any caption overlay
            if hasattr(self, 'caption_label'):
                self.caption_label.hide()


    def _ensure_service_running(self):
        """Start the persistent BLIP service if needed."""
        from PyQt6.QtCore import QProcess
        import sys
        
        # Get paths
        PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
        sys.path.insert(0, str(PROJECT_ROOT))
        from configs.paths import IMAGE_CAPTIONER_PYTHON
        
        if not hasattr(self, 'caption_process') or self.caption_process.state() == QProcess.ProcessState.NotRunning:
            print("[Camera] Starting BLIP Service...", file=sys.stderr)
            self.caption_process = QProcess()
            self.caption_process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
            self.caption_process.readyReadStandardOutput.connect(self._on_caption_ready)
            
            runner_path = PROJECT_ROOT / "apps" / "image_captioner" / "runner.py"
            
            # Start in service mode
            self.caption_process.start(str(IMAGE_CAPTIONER_PYTHON), [str(runner_path), "--service"])

    def _capture_for_caption(self):
        """Capture current frame and send to service."""
        print(f"[DEBUG] _capture_for_caption called: camera_on={self.camera_on}, ai_on={self.ai_describe_on}, cap={self.cap is not None}", file=sys.stderr)
        
        if not self.camera_on or not self.ai_describe_on or not self.cap:
            print("[DEBUG] Early return - conditions not met", file=sys.stderr)
            return
        
        # Check if process is running
        if not hasattr(self, 'caption_process'):
            print("[DEBUG] No caption_process, starting service", file=sys.stderr)
            self._ensure_service_running()
            return
            
        state = self.caption_process.state()
        print(f"[DEBUG] Process state: {state}", file=sys.stderr)
        
        if state != QProcess.ProcessState.Running:
            print("[DEBUG] Process not running, ensuring service", file=sys.stderr)
            self._ensure_service_running()
            return

        # Capture current frame
        ret, frame = self.cap.read()
        if not ret:
            print("[DEBUG] Failed to read frame", file=sys.stderr)
            return
        
        # Save to temp file (overwrite same file to save space)
        import tempfile
        import os
        temp_path = os.path.join(tempfile.gettempdir(), "neural_citadel_cam_frame.jpg")
        
        # Ensure write completes
        success = cv2.imwrite(temp_path, frame)
        if not success:
            print("[DEBUG] Failed to write image to temp", file=sys.stderr)
            return
            
        # Verify file exists and has size
        if not os.path.exists(temp_path) or os.path.getsize(temp_path) < 100:
            print(f"[DEBUG] Image file invalid: exists={os.path.exists(temp_path)}, size={os.path.getsize(temp_path) if os.path.exists(temp_path) else 0}", file=sys.stderr)
            return
            
        print(f"[DEBUG] Saved frame to {temp_path} ({os.path.getsize(temp_path)} bytes)", file=sys.stderr)
        
        # Send path to service
        cmd = f"{temp_path}\n"
        bytes_written = self.caption_process.write(cmd.encode())
        print(f"[DEBUG] Wrote {bytes_written} bytes to service", file=sys.stderr)
        
        # Show "Scanning..." feedback
        if not hasattr(self, 'caption_label'):
            self._show_caption_overlay("Scanning scene...")
        else:
            current = self.caption_label.text()
            if not current or "AI Ready" in current or "Unloaded" in current or "Scanning" in current:
                self._show_caption_overlay("Scanning scene...")
            elif " ⟳" not in current:
                # Add subtle refresh indicator to existing caption
                self.caption_label.setText(current + " ⟳")

    def _on_caption_ready(self):
        """Handle output from service."""
        if hasattr(self, 'caption_process'):
            # Read all available lines
            while self.caption_process.canReadLine():
                output = self.caption_process.readLine().data().decode().strip()
                
                if not output:
                    continue
                
                # Filter out logs
                if output == "READY":
                    print("[Camera] BLIP Service READY")
                    self.ai_service_ready.emit()
                    
                    # Start 10s warmup countdown
                    self.warmup_seconds = 10
                    self.status.setText(f"● Warming up ({self.warmup_seconds}s)...")
                    self.status.setStyleSheet(f"color: {ORANGE}; font-size: 10px; font-family: Consolas;")
                    
                    self.warmup_timer = QTimer(self)
                    self.warmup_timer.timeout.connect(self._update_warmup)
                    self.warmup_timer.start(1000)
                    continue
                    
                if output.startswith("[BLIP]") or output.startswith("Error"):
                    print(f"SERVICE LOG: {output}")
                    continue
                
                # Valid caption has CAPTION: prefix
                if output.startswith("CAPTION:"):
                    caption_text = output[8:]  # Remove "CAPTION:" prefix
                    print(f"[Camera] Caption: {caption_text}")
                    self._show_caption_overlay(caption_text)
                    
                    # Continuous loop: trigger next capture
                    if self.ai_describe_on:
                        QTimer.singleShot(100, self._capture_for_caption)
                else:
                    # Unknown output, log it
                    print(f"SERVICE OUTPUT: {output}")

    def _update_warmup(self):
        """Update warmup countdown."""
        self.warmup_seconds -= 1
        if self.warmup_seconds > 0:
            self.status.setText(f"● Warming up ({self.warmup_seconds}s)...")
        else:
            # Warmup done
            self.warmup_timer.stop()
            self.status.setText("● AI READY")
            self.status.setStyleSheet(f"color: {PINK}; font-size: 10px; font-family: Consolas; font-weight: bold;")
            
            # Enable AI toggle
            self.ai_toggle.setEnabled(True)
            self.ai_toggle.setToolTip("Toggle AI auto-describe")
            
            # If AI was somehow already enabled (re-load case), kickstart
            if self.ai_describe_on:
                self._show_caption_overlay("AI Ready...")
                self._capture_for_caption()
    
    def _show_caption_overlay(self, caption: str):
        """Show caption as overlay on camera feed."""
        theme = ThemeManager.get_theme()
        is_dark = theme.name == "dark"
        
        if not hasattr(self, 'caption_label'):
            # Parent to self (the main widget) to ensure it floats on top
            self.caption_label = QLabel(self)
            self.caption_label.setObjectName("CaptionLabel")
            self.caption_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # Add shadow effect
            from PyQt6.QtWidgets import QGraphicsDropShadowEffect
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(10)
            shadow.setColor(Qt.GlobalColor.black)
            shadow.setOffset(0, 2)
            self.caption_label.setGraphicsEffect(shadow)
        
        # Truncate if too long
        if len(caption) > 80:
            caption = caption[:77] + "..."
        
        # Dynamic sizing - single line for short text, wrap for long
        short_text = len(caption) < 40
        
        if short_text:
            self.caption_label.setWordWrap(False)
            self.caption_label.setMaximumWidth(400)
        else:
            self.caption_label.setWordWrap(True)
            self.caption_label.setMaximumWidth(280)
        
        # Theme-aware styling
        if is_dark:
            # Dark mode - Instagram dark gradient
            self.caption_label.setStyleSheet(f"""
                QLabel#CaptionLabel {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(30, 20, 40, 0.95),
                        stop:0.5 rgba(40, 20, 35, 0.95),
                        stop:1 rgba(35, 25, 30, 0.95));
                    color: #fff;
                    border: 1px solid {PINK};
                    border-radius: 12px;
                    padding: 6px 16px;
                    font-family: 'Segoe UI', sans-serif;
                    font-size: 11px;
                    font-weight: bold;
                }}
            """)
        else:
            # Light mode - light blue + pink gradient
            self.caption_label.setStyleSheet("""
                QLabel#CaptionLabel {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(230, 240, 255, 0.95),
                        stop:1 rgba(255, 230, 240, 0.95));
                    color: #3a3040;
                    border: 1px solid rgba(180, 150, 200, 0.5);
                    border-radius: 12px;
                    padding: 6px 16px;
                    font-family: 'Segoe UI', sans-serif;
                    font-size: 11px;
                    font-weight: bold;
                }
            """)
        
        self.caption_label.setText(f"✨ {caption}")
        self.caption_label.adjustSize()
        
        # Calculate position relative to the display widget
        display_geo = self.display.geometry()
        
        # Center horizontally relative to display
        x = display_geo.x() + (display_geo.width() - self.caption_label.width()) // 2
        
        # Position at bottom of display with padding
        y = display_geo.y() + display_geo.height() - self.caption_label.height() - 12
        
        self.caption_label.move(x, y)
        self.caption_label.show()
        self.caption_label.raise_()

    def closeEvent(self, event):
        """Ensure threads and subprocesses are killed."""
        self.stop()
        self.unload_ai_service()
        super().closeEvent(event)
