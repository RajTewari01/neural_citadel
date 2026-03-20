$python = "C:\Program Files\Python310\python.exe"

Write-Host "🩸 STARTING NUCLEAR REINSTALL OF AI STACK..." -ForegroundColor Red

# 1. UNINSTALL PHASE
Write-Host "❌ Uninstalling existing packages..." -ForegroundColor Yellow
$packages = "torch", "torchvision", "torchaudio", "xformers", "diffusers", "transformers", "accelerate", "compel", "safetensors", "omegaconf", "ftfy", "huggingface_hub"
foreach ($pkg in $packages) {
    Write-Host "   - Removing $pkg..."
    & $python -m pip uninstall -y $pkg | Out-Null
}

# 2. PYTORCH PHASE
Write-Host "⚡ Installing PyTorch 2.4.1 for CUDA 12.1..." -ForegroundColor Cyan
& $python -m pip install torch==2.4.1 torchvision==0.19.1 torchaudio==2.4.1 --index-url https://download.pytorch.org/whl/cu121

# 3. ECOSYSTEM PHASE
Write-Host "🦇 Installing AI Ecosystem (xFormers, Diffusers 0.29.2)..." -ForegroundColor Magenta
# Using diffusers 0.29.2 specifically for stability on Windows
& $python -m pip install xformers diffusers==0.29.2 compel transformers accelerate safetensors omegaconf ftfy scipy

Write-Host "✅ REINSTALL COMPLETE. THE BEAST IS READY." -ForegroundColor Green
