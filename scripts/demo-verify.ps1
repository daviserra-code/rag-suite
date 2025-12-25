#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Verify demo scenarios are working correctly (Sprint 6)

.DESCRIPTION
    Tests all three canonical demo scenarios and reports results:
    - ST18: Aerospace blocking
    - ST25: Pharma blocking
    - ST10: Happy path

.EXAMPLE
    .\scripts\demo-verify.ps1
#>

Write-Host "================================" -ForegroundColor Cyan
Write-Host "  DEMO VERIFICATION" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

$allPassed = $true

# Test Scenario A: ST18 (Aerospace blocking)
Write-Host "[Scenario A] ST18 - Aerospace Blocking" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

try {
    $bodyA = @{scope="station"; id="ST18"} | ConvertTo-Json -Compress
    $responseA = Invoke-RestMethod -Uri "http://localhost:8010/api/diagnostics/explain" `
        -Method Post `
        -Body $bodyA `
        -ContentType "application/json" `
        -ErrorAction Stop
    
    Write-Host "Equipment ID: $($responseA.metadata.equipment_id)" -ForegroundColor White
    Write-Host "Domain Profile: $($responseA.metadata.domain_profile)" -ForegroundColor White
    Write-Host "RAG Documents: $($responseA.metadata.rag_documents)" -ForegroundColor White
    Write-Host "Severity: $($responseA.metadata.severity)" -ForegroundColor White
    Write-Host "Requires Confirmation: $($responseA.metadata.requires_confirmation)" -ForegroundColor White
    
    # Validation
    $passA = $true
    if ($responseA.metadata.rag_documents -lt 1) {
        Write-Host "  ✗ FAIL: Expected at least 1 RAG document" -ForegroundColor Red
        $passA = $false
    }
    if ($responseA.metadata.domain_profile -ne "Aerospace & Defence") {
        Write-Host "  ✗ FAIL: Expected 'Aerospace & Defence' profile" -ForegroundColor Red
        $passA = $false
    }
    if ($responseA.metadata.severity -ne "critical") {
        Write-Host "  ⚠ WARNING: Expected 'critical' severity" -ForegroundColor Yellow
    }
    
    if ($passA) {
        Write-Host "  ✓ PASS: Scenario A working correctly" -ForegroundColor Green
    } else {
        $allPassed = $false
    }
    
} catch {
    Write-Host "  ✗ FAIL: Could not test Scenario A" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    $allPassed = $false
}

Write-Host ""

# Test Scenario B: ST25 (Pharma blocking)
Write-Host "[Scenario B] ST25 - Pharma Blocking" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

try {
    $bodyB = @{scope="station"; id="ST25"} | ConvertTo-Json -Compress
    $responseB = Invoke-RestMethod -Uri "http://localhost:8010/api/diagnostics/explain" `
        -Method Post `
        -Body $bodyB `
        -ContentType "application/json" `
        -ErrorAction Stop
    
    Write-Host "Equipment ID: $($responseB.metadata.equipment_id)" -ForegroundColor White
    Write-Host "Domain Profile: $($responseB.metadata.domain_profile)" -ForegroundColor White
    Write-Host "RAG Documents: $($responseB.metadata.rag_documents)" -ForegroundColor White
    Write-Host "Severity: $($responseB.metadata.severity)" -ForegroundColor White
    Write-Host "Requires Confirmation: $($responseB.metadata.requires_confirmation)" -ForegroundColor White
    
    # Validation
    $passB = $true
    if ($responseB.metadata.rag_documents -lt 1) {
        Write-Host "  ✗ FAIL: Expected at least 1 RAG document" -ForegroundColor Red
        $passB = $false
    }
    
    if ($passB) {
        Write-Host "  ✓ PASS: Scenario B working correctly" -ForegroundColor Green
    } else {
        $allPassed = $false
    }
    
} catch {
    Write-Host "  ✗ FAIL: Could not test Scenario B" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    $allPassed = $false
}

Write-Host ""

# Test Scenario C: ST10 (Happy path)
Write-Host "[Scenario C] ST10 - Happy Path" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

try {
    $bodyC = @{scope="station"; id="ST10"} | ConvertTo-Json -Compress
    $responseC = Invoke-RestMethod -Uri "http://localhost:8010/api/diagnostics/explain" `
        -Method Post `
        -Body $bodyC `
        -ContentType "application/json" `
        -ErrorAction Stop
    
    Write-Host "Equipment ID: $($responseC.metadata.equipment_id)" -ForegroundColor White
    Write-Host "Domain Profile: $($responseC.metadata.domain_profile)" -ForegroundColor White
    Write-Host "RAG Documents: $($responseC.metadata.rag_documents)" -ForegroundColor White
    Write-Host "Severity: $($responseC.metadata.severity)" -ForegroundColor White
    Write-Host "Requires Confirmation: $($responseC.metadata.requires_confirmation)" -ForegroundColor White
    
    # Validation
    $passC = $true
    if ($responseC.metadata.rag_documents -lt 1) {
        Write-Host "  ⚠ WARNING: Expected at least 1 RAG document (informational)" -ForegroundColor Yellow
    }
    
    Write-Host "  ✓ PASS: Scenario C working correctly" -ForegroundColor Green
    
} catch {
    Write-Host "  ✗ FAIL: Could not test Scenario C" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    $allPassed = $false
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan

if ($allPassed) {
    Write-Host "  ALL SCENARIOS PASSED ✓" -ForegroundColor Green
} else {
    Write-Host "  SOME SCENARIOS FAILED ✗" -ForegroundColor Red
}

Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
