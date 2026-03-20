"""
System Stats Widget - V3
Big semi-circle gauge, real GPU/CPU graphs
Instagram colors: Purple/Pink/Orange
Theme-aware for light/dark modes
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer, QPointF, QThread, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QPainterPath, QLinearGradient

import math

try:
    import GPUtil
    HAS_GPUTIL = True
except ImportError:
    HAS_GPUTIL = False

import psutil

from infra.gui.theme import ThemeManager

# Instagram gradient colors
PURPLE = "#833AB4"
PINK = "#E1306C"
ORANGE = "#F77737"


class SemiCircleGauge(QWidget):
    """Big semi-circle gauge for CPU/GPU - theme aware"""
    
    def __init__(self, title: str = "CPU"):
        super().__init__()
        self.title = title
        self.value = 0
        self.setMinimumSize(160, 100)
        self.setMaximumHeight(110)
    
    def set_value(self, value: int):
        self.value = min(100, max(0, value))
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        theme = ThemeManager.get_theme()
        is_dark = theme.name == "dark"
        
        w, h = self.width(), self.height()
        size = min(w, h * 2) - 30
        x = (w - size) // 2
        y = 10
        
        # Background arc - theme aware
        bg_color = "#1a1a1a" if is_dark else "#E8D0D0"
        pen = QPen(QColor(bg_color))
        pen.setWidth(12)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(x, y, size, size, 180 * 16, -180 * 16)  # Semi-circle
        
        # Foreground arc with Instagram gradient
        angle = int((self.value / 100) * 180)
        segments = 30
        
        for i in range(segments):
            if i * (180 / segments) > angle:
                break
            
            t = i / segments
            # Interpolate through purple -> pink -> orange
            if t < 0.5:
                t2 = t * 2
                r = int(131 + t2 * (225 - 131))  # Purple to Pink
                g = int(58 + t2 * (48 - 58))
                b = int(180 + t2 * (108 - 180))
            else:
                t2 = (t - 0.5) * 2
                r = int(225 + t2 * (247 - 225))  # Pink to Orange
                g = int(48 + t2 * (119 - 48))
                b = int(108 + t2 * (55 - 108))
            
            pen = QPen(QColor(r, g, b))
            pen.setWidth(12)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            
            start = 180 - int(i * (180 / segments))
            span = -int(180 / segments) - 2
            painter.drawArc(x, y, size, size, start * 16, span * 16)
        
        # Value text - theme aware
        text_color = "#ffffff" if is_dark else "#4a3535"
        painter.setPen(QColor(text_color))
        font = QFont("Consolas", 28, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(x, y + 20, size, size // 2, Qt.AlignmentFlag.AlignCenter, f"{self.value}%")
        
        # Title
        painter.setPen(QColor(PINK))
        font = QFont("Consolas", 10, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(x, y + size // 2 + 5, size, 20, Qt.AlignmentFlag.AlignCenter, self.title)


class RealTimeGraph(QWidget):
    """Real-time line graph for GPU/CPU usage - theme aware"""
    
    def __init__(self, title: str = "CPU", color: str = PINK):
        super().__init__()
        self.title = title
        self.color = QColor(color)
        self.data = [0] * 50
        self.setMinimumHeight(60)
        self.setMaximumHeight(70)
    
    def add_value(self, value: float):
        self.data = self.data[1:] + [value]
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        theme = ThemeManager.get_theme()
        is_dark = theme.name == "dark"
        
        w, h = self.width(), self.height()
        graph_h = h - 20
        
        # Title - theme aware
        title_color = "#888888" if is_dark else "#666666"
        painter.setPen(QColor(title_color))
        font = QFont("Consolas", 9)
        painter.setFont(font)
        painter.drawText(5, 14, self.title)
        
        # Graph area background - theme aware
        bg_color = "#0a0a0a" if is_dark else "#F8E8E8"
        painter.fillRect(0, 20, w, graph_h, QColor(bg_color))
        
        # Draw grid lines - theme aware
        grid_color = "#1a1a1a" if is_dark else "#E8D0D0"
        painter.setPen(QPen(QColor(grid_color), 1))
        for i in range(1, 4):
            y = 20 + int(graph_h * i / 4)
            painter.drawLine(0, y, w, y)
        
        # Draw line graph
        if len(self.data) > 1:
            pen = QPen(self.color)
            pen.setWidth(2)
            painter.setPen(pen)
            
            path = QPainterPath()
            step = w / (len(self.data) - 1)
            
            for i, val in enumerate(self.data):
                x = i * step
                y = 20 + graph_h - (val / 100 * graph_h)
                if i == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)
            
            painter.drawPath(path)
        
        # Current value - theme aware (with NaN protection)
        if self.data:
            import math
            last_val = self.data[-1]
            if math.isnan(last_val):
                last_val = 0
            text_color = "#ffffff" if is_dark else "#4a3535"
            painter.setPen(QColor(text_color))
            font = QFont("Consolas", 10, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(w - 50, 14, f"{int(last_val)}%")


class StatsWorker(QThread):
    """Background worker for collecting system stats without blocking UI"""
    stats_ready = pyqtSignal(float, float, float, float)  # cpu, mem, gpu, temp
    
    def run(self):
        cpu_pct = psutil.cpu_percent(interval=0)  # Non-blocking
        mem_pct = psutil.virtual_memory().percent
        gpu_pct = 0
        gpu_temp = 0
        
        if HAS_GPUTIL:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    gpu_pct = gpu.load * 100
                    gpu_temp = gpu.temperature
            except:
                pass
        
        self.stats_ready.emit(cpu_pct, mem_pct, gpu_pct, gpu_temp)


class SystemStatsWidget(QWidget):
    """System stats with semi-circle gauge and real graphs"""
    
    def __init__(self, update_interval_ms: int = 2000):
        super().__init__()
        self.update_interval = update_interval_ms
        self._setup_ui()
        self._start_timer()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Clock display (12-hour format)
        self.clock_label = QLabel("12:00:00 AM")
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.clock_label.setStyleSheet(f"""
            color: {PINK};
            font-size: 18px;
            font-family: Consolas;
            font-weight: bold;
        """)
        layout.addWidget(self.clock_label)
        
        # Big semi-circle gauge for CPU
        self.cpu_gauge = SemiCircleGauge("CPU USAGE")
        layout.addWidget(self.cpu_gauge)
        
        # Temperature display
        self.temp_label = QLabel("🌡 GPU: --°C")
        self.temp_label.setStyleSheet(f"color: {ORANGE}; font-size: 12px; font-family: Consolas;")
        self.temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.temp_label)
        
        # GPU usage graph
        self.gpu_graph = RealTimeGraph("GPU LOAD", PURPLE)
        layout.addWidget(self.gpu_graph)
        
        # CPU usage graph
        self.cpu_graph = RealTimeGraph("CPU LOAD", PINK)
        layout.addWidget(self.cpu_graph)
        
        # Memory usage graph
        self.mem_graph = RealTimeGraph("MEMORY", ORANGE)
        layout.addWidget(self.mem_graph)
        
        layout.addStretch()
    
    def _start_timer(self):
        # Stats timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._request_stats)
        self.timer.start(self.update_interval)
        self._request_stats()
        
        # Clock timer (1 second updates)
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)
        self._update_clock()
    
    def _update_clock(self):
        """Update clock display with current time in 12-hour format."""
        from datetime import datetime
        time_str = datetime.now().strftime("%I:%M:%S %p")
        self.clock_label.setText(time_str)
    
    def _request_stats(self):
        """Request stats update in background thread"""
        self.stats_worker = StatsWorker()
        self.stats_worker.stats_ready.connect(self._on_stats_ready)
        self.stats_worker.start()
    
    def _on_stats_ready(self, cpu_pct, mem_pct, gpu_pct, gpu_temp):
        """Update UI with stats from background thread"""
        self.cpu_gauge.set_value(int(cpu_pct))
        self.cpu_graph.add_value(cpu_pct)
        self.mem_graph.add_value(mem_pct)
        self.gpu_graph.add_value(gpu_pct)
        if gpu_temp > 0:
            self.temp_label.setText(f"🌡 GPU: {gpu_temp}°C")
