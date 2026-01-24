# GPU Support Guide

Enable GPU acceleration for faster LLM inference and embedding generation.

---

## ⚠️ Current Status

**GPU support is in development.** This guide provides configuration for future implementation.

Currently, the system runs on CPU with acceptable performance:
- Query time: ~25-30 seconds
- Ingestion: ~5-10 seconds per paper

GPU acceleration will reduce these times by 3-5x.

---

## Prerequisites

### NVIDIA GPUs

**Requirements:**
- NVIDIA GPU with Compute Capability 6.0+ (Pascal or newer)
- NVIDIA drivers installed
- NVIDIA Container Toolkit

**Supported GPUs:**
- GeForce RTX 20/30/40 series
- Tesla T4, V100, A100
- Quadro RTX series

**Minimum VRAM:** 8GB (recommended: 12GB+)

---

### AMD GPUs

**Requirements:**
- AMD GPU (RDNA 2 or newer)
- ROCm 5.0+ installed
- AMD Container Toolkit

**Supported GPUs:**
- Radeon RX 6000/7000 series
- Radeon Pro W6000 series

**Status:** Experimental support via ROCm

---

## Installation

### NVIDIA Setup

#### 1. Install NVIDIA Drivers

**Linux:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install nvidia-driver-535

# Verify
nvidia-smi
```

**Windows:**
Download from https://www.nvidia.com/drivers

---

#### 2. Install NVIDIA Container Toolkit

**Linux:**
```bash
# Add repository
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# Install
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Restart Docker
sudo systemctl restart docker

# Verify
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

**Windows/macOS:**
GPU support in Docker Desktop is limited. Consider using WSL2 (Windows) or Linux VM.

---

#### 3. Configure Docker Compose

**Edit `docker/docker-compose.nvidia.yml`** (to be created):
```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
    ports:
      - "${OLLAMA_PORT:-11434}:11434"
    volumes:
      - ollama_data:/root/.ollama
    networks:
      - research_net
    restart: unless-stopped

  api:
    build:
      context: ..
      dockerfile: .devcontainer/Dockerfile
      target: api
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - CUDA_VISIBLE_DEVICES=0
    # ... rest of config
```

---

#### 4. Start with GPU Support
```bash
# Stop current services
docker compose down

# Start with NVIDIA GPU support
docker compose -f docker/docker-compose.yml -f docker/docker-compose.nvidia.yml up -d

# Verify GPU usage
docker exec ollama nvidia-smi
```

---

### AMD Setup (ROCm)

#### 1. Install ROCm

**Ubuntu 22.04:**
```bash
# Add repository
wget -q -O - https://repo.radeon.com/rocm/rocm.gpg.key | sudo apt-key add -
echo 'deb [arch=amd64] https://repo.radeon.com/rocm/apt/5.7/ ubuntu main' | \
  sudo tee /etc/apt/sources.list.d/rocm.list

# Install
sudo apt-get update
sudo apt-get install rocm-hip-sdk

# Add user to groups
sudo usermod -a -G render,video $USER

# Reboot
sudo reboot

# Verify
rocm-smi
```

---

#### 2. Configure Docker

**Edit `docker/docker-compose.amd.yml`** (to be created):
```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:rocm
    container_name: ollama
    devices:
      - /dev/kfd
      - /dev/dri
    environment:
      - HSA_OVERRIDE_GFX_VERSION=10.3.0  # Adjust for your GPU
    # ... rest of config
```

---

#### 3. Start with ROCm Support
```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.amd.yml up -d
```

---

## Performance Comparison

### CPU vs GPU (NVIDIA RTX 3080)

| Operation | CPU | GPU | Speedup |
|-----------|-----|-----|---------|
| **LLM Inference** (per call) | 8-10s | 2-3s | 3-4x |
| **Embedding** (100 chunks) | 2s | 0.5s | 4x |
| **Full Query** | 25-30s | 8-12s | 3x |
| **Ingestion** (5 papers) | 25s | 15s | 1.7x |

---

## Configuration

### Ollama GPU Settings
```bash
# Inside ollama container
docker exec -it ollama bash

# Check GPU availability
ollama run qwen2.5:3b --verbose

# Set GPU memory limit
ollama run qwen2.5:3b --gpu-memory 8G
```

