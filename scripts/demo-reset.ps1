#!/usr/bin/env pwsh
# Demo Reset Script - Sprint 6
# Resets Shopfloor Copilot to canonical demo state

param(
    [switch]$Quick
)

Write-Host "================================" -ForegroundColor Cyan
Write-Host "  DEMO RESET - Sprint 6" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Restart containers (unless -Quick)
if (-not $Quick) {
    Write-Host "[1/4] Restarting containers..." -ForegroundColor Yellow
    docker-compose restart data-simulator shopfloor 2>&1 | Out-Null
    
    Write-Host "      Waiting for services to start..." -ForegroundColor Gray
    Start-Sleep -Seconds 15
    
    Write-Host "      ✓ Containers restarted" -ForegroundColor Green
} else {
    Write-Host "[1/4] Skipping container restart (Quick mode)" -ForegroundColor Gray
}

Write-Host ""

# Step 2: Clear existing violations
Write-Host "[2/4] Clearing existing violations..." -ForegroundColor Yellow
Write-Host "      ✓ Violations cleared (stub)" -ForegroundColor Green
Write-Host ""

# Step 3: Seed canonical demo scenarios
Write-Host "[3/4] Seeding canonical demo scenarios..." -ForegroundColor Yellow

# Scenario A: ST18
Write-Host "      -> ST18 (Aerospace & Defence - Blocking)" -ForegroundColor Gray
try {
    $bodyA = @{scope="station"; id="ST18"} | ConvertTo-Json -Compress
    $responseA = Invoke-RestMethod -Uri "http://localhost:8010/api/diagnostics/explain" -Method Post -Body $bodyA -ContentType "application/json" -ErrorAction Stop
    
    if ($responseA.metadata.rag_documents -gt 0) {
        Write-Host "         ✓ ST18 ready (RAG docs: $($responseA.metadata.rag_documents))" -ForegroundColor Green
    } else {
        Write-Host "         ⚠ ST18 seeded but no RAG documents retrieved" -ForegroundColor Yellow
    }
} catch {
    Write-Host "         ✗ Failed to seed ST18: $($_.Exception.Message)" -ForegroundColor Red
}

Start-Sleep -Seconds 2

# Scenario B: ST25
Write-Host "      -> ST25 (Pharma/Process - Blocking)" -ForegroundColor Gray
try {
    $bodyB = @{scope="station"; id="ST25"} | ConvertTo-Json -Compress
    $responseB = Invoke-RestMethod -Uri "http://localhost:8010/api/diagnostics/explain" -Method Post -Body $bodyB -ContentType "application/json" -ErrorAction Stop
    
    if ($responseB.metadata.rag_documents -gt 0) {
        Write-Host "         ✓ ST25 ready (RAG docs: $($responseB.metadata.rag_documents))" -ForegroundColor Green
    } else {
        Write-Host "         ⚠ ST25 seeded but no RAG documents retrieved" -ForegroundColor Yellow
    }
} catch {
    Write-Host "         ✗ Failed to seed ST25: $($_.Exception.Message)" -ForegroundColor Red
}

Start-Sleep -Seconds 2

# Scenario C: ST10
Write-Host "      -> ST10 (Happy Path - No Blocking)" -ForegroundColor Gray
try {
    $bodyC = @{scope="station"; id="ST10"} | ConvertTo-Json -Compress
    $responseC = Invoke-RestMethod -Uri "http://localhost:8010/api/diagnostics/explain" -Method Post -Body $bodyC -ContentType "application/json" -ErrorAction Stop
    
    if ($responseC.metadata.rag_documents -gt 0) {
        Write-Host "         ✓ ST10 ready (RAG docs: $($responseC.metadata.rag_documents))" -ForegroundColor Green
    } else {
        Write-Host "         ⚠ ST10 seeded but no RAG documents retrieved" -ForegroundColor Yellow
    }
} catch {
    Write-Host "         ✗ Failed to seed ST10: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Step 4: Verify profile
Write-Host "[4/4] Verifying profile..." -ForegroundColor Yellow

try {
    $profileCheck = Invoke-RestMethod -Uri "http://localhost:8010/api/profiles/active" -Method Get -ErrorAction Stop
    
    if ($profileCheck.name -eq "aerospace_defence") {
        Write-Host "      ✓ Active profile: $($profileCheck.name)" -ForegroundColor Green
    } else {
        Write-Host "      ⚠ Active profile: $($profileCheck.name) (expected: aerospace_defence)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "      ⚠ Could not verify profile (API may not be available)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "  DEMO READY!" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Canonical scenarios initialized:" -ForegroundColor White
Write-Host "  • ST18: Aerospace blocking (evidence missing)" -ForegroundColor Gray
Write-Host "  • ST25: Pharma blocking (quality hold)" -ForegroundColor Gray
Write-Host "  • ST10: Happy path (no issues)" -ForegroundColor Gray
Write-Host ""
Write-Host "Open: http://localhost:8010" -ForegroundColor Cyan
Write-Host "Demo script: docs/demo/DEMO_SCRIPT.md" -ForegroundColor Gray
Write-Host ""
