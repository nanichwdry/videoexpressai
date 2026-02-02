Write-Host "Testing GPU Control..." -ForegroundColor Cyan

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/gpu/status" -Method Get
    Write-Host "Status: $($response.status)" -ForegroundColor Green
    Write-Host "Workers Min: $($response.workers_min)"
    Write-Host "Workers Max: $($response.workers_max)"
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host "Make sure backend is running: python -m uvicorn main:app --reload --port 8000"
}
