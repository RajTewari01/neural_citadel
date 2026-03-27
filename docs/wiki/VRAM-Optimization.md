# 🧠 VRAM Optimization Strategy

Neural Citadel was explicitly engineered to run a staggering variety of AI pipelines on highly constrained hardware—specifically the **Nvidia GTX 1650 (4GB VRAM)**.

## The Mutual Exclusion Lock (Mutex)
It is physically impossible to keep an LLM, a Stable Diffusion pipeline, and a Whisper transcription model in 4GB of VRAM simultaneously. 

To solve this, Neural Citadel utilizes the `ResourceManager` singleton (`infra/server/resource_manager.py`).
- It holds an `asyncio.Lock` that dictates access to the GPU.
- When a new process requests GPU access (via `ResourceManager.request_execution(model_type)`), the manager checks if another process is holding the lock.
- If the current lock holder is non-essential, the `ResourceManager` issues a kill signal (`SIGKILL` equivalent on Windows), completely terminating the process and wiping it from system memory.
- It then allocates the lock to the new process, ensuring 100% VRAM is available.

## Precision Engineering for Turing

The GTX 1650 uses the Turing arch (specifically TU117), which is notorious for poor native FP16 handling, often resulting in cascading NaN (Not a Number) black-screen outputs during diffusion tasks.

- **FP32 Forcing:** Despite the memory cost, Neural Citadel forces specific mathematical operations back up into FP32 precision to guarantee visual stability.
- **Attention Slicing & CPU Offloading:** For SD pipelines, xformers are integrated, and `enable_sequential_cpu_offload()` is heavily utilized to shuttle weights back and forth from system RAM to VRAM on a layer-by-layer basis. `enable_vae_slicing()` ensures that image decoding doesn't trigger OOM (Out Of Memory) crashes at the absolute end of an otherwise successful generation.

## The Subprocess Advantage

By executing all models via subprocesses rather than importing them natively into the FastAPI server or PyQt GUI, Neural Citadel guarantees that **garbage collection is infallible**. 

When an API call finishes and the subprocess terminates, the operating system forcibly reclaims every single byte of VRAM, preventing memory leak degradation common in monolithic Python servers.
