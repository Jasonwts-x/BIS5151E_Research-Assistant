# Query Evaluation Metrics
# PowerShell script to retrieve evaluation data

param(
    [Parameter(Mandatory=$false)]
    [int]$Limit = 10
)

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Evaluation Metrics Query" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check if database records exist
Write-Host "Checking database records..." -ForegroundColor Yellow
$recordCount = docker exec -it postgres psql -U research_assistant -d research_assistant -t -c "SELECT COUNT(*) FROM records;" 2>$null

if ($recordCount -match '\d+') {
    $count = [int]($recordCount.Trim())
    Write-Host "✓ Found $count evaluation records in database" -ForegroundColor Green
} else {
    Write-Host "✗ Could not query database" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Query via API
Write-Host "Fetching leaderboard via API..." -ForegroundColor Yellow
try {
    $leaderboard = Invoke-RestMethod -Uri "http://localhost:8502/metrics/leaderboard?limit=$Limit" -Method Get
    
    Write-Host "✓ API Response:" -ForegroundColor Green
    Write-Host "  Total Records: $($leaderboard.total_records)" -ForegroundColor White
    Write-Host ""
    
    if ($leaderboard.entries.Count -gt 0) {
        Write-Host "Latest Evaluations:" -ForegroundColor Cyan
        Write-Host ""
        
        foreach ($entry in $leaderboard.entries) {
            Write-Host "  Record ID: $($entry.record_id)" -ForegroundColor White
            Write-Host "  Query: $($entry.query)" -ForegroundColor Gray
            Write-Host "  Overall Score: $($entry.overall_score)" -ForegroundColor Yellow
            Write-Host "  Groundedness: $($entry.groundedness)" -ForegroundColor Yellow
            Write-Host "  Answer Relevance: $($entry.answer_relevance)" -ForegroundColor Yellow
            Write-Host "  Timestamp: $($entry.timestamp)" -ForegroundColor Gray
            Write-Host "  ----" -ForegroundColor DarkGray
        }
    } else {
        Write-Host "  No evaluation entries returned from API" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "✗ API request failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan