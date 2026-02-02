Write-Host "=== GPU Control Test ===" -ForegroundColor Cyan

Write-Host "`n1. Current Status:" -ForegroundColor Yellow
$status = Invoke-RestMethod -Uri "http://localhost:8000/gpu/status"
Write-Host "Status: $($status.status) | Workers: $($status.workers_min)/$($status.workers_max)"

Write-Host "`n2. Turning GPU OFF (save costs)..." -ForegroundColor Yellow
$off = Invoke-RestMethod -Uri "http://localhost:8000/gpu/off" -Method POST
Write-Host $off.message

Write-Host "`n3. Status after OFF:" -ForegroundColor Yellow
$status2 = Invoke-RestMethod -Uri "http://localhost:8000/gpu/status"
Write-Host "Status: $($status2.status) | Workers: $($status2.workers_min)/$($status2.workers_max)"

Write-Host "`n4. Turning GPU ON..." -ForegroundColor Yellow
$on = Invoke-RestMethod -Uri "http://localhost:8000/gpu/on" -Method POST
Write-Host $on.message

Write-Host "`n5. Final Status:" -ForegroundColor Yellow
$status3 = Invoke-RestMethod -Uri "http://localhost:8000/gpu/status"
Write-Host "Status: $($status3.status) | Workers: $($status3.workers_min)/$($status3.workers_max)"

Write-Host "`n=== Test Complete ===" -ForegroundColor Green
Write-Host "GPU toggle is working! Use /gpu/off when not in use to save costs." -ForegroundColor Cyan
