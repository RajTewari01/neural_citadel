# 📱 Mobile Citadel (Neural Citadel Frontend)

> **Proprietary Software.** This frontend client is the unified interface bridging the Neural Citadel 4GB VRAM subprocess serving architecture to Edge/Android devices. 

Mobile Citadel is a sprawling, **system-level Flutter application** (50+ source files, 48 package dependencies) designed specifically to interface with the FastAPI gateway of the Neural Citadel backend. Unlike a simple REST API consumer, this application executes heavy, hardware-accelerated rendering and system-level interceptions (like acting as the native Android dialer) locally to minimize API latency and gateway throughput overhead.

---

## 🏗️ Core Architecture Overview

### 1. The Dual-Client Bridge Pattern
Mobile Citadel establishes a **Persistent Interactive Pipeline** with the backend. While standard requests (like image generation) are executed as one-shot REST calls, interactive sessions (like interacting with DeepSeek R1 or LLaMA 3.1) utilize persistent standard input/output streaming across the FastAPI bridge to prevent the 30-second model reload latency inherent to consumer GPUs. 

### 2. System-Level Dynamic Island
The most complex native integration is the **Neural Pulse Overlay** (`neural_pulse_overlay.dart`), a 605-line Dart isolate that implements a persistent, glassmorphic Dynamic Island overlay.
*   **Background Isolation:** Runs completely independently of the Flutter main thread via `@pragma("vm:entry-point") overlayMain()`. It persists across all applications when Mobile Citadel is in the background.
*   **Bidirectional Communication:** Utilizes `FlutterOverlayWindow.shareData()` to sync live call states, dynamic calibration offsets, and force-expand signals directly from the native Kotlin daemons.
*   **Visual Fidelity:** Implements a 60 FPS breathing Siri waveform with multi-layered sinusoidal gradients and heat-map particle routing.

### 3. Native Phone System Integration
Mobile Citadel is designed to completely replace the stock Android telephone application.
*   **Default Dialer Priority:** Registers natively via `MethodChannel('com.neuralcitadel/native')` to intercept cellular broadcasts.
*   **EventChannel Sync:** Real-time call state synchronization mapping Android `TelephonyManager` states (DIALING, RINGING, ACTIVE) directly to the Flutter UI layer with zero drift. 
*   **In-Call Screen Processing:** A massive 2,500+ line localized system handling DTMF keypad traversal, contact resolution, and ghost call prevention loops using 10-minute cache TTL resets.

### 4. 34+ Hardware-Accelerated Physics Engines
To avoid offloading visual computational complexity to the memory-starved GPU serving the AI models, Mobile Citadel handles all UI effects strictly on the Android client using multi-layered `CustomPainter` streams capped at 60 FPS:
*   **Starfield Warp:** 3D perspective projections with pre-cached `Path` vertex geometry arrays for asteroid collision simulations.
*   **Black Hole Accretion:** Multi-layered Gargantua render with Keplerian differential spin mechanics and real-time eclipse occlusion mapping.
*   **Particle Arrays:** Autonomous AI-steered rocket geometries featuring predictive raycast obstacle avoidance.

### 5. Offline Voice Commander
A localized intelligence system bridging intent execution:
*   **Hard-Reset Recovery:** Auto-wake loops with a 4-second heartbeat timer that force-recovers STT failures.
*   **Deep Linking:** 150+ predefined application registry mapping voice intents directly to Android package executions. 
*   **Trilingual Logic:** Natively handles English, Hindi, and Bengali token interpretation.

---

## 🔒 Security & Usage

Because this application bridges secure API gateways and assumes direct control over hardware modules (Cellular APIs, System Alert Windows, Audio Capture):
*   **All configuration variables (`google-services.json`, API secrets) must remain explicitly blacklisted from standard source control.**
*   **This software is unconditionally proprietary.** No portion of the Dart rendering pipeline or Kotlin bridging channels may be copied, analyzed, or utilized.

**Architecture Designer:** Biswadeep Tewari  
**Parent System:** [Neural Citadel](https://github.com/RajTewari01/neural_citadel)
