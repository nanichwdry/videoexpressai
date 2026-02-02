# Test GPU Control Endpoints

Write-Host "=== GPU Control Test ===" -ForegroundColor Cyan

# Check status
Write-Host "`n1. Checking GPU status..." -ForegroundColor Yellow
$status = Invoke-WebRequest -Uri http://localhost:8000/gpu/status
Write-Host $status.Content

# Turn ON
Write-Host "`n2. Turning GPU ON..." -ForegroundColor Yellow
$on = Invoke-WebRequest -Uri http://localhost:8000/gpu/on -Method POST
Write-Host $on.Content

# Check status again
Write-Host "`n3. Checking status after ON..." -ForegroundColor Yellow
$status2 = Invoke-WebRequest -Uri http://localhost:8000/gpu/status
Write-Host $status2.Content

# Turn OFF
Write-Host "`n4. Turning GPU OFF..." -ForegroundColor Yellow
$off = Invoke-WebRequest -Uri http://localhost:8000/gpu/off -Method POST
Write-Host $off.Content

# Final status
Write-Host "`n5. Final status..." -ForegroundColor Yellow
$status3 = Invoke-WebRequest -Uri http://localhost:8000/gpu/status
Write-Host $status3.Content

Write-Host "`n=== Test Complete ===" -ForegroundColor Green
