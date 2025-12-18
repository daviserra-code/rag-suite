# Test OPC Studio scenario/apply endpoint

Write-Host "Testing scenario/apply endpoint..." -ForegroundColor Cyan

$body = @{
    line = "A01"
    station = "ST17"
    event = "MaterialShortage"
    duration_min = 30
    impact = @{
        availability = -0.4
        alarms = @("MAT_SHORT")
    }
} | ConvertTo-Json

Write-Host "Request body:" -ForegroundColor Yellow
Write-Host $body

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8040/scenario/apply" -Method Post -Body $body -ContentType "application/json"
    
    Write-Host ""
    Write-Host "SUCCESS!" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Yellow
    $response | ConvertTo-Json -Depth 5
    
} catch {
    Write-Host ""
    Write-Host "ERROR!" -ForegroundColor Red
    Write-Host $_.Exception.Message
}

# Check the updated state
Write-Host ""
Write-Host "Checking updated plant state..." -ForegroundColor Cyan

try {
    $snapshot = Invoke-RestMethod -Uri "http://localhost:8040/snapshot" -Method Get
    
    Write-Host "Line A01 Status:" -ForegroundColor Yellow
    $snapshot.data.lines.A01 | ConvertTo-Json -Depth 3
    
} catch {
    Write-Host "ERROR reading snapshot: $_" -ForegroundColor Red
}
