# Test backend API (PowerShell version)

Write-Host "Testing Backend..." -ForegroundColor Cyan

# Test 1: Health check
Write-Host "`n1. Health Check" -ForegroundColor Yellow
$health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
Write-Host "Status: $($health.status)" -ForegroundColor Green
Write-Host "RunPod Connected: $($health.runpod_connected)" -ForegroundColor Green

# Test 2: Create job
Write-Host "`n2. Creating Test Job" -ForegroundColor Yellow
$body = @{
    type = "RENDER"
    params = @{
        prompt = "test video"
        duration = 5
    }
} | ConvertTo-Json

$job = Invoke-RestMethod -Uri "http://localhost:8000/jobs" -Method Post -Body $body -ContentType "application/json"
Write-Host "Job ID: $($job.job_id)" -ForegroundColor Green
Write-Host "Status: $($job.status)" -ForegroundColor Green

# Test 3: Check job status
Write-Host "`n3. Checking Job Status" -ForegroundColor Yellow
Start-Sleep -Seconds 2
$status = Invoke-RestMethod -Uri "http://localhost:8000/jobs/$($job.job_id)" -Method Get
Write-Host "Status: $($status.status)" -ForegroundColor Green
Write-Host "Progress: $($status.progress)%" -ForegroundColor Green

Write-Host "`nTests Complete!" -ForegroundColor Cyan
