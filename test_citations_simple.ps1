#!/usr/bin/env pwsh
# Simple Citation Test - Sprint 5

Write-Host "="*80 -ForegroundColor Cyan
Write-Host "SPRINT 5 - CITATION DISCIPLINE TEST" -ForegroundColor Cyan
Write-Host "="*80 -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8010"

# Test with aerospace_defence profile
Write-Host "Testing aerospace_defence profile (ST22 automotive downtime)..." -ForegroundColor Yellow
Write-Host ""

$body = @{
    scope = "station"
    id = "ST22"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/diagnostics/explain" `
        -Method POST `
        -Body $body `
        -ContentType "application/json" `
        -TimeoutSec 30
    
    Write-Host "Response received!" -ForegroundColor Green
    Write-Host ""
    
    # Combine all sections
    $allText = @(
        $response.what_is_happening,
        $response.why_this_is_happening,
        $response.what_to_do_now,
        $response.what_to_check_next
    ) -join "`n`n"
    
    # Check for citations
    Write-Host "WHAT IS HAPPENING:" -ForegroundColor Cyan
    Write-Host $response.what_is_happening
    Write-Host ""
    
    Write-Host "WHY THIS IS HAPPENING:" -ForegroundColor Cyan
    Write-Host $response.why_this_is_happening
    Write-Host ""
    
    Write-Host "WHAT TO DO NOW:" -ForegroundColor Cyan
    Write-Host $response.what_to_do_now
    Write-Host ""
    
    Write-Host "WHAT TO CHECK NEXT:" -ForegroundColor Cyan
    Write-Host $response.what_to_check_next
    Write-Host ""
    
    # Search for citations
    $hasCitations = $false
    if ($allText -match "According to" -or $allText -match "As per" -or $allText -match "As specified in") {
        $hasCitations = $true
    }
    
    # Extract document IDs
    $matches = [regex]::Matches($allText, '\b(WI-\w+-[\w-]+|SOP-[\w-]+|CAL-[\w-]+|DOWNTIME-\d+|MAINT-[\w-]+)\b')
    $citedDocs = @()
    foreach ($match in $matches) {
        $citedDocs += $match.Value
    }
    $citedDocs = $citedDocs | Select-Object -Unique
    
    Write-Host "="*80 -ForegroundColor Cyan
    Write-Host "CITATION ANALYSIS:" -ForegroundColor Cyan
    Write-Host ""
    
    if ($hasCitations) {
        Write-Host "[PASS] Citation keywords found" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] No citation keywords found" -ForegroundColor Red
    }
    
    if ($citedDocs.Count -gt 0) {
        Write-Host "[PASS] Document IDs found: $($citedDocs.Count)" -ForegroundColor Green
        Write-Host ""
        Write-Host "Cited documents:" -ForegroundColor Yellow
        foreach ($doc in $citedDocs) {
            Write-Host "  - $doc" -ForegroundColor Cyan
        }
    } else {
        Write-Host "[FAIL] No document IDs found" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "="*80 -ForegroundColor Cyan
    
    # Check metadata
    if ($response.metadata) {
        Write-Host "METADATA:" -ForegroundColor Cyan
        Write-Host "  Domain Profile: $($response.metadata.domain_profile)"
        Write-Host "  RAG Documents: $($response.metadata.rag_documents)"
        Write-Host ""
    }
    
} catch {
    Write-Host "[ERROR] API call failed:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Full error:" -ForegroundColor Yellow
    Write-Host $_ -ForegroundColor Yellow
}
