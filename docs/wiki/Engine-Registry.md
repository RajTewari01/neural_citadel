# ⚙️ Engine Registry

Neural Citadel is powered by a massively decoupled ecosystem of 12 distinct internal applications (`apps/`) and 7 standalone utilities (`infra/standalone/`).

## The 12 Apps

| App Folder | Venv Path | Core Technology | Role |
|------------|----------|-----------------|------|
| `image_gen` | `image_venv` | Diffusers, xformers 0.0.29 | Generates 15 styles of images via Stable Diffusion pipelines with 3 ControlNet backbonenes and LoRA fusion. |
| `image_surgeon` | `image_venv` | GroundingDINO, SAM2, CatVTON | 6-Stage inpainting, background removal, outpainting, and virtual try-on module. |
| `llm_agent` | `coreagentvenv`| Llama-CPP, Langchain | Fast token-by-token reasoning streaming pipeline with customized `<think>` tags. |
| `movie_downloader`| `movie_venv` | yt-dlp, libtorrent | Asynchronous acquisition of media from thousands of sites, bypassing standard APIs. |
| `newspaper_publisher`| `server_venv` | ReportLab, PIL | Synthesizes daily RSS feeds into highly formatted PDF newspaper broadsheets. |
| `qr_studio` | `server_venv` | qrcode, PIL | A colossal 94K line handler providing 61 distinct stylized SVG/PNG QR Code variants. |
| `social_automation`| `social_automation`| Selenium, Instagrapi | Headless browser puppeteering for Instagram/X posting and metric scraping. |
| `audio_transcriber`| `speech_venv` | faster-whisper | VAD-filtered CTranslate2 GPU transcription pipeline. |
| `voice_synthesizer`| `speech_venv` | MeloTTS / Coqui | Real-time text-to-speech engine bridging to the Mobile UI. |
| `image_captioner` | `image_captioner`| BLIP-2 (CPU) | Forced-CPU image analysis to preserve precious VRAM. |
| `code_agent` | `coreagentvenv`| Langchain | Specialized codebase retrieval and generation. |
| `hacking_agent` | `coreagentvenv`| LLM + Standalone | Automated vulnerability scanning parsing via natural language. |

## The 7 Standalone Engines
Found in `infra/standalone/`, these provide raw OS-level utilities without the overhead of the `apps/` router interface:
- `app_scanner.py`: Detects installed desktop software.
- `camera_module.py`: OpenCV hardware pipeline.
- `news_fetcher.py`: RSS aggregator.
- `sys_monitor.py`: Real-time `psutil` + `GPUtil` metrics.
- `terminal_executor.py`: Sandbox runner.
- `test_alert.py`: Diagnostic utility.
- `test_vision.py`: Vision tracking debugger.
