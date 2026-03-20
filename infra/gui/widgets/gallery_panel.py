"""
Gallery Panel
=============

A centralized media hub for accessing generated and downloaded content.
Features:
- Tabs for Categories (Downloaded, Generated, Songs, QR Codes)
- Grid View with Thumbnails
- In-App Large Preview (Overlay)
- Selection Mode for Bulk Actions
"""

import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QFrame, QStackedWidget,
    QMenu, QMessageBox, QAbstractItemView, QGraphicsOpacityEffect,
    QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QThread, QUrl
from PyQt6.QtGui import QIcon, QPixmap, QAction, QCursor, QDesktopServices, QColor
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

from infra.gui.theme import ThemeManager

# Constants
THUMB_SIZE = QSize(160, 120)
ICON_SIZE = QSize(48, 48)

class GalleryItem(QListWidgetItem):
    """Custom Item for Gallery Grid"""
    def __init__(self, path, icon, name, category):
        super().__init__()
        self.file_path = path
        self.category = category
        self.setText(name)
        self.setIcon(icon)
        self.setSizeHint(QSize(180, 160))
        self.setToolTip(path)

# === WORKER THREAD FOR SCANNING ===

# === WORKER THREAD FOR SCANNING ===

class FileWorker(QThread):
    """Async worker to scan directories and generate thumbnails."""
    batch_ready = pyqtSignal(list) # list of tuples: (path, name, category, QImage/None)

    def __init__(self, category: str):
        super().__init__()
        self.category = category
        self.root = Path(__file__).resolve().parents[3] / "assets"
        self._is_running = True

    def run(self):
        target_dir = None
        extensions = []
        
        if self.category == "Generated":
            target_dir = self.root / "generated" / "images"
            extensions = [".png", ".jpg", ".jpeg"]
        elif self.category == "Downloaded":
            target_dir = self.root / "downloaded"
            extensions = [".mp4", ".mkv", ".avi", ".mov"]
        elif self.category == "Songs":
            target_dir = self.root / "downloaded" / "songs"
            extensions = [".mp3", ".wav", ".aac", ".flac"]
        elif self.category == "Newspaper":
            target_dir = self.root / "generated" / "newspaper"
            extensions = [".pdf"]
        elif self.category == "Docs":
            target_dir = self.root / "generated" / "docs"
            extensions = [".pdf"]
        elif self.category == "QR Codes":
            target_dir = self.root / "qr_code"
            extensions = [".svg", ".png"]

        # Auto-create if missing
        if target_dir and not target_dir.exists():
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"[Gallery] Failed to create {target_dir}: {e}")
                return

        if not target_dir or not target_dir.exists():
            return

        from PyQt6.QtGui import QImage, QImageReader

        buffer = []
        BATCH_SIZE = 10
        
        # Recursive scan
        for path in target_dir.rglob("*"):
            if not self._is_running: break
            
            suffix = path.suffix.lower()
            if suffix in extensions:
                thumb_image = None
                
                # Generate thumbnail in thread (CPU bound, but keeps main thread valid)
                if suffix in [".png", ".jpg", ".jpeg"]:
                    reader = QImageReader(str(path))
                    # Read scaled directly to save memory
                    reader.setScaledSize(THUMB_SIZE) 
                    thumb_image = reader.read()
                elif suffix in [".mp4", ".mkv", ".avi", ".mov"]:
                    # Generate video thumbnail using OpenCV
                    thumb_image = self._generate_video_thumbnail(str(path))
                elif suffix == ".pdf":
                    # Generate PDF thumbnail using PyMuPDF
                    thumb_image = self._generate_pdf_thumbnail(str(path))
                
                buffer.append((str(path), path.name, self.category, thumb_image))
                
                if len(buffer) >= BATCH_SIZE:
                    self.batch_ready.emit(buffer)
                    buffer = []
                    self.msleep(10) # Yield slightly
        
        # Flush remaining
        if buffer:
            self.batch_ready.emit(buffer)
    
    def _generate_video_thumbnail(self, video_path: str):
        """Generate a thumbnail from a video file using OpenCV."""
        try:
            import cv2
            from PyQt6.QtGui import QImage
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return None
            
            # Get total frames and seek to 10% into the video for a better thumbnail
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            target_frame = max(1, total_frames // 10)
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            
            ret, frame = cap.read()
            cap.release()
            
            if not ret or frame is None:
                return None
            
            # Resize to thumbnail size
            h, w = frame.shape[:2]
            target_w, target_h = THUMB_SIZE.width(), THUMB_SIZE.height()
            
            # Calculate aspect ratio preserving resize
            scale = min(target_w / w, target_h / h)
            new_w, new_h = int(w * scale), int(h * scale)
            
            frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
            
            # Convert BGR to RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Create QImage
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            
            return qimg.copy()  # Copy to detach from numpy memory
            
        except Exception as e:
            print(f"[Gallery] Video thumbnail error: {e}")
            return None
    
    def _generate_pdf_thumbnail(self, pdf_path: str):
        """Generate a thumbnail from the first page of a PDF using PyMuPDF."""
        try:
            import fitz  # PyMuPDF
            from PyQt6.QtGui import QImage
            
            doc = fitz.open(pdf_path)
            if len(doc) == 0:
                doc.close()
                return None
            
            # Get first page
            page = doc[0]
            
            # Render at a reasonable resolution for thumbnail
            zoom = 0.5  # 50% of original size
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            doc.close()
            
            # Convert to QImage
            if pix.alpha:
                qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGBA8888)
            else:
                qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
            
            # Scale to thumbnail size
            scaled = qimg.scaled(
                THUMB_SIZE.width(), THUMB_SIZE.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            return scaled.copy()
            
        except Exception as e:
            print(f"[Gallery] PDF thumbnail error: {e}")
            return None

    def stop(self):
        self._is_running = False
        self.wait()



# === PHOTO VIEWER FOR ZOOM/PAN ===
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QFrame
from PyQt6.QtGui import QPainter

class PhotoViewer(QGraphicsView):
    clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._pixmap_item = QGraphicsPixmapItem()
        self._scene.addItem(self._pixmap_item)
        
        # High Quality Rendering Hints
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing, False)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setBackgroundBrush(QColor(0, 0, 0, 255))
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus) 
        
        self._is_zoomed = False
        self._full_pixmap = None
        self._fit_pixmap = None
        
    def set_image(self, pixmap):
        self._full_pixmap = pixmap
        
        # Generate high-quality downscaled version to eliminate grains in fit mode
        view_size = self.viewport().size()
        if view_size.isEmpty(): 
            view_size = QSize(1280, 720) # Reasonable fallback
            
        self._fit_pixmap = pixmap.scaled(
            view_size, 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        
        self._pixmap_item.setPixmap(self._fit_pixmap)
        self._pixmap_item.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
        self.fitInView(self._pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
        self.setSceneRect(self._pixmap_item.boundingRect())
        self._is_zoomed = False

    def resizeEvent(self, event):
        if not self._is_zoomed and self._fit_pixmap:
             self.fitInView(self._pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
        super().resizeEvent(event)

    def wheelEvent(self, event):
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse) 
        if not self._is_zoomed:
             if self._full_pixmap: # Safety Check
                 self._pixmap_item.setPixmap(self._full_pixmap)
                 self.setSceneRect(self._pixmap_item.boundingRect()) 
                 self._is_zoomed = True
             
        if event.angleDelta().y() > 0:
            # Zoom In
            factor = 1.15
            self.scale(factor, factor)
        else:
            # Zoom Out
            factor = 0.85
            self.scale(factor, factor)
            
            # Check if we zoomed out too far (image fits in view)
            # If the view rect contains the item rect, snap back to 'Fit' mode
            view_rect = self.mapToScene(self.viewport().rect()).boundingRect()
            item_rect = self._pixmap_item.boundingRect()
            
            if view_rect.contains(item_rect):
                self._pixmap_item.setPixmap(self._fit_pixmap)
                self.fitInView(self._pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
                self.setSceneRect(self._pixmap_item.boundingRect())
                self._is_zoomed = False

        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor) 

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self._is_zoomed:
            # Zoom Out (Fit)
            self._pixmap_item.setPixmap(self._fit_pixmap)
            self.fitInView(self._pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
            self.setSceneRect(self._pixmap_item.boundingRect())
            self._is_zoomed = False
        else:
            # Zoom In
            # 1. Capture RELATIVE click position (0-1) on the 'Fit' image
            click_scene_pos = self.mapToScene(event.position().toPoint())
            fit_width = self._fit_pixmap.width()
            fit_height = self._fit_pixmap.height()
            
            if fit_width > 0 and fit_height > 0:
                rel_x = click_scene_pos.x() / fit_width
                rel_y = click_scene_pos.y() / fit_height
            else:
                rel_x, rel_y = 0.5, 0.5
            
            # 2. Swap to Full Res
            if not self._full_pixmap: return # Safety Check
            
            self._pixmap_item.setPixmap(self._full_pixmap)
            self._pixmap_item.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
            self.setSceneRect(self._pixmap_item.boundingRect()) # Critical: Allow scrolling full image
            
            # 3. Apply Zoom Scale (0.5 = 50% Native)
            self.resetTransform()
            self.scale(0.5, 0.5) 
            
            # 4. Center on the SAME relative point in the 'Full' image
            full_width = self._full_pixmap.width()
            full_height = self._full_pixmap.height()
            
            target_x = full_width * rel_x
            target_y = full_height * rel_y
            
            self.centerOn(target_x, target_y)
            self._is_zoomed = True


class GalleryPanel(QWidget):
    """
    Main Gallery Widget.
    """
    back_to_chat_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus) # Essential for keyboard events
        self.current_category = "Generated"
        self.selection_mode = False
        self.worker = None
        self.marked_for_delete = set()  # Track items marked for deletion in preview mode
        
        self._setup_ui()
        self._connect_signals()
        
        # Initial Load
        self._refresh_gallery()
    
    def showEvent(self, event):
        """Ensure focus when shown to enable keyboard nav"""
        super().showEvent(event)
        self.grid_list.setFocus()

    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # === 1. Header ===
        self.header = QFrame()
        self.header_layout = QHBoxLayout(self.header)
        # Increase bottom padding to prevent "underline" look (was 15)
        self.header_layout.setContentsMargins(20, 15, 20, 25) 
        
        # Back Button
        self.back_btn = QPushButton("◀ Back")
        self.back_btn.setFixedSize(80, 32)
        self.back_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.back_btn.clicked.connect(self.back_to_chat_requested.emit)
        self.header_layout.addWidget(self.back_btn)

        # Title
        self.title_label = QLabel("Gallery")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold; font-family: 'Segoe UI';")
        self.header_layout.addWidget(self.title_label)
        
        self.header_layout.addStretch()

        # Selection Toggle
        self.select_btn = QPushButton("Select")
        self.select_btn.setCheckable(True)
        self.select_btn.setFixedSize(80, 32)
        self.select_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.select_btn.clicked.connect(self._toggle_selection_mode)
        self.header_layout.addWidget(self.select_btn)
        
        # Bulk Actions (Hidden by default)
        self.bulk_actions = QFrame()
        bulk_layout = QHBoxLayout(self.bulk_actions)
        bulk_layout.setContentsMargins(0, 0, 0, 0)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setStyleSheet("background-color: #d32f2f; color: white; border-radius: 4px;")
        self.delete_btn.setFixedSize(80, 32)
        self.delete_btn.clicked.connect(self._delete_selected)
        bulk_layout.addWidget(self.delete_btn)
        
        self.share_btn = QPushButton("Share")
        self.share_btn.setFixedSize(80, 32)
        self.share_btn.clicked.connect(self._share_selected)
        bulk_layout.addWidget(self.share_btn)
        
        self.bulk_actions.hide()
        self.header_layout.addWidget(self.bulk_actions)

        self.layout.addWidget(self.header)
        


        # === 2. Categories Tabs ===
        self.tabs_container = QFrame()
        self.tabs_layout = QHBoxLayout(self.tabs_container)
        self.tabs_layout.setContentsMargins(20, 0, 20, 10)
        self.tabs_layout.setSpacing(10)

        self.categories = ["Generated", "Downloaded", "Songs", "Newspaper", "Docs", "QR Codes"]
        self.cat_buttons = {}
        
        for cat in self.categories:
            btn = QPushButton(cat)
            btn.setCheckable(True)
            btn.setFixedSize(100, 32)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.clicked.connect(lambda checked, c=cat: self._switch_category(c))
            self.tabs_layout.addWidget(btn)
            self.cat_buttons[cat] = btn
        
        self.tabs_layout.addStretch()
        self.layout.addWidget(self.tabs_container)

        # === 3. Content Area (Stacked: Grid vs Preview) ===
        self.stack = QStackedWidget()
        
        # View 1: Grid
        self.grid_list = QListWidget()
        self.grid_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.grid_list.setIconSize(THUMB_SIZE)
        self.grid_list.setSpacing(15)
        self.grid_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.grid_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.grid_list.itemClicked.connect(self._on_item_clicked)
        
        # Performance Optimizations
        self.grid_list.setUniformItemSizes(True) # Critical for layout speed
        self.grid_list.setLayoutMode(QListWidget.LayoutMode.Batched) # Layout in batches
        self.grid_list.setBatchSize(100)
        self.grid_list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel) # Smoother scroll
        
        # Style for ListWidget
        self.grid_list.setStyleSheet("""
            QListWidget { background: transparent; border: none; }
            QListWidget::item { 
                background: rgba(255,255,255,0.05); 
                border-radius: 8px; 
                padding: 10px;
                color: #ddd;
            }
            QListWidget::item:selected {
                background: rgba(225, 48, 108, 0.2);
                border: 1px solid #E1306C;
            }
            QListWidget::item:hover {
                background: rgba(255,255,255,0.1);
            }
        """)
        self.stack.addWidget(self.grid_list)
        
        # View 2: Preview Overlay
        self.preview_widget = QWidget()
        preview_layout = QVBoxLayout(self.preview_widget)
        
        # Preview Header
        prev_head = QHBoxLayout()
        self.close_preview_btn = QPushButton("✕ Close")
        self.close_preview_btn.setFixedSize(80, 32)
        self.close_preview_btn.clicked.connect(self._close_preview)
        prev_head.addWidget(self.close_preview_btn)
        
        prev_head.addStretch()
        
        # Checkbox in a rounded container frame
        from PyQt6.QtWidgets import QCheckBox
        self.checkbox_container = QFrame()
        self.checkbox_container.setObjectName("checkboxContainer")
        checkbox_layout = QHBoxLayout(self.checkbox_container)
        checkbox_layout.setContentsMargins(12, 0, 12, 0)
        checkbox_layout.setSpacing(8)
        
        self.preview_checkbox = QCheckBox("Mark for Delete")
        self.preview_checkbox.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.preview_checkbox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.preview_checkbox.stateChanged.connect(self._on_preview_checkbox_changed)
        checkbox_layout.addWidget(self.preview_checkbox)
        
        self.checkbox_container.setFixedHeight(32)
        prev_head.addWidget(self.checkbox_container)
        
        self.preview_delete_btn = QPushButton("Delete Marked")
        self.preview_delete_btn.setFixedSize(110, 32)
        self.preview_delete_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.preview_delete_btn.clicked.connect(self._delete_marked_items)
        self.preview_delete_btn.hide()  # Show only when items are marked
        prev_head.addWidget(self.preview_delete_btn)
        
        preview_layout.addLayout(prev_head)
        
        # Content Row (Prev Btn - Media - Next Btn)
        content_row = QHBoxLayout()
        content_row.setSpacing(20)
        
        # Previous Button
        self.prev_btn = QPushButton("❮")
        self.prev_btn.setFixedSize(50, 50)
        self.prev_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.prev_btn.clicked.connect(lambda: self._navigate_image(-1))
        content_row.addWidget(self.prev_btn)
        
        # Media Container (Stack for Video vs Image)
        self.media_stack = QStackedWidget()
        self.media_stack.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        
        # Image Viewer
        self.image_preview = PhotoViewer()
        self.image_preview.clicked.connect(self.setFocus) # Restore focus on click
        self.media_stack.addWidget(self.image_preview)
        
        # Video Player
        self.video_widget = QVideoWidget()
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_stack.addWidget(self.video_widget)
        
        content_row.addWidget(self.media_stack, stretch=1)
        
        # Next Button
        self.next_btn = QPushButton("❯")
        self.next_btn.setFixedSize(50, 50)
        self.next_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.next_btn.clicked.connect(lambda: self._navigate_image(1))
        content_row.addWidget(self.next_btn)
        
        preview_layout.addLayout(content_row, stretch=1)
        
        # Playback Controls (Only for video/audio)
        self.controls_widget = QWidget()
        controls_layout = QHBoxLayout(self.controls_widget)
        
        self.play_btn = QPushButton("⏯")
        self.play_btn.setFixedSize(40, 40)
        self.play_btn.clicked.connect(self._toggle_playback)
        controls_layout.addWidget(self.play_btn)
        
        controls_layout.addStretch()
        preview_layout.addWidget(self.controls_widget)
        self.controls_widget.hide()
        
        self.stack.addWidget(self.preview_widget)
        
        self.layout.addWidget(self.stack)

        self._update_theme()
    
    def keyPressEvent(self, event):
        """Handle arrow keys for navigation"""
        if self.stack.currentIndex() == 1: # In preview mode
            if event.key() == Qt.Key.Key_Left:
                self._navigate_image(-1)
                event.accept()
            elif event.key() == Qt.Key.Key_Right:
                self._navigate_image(1)
                event.accept()
            elif event.key() == Qt.Key.Key_Escape:
                self._close_preview()
                event.accept()
        super().keyPressEvent(event)

    def _update_theme(self, theme=None):
        if theme is None:
            theme = ThemeManager.get_theme()
        is_dark = theme.name == "dark"
        
        bg = "#121212" if is_dark else "#f5f5f7"
        text = "#ffffff" if is_dark else "#000000"
        btn_bg = "rgba(255,255,255,0.1)" if is_dark else "#e0e0e0"
        
        self.setStyleSheet(f"background-color: {bg}; color: {text};")
        

        
        btn_style = f"""
            QPushButton {{
                background-color: {btn_bg};
                border: none;
                border-radius: 16px;
                padding: 4px;
            }}
            QPushButton:checked {{
                background-color: #E1306C;
                color: white;
            }}
            QPushButton:hover {{
                background-color: rgba(225, 48, 108, 0.3);
            }}
        """
        
        nav_style = f"""
            QPushButton {{
                background-color: rgba(0, 0, 0, 0.3);
                color: white;
                border-radius: 25px;
                font-size: 24px;
                font-family: Arial;
            }}
            QPushButton:hover {{
                background-color: rgba(225, 48, 108, 0.6);
            }}
        """
        
        # Scrollbar Styling
        # Merged Premium Stylesheet (List + Scrollbar)
        
        # List Item Styling (Better contrast)
        item_text = "#eeeeee" if is_dark else "#111111"
        item_bg = "rgba(255,255,255,0.05)" if is_dark else "rgba(0,0,0,0.05)"
        item_hover = "rgba(255,255,255,0.1)" if is_dark else "rgba(0,0,0,0.1)"
        
        self.grid_list.setStyleSheet(f"""
            QListWidget {{ 
                background: transparent; 
                border: none; 
                outline: none; 
            }}
            QListWidget::item {{ 
                background: {item_bg}; 
                border-radius: 8px; 
                padding: 10px;
                color: {item_text};
                font-size: 11px;
            }}
            QListWidget::item:selected {{
                background: rgba(225, 48, 108, 0.2);
                border: 1px solid #E1306C;
                color: {item_text};
            }}
            QListWidget::item:hover {{
                background: {item_hover};
            }}
            
            /* Sleek, Premium Scrollbar */
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                margin: 0px 0px 0px 0px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(120, 120, 120, 0.3); /* Subtle handle */
                min-height: 20px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgba(120, 120, 120, 0.5);
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px; /* Hide arrows */
                background: none;
                border: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none; /* Transparent track */
            }}
        """)
        
        for btn in self.cat_buttons.values():
            btn.setStyleSheet(btn_style)
            
        self.back_btn.setStyleSheet(btn_style)
        self.select_btn.setStyleSheet(btn_style)
        self.close_preview_btn.setStyleSheet(btn_style)
        self.play_btn.setStyleSheet(btn_style)
        
        # Red delete button style
        delete_style = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #d32f2f, stop:1 #ff5252);
                color: white;
                border: none;
                border-radius: 16px;
                font-family: Consolas;
                font-size: 11px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff5252, stop:1 #ff8a80);
            }
        """
        self.preview_delete_btn.setStyleSheet(delete_style)
        
        # Checkbox container styling - rounded corners on the frame
        if is_dark:
            cb_text = "#aaaaaa"
            cb_bg = "rgba(255, 255, 255, 0.05)"
            cb_bg_hover = "rgba(255, 255, 255, 0.1)"
            indicator_bg = "rgba(255, 255, 255, 0.15)"
            indicator_checked = "#E1306C"
        else:
            cb_text = "#555555"
            cb_bg = "rgba(0, 0, 0, 0.05)"
            cb_bg_hover = "rgba(0, 0, 0, 0.08)"
            indicator_bg = "rgba(0, 0, 0, 0.1)"
            indicator_checked = "#E1306C"
        
        # Style the container frame for rounded corners
        self.checkbox_container.setStyleSheet(f"""
            #checkboxContainer {{
                background: {cb_bg};
                border: none;
                border-radius: 16px;
            }}
            #checkboxContainer:hover {{
                background: {cb_bg_hover};
            }}
        """)
        
        # Style the checkbox inside
        checkbox_style = f"""
            QCheckBox {{
                color: {cb_text};
                font-family: Consolas;
                font-size: 12px;
                spacing: 6px;
                background: transparent;
            }}
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
                border-radius: 3px;
                border: none;
                background: {indicator_bg};
            }}
            QCheckBox::indicator:checked {{
                background: {indicator_checked};
            }}
        """
        self.preview_checkbox.setStyleSheet(checkbox_style)
        
        self.prev_btn.setStyleSheet(nav_style)
        self.next_btn.setStyleSheet(nav_style)
        
        # Initial Category Highlight
        if self.current_category in self.cat_buttons:
            self.cat_buttons[self.current_category].setChecked(True)

    def _connect_signals(self):
        ThemeManager.add_listener(self._update_theme)

    def _switch_category(self, category):
        if self.worker:
            self.worker.stop()
            self.worker.deleteLater()
            self.worker = None

        self.current_category = category
        for name, btn in self.cat_buttons.items():
            btn.setChecked(name == category)
            
        self._refresh_gallery()

    def _refresh_gallery(self):
        self.grid_list.clear() # Clear existing
        
        # Start Worker
        self.worker = FileWorker(self.current_category)
        self.worker.batch_ready.connect(self._add_item_batch)
        self.worker.start()

    def _add_item_batch(self, items):
        """Add a batch of items to the list widget."""
        # Fix Race Condition: Check if batch belongs to current category
        if not items or items[0][2] != self.current_category:
            return

        # Stop updates for massive speedup
        self.grid_list.setUpdatesEnabled(False)
        
        for path_str, name, category, thumb_image in items:
            icon = QIcon()
            
            if thumb_image:
                # Convert QImage to QPixmap -> QIcon (fast in memory)
                icon = QIcon(QPixmap.fromImage(thumb_image))
            else:
                # Fallback for non-images
                suffix = Path(path_str).suffix.lower()
                if suffix == ".svg":
                    icon = QIcon(path_str) # SVG renders fast
                elif suffix in [".mp3", ".wav", ".flac"]:
                    # TODO: Use generic icon
                    pass
                elif suffix in [".mp4", ".mkv"]:
                    # TODO: Use generic icon
                    pass
            
            # Create item
            item = GalleryItem(path_str, icon, name, category)
            self.grid_list.addItem(item)
            
        self.grid_list.setUpdatesEnabled(True)


    def _toggle_selection_mode(self):
        self.selection_mode = self.select_btn.isChecked()
        if self.selection_mode:
            self.grid_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
            self.bulk_actions.show()
            self.select_btn.setText("Cancel")
        else:
            self.grid_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
            self.grid_list.clearSelection()
            self.bulk_actions.hide()
            self.select_btn.setText("Select")

    def _on_item_clicked(self, item):
        if self.selection_mode:
            return # Let default selection handle it
        
        # Standard Mode: Open Preview
        self._open_preview(item)

    def _open_preview(self, item):
        path = item.file_path
        suffix = Path(path).suffix.lower()
        
        # FIX: Open PDFs externally instead of in-app preview
        if suffix == ".pdf":
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
            return

        self.current_preview_row = self.grid_list.row(item)
        self.stack.setCurrentIndex(1)
        
        # Sync checkbox with marked state
        self.preview_checkbox.blockSignals(True)
        self.preview_checkbox.setChecked(path in self.marked_for_delete)
        self.preview_checkbox.blockSignals(False)
        
        if suffix in [".png", ".jpg", ".jpeg", ".svg"]:
            # Image Mode
            pixmap = QPixmap(path)
            # Fix: Use set_image for PhotoViewer, not setPixmap
            self.image_preview.set_image(pixmap) 
            self.media_stack.setCurrentIndex(0)
            self.controls_widget.hide()
            
        elif suffix in [".mp4", ".mkv", ".avi", ".mov", ".mp3", ".wav", ".flac"]:
            # Video/Audio Mode
            self.media_player.setSource(QUrl.fromLocalFile(path))
            self.media_stack.setCurrentIndex(1)
            self.controls_widget.show()
            self.media_player.play()
            
        self.setFocus() # Ensure GalleryPanel gets key events

    def _close_preview(self):
        self.media_player.stop()
        self.stack.setCurrentIndex(0)

    def _toggle_playback(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def _navigate_image(self, delta):
        """Navigate to next/previous image in the grid"""
        if not hasattr(self, 'current_preview_row') or self.current_preview_row is None:
            return
            
        count = self.grid_list.count()
        new_row = self.current_preview_row + delta
        
        if 0 <= new_row < count:
            item = self.grid_list.item(new_row)
            self._open_preview(item)
        else:
            # Reached end/start
            pass

    def _show_styled_confirm(self, title: str, message: str) -> bool:
        """Show a styled confirmation dialog matching the app theme."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
        
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        dialog.setFixedSize(340, 180)
        
        # Main container with rounded edges
        container = QFrame(dialog)
        container.setGeometry(0, 0, 340, 180)
        container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a3e, stop:0.5 #2d1b4e, stop:1 #1e3a5f);
                border: 2px solid #E1306C;
                border-radius: 20px;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(15)
        
        # Message label directly (no nested frame to avoid styling issues)
        msg_label = QLabel(f"🗑️ {message}")
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg_label.setMinimumHeight(50)
        msg_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-family: Consolas;
                font-size: 14px;
                background: rgba(0, 0, 0, 0.4);
                border-radius: 10px;
                padding: 15px;
            }
        """)
        layout.addWidget(msg_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(100, 40)
        cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid #666;
                border-radius: 20px;
                font-family: Consolas;
                font-size: 12px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
                border: 1px solid #888;
            }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        delete_btn = QPushButton("🗑 Delete")
        delete_btn.setFixedSize(100, 40)
        delete_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        delete_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #d32f2f, stop:1 #ff5252);
                color: white;
                border: none;
                border-radius: 20px;
                font-family: Consolas;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff5252, stop:1 #ff8a80);
            }
        """)
        delete_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(delete_btn)
        
        layout.addLayout(btn_layout)
        
        return dialog.exec() == QDialog.DialogCode.Accepted

    def _on_preview_checkbox_changed(self, state):
        """Handle checkbox state change for marking items for deletion."""
        if not hasattr(self, 'current_preview_row') or self.current_preview_row is None:
            return
            
        item = self.grid_list.item(self.current_preview_row)
        if not item:
            return
        
        # state is Qt.CheckState enum value (0=unchecked, 2=checked)
        is_checked = state == 2
        
        # Update checkbox text based on state
        if is_checked:
            self.preview_checkbox.setText("Marked")
            self.marked_for_delete.add(item.file_path)
        else:
            self.preview_checkbox.setText("Mark for Delete")
            self.marked_for_delete.discard(item.file_path)
        
        # Show/hide delete button based on marked count
        if self.marked_for_delete:
            self.preview_delete_btn.setText(f"Delete ({len(self.marked_for_delete)})")
            self.preview_delete_btn.show()
        else:
            self.preview_delete_btn.hide()
    
    def _delete_marked_items(self):
        """Delete all items marked for deletion."""
        if not self.marked_for_delete:
            return
            
        count = len(self.marked_for_delete)
        if self._show_styled_confirm("Delete Files", f"Delete {count} marked item{'s' if count > 1 else ''}?"):
            deleted = 0
            for path in list(self.marked_for_delete):
                try:
                    os.remove(path)
                    # Find and remove from grid
                    for i in range(self.grid_list.count()):
                        item = self.grid_list.item(i)
                        if item and item.file_path == path:
                            self.grid_list.takeItem(i)
                            break
                    deleted += 1
                except Exception as e:
                    print(f"[Gallery] Failed to delete {path}: {e}")
            
            print(f"[Gallery] Deleted {deleted}/{count} marked files")
            self.marked_for_delete.clear()
            self.preview_delete_btn.hide()
            self.preview_checkbox.setChecked(False)
            self.preview_checkbox.setText("Mark for Delete")
            self._close_preview()

    def _delete_selected(self):
        selected = self.grid_list.selectedItems()
        if not selected:
            return
        
        count = len(selected)
        msg = f"Delete {count} item{'s' if count > 1 else ''}?"
        
        if self._show_styled_confirm("Delete Files", msg):
            deleted = 0
            for item in selected:
                try:
                    os.remove(item.file_path)
                    row = self.grid_list.row(item)
                    self.grid_list.takeItem(row)
                    deleted += 1
                except Exception as e:
                    print(f"[Gallery] Failed to delete {item.file_path}: {e}")
            
            print(f"[Gallery] Deleted {deleted}/{count} files")
            
            # Exit selection mode
            self.select_btn.setChecked(False)
            self._toggle_selection_mode()

    def _share_selected(self):
        # Placeholder for share
        print("Sharing selected")