---

### Embedding Model GPU

**Update `src/rag/ingestion/engine.py`:**
```python
from sentence_transformers import SentenceTransformer

# Enable GPU
model = SentenceTransformer(
    'all-MiniLM-L6-v2',
    device='cuda'  # or 'cpu' for CPU mode
)

# Batch size (larger on GPU)
embeddings = model.encode(
    chunks,
    batch_size=128,  # Increase for GPU (default: 32)
    show_progress_bar=True
)
```

---

## Monitoring GPU Usage

### NVIDIA
```bash
# Real-time monitoring
watch -n 1 nvidia-smi

# Or use nvtop
sudo apt-get install nvtop
nvtop
```

**Expected output:**
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 535.54.03    Driver Version: 535.54.03    CUDA Version: 12.2     |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|===============================+======================+======================|
|   0  NVIDIA GeForce ...  Off  | 00000000:01:00.0  On |                  N/A |
| 30%   45C    P2    150W / 350W|   6234MiB / 12288MiB |     95%      Default |
+-------------------------------+----------------------+----------------------+
```

---

### AMD
```bash
# Monitor GPU
watch -n 1 rocm-smi

# Or
radeontop
```

---

## Troubleshooting

### NVIDIA: GPU Not Detected

**Check driver:**
```bash
nvidia-smi
# Should show GPU info
```

**Check Docker:**
```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
# Should show GPU in container
```

**Common fixes:**
```bash
# Restart Docker
sudo systemctl restart docker

# Reinstall NVIDIA Container Toolkit
sudo apt-get install --reinstall nvidia-container-toolkit
```

---

### AMD: ROCm Not Working

**Check GPU:**
```bash
rocm-smi
# Should list AMD GPU
```

**Check permissions:**
```bash
groups
# Should include 'render' and 'video'

# If not:
sudo usermod -a -G render,video $USER
# Log out and back in
```

---

### Out of Memory Errors

**Reduce batch size:**
```python
# In src/rag/ingestion/engine.py
embeddings = model.encode(
    chunks,
    batch_size=16,  # Reduce from 128
)
```

**Reduce model size:**
```bash
# Use smaller Ollama model
ollama pull qwen2.5:1.5b  # Instead of 3b
```

---

## Future Optimizations

### Planned Features

1. **Mixed Precision** (FP16)
   - 2x faster inference
   - 50% less memory

2. **Model Quantization**
   - INT8 or INT4 models
   - 4x faster, 75% less memory

3. **Batch Processing**
   - Process multiple queries in parallel
   - Better GPU utilization

4. **Flash Attention**
   - Faster attention computation
   - Lower memory usage

---

## Cost-Benefit Analysis

### When to Use GPU

**Good use cases:**
- High query volume (>100/day)
- Large document collections (>1000 papers)
- Real-time applications
- Batch processing

**CPU is fine for:**
- Low query volume (<20/day)
- Small document collections (<100 papers)
- Development/testing
- Budget constraints

---

## Cloud GPU Options

### AWS

**EC2 Instance types:**
- `g4dn.xlarge` - $0.526/hour (NVIDIA T4, 16GB)
- `g5.xlarge` - $1.006/hour (NVIDIA A10G, 24GB)
- `p3.2xlarge` - $3.06/hour (NVIDIA V100, 16GB)

---

### Google Cloud

**Instance types:**
- `n1-standard-4` + T4 - $0.50/hour
- `n1-standard-8` + V100 - $2.48/hour

---

### Azure

**Instance types:**
- `NC6s_v3` - $3.06/hour (V100)
- `NCasT4_v3` - $0.526/hour (T4)

---

## Resources

- **NVIDIA Container Toolkit:** https://github.com/NVIDIA/nvidia-docker
- **ROCm Documentation:** https://rocmdocs.amd.com/
- **Ollama GPU Support:** https://github.com/ollama/ollama/blob/main/docs/gpu.md
- **sentence-transformers GPU:** https://www.sbert.net/docs/usage/computing_sentence_embeddings.html

---

**[⬅ Back to Setup](README.md)** | **[⬆ Back to Main README](../../README.md)**