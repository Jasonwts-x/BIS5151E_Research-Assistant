# scripts/setup/install_gpu_support_windows.ps1
# Checks GPU setup on Windows and provides installation guidance

# Require admin
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ This script must be run as Administrator" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

Write-Host "==========================================" -ForegroundColor Blue
Write-Host "GPU Support Check - Windows" -ForegroundColor Blue
Write-Host "==========================================" -ForegroundColor Blue
Write-Host ""

# ============================================================================
# Step 1: Detect GPU
# ============================================================================
Write-Host "Step 1: Detecting GPU" -ForegroundColor Blue

$nvidiaGpu = Get-WmiObject Win32_VideoController | Where-Object { $_.Name -like "*NVIDIA*" }
$amdGpu = Get-WmiObject Win32_VideoController | Where-Object { $_.Name -like "*AMD*" -or $_.Name -like "*Radeon*" }

$gpuType = "none"

if ($nvidiaGpu) {
    $gpuType = "nvidia"
    Write-Host "✅ NVIDIA GPU detected: $($nvidiaGpu.Name)" -ForegroundColor Green
} elseif ($amdGpu) {
    $gpuType = "amd"
    Write-Host "✅ AMD GPU detected: $($amdGpu.Name)" -ForegroundColor Green
    Write-Host "⚠️  WARNING: AMD GPU support in Docker is LIMITED on Windows" -ForegroundColor Yellow
} else {
    Write-Host "ℹ️  No GPU detected - will use CPU mode" -ForegroundColor Yellow
    exit 0
}
Write-Host ""

# ============================================================================
# Step 2: Check Docker Desktop
# ============================================================================
Write-Host "Step 2: Checking Docker Desktop" -ForegroundColor Blue

$dockerPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
if (Test-Path $dockerPath) {
    Write-Host "✅ Docker Desktop installed" -ForegroundColor Green
} else {
    Write-Host "❌ Docker Desktop not found" -ForegroundColor Red
    Write-Host ""
    Write-Host "Install Docker Desktop:" -ForegroundColor Yellow
    Write-Host "1. Download from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    Write-Host "2. Run installer and reboot" -ForegroundColor Yellow
    Write-Host "3. Re-run this script" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# ============================================================================
# Step 3: Check GPU Drivers (NVIDIA)
# ============================================================================
if ($gpuType -eq "nvidia") {
    Write-Host "Step 3: Checking NVIDIA Drivers" -ForegroundColor Blue
    
    $nvidiaSmi = "C:\Windows\System32\nvidia-smi.exe"
    if (Test-Path $nvidiaSmi) {
        Write-Host "✅ NVIDIA drivers installed" -ForegroundColor Green
        & $nvidiaSmi --query-gpu=name,driver_version --format=csv,noheader
    } else {
        Write-Host "❌ NVIDIA drivers not installed" -ForegroundColor Red
        Write-Host ""
        Write-Host "Install NVIDIA drivers:" -ForegroundColor Yellow
        Write-Host "1. Go to: https://www.nvidia.com/Download/index.aspx" -ForegroundColor Yellow
        Write-Host "2. Download driver for your GPU" -ForegroundColor Yellow
        Write-Host "3. Install and reboot" -ForegroundColor Yellow
        Write-Host "4. Re-run this script" -ForegroundColor Yellow
        exit 1
    }
    Write-Host ""
    
    # ============================================================================
    # Step 4: Check Docker GPU Settings
    # ============================================================================
    Write-Host "Step 4: Checking Docker GPU Configuration" -ForegroundColor Blue
    
    Write-Host "⚠️  Manual check required:" -ForegroundColor Yellow
    Write-Host "1. Open Docker Desktop" -ForegroundColor Yellow
    Write-Host "2. Go to Settings → Resources → WSL Integration" -ForegroundColor Yellow
    Write-Host "3. Ensure GPU support is enabled" -ForegroundColor Yellow
    Write-Host "4. If using WSL2, enable integration with your distro" -ForegroundColor Yellow
    Write-Host ""
    
    Read-Host "Press Enter after verifying Docker Desktop settings"
    
    # ============================================================================
    # Step 5: Test GPU in Docker
    # ============================================================================
    Write-Host "Step 5: Testing GPU in Docker" -ForegroundColor Blue
    
    Write-Host "Starting test container..." -ForegroundColor Yellow
    docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ GPU works in Docker!" -ForegroundColor Green
        Write-Host ""
        Write-Host "==========================================" -ForegroundColor Green
        Write-Host "✅ NVIDIA SETUP COMPLETE" -ForegroundColor Green
        Write-Host "==========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Use this command to start with GPU:" -ForegroundColor Cyan
        Write-Host "  docker compose -f docker/docker-compose.yml -f docker/docker-compose.nvidia.yml up -d" -ForegroundColor White
    } else {
        Write-Host "❌ GPU test failed" -ForegroundColor Red
        Write-Host ""
        Write-Host "Troubleshooting:" -ForegroundColor Yellow
        Write-Host "1. Ensure Docker Desktop is running" -ForegroundColor Yellow
        Write-Host "2. Check Docker Desktop → Settings → Resources → WSL Integration" -ForegroundColor Yellow
        Write-Host "3. Try restarting Docker Desktop" -ForegroundColor Yellow
        Write-Host "4. Reboot and try again" -ForegroundColor Yellow
        exit 1
    }
}

# ============================================================================
# AMD GPU (Windows)
# ============================================================================
if ($gpuType -eq "amd") {
    Write-Host "Step 3: AMD GPU Check" -ForegroundColor Blue
    Write-Host ""
    Write-Host "❌ AMD GPU support in Docker is NOT RECOMMENDED on Windows" -ForegroundColor Red
    Write-Host ""
    Write-Host "Recommendation: Use CPU mode instead" -ForegroundColor Yellow
    Write-Host "  docker compose -f docker/docker-compose.yml up -d" -ForegroundColor White
    Write-Host ""
    Write-Host "If you must try AMD:" -ForegroundColor Yellow
    Write-Host "1. Install latest AMD drivers" -ForegroundColor Yellow
    Write-Host "2. Use at your own risk (experimental/unsupported)" -ForegroundColor Yellow
}