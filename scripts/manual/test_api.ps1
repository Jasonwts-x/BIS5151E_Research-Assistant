# test-api.ps1
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "Research Assistant API Diagnostic" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

# Test 1: Docker Compose Services
Write-Host "[1/6] Checking Docker services..." -ForegroundColor Yellow
try {
    $services = docker compose ps --format json | ConvertFrom-Json
    foreach ($service in $services) {
        $status = if ($service.State -eq "running") { "✓" } else { "✗" }
        $color = if ($service.State -eq "running") { "Green" } else { "Red" }
        Write-Host "  $status $($service.Service): $($service.State)" -ForegroundColor $color
    }
} catch {
    Write-Host "  ✗ Error checking Docker services" -ForegroundColor Red
    Write-Host "  Run: docker compose up -d" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Test 2: API Health
Write-Host "[2/6] Testing API health endpoint..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 5
    Write-Host "  ✓ API is healthy: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ API health check failed" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "  Check logs: docker compose logs api" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Test 3: CrewAI Health
Write-Host "[3/6] Testing CrewAI service..." -ForegroundColor Yellow
try {
    $crewHealth = Invoke-RestMethod -Uri "http://localhost:8100/health" -Method Get -TimeoutSec 5 -ErrorAction SilentlyContinue
    Write-Host "  ✓ CrewAI is healthy" -ForegroundColor Green
} catch {
    Write-Host "  ! CrewAI service not accessible from host (this is expected)" -ForegroundColor Yellow
    Write-Host "    CrewAI is internal-only, accessed via API gateway" -ForegroundColor Yellow
}
Write-Host ""

# Test 4: Weaviate
Write-Host "[4/6] Testing Weaviate..." -ForegroundColor Yellow
try {
    $weaviate = Invoke-RestMethod -Uri "http://localhost:8080/v1/.well-known/ready" -Method Get -TimeoutSec 5
    Write-Host "  ✓ Weaviate is ready" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Weaviate not responding" -ForegroundColor Red
    Write-Host "  Check logs: docker compose logs weaviate" -ForegroundColor Yellow
}
Write-Host ""

# Test 5: Ollama
Write-Host "[5/6] Testing Ollama..." -ForegroundColor Yellow
try {
    $ollama = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 5
    Write-Host "  ✓ Ollama is running" -ForegroundColor Green
    Write-Host "  Models loaded:" -ForegroundColor Gray
    foreach ($model in $ollama.models) {
        Write-Host "    - $($model.name)" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ✗ Ollama not responding" -ForegroundColor Red
    Write-Host "  Check logs: docker compose logs ollama" -ForegroundColor Yellow
}
Write-Host ""

# Test 6: Quick ArXiv Test
Write-Host "[6/6] Testing ArXiv ingestion (small test)..." -ForegroundColor Yellow
try {
    $body = @{
        query = "quantum computing"
        max_results = 1
    } | ConvertTo-Json

    Write-Host "  Sending request... (may take 30-60 seconds)" -ForegroundColor Gray
    $result = Invoke-RestMethod -Uri "http://localhost:8000/rag/ingest/arxiv" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body `
        -TimeoutSec 120

    if ($result.success) {
        Write-Host "  ✓ ArXiv ingestion successful" -ForegroundColor Green
        Write-Host "    Papers loaded: $($result.documents_loaded)" -ForegroundColor Gray
        Write-Host "    Chunks created: $($result.chunks_created)" -ForegroundColor Gray
    } else {
        Write-Host "  ! Ingestion completed with warnings" -ForegroundColor Yellow
        Write-Host "    Errors: $($result.errors -join ', ')" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ✗ ArXiv ingestion failed" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    
    # Show last 20 lines of API logs
    Write-Host ""
    Write-Host "  Recent API logs:" -ForegroundColor Yellow
    docker compose logs api --tail=20
}
Write-Host ""

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "Diagnostic Complete" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan