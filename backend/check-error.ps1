# Check job error details
$job = Invoke-RestMethod -Uri "http://localhost:8000/jobs/c76ed6a3-7733-4f11-a797-96bf102ff1e1" -Method Get
Write-Host "Status: $($job.status)" -ForegroundColor Yellow
Write-Host "Progress: $($job.progress)%" -ForegroundColor Yellow
if ($job.error) {
    Write-Host "`nError Code: $($job.error.code)" -ForegroundColor Red
    Write-Host "Error Message: $($job.error.message)" -ForegroundColor Red
}
