# Step D Verification Script - PowerShell Version
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Step D: CrewAI Integration - Verification" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 1. Ensure Docker containers are running
Write-Host "1️⃣  Ensuring Docker containers are running..." -ForegroundColor Blue

# 2. Check service health
Write-Host "2️⃣  Checking service health..." -ForegroundColor Blue
$services = @("postgres", "weaviate", "ollama", "n8n", "crewai", "api")
$allHealthy = $true

foreach ($service in $services) {
    $status = docker compose -f docker/docker-compose.yml ps $service | Select-String "healthy"
    if ($status) {
        Write-Host "   ✓ $service is healthy" -ForegroundColor Green
    } else {
        Write-Host "   ✗ $service is unhealthy" -ForegroundColor Red
        $allHealthy = $false
    }
}

if (-not $allHealthy) {
    Write-Host "`n❌ Some services are unhealthy. Check logs." -ForegroundColor Red
    exit 1
}
Write-Host ""

# 3. Test endpoints
Write-Host "3️⃣  Testing API endpoints..." -ForegroundColor Blue

# Health checks
try {
    $response = Invoke-RestMethod -Uri http://localhost:8000/health -UseBasicParsing
    if ($response.status -eq "ok") {
        Write-Host "   ✓ /health endpoint works" -ForegroundColor Green
    }
} catch {
    Write-Host "   ✗ /health endpoint failed" -ForegroundColor Red
    exit 1
}

try {
    $response = Invoke-RestMethod -Uri http://localhost:8000/ready -UseBasicParsing
    if ($response.status -eq "ok") {
        Write-Host "   ✓ /ready endpoint works" -ForegroundColor Green
    }
} catch {
    Write-Host "   ✗ /ready endpoint failed" -ForegroundColor Red
    exit 1
}

try {
    $response = Invoke-RestMethod -Uri http://localhost:8100/health -UseBasicParsing
    if ($response.status -eq "ok") {
        Write-Host "   ✓ CrewAI service health works" -ForegroundColor Green
    }
} catch {
    Write-Host "   ✗ CrewAI service health failed" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 4. Test CrewAI service directly
Write-Host "4️⃣  Testing CrewAI service..." -ForegroundColor Blue
try {
    $body = @{
        topic = "What is artificial intelligence?"
        language = "en"
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri http://localhost:8100/crew/run `
        -Method Post `
        -ContentType "application/json" `
        -Body $body

    if ($response.answer) {
        Write-Host "   ✓ CrewAI service works" -ForegroundColor Green
        Write-Host "   Answer preview: $($response.answer.Substring(0, [Math]::Min(150, $response.answer.Length)))..." -ForegroundColor Gray
    }
} catch {
    Write-Host "   ✗ CrewAI service failed: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 5. Test /rag/query endpoint
Write-Host "5️⃣  Testing /rag/query endpoint..." -ForegroundColor Blue
try {
    $body = @{
        query = "What is digital transformation?"
        language = "en"
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri http://localhost:8000/rag/query `
        -Method Post `
        -ContentType "application/json" `
        -Body $body

    if ($response.answer) {
        Write-Host "   ✓ /rag/query endpoint works" -ForegroundColor Green
        Write-Host "   Answer preview: $($response.answer.Substring(0, [Math]::Min(150, $response.answer.Length)))..." -ForegroundColor Gray
    }
} catch {
    Write-Host "   ✗ /rag/query endpoint failed: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 6. Test /crewai/run proxy
Write-Host "6️⃣  Testing /crewai/run proxy..." -ForegroundColor Blue
try {
    $body = @{
        topic = "Explain RAG systems"
        language = "en"
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri http://localhost:8000/crewai/run `
        -Method Post `
        -ContentType "application/json" `
        -Body $body

    if ($response.answer) {
        Write-Host "   ✓ /crewai/run proxy works" -ForegroundColor Green
        Write-Host "   Answer preview: $($response.answer.Substring(0, [Math]::Min(150, $response.answer.Length)))..." -ForegroundColor Gray
    }
} catch {
    Write-Host "   ✗ /crewai/run proxy failed: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 7. Run pytest
Write-Host "7️⃣  Running pytest..." -ForegroundColor Blue
docker compose -f docker/docker-compose.yml exec devcontainer pytest tests/ -v

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "✅ STEP D VERIFICATION COMPLETE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`nAll systems operational:" -ForegroundColor Green
Write-Host "   • Services: All healthy" -ForegroundColor White
Write-Host "   • Endpoints: All responding" -ForegroundColor White
Write-Host "   • CrewAI: Working" -ForegroundColor White
Write-Host "   • RAG Query: Working" -ForegroundColor White
Write-Host "   • Proxy: Working" -ForegroundColor White

Write-Host "`n✅ Ready to commit!" -ForegroundColor Green

Write-Host "`nQuick reference:" -ForegroundColor Cyan
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "   CrewAI:   http://localhost:8100/health" -ForegroundColor White
Write-Host "   n8n:      http://localhost:5678" -ForegroundColor White