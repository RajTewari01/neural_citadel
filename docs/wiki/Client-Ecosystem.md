# 📱 Client Ecosystem

## Flutter Mobile Citadel
The `mobile_citadel` is an advanced Android application acting as the primary remote control for the Neural Citadel network.

**Tech Stack:** Dart 3.x, Flutter, Provider, Firebase, MethodChannels
**Scale:** Over 300+ line `main.dart`, 10 distinct UI screens, 14 background services.

### Key Capabilities:
- **Streaming UI Architecture:** The `ApiService` is heavily optimized for `stream: true` endpoints from the FastAPI gateway. It handles chunked HTTP responses precisely, rendering LLM outputs token-by-token (with specific parsing for `<think>` blocks if using a reasoning model).
- **Background Persistence:** Utilizing `FlutterBackgroundService` and `FlutterOverlayWindow`, Mobile Citadel remains active even when swiped away, monitoring the Neural Citadel gateway in real-time.
- **Native OS Hooks:** The 800-line `VoiceCommander` acts directly on Android intents, sporting a 150+ app registry that allows voice commands to natively launch arbitrary Android packages, emulate the dialer with `flutter_phone_direct_caller`, and intercept incoming state states.
- **Shake-to-Report:** A custom gyroscope listener allows users to physically shake their phone to trigger a bug-reporting/feedback overlay seamlessly into a Firebase database.

---

## PyQt6 Desktop Dashboard
The `infra/gui/` module provides a comprehensive command-center view into the host machine.

**Tech Stack:** Python 3.11, PyQt6, QProcess, GPUtil, OpenCV

### Key Capabilities:
- **Direct Execution:** Employs parallel `QThreadPool` and `QProcess` workers to instantiate python virtual environments entirely free of HTTP network overhead.
- **Live Server Logs:** Interfaces directly with `stdout` pipelines to create rich, color-coded logging consoles right inside the GUI.
- **Component Views:** 
  - *Vision Panel:* Directly embeds OpenCV matrices into `QPixmap` buffers for real-time tracking viewing.
  - *Metrics Pane:* Live charts of VRAM, CPU, and RAM consumption parsing `psutil` and `GPUtil` stats instantly.
