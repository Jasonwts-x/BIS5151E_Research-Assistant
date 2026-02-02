# GPU Acceleration Setup (NVIDIA)

Enable GPU acceleration for 3-5x faster LLM inference.

**Prerequisites**: NVIDIA GPU with 8GB+ VRAM

---

## ⚠️ Important Notes

- **Only NVIDIA GPUs are supported** (AMD support is experimental and not covered here)
- **Requires NVIDIA GPU with CUDA support** (Check: https://developer.nvidia.com/cuda-gpus)
- **Minimum 8GB VRAM** recommended (16GB+ for larger models)
- **Windows users**: WSL2 required
- **Linux users**: Native Docker support

---

## 📋 Prerequisites

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **GPU** | NVIDIA GPU (CUDA 11.0+) | RTX 3060 or better |
| **VRAM** | 8GB | 16GB+ |
| **System RAM** | 16GB | 32GB |
| **CUDA Compute** | 6.0+ | 7.0+ |

**Check your GPU compatibility**: https://developer.nvidia.com/cuda-gpus

### Software Requirements

| Software | Version | Required |
|----------|---------|----------|
| **NVIDIA Driver** | 525.60.13+ | ✅ Yes |
| **Docker Desktop** | 20.10+ | ✅ Yes |
| **NVIDIA Container Toolkit** | Latest | ✅ Yes |
| **WSL2** (Windows only) | Latest | ✅ Yes (Windows) |

---

## 🔧 Installation Steps

### Step 1: Install/Update NVIDIA Drivers

You must install NVIDIA drivers on your **host system** (not inside Docker).

#### Windows

1. **Download latest drivers**:
   - Visit: https://www.nvidia.com/Download/index.aspx
   - Select your GPU model
   - Download and install "Game Ready Driver" or "Studio Driver"

2. **Verify installation**:
```powershell
   nvidia-smi
```
   
   **Expected output**:
```
   +-----------------------------------------------------------------------------+
   | NVIDIA-SMI 535.xx.xx    Driver Version: 535.xx.xx    CUDA Version: 12.2     |
   |-------------------------------+----------------------+----------------------+
   | GPU  Name        ...
```

3. **Install WSL2** (if not already installed):
```powershell
   # Run as Administrator
   wsl --install
   
   # Restart computer
   
   # Update WSL
   wsl --update
```

#### Linux (Ubuntu/Debian)
```bash
# Add NVIDIA package repository
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.0-1_all.deb
sudo dpkg -i cuda-keyring_1.0-1_all.deb
sudo apt-get update

# Install NVIDIA driver
sudo apt-get install -y nvidia-driver-535

# Reboot
sudo reboot

# Verify
nvidia-smi
```

#### macOS

**Note**: NVIDIA GPUs are not supported on macOS (Apple Silicon uses Metal, not CUDA).

---

### Step 2: Install NVIDIA Container Toolkit

This allows Docker to access your GPU.

#### Windows (WSL2)

**The NVIDIA drivers installed in Step 1 are sufficient for WSL2. No additional installation needed inside WSL2.**

Verify Docker can see GPU:
```bash
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi
```

If this works, skip to Step 3.

If it fails, continue:
```bash
# Inside WSL2 terminal
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Configure Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

#### Linux (Ubuntu/Debian)
```bash
# Add NVIDIA Container Toolkit repository
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Install
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Configure Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Verify
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi
```

**Expected output**: Should show your GPU information inside the container.

---

### Step 3: Configure Docker Desktop (Windows/macOS)

#### Windows

1. Open **Docker Desktop**
2. Go to **Settings** → **Resources** → **WSL Integration**
3. Enable integration with your WSL2 distro (e.g., Ubuntu)
4. Click **Apply & Restart**

#### macOS

**NVIDIA GPUs not supported on macOS.** Use CPU mode or cloud GPU.

---

### Step 4: Verify GPU Access

Test that Docker can access your GPU:
```bash
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi
```

**Expected output**:
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 535.xx.xx    Driver Version: 535.xx.xx    CUDA Version: 12.2     |
|-------------------------------+----------------------+----------------------+
| GPU  Name            TCC/WDDM | Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|===============================+======================+======================|
|   0  NVIDIA GeForce ... WDDM  | 00000000:01:00.0  On |                  N/A |
| 30%   45C    P8    15W / 350W |    500MiB / 12288MiB |      0%      Default |
+-------------------------------+----------------------+----------------------+
```

If you see your GPU, you're ready!

---

## 🚀 Start with GPU Support

### Option 1: Start All Services with GPU
```bash
# Stop existing services (if running)
docker compose -f docker/docker-compose.yml down

# Start with GPU support
docker compose -f docker/docker-compose.yml -f docker/docker-compose.nvidia.yml up -d
```

### Option 2: GPU for Ollama Only

If you only want GPU for Ollama (recommended):

The `docker-compose.nvidia.yml` file already configures this. Just use the command above.

---

## ✅ Verify GPU Usage

### Check Ollama is Using GPU
```bash
# View Ollama logs
docker compose logs ollama

# Should see messages like:
# "CUDA device: NVIDIA GeForce RTX 3080"
# "GPU memory: 10240 MB"
```

### Monitor GPU Usage

**While running a query**:
```bash
# In one terminal, watch GPU usage
watch -n 1 nvidia-smi

# In another terminal, run a query
```
```powershell
# PowerShell
$body = @{
    query = "Explain quantum computing"
    language = "en"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/research/query" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

**Expected**: GPU utilization should spike to 60-90% during generation.

---

## 📊 Performance Comparison

### CPU vs GPU Benchmarks

| Operation | CPU (8 cores) | GPU (RTX 3080) | Speedup |
|-----------|---------------|----------------|---------|
| **Embedding generation** (100 docs) | ~12s | ~3s | 4x |
| **LLM inference** (300 tokens) | ~25s | ~6s | 4.2x |
| **Full query workflow** | ~35s | ~10s | 3.5x |

**Model**: qwen3:1.7b

**Note**: Speedup varies by GPU model and workload.

---

## 🔧 Troubleshooting

### Issue: `docker: Error response from daemon: could not select device driver "" with capabilities: [[gpu]]`

**Solution**:
```bash
# Restart Docker daemon
sudo systemctl restart docker

# Or restart Docker Desktop (Windows/macOS)
```

### Issue: `nvidia-smi` not found in container

**Solution**: NVIDIA drivers not installed or Container Toolkit not configured.
```bash
# Verify host drivers
nvidia-smi

# Reinstall Container Toolkit (Linux)
sudo apt-get install --reinstall nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### Issue: GPU not being used (low utilization)

**Possible causes**:
1. Model not loaded on GPU
2. Batch size too small
3. CPU bottleneck elsewhere

**Solution**:
```bash
# Check Ollama logs for GPU initialization
docker compose logs ollama | grep -i cuda

# Should see: "CUDA device: ..."
```

### Issue: Out of memory (OOM) errors

**Solution**:
```bash
# Use smaller model
# Edit docker/.env
OLLAMA_MODEL=qwen3:1.7b  # Instead of larger models

# Or reduce concurrent requests
# Edit .env
OLLAMA_NUM_PARALLEL=1
OLLAMA_MAX_LOADED_MODELS=1
```

---

## ⚙️ GPU Configuration Options

### Ollama GPU Settings

Edit `docker/.env` to configure:
```env
# Number of parallel requests (default: 1)
# Higher = more VRAM usage
OLLAMA_NUM_PARALLEL=2

# Maximum loaded models (default: 1)
OLLAMA_MAX_LOADED_MODELS=1

# Keep model in memory (default: 30m)
# Longer = faster subsequent queries, more VRAM usage
OLLAMA_KEEP_ALIVE=1h

# GPU layers (default: auto)
# Set to specific number to limit VRAM usage
# OLLAMA_GPU_LAYERS=32
```

### Advanced: Multi-GPU Setup

If you have multiple GPUs:
```yaml
# docker/docker-compose.nvidia.yml
services:
  ollama:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['0', '1']  # Use GPU 0 and 1
              capabilities: [gpu]
```

---

## 🔄 Switching Between CPU and GPU

### Switch to GPU
```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.nvidia.yml up -d
```

### Switch Back to CPU
```bash
docker compose -f docker/docker-compose.yml up -d
```

**Note**: Switching will restart services and take ~2 minutes.

---

## 📈 Optimizing GPU Performance

### 1. Use Quantized Models

Smaller models = faster inference:
```env
# docker/.env
OLLAMA_MODEL=qwen3:1.7b  # Fastest
# OLLAMA_MODEL=qwen3:4b    # Balanced
# OLLAMA_MODEL=qwen2.5:3b  # Alternative
```

### 2. Increase Batch Size

For multiple queries:
```env
OLLAMA_NUM_PARALLEL=2  # Process 2 queries at once
```

### 3. Keep Models in VRAM
```env
OLLAMA_KEEP_ALIVE=2h  # Keep model loaded for 2 hours
```

### 4. Monitor VRAM Usage
```bash
# Watch VRAM
watch -n 1 "nvidia-smi --query-gpu=memory.used,memory.free --format=csv"
```

---

## 📚 Additional Resources

### NVIDIA Documentation
- **CUDA GPUs**: https://developer.nvidia.com/cuda-gpus
- **Container Toolkit**: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
- **Docker GPU Support**: https://docs.docker.com/config/containers/resource_constraints/#gpu

### Ollama GPU Documentation
- **Ollama GPU Guide**: https://github.com/ollama/ollama/blob/main/docs/gpu.md
- **Model Library**: https://ollama.com/library

---

## ❓ FAQ

**Q: Can I use AMD GPUs?**  
A: AMD GPU support is experimental. We recommend NVIDIA for production use.

**Q: My GPU has 6GB VRAM. Will it work?**  
A: It might work with smaller models (qwen3:1.7b), but 8GB+ is recommended.

**Q: Can I use GPU for embeddings too?**  
A: Currently, only Ollama LLM inference uses GPU. Embeddings use CPU (sentence-transformers). GPU embedding support is planned.

**Q: Does this work in cloud environments (AWS, GCP)?**  
A: Yes! Use GPU-enabled instances (AWS p3/g4, GCP N1 with GPUs). Install NVIDIA drivers and Container Toolkit.

---

**[⬅ Back to Setup Guide](README.md)** | **[⬆ Back to Installation](INSTALLATION.md)**