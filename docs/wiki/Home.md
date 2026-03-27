# Welcome to the Neural Citadel Wiki

Neural Citadel is a highly modular, multi-agent AI operating system designed to run entirely locally on consumer-grade hardware (specifically targeted at the Nvidia GTX 1650 4GB). It provides an expansive suite of 12 distinct AI applications operating across 11 fully isolated Python virtual environments.

### 📚 Wiki Directory

Begin exploring the architecture and ecosystem of Neural Citadel:

1. **[🛠️ Setup & Installation Guide](Setup-Guide.md)**
   Learn how to clone the repository, install Python 3.11 for Windows, and bootstrap the 11 virtual environments using the provided scripts.

2. **[🏭 Systems Architecture](Architecture.md)**
   Understand the revolutionary Dual-Client Bridge (PyQt QProcess vs. Flutter HTTP) and how the lightweight FastAPI gateway orchestrates the massive monorepo.

3. **[🧠 VRAM Optimization Strategy](VRAM-Optimization.md)**
   Deep dive into how we fit heavy models (Stable Diffusion, Whisper, LLMs) onto 4GB VRAM using the `ResourceManager` singleton, sequential execution, and CPU-offloading.

4. **[📱 Client Ecosystem](Client-Ecosystem.md)**
   Explore the dual frontends: the massively capable 10-screen Flutter mobile agent and the stacked-view PyQt6 desktop dashboard.

5. **[⚙️ Engine Registry](Engine-Registry.md)**
   Examine the pipeline breakdown of all 12 core apps (Image Gen, Social Automation, QR Studio, etc.) and their specific virtual environment dependencies.

---
_The Neural Citadel platform is Proprietary software. All rights reserved._
