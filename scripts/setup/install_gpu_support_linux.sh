#!/bin/bash
# scripts/setup/install_gpu_support_linux.sh
# Auto-installs GPU support on Linux (NVIDIA or AMD)

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "GPU Support Installation - Linux"
echo -e "==========================================${NC}"
echo ""

# Require root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ This script must be run as root${NC}"
    echo "Run: sudo bash $0"
    exit 1
fi

# ============================================================================
# Step 1: Detect GPU Type
# ============================================================================
echo -e "${BLUE}Step 1: Detecting GPU${NC}"

GPU_TYPE="none"

if lspci | grep -i nvidia > /dev/null; then
    GPU_TYPE="nvidia"
    echo -e "${GREEN}✅ NVIDIA GPU detected${NC}"
    lspci | grep -i nvidia | head -n1
elif lspci | grep -i 'vga.*amd' > /dev/null; then
    GPU_TYPE="amd"
    echo -e "${GREEN}✅ AMD GPU detected${NC}"
    lspci | grep -i 'vga.*amd' | head -n1
else
    echo -e "${YELLOW}ℹ️  No GPU detected${NC}"
    echo "This system will use CPU mode."
    exit 0
fi
echo ""

# ============================================================================
# Step 2: Check Docker
# ============================================================================
echo -e "${BLUE}Step 2: Checking Docker${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not installed${NC}"
    echo ""
    echo "Installing Docker..."
    
    # Install Docker (Ubuntu/Debian)
    apt-get update
    apt-get install -y ca-certificates curl gnupg lsb-release
    
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    systemctl start docker
    systemctl enable docker
    
    echo -e "${GREEN}✅ Docker installed${NC}"
else
    echo -e "${GREEN}✅ Docker already installed${NC}"
fi
echo ""

# ============================================================================
# NVIDIA GPU Setup
# ============================================================================
if [ "$GPU_TYPE" = "nvidia" ]; then
    echo -e "${BLUE}Step 3: NVIDIA GPU Setup${NC}"
    
    # Check if drivers are installed
    if command -v nvidia-smi &> /dev/null; then
        echo -e "${GREEN}✅ NVIDIA drivers installed${NC}"
        nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
    else
        echo -e "${RED}❌ NVIDIA drivers not installed${NC}"
        echo ""
        echo "NVIDIA drivers must be installed manually:"
        echo "1. Go to: https://www.nvidia.com/Download/index.aspx"
        echo "2. Download driver for your GPU"
        echo "3. Install and reboot"
        echo "4. Re-run this script"
        exit 1
    fi
    echo ""
    
    # Install NVIDIA Container Toolkit
    echo "Installing NVIDIA Container Toolkit..."
    
    distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
    curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
        tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
    
    apt-get update
    apt-get install -y nvidia-container-toolkit
    
    # Configure Docker
    nvidia-ctk runtime configure --runtime=docker
    systemctl restart docker
    
    echo -e "${GREEN}✅ NVIDIA Container Toolkit installed${NC}"
    echo ""
    
    # Test GPU in Docker
    echo "Testing GPU access in Docker..."
    if docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
        echo -e "${GREEN}✅ GPU works in Docker!${NC}"
        echo ""
        echo -e "${GREEN}=========================================="
        echo "✅ NVIDIA SETUP COMPLETE"
        echo "==========================================${NC}"
        echo ""
        echo "Use this command to start with GPU:"
        echo "  docker compose -f docker/docker-compose.yml -f docker/docker-compose.nvidia.yml up -d"
    else
        echo -e "${RED}❌ GPU test failed${NC}"
        echo "Try rebooting and running the test again"
        exit 1
    fi
fi

# ============================================================================
# AMD GPU Setup
# ============================================================================
if [ "$GPU_TYPE" = "amd" ]; then
    echo -e "${BLUE}Step 3: AMD GPU Setup (ROCm)${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  WARNING: AMD/ROCm support is EXPERIMENTAL${NC}"
    echo "AMD GPU support in Docker/Ollama is limited."
    echo ""
    read -p "Continue with AMD setup? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo "Setup cancelled. Use CPU mode instead."
        exit 0
    fi
    
    # Check if ROCm drivers are installed
    if command -v rocm-smi &> /dev/null; then
        echo -e "${GREEN}✅ ROCm drivers installed${NC}"
        rocm-smi --showproductname
    else
        echo -e "${RED}❌ ROCm drivers not installed${NC}"
        echo ""
        echo "Installing ROCm drivers..."
        echo "This may take several minutes..."
        
        # Add ROCm repository
        wget -q -O - https://repo.radeon.com/rocm/rocm.gpg.key | apt-key add -
        echo 'deb [arch=amd64] https://repo.radeon.com/rocm/apt/debian/ ubuntu main' | tee /etc/apt/sources.list.d/rocm.list
        
        apt-get update
        apt-get install -y rocm-dkms
        
        # Add user to video and render groups
        usermod -a -G video,render $SUDO_USER
        
        echo -e "${GREEN}✅ ROCm installed${NC}"
        echo -e "${YELLOW}⚠️  REBOOT REQUIRED${NC}"
        echo "Run 'sudo reboot' then re-run this script"
        exit 0
    fi
    echo ""
    
    # Check device files
    if [ -e "/dev/kfd" ] && [ -e "/dev/dri" ]; then
        echo -e "${GREEN}✅ ROCm device files exist${NC}"
    else
        echo -e "${RED}❌ ROCm device files missing${NC}"
        echo "Reboot may be required"
        exit 1
    fi
    echo ""
    
    echo -e "${GREEN}=========================================="
    echo "✅ AMD SETUP COMPLETE (EXPERIMENTAL)"
    echo "==========================================${NC}"
    echo ""
    echo "Use this command to start with AMD GPU:"
    echo "  docker compose -f docker/docker-compose.yml -f docker/docker-compose.amd.yml up -d"
    echo ""
    echo "Note: AMD support is experimental. Monitor performance carefully."
fi